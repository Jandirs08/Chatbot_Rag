"""API routes for chat management."""
import logging
import uuid
import json
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
import pandas as pd
from io import BytesIO
from datetime import datetime

# Importar modelos Pydantic
from .schemas import ( # Cambio aquí: ...schemas -> .schemas
    # ChatRequest se usaría si el body se parseara con Pydantic antes,
    # pero aquí se lee data = await request.json() directamente.
    # Para consistencia, podríamos definir un ChatStreamRequest si el input es complejo.
    # Por ahora, se mantiene la lectura directa del JSON.
    StreamEventData, # Para la estructura DENTRO del stream
    ClearHistoryResponse,
    ChatRequest # Para validación de la entrada del endpoint de stream si se decide usarlo
)

from ....database.mongodb import MongodbClient

# from ..chat.manager import ChatManager # Se inyectará desde el estado de la app
# from ..rag.retrieval.retriever import RAGRetriever # Se inyectará desde el estado de la app

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/stream_log")
async def chat_stream_log(request: Request):
    """Endpoint para chat con streaming y logging."""
    chat_manager = request.app.state.chat_manager
    rag_retriever = request.app.state.rag_retriever
    bot = request.app.state.bot_instance
    
    try:
        # Verificar si el bot está activo
        if not bot.is_active:
            raise HTTPException(
                status_code=503,
                detail="El bot está desactivado actualmente"
            )
            
        data = await request.json()
        # Validar con Pydantic ChatRequest si queremos ser estrictos con la entrada
        try:
            chat_input = ChatRequest(**data)
        except Exception as pydantic_error:
            logger.error(f"Error de validación en la entrada de chat_stream_log: {pydantic_error}")
            raise HTTPException(status_code=422, detail=f"Cuerpo de la solicitud inválido: {pydantic_error}")

        input_text = chat_input.input
        conversation_id = chat_input.conversation_id or str(uuid.uuid4()) # Usar el default de Pydantic o generar uno
        
        if not input_text:
            # ChatRequest ya lo valida con Field(..., description="User message")
            raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío")
        
        logger.info(f"Recibida solicitud de chat: '{input_text}' para conversación {conversation_id}")
        
        # La lógica de RAG (retrieve_documents y format_context) ahora está dentro de ChatManager.generate_response
        # por lo que no es necesario hacerlo aquí.
        # relevant_docs = await rag_retriever.retrieve_documents(input_text)
        # logger.info(f"Documentos relevantes encontrados: {len(relevant_docs)}")
        # context = rag_retriever.format_context_from_documents(relevant_docs)
        # logger.info(f"Contexto formateado: {len(context)} caracteres")
        
        # Llamar a ChatManager solo con input_text y conversation_id
        response_content = await chat_manager.generate_response(input_text, conversation_id)
        logger.info("Respuesta generada por ChatManager")
        
        # Construir el objeto StreamEventData
        response_data_obj = StreamEventData(
            streamed_output=response_content,
            # ops no se usa en esta implementación simple de stream, LangServe los añade.
            # Si esta ruta debe emular LangServe, se necesitaría más lógica aquí.
            # Por ahora, se omite 'ops' o se deja None según el modelo Pydantic.
            ops=None 
        )
        
        async def generate():
            try:
                # Enviar respuesta inicial (en formato de evento Server-Sent Event)
                yield f"data: {response_data_obj.model_dump_json()}\n\n"
                # Enviar evento de finalización
                yield "event: end\ndata: {}\n\n"
            except Exception as e_stream:
                logger.error(f"Error en streaming: {str(e_stream)}", exc_info=True)
                # Para errores durante el stream, es difícil enviar un JSONResponse normal.
                # Se podría enviar un evento de error dentro del stream.
                error_event_data = StreamEventData(
                    streamed_output="Lo siento, hubo un error al procesar tu solicitud durante el streaming.",
                    ops=None
                )
                yield f"event: error\ndata: {error_event_data.model_dump_json()}\n\n"
                yield "event: end\ndata: {}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except HTTPException as http_exc:
        logger.error(f"Error HTTP en chat_stream_log: {http_exc.detail}")
        raise # Re-lanzar para que FastAPI la maneje como JSONResponse
    except Exception as e:
        logger.error(f"Error general en chat_stream_log: {str(e)}", exc_info=True)
        # Para errores antes de iniciar el stream, se puede devolver JSONResponse
        # Esto requiere que el import de JSONResponse esté presente.
        from fastapi.responses import JSONResponse # Importación local para este bloque
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error interno del servidor en chat: {str(e)}"}
        )

