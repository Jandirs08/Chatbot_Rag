#!/usr/bin/env python
"""Script para añadir documentos de prueba al vector store."""
import asyncio
import logging
import sys
import uuid
from pathlib import Path
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings

# Agregar el directorio raíz al path para importaciones
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.rag.retrieval.retriever import RAGRetriever
from backend.rag.vector_store.vector_store import VectorStore
from backend.config import get_settings

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def add_test_documents():
    """Añade documentos de prueba al vector store."""
    settings = get_settings()
    
    # Inicializar componentes
    embedding_model = HuggingFaceEmbeddings(model_name=settings.embedding_model)
    vector_store = VectorStore(
        persist_directory=settings.vector_store_path,
        embedding_function=embedding_model
    )
    
    # Crear datos de prueba con IDs únicos
    test_data = [
        {
            "id": "doc_beca_001",
            "text": "Los requisitos para obtener una beca incluyen mantener un promedio mínimo de 8.5, estar inscrito como estudiante de tiempo completo, y presentar una carta de motivos junto con documentación socioeconómica.",
            "metadata": {"source": "info_becas.pdf", "page": 1, "chunk_type": "paragraph", "content_hash": "hash1"}
        },
        {
            "id": "doc_curso_001",
            "text": "Para inscribirte en un curso debes acceder al portal académico, seleccionar los cursos de tu interés dentro del período de inscripciones, y asegurarte de no tener adeudos financieros o administrativos.",
            "metadata": {"source": "manual_estudiante.pdf", "page": 5, "chunk_type": "paragraph", "content_hash": "hash2"}
        },
        {
            "id": "doc_matricula_001",
            "text": "Los documentos necesarios para completar la matrícula son: certificado de estudios previos, identificación oficial, comprobante de domicilio reciente, fotografías tamaño infantil, y comprobante de pago de la cuota de inscripción.",
            "metadata": {"source": "proceso_inscripcion.pdf", "page": 2, "chunk_type": "bullet_list", "content_hash": "hash3"}
        },
        {
            "id": "doc_horarios_001",
            "text": "Los horarios de atención de la oficina de servicios escolares son de lunes a viernes de 9:00 a 18:00 horas y sábados de 9:00 a 13:00 horas. Durante periodos vacacionales el horario se reduce.",
            "metadata": {"source": "servicios_campus.pdf", "page": 3, "chunk_type": "paragraph", "content_hash": "hash4"}
        },
        {
            "id": "doc_contacto_001",
            "text": "Para contactar a un asesor académico, puedes agendar una cita a través del sistema de citas en línea, enviar un correo a asesoria@universidad.edu, o llamar al teléfono 55-1234-5678 en horario de oficina.",
            "metadata": {"source": "servicios_estudiantes.pdf", "page": 7, "chunk_type": "paragraph", "content_hash": "hash5"}
        },
    ]
    
    try:
        # Eliminar documentos existentes para empezar limpio
        logger.info("Eliminando documentos existentes...")
        try:
            # Usar el método async del VectorStore para eliminar toda la colección
            await vector_store.delete_collection()
            logger.info("Documentos existentes eliminados.")
        except Exception as e:
            logger.warning(f"No se pudieron eliminar documentos existentes: {e}. Continuando...")
        
        # Añadir documentos usando el método asíncrono del VectorStore
        logger.info(f"Añadiendo {len(test_data)} documentos de prueba al vector store...")
        docs = [Document(page_content=item["text"], metadata={**item["metadata"], "id": item["id"]}) for item in test_data]
        await vector_store.add_documents(docs)
        logger.info("Documentos de prueba añadidos exitosamente")
        # Verificar cuántos documentos hay en la colección
        count = vector_store.store._collection.count()
        logger.info(f"La colección ahora tiene {count} documentos.")
        
        # Verificar que se guardaron correctamente
        query = "becas requisitos"
        query_embedding = embedding_model.embed_query(query)
        results = vector_store.store._collection.query(
            query_embeddings=[query_embedding],
            n_results=2
        )
                
        logger.info(f"Prueba de recuperación: {len(results['documents'][0])} documentos encontrados")
        for i, doc in enumerate(results['documents'][0]):
            logger.info(f"Documento {i+1}: {doc[:50]}...")
        
        return True
    except Exception as e:
        logger.error(f"Error al añadir documentos de prueba: {e}", exc_info=True)
        return False

async def clear_all_documents():
    """Elimina todos los documentos del vector store."""
    settings = get_settings()
    
    # Inicializar componentes necesarios solo para limpiar
    # No necesitamos embedding_model ni nada más si solo vamos a eliminar la colección
    try:
        vector_store = VectorStore(
            persist_directory=settings.vector_store_path,
            # No necesitamos embedding_function para eliminar la colección completa
            embedding_function=None 
        )
        
        logger.info("Iniciando limpieza de la colección del vector store...")
        # Usar el método async del VectorStore para eliminar toda la colección
        await vector_store.delete_collection()
        logger.info("Colección del vector store limpiada exitosamente.")
        return True
    except Exception as e:
        logger.error(f"Error al limpiar el vector store: {e}", exc_info=True)
        # logger.error(f"Asegúrate de que el backend no esté corriendo, o que no haya otra instancia accediendo a ChromaDB/Redis.")
        return False

async def main():
    """Función principal para limpiar el vector store."""
    success = await clear_all_documents()
    if success:
        logger.info("Proceso de limpieza completado.")
    else:
        logger.error("El proceso de limpieza falló.")

if __name__ == "__main__":
    asyncio.run(main()) 