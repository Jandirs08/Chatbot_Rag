"""PDF Processor for managing PDF operations."""
import logging
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from ..storage.documents.pdf_manager import PDFManager
from .pdf_loader import PDFContentLoader

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Clase para procesar y gestionar PDFs."""
    
    def __init__(self, pdf_file_manager: PDFManager, pdf_content_loader: PDFContentLoader):
        """Inicializa el procesador de PDFs.
        
        Args:
            pdf_file_manager: Gestor de archivos PDF.
            pdf_content_loader: Cargador de contenido PDF.
        """
        self.pdf_file_manager = pdf_file_manager
        self.pdf_content_loader = pdf_content_loader
        logger.info("PDFProcessor inicializado")

    async def list_pdfs(self) -> List[Dict[str, Any]]:
        """Lista todos los PDFs disponibles.
        
        Returns:
            Lista de diccionarios con información de los PDFs.
        """
        try:
            return await self.pdf_file_manager.list_pdfs()
        except Exception as e:
            logger.error(f"Error al listar PDFs: {str(e)}", exc_info=True)
            raise

    def get_vector_store_info(self) -> Dict[str, Any]:
        """Obtiene información sobre el vector store.
        
        Returns:
            Diccionario con información del vector store.
        """
        try:
            vector_store_path = Path(self.pdf_file_manager.pdf_dir).parent / "vector_store"
            exists = vector_store_path.exists()
            size = 0
            if exists:
                size = sum(f.stat().st_size for f in vector_store_path.rglob("*") if f.is_file())
            
            return {
                "path": vector_store_path,
                "exists": exists,
                "size": size
            }
        except Exception as e:
            logger.error(f"Error al obtener información del vector store: {str(e)}", exc_info=True)
            raise

    async def clear_pdfs(self) -> Dict[str, Any]:
        """Limpia todos los PDFs del directorio.
        
        Returns:
            Diccionario con resultados de la operación.
        """
        try:
            return await self.pdf_file_manager.clear_all_pdfs()
        except Exception as e:
            logger.error(f"Error al limpiar PDFs: {str(e)}", exc_info=True)
            raise

    async def process_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """Procesa un PDF específico.
        
        Args:
            pdf_path: Ruta al archivo PDF.
            
        Returns:
            Diccionario con información del procesamiento.
        """
        try:
            # Cargar y dividir el PDF
            chunks = self.pdf_content_loader.load_and_split_pdf(pdf_path)
            
            return {
                "filename": pdf_path.name,
                "chunks": len(chunks),
                "processed_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error al procesar PDF {pdf_path.name}: {str(e)}", exc_info=True)
            raise 