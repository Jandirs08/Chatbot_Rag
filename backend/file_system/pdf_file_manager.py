"""Utilidades para la gestión de archivos PDF en el sistema de archivos."""
import os
import aiofiles
import asyncio
from pathlib import Path
from typing import List, Optional, Dict
from fastapi import UploadFile, HTTPException
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial

logger = logging.getLogger(__name__)

class PDFFileManager:
    """Clase para manejar las operaciones de archivos PDF en el sistema de archivos."""
    
    def __init__(self, base_dir: Optional[Path] = None, max_workers: int = 4):
        """Inicializa el gestor de archivos PDF.
        
        Args:
            base_dir: Directorio base desde donde se calculará la ruta de pdf_dir.
            max_workers: Número máximo de workers para operaciones paralelas.
        """
        effective_base_dir = base_dir or Path(__file__).resolve().parent.parent.parent 
        self.pdf_dir = effective_base_dir / "data" / "pdfs"
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._ensure_directories()
        
    def _ensure_directories(self) -> None:
        """Asegura que el directorio de PDFs exista."""
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        
    async def save_pdf(self, file: UploadFile, chunk_size: int = 1024 * 1024) -> Path:
        """Guarda un archivo PDF de forma asíncrona y eficiente.
        
        Args:
            file: Archivo PDF a guardar.
            chunk_size: Tamaño del chunk para lectura/escritura (1MB por defecto).
            
        Returns:
            Path al archivo guardado.
        """
        if not file.filename.lower().endswith('.pdf'):
            logger.warning(f"Intento de subir archivo no PDF: {file.filename}")
            raise HTTPException(status_code=400, detail="El archivo debe ser un PDF.")
        
        file_path = self.pdf_dir / Path(file.filename).name
        
        try:
            async with aiofiles.open(file_path, 'wb') as out_file:
                while content := await file.read(chunk_size):
                    await out_file.write(content)
                    
            logger.info(f"PDF guardado exitosamente: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error al guardar PDF '{file.filename}': {str(e)}", exc_info=True)
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(status_code=500, detail=f"Error interno al guardar el PDF: {str(e)}")
            
    async def list_pdfs(self) -> List[Dict]:
        """Lista los PDFs disponibles de forma asíncrona.
        
        Returns:
            Lista de diccionarios con información de los PDFs.
        """
        if not self.pdf_dir.exists():
            return []
            
        try:
            # Usar ThreadPoolExecutor para operaciones de sistema de archivos
            loop = asyncio.get_event_loop()
            pdf_files = list(self.pdf_dir.glob("*.pdf"))
            
            async def get_file_info(pdf_file: Path) -> Optional[Dict]:
                try:
                    stat_info = await loop.run_in_executor(self.executor, pdf_file.stat)
                    return {
                        "filename": pdf_file.name,
                        "path": str(pdf_file.resolve()),
                        "size": stat_info.st_size,
                        "last_modified": stat_info.st_mtime
                    }
                except Exception as e:
                    logger.warning(f"Error al obtener info de {pdf_file}: {e}")
                    return None
            
            # Procesar archivos en paralelo
            tasks = [get_file_info(pdf) for pdf in pdf_files]
            results = await asyncio.gather(*tasks)
            
            # Filtrar resultados None
            return [r for r in results if r is not None]
            
        except Exception as e:
            logger.error(f"Error al listar PDFs: {str(e)}", exc_info=True)
            return []
            
    async def delete_pdf(self, filename: str) -> bool:
        """Elimina un PDF específico de forma asíncrona.
        
        Args:
            filename: Nombre del archivo a eliminar.
            
        Returns:
            True si se eliminó correctamente.
        """
        if not filename:
            raise HTTPException(status_code=400, detail="Nombre de archivo no puede estar vacío.")

        file_path = self.pdf_dir / Path(filename).name
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"PDF '{filename}' no encontrado.")
            
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.executor, file_path.unlink)
            logger.info(f"PDF eliminado: {filename}")
            return True
        except Exception as e:
            logger.error(f"Error al eliminar PDF '{filename}': {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error al eliminar el PDF: {str(e)}")
            
    async def clear_all_pdfs(self) -> Dict:
        """Limpia todos los PDFs de forma asíncrona y paralela.
        
        Returns:
            Diccionario con resultados de la operación.
        """
        if not self.pdf_dir.exists():
            return {"deleted_count": 0, "errors_count": 0, "error_details": []}
            
        deleted_count = 0
        errors_count = 0
        errors_details = []
        
        try:
            pdf_files = list(self.pdf_dir.glob("*.pdf"))
            
            async def delete_file(pdf_file: Path) -> tuple:
                try:
                    await asyncio.get_event_loop().run_in_executor(self.executor, pdf_file.unlink)
                    return True, None
                except Exception as e:
                    return False, (pdf_file.name, str(e))
            
            # Eliminar archivos en paralelo
            tasks = [delete_file(pdf) for pdf in pdf_files]
            results = await asyncio.gather(*tasks)
            
            for success, error in results:
                if success:
                    deleted_count += 1
                else:
                    errors_count += 1
                    if error:
                        errors_details.append({"filename": error[0], "error": error[1]})
            
            return {
                "deleted_count": deleted_count,
                "errors_count": errors_count,
                "error_details": errors_details
            }
            
        except Exception as e:
            logger.error(f"Error en clear_all_pdfs: {str(e)}", exc_info=True)
            return {
                "deleted_count": deleted_count,
                "errors_count": errors_count + 1,
                "error_details": errors_details + [{"error": str(e)}]
            }
            
    def __del__(self):
        """Limpieza al destruir la instancia."""
        self.executor.shutdown(wait=True)

# Ejemplo de cómo podría usarse (esto no iría aquí usualmente):
# if __name__ == '__main__':
#     # Suponiendo que este archivo está en backend/file_system/pdf_file_manager.py
#     # El base_dir por defecto sería la raíz del proyecto.
#     pdf_manager = PDFFileManager() 
#     print(f"Directorio de PDFs: {pdf_manager.pdf_dir}")
#     # Para probar, necesitarías un objeto UploadFile mock o un archivo real.

# Ejemplo de cómo podría usarse (esto no iría aquí usualmente):
# if __name__ == '__main__':
#     # Suponiendo que este archivo está en backend/file_system/pdf_file_manager.py
#     # El base_dir por defecto sería la raíz del proyecto.
#     pdf_manager = PDFFileManager() 
#     print(f"Directorio de PDFs: {pdf_manager.pdf_dir}")
#     # Para probar, necesitarías un objeto UploadFile mock o un archivo real. 