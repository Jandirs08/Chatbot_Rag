import asyncio
import logging
import time
from pathlib import Path
import sys
import os

# Agregar el directorio raíz al path para importaciones
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.rag.retrieval.retriever import RAGRetriever
from backend.rag.vector_store.vector_store import VectorStore
from backend.rag.embeddings.embedding_manager import EmbeddingManager
from backend.utils.chain_cache import ChatbotCache, CacheTypes
from backend.config import get_settings
from langchain_community.embeddings import HuggingFaceEmbeddings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_rag_performance():
    """Prueba el rendimiento del RAG con diferentes escenarios."""
    settings = get_settings()
    
    # Inicializar componentes
    embedding_model = HuggingFaceEmbeddings(model_name=settings.embedding_model)
    vector_store = VectorStore(
        persist_directory=settings.vector_store_path,
        embedding_function=embedding_model
    )
    
    # Crear instancia del retriever
    retriever = RAGRetriever(
        vector_store=vector_store,
        embedding_manager=embedding_model,
        cache_enabled=True
    )
    
    # Consultas de prueba
    test_queries = [
        "¿Cuáles son los requisitos para obtener una beca?",
        "¿Cómo puedo inscribirme en un curso?",
        "¿Qué documentos necesito para la matrícula?",
        "¿Cuáles son los horarios de atención?",
        "¿Cómo puedo contactar a un asesor?"
    ]
    
    # Probar con caché habilitado
    logger.info("Probando con caché habilitado...")
    tiempos_cache = []
    for i, query in enumerate(test_queries, 1):
        logger.info(f"\nConsulta {i}: {query}")
        start_time = time.perf_counter()
        docs = await retriever.retrieve_documents(query)
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        tiempos_cache.append(elapsed)
        logger.info(f"Tiempo total: {elapsed:.3f}s")
        logger.info(f"Documentos recuperados: {len(docs)}")
    logger.info(f"Tiempo promedio con caché: {sum(tiempos_cache)/len(tiempos_cache):.3f}s")

    # Probar con caché deshabilitado
    logger.info("\nProbando con caché deshabilitado...")
    retriever.cache_enabled = False
    tiempos_no_cache = []
    for i, query in enumerate(test_queries, 1):
        logger.info(f"\nConsulta {i}: {query}")
        start_time = time.perf_counter()
        docs = await retriever.retrieve_documents(query)
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        tiempos_no_cache.append(elapsed)
        logger.info(f"Tiempo total: {elapsed:.3f}s")
        logger.info(f"Documentos recuperados: {len(docs)}")
    logger.info(f"Tiempo promedio sin caché: {sum(tiempos_no_cache)/len(tiempos_no_cache):.3f}s")

    # Probar fallback a InMemoryCache
    logger.info("\nProbando fallback a InMemoryCache...")
    cache = ChatbotCache.create(
        cache_type=CacheTypes.RedisCache,
        settings=settings,
        ttl=3600
    )
    
    # Simular fallo de Redis
    logger.info("Simulando fallo de Redis...")
    cache._init_cache()  # Esto debería fallar y hacer fallback a InMemoryCache
    
    # Verificar que el caché sigue funcionando
    logger.info("Verificando operaciones de caché...")
    try:
        cache.get_cache_instance()
        logger.info("Caché funcionando correctamente después del fallback")
    except Exception as e:
        logger.error(f"Error en el caché: {e}")

async def main():
    """Función principal de prueba."""
    try:
        await test_rag_performance()
    except Exception as e:
        logger.error(f"Error durante las pruebas: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
