"""API routes for RAG management."""
import logging
import datetime
from fastapi import APIRouter, HTTPException, Request
from pathlib import Path

# from ..utils.pdf_utils import PDFProcessor # Se inyectará desde el estado de la app
# from ..rag.retrieval.retriever import RAGRetriever # Se inyectará desde el estado de la app

# Importar modelos Pydantic desde el módulo centralizado
from ...schemas import (
    RAGStatusResponse,
    ClearRAGResponse,
    RAGStatusPDFDetail,
    RAGStatusVectorStoreDetail # Asegurar que PDFListItem se importa si RAGStatusPDFDetail no lo redefine todo
)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/rag-status", response_model=RAGStatusResponse)
async def rag_status(request: Request):
    """Endpoint para obtener el estado actual del RAG."""
    pdf_manager = request.app.state.pdf_file_manager
    try:
        pdfs_raw = await pdf_manager.list_pdfs()
        
        # Formatear los PDFs al formato esperado por el esquema
        pdf_details = [
            RAGStatusPDFDetail(
                filename=p["filename"],
                path=p["path"],
                size=p["size"],
                last_modified=datetime.datetime.fromtimestamp(p["last_modified"])
            ) for p in pdfs_raw
        ]
        
        # Usar la ruta correcta del vector store desde las settings de la aplicación
        vector_store_full_path = Path(request.app.state.settings.vector_store_path).resolve()
        vector_store_exists = vector_store_full_path.exists()
        vector_store_size = 0
        if vector_store_exists:
            # Calcular el tamaño del directorio del vector store
            vector_store_size = sum(f.stat().st_size for f in vector_store_full_path.rglob("*") if f.is_file())
        
        vector_store_detail = RAGStatusVectorStoreDetail(
            path=str(vector_store_full_path),
            exists=vector_store_exists,
            size=vector_store_size
        )
        
        # Obtener el conteo real de documentos (chunks) del vector store
        vector_store_documents_count = await request.app.state.vector_store.get_document_count()

        return RAGStatusResponse(
            pdfs=pdf_details,
            vector_store=vector_store_detail,
            total_documents=vector_store_documents_count # Ahora refleja el conteo real del vector store
        )
    except Exception as e:
        logger.error(f"Error al obtener estado RAG: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno del servidor al obtener estado RAG: {str(e)}")

@router.post("/clear-rag", response_model=ClearRAGResponse)
async def clear_rag(request: Request):
    """Endpoint para limpiar el RAG."""
    pdf_manager = request.app.state.pdf_file_manager
    rag_retriever = request.app.state.rag_retriever
    try:
        logger.info("Iniciando limpieza del RAG...")
        
        rag_retriever.clear()
        logger.info("Vector store limpiado")
        
        clear_result = await pdf_manager.clear_all_pdfs()
        logger.info("Directorio de PDFs limpiado")
        
        pdfs_after_clear = await pdf_manager.list_pdfs()
        vector_store_path = Path(pdf_manager.pdf_dir).parent / "vector_store"
        vector_store_size = 0
        if vector_store_path.exists():
            vector_store_size = sum(f.stat().st_size for f in vector_store_path.rglob("*") if f.is_file())

        status_val = "success"
        message_val = "RAG limpiado exitosamente"

        if clear_result["errors_count"] > 0 or vector_store_size > 0:
            logger.warning("Algunos archivos no se pudieron limpiar completamente del RAG.")
            status_val = "warning"
            message_val = "RAG limpiado parcialmente. Algunos archivos o datos del vector store no se pudieron eliminar."
        
        return ClearRAGResponse(
            status=status_val,
            message=message_val,
            remaining_pdfs=len(pdfs_after_clear),
            vector_store_size=vector_store_size
        )
    except Exception as e:
        logger.error(f"Error al limpiar RAG: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno del servidor al limpiar RAG: {str(e)}") 