@router.post("/clear/{conversation_id}", response_model=ClearHistoryResponse)
async def clear_history(request: Request, conversation_id: str):
    """Endpoint para limpiar el historial de una conversación."""
    chat_manager = request.app.state.chat_manager
    try:
        if hasattr(chat_manager, 'db') and hasattr(chat_manager.db, 'clear_conversation'):
            await chat_manager.db.clear_conversation(conversation_id)
            return ClearHistoryResponse(message="Historial limpiado exitosamente")
        else:
            logger.error("Error: chat_manager.db o clear_conversation no están disponibles.")
            raise HTTPException(status_code=500, detail="Error interno del servidor: Configuración de base de datos incorrecta.")
    except Exception as e:
        logger.error(f"Error al limpiar historial '{conversation_id}': {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno del servidor al limpiar historial: {str(e)}")

@router.get("/export-conversations")
async def export_conversations(request: Request):
    """
    Exporta todas las conversaciones a un archivo Excel.
    Todas las conversaciones se muestran en una sola hoja, agrupadas por conversation_id.
    """
    try:
        # Usar la instancia de MongoDB del chat_manager
        chat_manager = request.app.state.chat_manager
        db = chat_manager.db
        
        # Obtener todas las conversaciones
        cursor = db.messages.find({}).sort([("conversation_id", 1), ("timestamp", 1)])
        messages = await cursor.to_list(length=None)
        
        if not messages:
            raise HTTPException(status_code=404, detail="No se encontraron conversaciones para exportar")
        
        # Crear DataFrame con los mensajes
        df = pd.DataFrame(messages)
        
        # Crear un archivo Excel en memoria
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Ordenar por conversation_id y timestamp
            df = df.sort_values(['conversation_id', 'timestamp'])
            
            # Formatear timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Renombrar columnas
            df = df.rename(columns={
                'conversation_id': 'ID Conversación',
                'timestamp': 'Fecha y Hora',
                'role': 'Rol',
                'content': 'Mensaje'
            })
            
            # Reordenar columnas
            df = df[['ID Conversación', 'Fecha y Hora', 'Rol', 'Mensaje']]
            
            # Escribir en una sola hoja
            df.to_excel(writer, sheet_name='Conversaciones', index=False)
            
            # Obtener el workbook y la hoja
            workbook = writer.book
            worksheet = writer.sheets['Conversaciones']
            
            # Definir formatos
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#D9E1F2',
                'border': 1
            })
            
            conversation_format = workbook.add_format({
                'bg_color': '#E2EFDA',
                'border': 1
            })
            
            message_format = workbook.add_format({
                'border': 1,
                'text_wrap': True
            })
            
            # Aplicar formato al encabezado
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Aplicar formatos a las celdas
            current_conversation = None
            for row_num, row in enumerate(df.itertuples(), start=1):
                # Si es una nueva conversación, aplicar formato de conversación
                if row[1] != current_conversation:
                    current_conversation = row[1]
                    worksheet.write(row_num, 0, row[1], conversation_format)
                else:
                    worksheet.write(row_num, 0, row[1], message_format)
                
                # Escribir el resto de las columnas
                worksheet.write(row_num, 1, row[2], message_format)
                worksheet.write(row_num, 2, row[3], message_format)
                worksheet.write(row_num, 3, row[4], message_format)
            
            # Ajustar ancho de columnas
            worksheet.set_column('A:A', 36)  # ID Conversación
            worksheet.set_column('B:B', 20)  # Fecha y Hora
            worksheet.set_column('C:C', 10)  # Rol
            worksheet.set_column('D:D', 100)  # Mensaje
            
            # Agregar filtros
            worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
            
            # Congelar la primera fila
            worksheet.freeze_panes(1, 0)
        
        output.seek(0)
        
        # Generar nombre de archivo con fecha actual
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'conversaciones_{current_time}.xlsx'
        
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
        
    except Exception as e:
        logger.error(f"Error al exportar conversaciones: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al exportar conversaciones: {str(e)}")

@router.get("/stats")
async def get_stats(request: Request):
    """
    Obtiene estadísticas de consultas, usuarios activos y PDFs cargados.
    """
    try:
        chat_manager = request.app.state.chat_manager
        db = chat_manager.db
        pdf_file_manager = request.app.state.pdf_file_manager
        
        # Obtener total de consultas (mensajes)
        total_queries = await db.messages.count_documents({})
        
        # Obtener usuarios únicos (basado en conversation_id)
        unique_users = await db.messages.distinct("conversation_id")
        total_users = len(unique_users)
        
        # Obtener total de PDFs del RAG
        pdfs = await pdf_file_manager.list_pdfs()
        total_pdfs = len(pdfs)
        
        return {
            "total_queries": total_queries,
            "total_users": total_users,
            "total_pdfs": total_pdfs
        }
        
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}") 