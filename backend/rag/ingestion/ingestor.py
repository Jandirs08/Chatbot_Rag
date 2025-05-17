"""Módulo optimizado para la ingesta de documentos en el sistema RAG."""
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Set
import logging
import time
from concurrent.futures import ThreadPoolExecutor

from langchain_core.documents import Document

from ...file_system.pdf_file_manager import PDFFileManager
from ..pdf_processor.pdf_loader import PDFContentLoader
from ..embeddings.embedding_manager import EmbeddingManager
from ..vector_store.vector_store import VectorStore
from ...config import settings

logger = logging.getLogger(__name__)

class RAGIngestor:
    """Gestor optimizado de ingesta de documentos para RAG."""

    def __init__(
        self,
        pdf_file_manager: PDFFileManager,
        pdf_content_loader: PDFContentLoader,
        embedding_manager: EmbeddingManager,
        vector_store: VectorStore,
        batch_size: int = 100,
        max_workers: int = 4
    ):
        """Inicializa el gestor de ingesta.
        
        Args:
            pdf_file_manager: Gestor de archivos PDF.
            pdf_content_loader: Procesador de contenido PDF.
            embedding_manager: Gestor de embeddings.
            vector_store: Almacenamiento vectorial.
            batch_size: Tamaño del lote para procesamiento.
            max_workers: Número máximo de workers para procesamiento paralelo.
        """
        self.pdf_file_manager = pdf_file_manager
        self.pdf_content_loader = pdf_content_loader
        self.embedding_manager = embedding_manager
        self.vector_store = vector_store
        self.batch_size = batch_size
        self.max_workers = max_workers
        self._processed_hashes: Set[str] = set()
        logger.info(f"RAGIngestor inicializado con batch_size={batch_size}, max_workers={max_workers}")

    async def ingest_single_pdf(self, pdf_path: Path, force_update: bool = False) -> Dict:
        """Procesa un PDF individual con optimizaciones.
        
        Args:
            pdf_path: Ruta al archivo PDF.
            force_update: Forzar actualización aunque exista.
            
        Returns:
            Diccionario con resultados de la ingesta.
        """
        filename = pdf_path.name
        logger.info(f"Iniciando ingesta de: {filename}")
        
        try:
            # Verificar archivo
            if not pdf_path.exists() or not pdf_path.is_file():
                return self._error_result(filename, "Archivo no encontrado")
            
            # Verificar si ya está procesado
            if not force_update and await self._is_already_processed(pdf_path):
                return {
                    "filename": filename,
                    "status": "skipped",
                    "reason": "already_processed"
                }
            
            # Procesar PDF
            chunks = self.pdf_content_loader.load_and_split_pdf(pdf_path)
            if not chunks:
                return self._error_result(filename, "No se generaron chunks")
            
            # Deduplicar chunks
            unique_chunks, unique_embeddings = await self._deduplicate_chunks(chunks, return_embeddings=True)
            if not unique_chunks:
                return self._error_result(filename, "No quedaron chunks después de deduplicación")
            
            # Procesar en lotes
            total_added = 0
            for i in range(0, len(unique_chunks), self.batch_size):
                batch = unique_chunks[i:i + self.batch_size]
                batch_embeddings = unique_embeddings[i:i + self.batch_size] if unique_embeddings else None
                try:
                    for doc in batch:
                        content_hash = doc.metadata.get('content_hash')
                        if content_hash:
                            await self.vector_store.delete_documents(filter={"content_hash": content_hash})
                    if not isinstance(batch, list):
                        raise TypeError(f"Batch is not a list before adding to vector store. Type: {type(batch)}")
                    if not batch:
                        logger.warning(f"Batch is empty before adding to vector store. Skipping batch {i//self.batch_size + 1}.")
                        continue
                    logger.debug(f"Calling _add_batch_to_vector_store for batch {i//self.batch_size + 1}.")
                    try:
                        await self._add_batch_to_vector_store(batch, i//self.batch_size + 1, embeddings=batch_embeddings)
                        total_added += len(batch)
                        logger.info(f"Lote {i//self.batch_size + 1} procesado: {len(batch)} chunks")
                    except Exception as add_err:
                        logger.error(f"Error procesando lote {i//self.batch_size + 1} en vector store: {add_err}", exc_info=True)
                except Exception as e:
                    logger.error(f"Error en lote {i//self.batch_size + 1}: {str(e)}", exc_info=True)
            
            # Actualizar hashes procesados
            self._update_processed_hashes(unique_chunks)
            
            return {
                "filename": filename,
                "status": "success",
                "chunks_original": len(chunks),
                "chunks_unique": len(unique_chunks),
                "chunks_added": total_added
            }
            
        except Exception as e:
            return self._error_result(filename, str(e))

    async def ingest_pdfs_from_directory(
        self,
        specific_directory: Optional[Path] = None,
        parallel: bool = True,
        force_update: bool = False
    ) -> List[Dict]:
        """Procesa PDFs de un directorio con paralelización opcional.
        
        Args:
            specific_directory: Directorio específico a procesar.
            parallel: Si usar procesamiento paralelo.
            force_update: Forzar actualización de documentos existentes.
            
        Returns:
            Lista de resultados de ingesta.
        """
        source_dir = specific_directory or self.pdf_file_manager.pdf_dir
        logger.info(f"Procesando PDFs desde: {source_dir}")
        
        # Obtener lista de PDFs
        pdf_files = self._get_pdf_files(source_dir)
        if not pdf_files:
            logger.warning(f"No se encontraron PDFs en {source_dir}")
            return []
        
        results = []
        if parallel and len(pdf_files) > 1:
            # Procesamiento paralelo
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Crear tareas
                tasks = [
                    self._process_pdf_parallel(pdf_info, force_update)
                    for pdf_info in pdf_files
                ]
                # Ejecutar y esperar resultados
                results = await asyncio.gather(*tasks)
        else:
            # Procesamiento secuencial
            for pdf_info in pdf_files:
                result = await self.ingest_single_pdf(
                    Path(pdf_info["path"]),
                    force_update=force_update
                )
                results.append(result)
        
        # Resumen
        successful = sum(1 for r in results if r["status"] == "success")
        failed = sum(1 for r in results if r["status"] == "error")
        skipped = sum(1 for r in results if r["status"] == "skipped")
        
        logger.info(
            f"Ingesta completada. "
            f"Éxitos: {successful}, "
            f"Fallos: {failed}, "
            f"Omitidos: {skipped} "
            f"de {len(results)} PDFs."
        )
        
        return results

    async def _process_pdf_parallel(self, pdf_info: Dict, force_update: bool) -> Dict:
        """Procesa un PDF en un worker paralelo."""
        try:
            return await self.ingest_single_pdf(
                Path(pdf_info["path"]),
                force_update=force_update
            )
        except Exception as e:
            return self._error_result(pdf_info["filename"], str(e))

    def _get_pdf_files(self, directory: Path) -> List[Dict]:
        """Obtiene lista de archivos PDF válidos."""
        if directory != self.pdf_file_manager.pdf_dir:
            return [
                {"path": str(p), "filename": p.name}
                for p in directory.glob("*.pdf")
                if p.is_file()
            ]
        return self.pdf_file_manager.list_pdfs()

    async def _is_already_processed(self, pdf_path: Path) -> bool:
        """Verifica si un PDF ya está procesado en el vector store."""
        try:
            # Verificar si hay documentos con la misma fuente (nombre de archivo)
            # La operación de get en Chroma es síncrona
            existing_docs = self.vector_store.store._collection.get(
                where={"source": pdf_path.name},
            )
            # Si la lista de IDs no está vacía, significa que ya existen documentos para esta fuente.
            return bool(existing_docs.get("ids"))
        except Exception as e:
            logger.error(f"Error verificando PDF procesado: {str(e)}")
            return False

    async def _deduplicate_chunks(self, chunks: List[Document], return_embeddings: bool = False) -> (List[Document], list):
        """Elimina chunks duplicados o muy similares y retorna también los embeddings si se solicita."""
        if not chunks:
            return ([], []) if return_embeddings else []
        unique_chunks = []
        unique_embeddings = []
        content_hashes = set()
        chunk_texts = [c.page_content for c in chunks]
        embeddings = self.embedding_manager.embed_documents(chunk_texts)
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        for i, chunk in enumerate(chunks):
            content_hash = chunk.metadata.get('content_hash')
            if content_hash in content_hashes:
                continue
            if unique_chunks:
                existing_embeddings = [embeddings[chunks.index(c)] for c in unique_chunks]
                similarities = cosine_similarity([embeddings[i]], existing_embeddings)[0]
                if np.max(similarities) > settings.deduplication_threshold:
                    continue
            unique_chunks.append(chunk)
            unique_embeddings.append(embeddings[i])
            if content_hash:
                content_hashes.add(content_hash)
        if return_embeddings:
            return unique_chunks, unique_embeddings
        return unique_chunks

    def _update_processed_hashes(self, chunks: List[Document]) -> None:
        """Actualiza el conjunto de hashes procesados."""
        for chunk in chunks:
            content_hash = chunk.metadata.get('content_hash')
            if content_hash:
                self._processed_hashes.add(content_hash)

    def _error_result(self, filename: str, error_message: str) -> Dict:
        """Genera un resultado de error estandarizado."""
        logger.error(f"Error en {filename}: {error_message}")
        return {
            "filename": filename,
            "status": "error",
            "error": error_message
        }

    async def clear_vector_store_content(self) -> None:
        """Limpia el contenido del vector store."""
        logger.info("Limpiando vector store...")
        try:
            await self.vector_store.delete_collection()
            self._processed_hashes.clear()
            logger.info("Vector store limpiado exitosamente")
        except Exception as e:
            logger.error(f"Error limpiando vector store: {str(e)}")
            raise

    async def _add_batch_to_vector_store(self, batch: List[Document], batch_number: int, embeddings: list = None):
        """Función auxiliar asíncrona para añadir un lote de documentos al vector store, permitiendo pasar embeddings."""
        if not batch:
            logger.warning(f"_add_batch_to_vector_store llamado con lote vacío para el lote {batch_number}.")
            return # No hacer nada si el lote está vacío
        if not isinstance(batch, list):
            raise TypeError(f"Batch is not a list inside _add_batch_to_vector_store for batch {batch_number}. Type: {type(batch)}")
        if not batch[0] or not isinstance(batch[0], Document):
             raise TypeError(f"First element in batch is not a valid Document inside _add_batch_to_vector_store for batch {batch_number}. Type: {type(batch[0])}")
        logger.debug(f"Attempting to add batch {batch_number} to vector store. Batch size: {len(batch)}.")
        try:
            await self.vector_store.add_documents(batch, embeddings=embeddings)
            logger.debug(f"vector_store.add_documents completed successfully for batch {batch_number}.")
        except TypeError as te:
            raise TypeError(f"TypeError during vector_store.add_documents for batch {batch_number}. Error: {te}") from te
        except Exception as ex:
            logger.error(f"Unexpected error during vector_store.add_documents for batch {batch_number}: {ex}", exc_info=True)
            raise ex # Re-lanzar la excepción principal si ocurre un error no manejado aquí

    # Ejemplo de cómo se instanciaría (no va aquí):
    # from ...config import Settings
    # settings_instance = Settings()
    # pdf_manager = PDFFileManager(base_dir=Path("ruta/a/tu/proyecto")) # Ajustar base_dir
    # content_loader = PDFContentLoader(chunk_size=settings_instance.chunk_size, chunk_overlap=settings_instance.chunk_overlap)
    # embedding_mgr = EmbeddingManager(model_name=settings_instance.embedding_model)
    # vector_db = VectorStore(persist_directory=Path("ruta/a/tu/vector_store"), embedding_function=embedding_mgr.get_embedding_model())
    # ingestor = RAGIngestor(pdf_manager, content_loader, embedding_mgr, vector_db)
    # resultados_ingesta = ingestor.ingest_pdfs_from_directory()
    # print(resultados_ingesta) 