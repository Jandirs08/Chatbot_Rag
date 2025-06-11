"""API routes for chat management."""
import logging
import uuid
import json
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

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