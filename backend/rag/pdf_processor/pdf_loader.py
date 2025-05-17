"""Módulo para cargar y procesar contenido de PDFs."""
import re
import hashlib
from typing import List, Optional, Dict
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.document_loaders import UnstructuredPDFLoader
import logging

logger = logging.getLogger(__name__)

class PDFContentLoader:
    """Cargador optimizado de contenido PDF con pre y post procesamiento."""
    
    def __init__(self, 
                 chunk_size: int = 700, 
                 chunk_overlap: int = 150,
                 min_chunk_length: int = 100):
        """Inicializa el cargador con parámetros mejorados.
        
        Args:
            chunk_size: Tamaño de los chunks para la división de texto.
            chunk_overlap: Solapamiento entre chunks.
            min_chunk_length: Longitud mínima para considerar un chunk válido.
        """
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=[
                "\n\n",  # Párrafos
                "\n",    # Líneas
                ".",     # Oraciones
                ";",     # Cláusulas
                ":",     # Listas/definiciones
                "!",     # Exclamaciones
                "?",     # Preguntas
                ",",     # Frases
                " ",     # Palabras
                ""       # Caracteres
            ]
        )
        self.min_chunk_length = min_chunk_length
        logger.info(
            f"PDFContentLoader inicializado con chunk_size={chunk_size}, "
            f"chunk_overlap={chunk_overlap}, min_chunk_length={min_chunk_length}"
        )

    def load_and_split_pdf(self, pdf_path: Path) -> List[Document]:
        """Carga un PDF, lo divide en chunks y aplica pre/post procesamiento.
        
        Args:
            pdf_path: Ruta al archivo PDF.
            
        Returns:
            Lista de Documents procesados y optimizados.
        """
        logger.info(f"Procesando PDF: {pdf_path.name}")
        try:
            # Usar UnstructuredPDFLoader para mejor extracción
            loader = UnstructuredPDFLoader(str(pdf_path))
            documents = loader.load()
            
            if not documents:
                logger.warning(f"No se pudo extraer contenido de: {pdf_path.name}")
                return []
                
            logger.info(f"PDF cargado: {len(documents)} páginas desde {pdf_path.name}")
            
            # Pre-procesar documentos
            processed_docs = self._preprocess_documents(documents)
            logger.info(f"Documentos pre-procesados para {pdf_path.name}")
            
            # Dividir en chunks
            chunks = self.text_splitter.split_documents(processed_docs)
            logger.info(f"Documentos divididos en {len(chunks)} chunks iniciales")
            
            # Post-procesar y filtrar chunks
            final_chunks = self._postprocess_chunks(chunks, pdf_path)
            logger.info(f"Post-procesamiento completado. {len(final_chunks)} chunks finales")
            
            return final_chunks
            
        except Exception as e:
            logger.error(f"Error procesando PDF {pdf_path.name}: {str(e)}", exc_info=True)
            raise

    def _preprocess_documents(self, documents: List[Document]) -> List[Document]:
        """Mejora la calidad del texto antes de la división.
        
        Args:
            documents: Lista de documentos extraídos del PDF.
            
        Returns:
            Lista de documentos pre-procesados.
        """
        processed_docs = []
        for doc in documents:
            text = doc.page_content
            
            # Limpiar el texto
            text = self._clean_text(text)
            
            # Normalizar espacios y puntuación
            text = self._normalize_text(text)
            
            # Detectar y preservar estructuras importantes
            text = self._preserve_structures(text)
            
            # Actualizar el contenido procesado
            doc.page_content = text
            processed_docs.append(doc)
            
        return processed_docs

    def _clean_text(self, text: str) -> str:
        """Limpia el texto de caracteres y patrones no deseados."""
        # Eliminar caracteres de control excepto saltos de línea
        text = ''.join(char for char in text if char == '\n' or char.isprintable())
        
        # Eliminar múltiples espacios en blanco
        text = re.sub(r'\s+', ' ', text)
        
        # Eliminar líneas vacías múltiples
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        # Eliminar espacios al inicio y final de líneas
        text = '\n'.join(line.strip() for line in text.splitlines())
        
        return text.strip()

    def _normalize_text(self, text: str) -> str:
        """Normaliza espacios, puntuación y formato del texto."""
        # Normalizar puntuación
        text = re.sub(r'[\s]*([.,!?;:])', r'\1', text)
        
        # Asegurar espacio después de puntuación
        text = re.sub(r'([.,!?;:])([^\s])', r'\1 \2', text)
        
        # Normalizar guiones
        text = re.sub(r'[\u2010-\u2015]', '-', text)
        
        # Normalizar comillas
        text = re.sub(r'[\u2018\u2019]', "'", text)
        text = re.sub(r'[\u201C\u201D]', '"', text)
        
        return text

    def _preserve_structures(self, text: str) -> str:
        """Detecta y preserva estructuras importantes en el texto."""
        # Preservar listas numeradas
        text = re.sub(r'(\d+\.\s*)(\n\s*)', r'\1', text)
        
        # Preservar listas con viñetas
        text = re.sub(r'([\u2022\-*]\s*)(\n\s*)', r'\1', text)
        
        # Preservar títulos y encabezados
        text = re.sub(r'([A-Z][^.!?]*:)(\n\s*)', r'\1 ', text)
        
        return text

    def _postprocess_chunks(self, chunks: List[Document], pdf_path: Path) -> List[Document]:
        """Mejora y filtra los chunks después de la división.
        
        Args:
            chunks: Lista de chunks generados.
            pdf_path: Ruta al archivo PDF original.
            
        Returns:
            Lista de chunks procesados y filtrados.
        """
        final_chunks = []
        for chunk in chunks:
            # Filtrar chunks muy cortos o sin contenido significativo
            if len(chunk.page_content.strip()) < self.min_chunk_length:
                continue
            
            # Calcular métricas de calidad
            content = chunk.page_content
            quality_score = self._calculate_chunk_quality(content)
            
            if quality_score < 0.3:  # Umbral mínimo de calidad
                continue
                
            # Mejorar metadata
            chunk.metadata.update({
                "source": pdf_path.name,
                "file_path": str(pdf_path.resolve()),
                "chunk_type": self._detect_chunk_type(content),
                "content_hash": self._generate_content_hash(content),
                "quality_score": quality_score,
                "word_count": len(content.split()),
                "char_count": len(content)
            })
            
            final_chunks.append(chunk)
        
        return final_chunks

    def _calculate_chunk_quality(self, content: str) -> float:
        """Calcula un score de calidad para el chunk."""
        # Inicializar score base
        score = 1.0
        
        # Penalizar chunks muy cortos
        length_score = min(len(content) / 1000, 1.0)
        score *= length_score
        
        # Penalizar chunks con poco contenido significativo
        words = content.split()
        word_density = len(words) / (len(content) + 1)
        score *= min(word_density * 5, 1.0)
        
        # Penalizar chunks con muchos caracteres especiales
        special_char_ratio = len(re.findall(r'[^a-zA-Z0-9\s.,!?]', content)) / (len(content) + 1)
        score *= (1 - special_char_ratio)
        
        # Bonificar chunks con estructura clara
        if re.search(r'^[A-Z].*[.!?]$', content):  # Comienza con mayúscula y termina con puntuación
            score *= 1.2
            
        return min(score, 1.0)

    def _detect_chunk_type(self, content: str) -> str:
        """Detecta el tipo de contenido del chunk."""
        if re.match(r'^\d+\.', content):
            return "numbered_list"
        elif re.match(r'^[\u2022\-*]', content):
            return "bullet_list"
        elif re.match(r'^[A-Z][^.!?]*:', content):
            return "header"
        elif len(content.split('\n')) > 3:
            return "paragraph"
        else:
            return "text"

    def _generate_content_hash(self, content: str) -> str:
        """Genera un hash único para el contenido del chunk."""
        # Normalizar el contenido para el hash
        normalized = re.sub(r'\s+', ' ', content.lower().strip())
        return hashlib.md5(normalized.encode()).hexdigest()

    # El método process_directory se puede eliminar si el RAGIngestor maneja la iteración
    # def process_directory(self, directory: Path) -> List[Document]:
    #     """Procesa todos los PDFs en un directorio."""
    #     all_docs = []
    #     logger.info(f"Procesando directorio para carga de PDFs: {directory}")
    #     for pdf_file in directory.glob("*.pdf"):
    #         if pdf_file.is_file():
    #             try:
    #                 docs = self.load_and_split_pdf(pdf_file)
    #                 all_docs.extend(docs)
    #             except Exception as e:
    #                 logger.error(f"Error procesando archivo {pdf_file.name} en directorio: {str(e)}")
    #                 continue 
    #     logger.info(f"Directorio {directory} procesado. Total de chunks: {len(all_docs)}")
    #     return all_docs 