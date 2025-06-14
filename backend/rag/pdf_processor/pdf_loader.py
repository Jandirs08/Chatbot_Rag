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
                 chunk_size: int = 1000,  # Aumentado de 700
                 chunk_overlap: int = 200,  # Aumentado de 150
                 min_chunk_length: int = 50):  # Reducido de 100
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
        # Eliminar caracteres de control excepto saltos de línea y tabulaciones
        text = ''.join(char for char in text if char in ['\n', '\t'] or char.isprintable())
        
        # Preservar múltiples espacios en blanco que podrían ser significativos
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Preservar saltos de línea significativos
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        # Eliminar espacios al inicio y final de líneas, pero preservar indentación
        lines = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped:
                # Preservar la indentación original
                indent = len(line) - len(line.lstrip())
                lines.append(' ' * indent + stripped)
        
        return '\n'.join(lines)

    def _normalize_text(self, text: str) -> str:
        """Normaliza espacios, puntuación y formato del texto."""
        # Preservar espacios alrededor de puntuación cuando sea significativo
        text = re.sub(r'[\s]*([.,!?;:])[\s]*', r'\1 ', text)
        
        # Asegurar espacio después de puntuación solo si no hay ya un espacio
        text = re.sub(r'([.,!?;:])([^\s])', r'\1 \2', text)
        
        # Normalizar guiones manteniendo su significado
        text = re.sub(r'[\u2010-\u2015]', '-', text)
        
        # Normalizar comillas preservando su significado
        text = re.sub(r'[\u2018\u2019]', "'", text)
        text = re.sub(r'[\u201C\u201D]', '"', text)
        
        return text

    def _preserve_structures(self, text: str) -> str:
        """Detecta y preserva estructuras importantes en el texto."""
        # Preservar listas numeradas con mejor manejo de formato
        text = re.sub(r'(\d+\.\s*)(\n\s*)', r'\1', text)
        
        # Preservar listas con viñetas y diferentes estilos
        text = re.sub(r'([\u2022\-*•]\s*)(\n\s*)', r'\1', text)
        
        # Preservar títulos y encabezados con mejor detección
        text = re.sub(r'([A-Z][^.!?]*:)(\n\s*)', r'\1 ', text)
        
        # Preservar tablas y estructuras tabulares
        text = re.sub(r'(\|\s*[^\n]+\s*\|)(\n\s*)', r'\1', text)
        
        # Preservar definiciones y términos importantes
        text = re.sub(r'([A-Z][a-z]+:)(\n\s*)', r'\1 ', text)
        
        return text

    def _postprocess_chunks(self, chunks: List[Document], pdf_path: Path) -> List[Document]:
        """Mejora y filtra los chunks después de la división."""
        final_chunks = []
        for chunk in chunks:
            # Reducir el umbral mínimo de longitud
            if len(chunk.page_content.strip()) < self.min_chunk_length:
                continue
            
            # Calcular métricas de calidad con umbral más bajo
            content = chunk.page_content
            quality_score = self._calculate_chunk_quality(content)
            
            if quality_score < 0.2:  # Reducido de 0.3
                continue
                
            # Mejorar metadata con información más detallada
            chunk.metadata.update({
                "source": pdf_path.name,
                "file_path": str(pdf_path.resolve()),
                "chunk_type": self._detect_chunk_type(content),
                "content_hash": self._generate_content_hash(content),
                "quality_score": quality_score,
                "word_count": len(content.split()),
                "char_count": len(content),
                "has_important_terms": bool(self._extract_important_terms(content)),
                "structure_type": self._detect_structure_type(content)
            })
            
            final_chunks.append(chunk)
        
        return final_chunks

    def _extract_important_terms(self, text: str) -> List[str]:
        """Extrae términos importantes del texto basándose en patrones y contexto."""
        important_terms = set()
        
        # Patrones genéricos para identificar términos importantes
        patterns = [
            r'(?:importante|requisito|necesario|requiere|debe|obligatorio)[:\s]+([^.\n]+)',
            r'(?:proceso|procedimiento|instrucciones)[:\s]+([^.\n]+)',
            r'(?:nota|atención|consideración)[:\s]+([^.\n]+)',
            r'(?:requisitos|documentación)[:\s]+([^.\n]+)',
            r'(?:definición|concepto|término)[:\s]+([^.\n]+)',
            r'(?:objetivo|meta|propósito)[:\s]+([^.\n]+)',
            r'(?:característica|propiedad|atributo)[:\s]+([^.\n]+)',
            r'(?:clasificación|categoría|tipo)[:\s]+([^.\n]+)'
        ]
        
        # Buscar términos usando patrones
        for pattern in patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                term = match.group(1).strip()
                if len(term.split()) <= 4:  # Limitar a frases de hasta 4 palabras
                    important_terms.add(term)
        
        # Extraer términos de listas numeradas o con viñetas
        list_items = re.findall(r'(?:^|\n)[•\-\*]\s*([^.\n]+)', text)
        important_terms.update(item.strip() for item in list_items)
        
        # Extraer términos después de dos puntos
        colon_terms = re.findall(r':\s*([^.\n]+)', text)
        important_terms.update(term.strip() for term in colon_terms if len(term.split()) <= 4)
        
        # Extraer términos en negrita o cursiva si están disponibles en el PDF
        emphasis_terms = re.findall(r'\*\*([^*]+)\*\*|\*([^*]+)\*', text)
        for term in emphasis_terms:
            if isinstance(term, tuple):
                term = term[0] or term[1]
            if term and len(term.split()) <= 4:
                important_terms.add(term.strip())
        
        return list(important_terms)

    def _calculate_chunk_quality(self, content: str) -> float:
        """Calcula la calidad de un chunk con criterios más flexibles."""
        score = 1.0
        
        # Penalización más suave por chunks cortos
        if len(content) < 50:
            score *= 0.8  # Reducido de 0.7
        
        # Penalización por contenido repetitivo
        words = content.split()
        if len(words) > 0:
            unique_words = set(words)
            repetition_ratio = len(unique_words) / len(words)
            score *= (0.5 + repetition_ratio * 0.5)
        
        # Bonus por estructuras importantes
        if self._detect_structure_type(content) != "plain_text":
            score *= 1.2
        
        # Bonus por términos importantes
        if self._extract_important_terms(content):
            score *= 1.1
        
        return min(1.0, score)

    def _detect_structure_type(self, content: str) -> str:
        """Detecta el tipo de estructura en el contenido."""
        if re.search(r'^\d+\.\s', content, re.MULTILINE):
            return "numbered_list"
        elif re.search(r'^[\u2022\-*•]\s', content, re.MULTILINE):
            return "bullet_list"
        elif re.search(r'^\|\s*[^\n]+\s*\|', content, re.MULTILINE):
            return "table"
        elif re.search(r'^[A-Z][^.!?]*:', content, re.MULTILINE):
            return "definition"
        else:
            return "plain_text"

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