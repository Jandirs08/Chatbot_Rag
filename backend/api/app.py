"""FastAPI application for the chatbot."""
import os # Necesario para getenv
import logging # Necesario para configurar logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path

from ..config import get_settings, settings # Importar settings directamente también si se usa para logging
from ..chat.manager import ChatManager
from ..rag.retrieval.retriever import RAGRetriever
# Asegurarse de que la ruta de importación es correcta después de mover pdf_utils.py
# from ..utils.pdf_utils import PDFProcessor # Ruta antigua
from ..file_system.pdf_file_manager import PDFFileManager # Nueva ruta y nombre

# --- Importar Routers --- 
# Ajusta estas rutas si la estructura de tus routers es diferente.
from .health_check_routes import router as health_router # Corregido: .health_check_routes
# Suponiendo que cada subdirectorio en api/routes/ tiene un archivo router.py que define 'router'
# Si el archivo se llama diferente (ej. api/routes/pdf/main.py), ajusta la importación.
from .routes.pdf.pdf_routes import router as pdf_router
from .routes.rag.rag_routes import router as rag_router
from .routes.chat.chat_routes import router as chat_router

# Dependencias para inicializar managers (ejemplo, deben ajustarse a la refactorización previa)
from ..bot import Bot
from ..memory import MemoryTypes, MEM_TO_CLASS # Para configurar el Bot con memoria
from ..rag.pdf_processor.pdf_loader import PDFContentLoader
from ..rag.embeddings.embedding_manager import EmbeddingManager
# Asumiendo que VectorStore es la clase base o una específica como ChromaVectorStore
from ..rag.vector_store.vector_store import VectorStore # Asumiendo que es ChromaVectorStore o similar
from ..rag.ingestion.ingestor import RAGIngestor

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for setup and teardown."""
    logger = logging.getLogger(__name__)
    logger.info("Iniciando aplicación y configurando recursos...")
    
    try:
        s = get_settings()
        app.state.settings = s

        # Inicializar componentes
        app.state.pdf_file_manager = PDFFileManager(base_dir=Path(s.base_data_dir).resolve() if s.base_data_dir else None)
        logger.info(f"PDFFileManager inicializado. Directorio de PDFs: {app.state.pdf_file_manager.pdf_dir}")

        app.state.pdf_content_loader = PDFContentLoader(chunk_size=s.chunk_size, chunk_overlap=s.chunk_overlap)
        logger.info(f"PDFContentLoader inicializado con chunk_size={s.chunk_size}, overlap={s.chunk_overlap}")

        app.state.embedding_manager = EmbeddingManager(model_name=s.embedding_model)
        logger.info(f"EmbeddingManager inicializado con modelo: {s.embedding_model}")

        vector_store_path = Path(s.vector_store_path).resolve()
        vector_store_path.mkdir(parents=True, exist_ok=True)
        app.state.vector_store = VectorStore(
            persist_directory=str(vector_store_path),
            embedding_function=app.state.embedding_manager
        )
        logger.info(f"VectorStore inicializado en: {vector_store_path}")

        app.state.rag_ingestor = RAGIngestor(
            pdf_file_manager=app.state.pdf_file_manager,
            pdf_content_loader=app.state.pdf_content_loader,
            embedding_manager=app.state.embedding_manager,
            vector_store=app.state.vector_store
        )
        logger.info("RAGIngestor inicializado.")

        app.state.rag_retriever = RAGRetriever(
            vector_store=app.state.vector_store,
            embedding_manager=app.state.embedding_manager
        )
        logger.info("RAGRetriever inicializado.")

        bot_memory_type = MemoryTypes.BASE_MEMORY
        if s.memory_type:
            try:
                bot_memory_type = MemoryTypes[s.memory_type.upper()]
            except KeyError:
                logger.warning(f"Tipo de memoria '{s.memory_type}' no válido en settings. Usando BASE_MEMORY.")

        app.state.bot_instance = Bot(
            settings=settings,
            memory_type=bot_memory_type,
            memory_kwargs={"conversation_id": "default_session"},
            cache=None
        )
        logger.info(f"Instancia de Bot creada con tipo de memoria: {bot_memory_type}")

        app.state.chat_manager = ChatManager(
            bot_instance=app.state.bot_instance,
            rag_retriever_instance=app.state.rag_retriever
        )
        logger.info("ChatManager inicializado.")

        logger.info("Todos los managers y procesadores inicializados y disponibles en app.state.")

    except Exception as e:
        logger.error(f"Error fatal durante la inicialización en lifespan: {e}", exc_info=True)
        raise

    yield
    
    logger.info("Cerrando aplicación y liberando recursos...")
    try:
        # Cerrar ChatManager
        if hasattr(app.state, 'chat_manager'):
            if hasattr(app.state.chat_manager, 'close'):
                if asyncio.iscoroutinefunction(app.state.chat_manager.close):
                    await app.state.chat_manager.close()
                else:
                    app.state.chat_manager.close()
            logger.info("ChatManager cerrado.")

        # Cerrar VectorStore
        if hasattr(app.state, 'vector_store'):
            if hasattr(app.state.vector_store, 'close'):
                if asyncio.iscoroutinefunction(app.state.vector_store.close):
                    await app.state.vector_store.close()
                else:
                    app.state.vector_store.close()
            logger.info("VectorStore cerrado.")

        # Cerrar EmbeddingManager
        if hasattr(app.state, 'embedding_manager'):
            if hasattr(app.state.embedding_manager, 'close'):
                if asyncio.iscoroutinefunction(app.state.embedding_manager.close):
                    await app.state.embedding_manager.close()
                else:
                    app.state.embedding_manager.close()
            logger.info("EmbeddingManager cerrado.")

    except Exception as e:
        logger.error(f"Error durante la limpieza de recursos: {e}", exc_info=True)
    finally:
        logger.info("Proceso de limpieza completado.")

def create_app() -> FastAPI:
    """Create the FastAPI application."""
    # Configurar logging (debe hacerse antes si otros módulos loggean al importarse)
    # No, settings ya se importa, así que esto debería estar bien aquí.
    logging.basicConfig(
        level=settings.log_level.upper(), # Logging level debe ser en mayúsculas
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    main_logger = logging.getLogger(__name__) # Logger para create_app
    main_logger.info("Creando instancia de FastAPI...")

    # Verificar OpenAI API key (u otras configuraciones críticas)
    if settings.model_type == "OPENAI" and not settings.openai_api_key: # Usar settings
        main_logger.error("Error Crítico: OpenAI API key (OPENAI_API_KEY) no está configurada en las settings o el entorno para el modelo OPENAI.")
        raise ValueError("OpenAI API key es requerida para el modelo OPENAI y no está configurada.")
    
    # Cargar settings (ya se hizo arriba para logging, pero bien tenerlo aquí para el app)
    # app_settings = get_settings() # Ya tenemos 'settings' importado globalmente en el módulo
    
    app = FastAPI(
        title=settings.app_title or "LangChain Chatbot API",
        description=settings.app_description or "API for the LangChain chatbot",
        version=settings.app_version or "1.0.0",
        lifespan=lifespan # Pasar la función lifespan
    )
    
    cors_origins_setting = settings.cors_origins
    if cors_origins_setting:
        allow_origins_list = []
        if isinstance(cors_origins_setting, str):
            allow_origins_list = [origin.strip() for origin in cors_origins_setting.split(',') if origin.strip()]
        elif isinstance(cors_origins_setting, list):
            allow_origins_list = cors_origins_setting
        else:
            main_logger.warning(f"cors_origins tiene un tipo inesperado: {type(cors_origins_setting)}. Usando default ['*'].")
            allow_origins_list = ["*"]
            
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        main_logger.info(f"CORS configurado para orígenes: {allow_origins_list}")
    else:
        # Default a permitir todo si no se especifica (para desarrollo)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        main_logger.info("CORS configurado para permitir todos los orígenes (default). Es recomendable especificar cors_origins en producción.")
    
    # Registrar routers
    # Asegúrate que las rutas de importación de los routers sean correctas
    # Por ejemplo, si están en un subdirectorio api/routes/
    # from .routes import health_router, pdf_router, rag_router, chat_router
    
    # Usando las importaciones ya hechas arriba:
    app.include_router(health_router, prefix="/api/v1", tags=["Health"])
    app.include_router(pdf_router, prefix="/api/v1", tags=["PDFs"])
    app.include_router(rag_router, prefix="/api/v1", tags=["RAG"])
    app.include_router(chat_router, prefix="/api/v1", tags=["Chat"])
    main_logger.info("Routers registrados.")

    main_logger.info("Aplicación FastAPI creada y configurada exitosamente.")
    return app 

# --- Creación de la instancia global de la aplicación --- 
# Esto permite que Uvicorn la encuentre si se ejecuta este archivo directamente (aunque es mejor usar main.py)
# global_app = create_app() # Comentado o eliminado si main.py es el único punto de entrada.