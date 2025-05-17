# Estructura del Backend del Chatbot

Este documento describe la estructura de directorios y archivos del backend de la aplicación chatbot.

## Raíz del Backend (`ChatBotRag-main/backend/`)

*   **`main.py`**: Punto de entrada principal de la aplicación FastAPI. Inicializa la app y registra los routers de la API.
*   **`config.py`**: Contiene la configuración centralizada de la aplicación utilizando Pydantic Settings (clase `Settings`). Carga configuraciones desde variables de entorno y archivos `.env`.
*   **`bot.py`**: Define la clase `Bot`, que encapsula la lógica principal del agente de chat, incluyendo la gestión de la cadena de LangChain, la memoria, las herramientas y la personalidad del bot.
*   **`chain.py`**: Define `ChainManager`, responsable de construir y gestionar las cadenas de LangChain (LLM, prompts).
*   **`__init__.py`**: Inicializa el paquete `backend` y expone componentes clave como `settings` y `ChatManager`.
*   **`prompt.py`**: Contiene plantillas de prompts predefinidas, como `BOT_PERSONALITY` y `SHELDON_REACT_PROMPT`.
*   **`gradio_ui.py`**: Contiene la lógica para una interfaz de usuario basada en Gradio (probablemente para pruebas o demostraciones).
*   **`requirements.txt`**: Lista las dependencias de Python necesarias para el backend.
*   **`README.md`**: Documentación específica del backend (si existe, podría ser más general).
*   **`Dockerfile`**: Instrucciones para construir una imagen Docker del backend.

*   **`api/`**: Directorio que contiene la lógica de la API FastAPI.
    *   **`__init__.py`**: Inicializa el módulo API y exporta los routers y `create_app`.
    *   **`app.py`**: Contiene la función `create_app()` que construye la instancia de FastAPI y maneja el ciclo de vida de la aplicación (startup/shutdown) para inicializar servicios como `ChatManager`, `RAGRetriever`, `PDFProcessor`.
    *   **`models.py`**: Define los modelos Pydantic para la validación de solicitudes y respuestas de la API.
    *   **`routes.py`**: Contiene rutas genéricas de la API, como el endpoint de health check (`/health`).
    *   **`pdf_routes.py`**: Contiene las rutas de la API relacionadas con la gestión de archivos PDF (subir, listar, eliminar).
    *   **`rag_routes.py`**: Contiene las rutas de la API para la gestión del sistema RAG (estado, limpieza).
    *   **`chat_routes.py`**: Contiene las rutas de la API para la funcionalidad de chat (streaming de respuestas, limpieza de historial).

*   **`chat/`**: Módulo relacionado con la gestión de chats.
    *   **`__init__.py`**: Inicializador del módulo `chat`.
    *   **`manager.py`**: (`ChatManager`) Lógica para gestionar las interacciones de chat, generar respuestas y coordinar con la base de datos y el RAG.

*   **`common/`**: Directorio para utilidades o constantes comunes.
    *   **`__init__.py`**: Inicializador del módulo `common`.
    *   **`constants.py`**: Define constantes utilizadas en la aplicación (ej. `ANONYMIZED_FIELDS`, `USER_ROLE`).
    *   **`objects.py`**: Define objetos de datos comunes, como `Message` y `MessageTurn`.

*   **`database/`**: Módulo para la interacción con la base de datos.
    *   **`__init__.py`**: Inicializador del módulo `database`.
    *   **`mongodb.py`**: (`MongoDatabase`) Clase para manejar la conexión y operaciones con MongoDB para el historial de chat.

*   **`examples/`**: Contiene scripts de ejemplo.
    *   **`run_llama_cpp.py`**: Ejemplo de cómo ejecutar el bot con un modelo LlamaCPP y una UI de Gradio.

*   **`memory/`**: Módulo para la gestión de la memoria de conversación.
    *   **`__init__.py`**: Inicializador del módulo `memory`. Exporta tipos de memoria y clases.
    *   **`base_memory.py`**: (`BaseChatbotMemory`) Clase base para diferentes implementaciones de memoria de LangChain.
    *   **`custom_memory.py`**: (`CustomMongoChatbotMemory`, `BaseCustomMongoChatbotMemory`) Implementación de memoria personalizada utilizando MongoDB.
    *   **`memory_types.py`**: Define enums o tipos para las diferentes estrategias de memoria.
    *   **`mongo_memory.py`**: (`MongoChatbotMemory`) Implementación de memoria que utiliza `MongoDBChatMessageHistory` de LangChain.

*   **`models/`**: Define tipos de modelos LLM.
    *   **`__init__.py`**: Inicializador del módulo `models`.
    *   **`model_types.py`**: Define enums o tipos para los diferentes modelos LLM soportados (OpenAI, Vertex, LlamaCPP).
    *   **`README.md`**: Documentación para los modelos.

*   **`rag/`**: Módulo para la funcionalidad de Retrieval Augmented Generation (RAG).
    *   **`__init__.py`**: Inicializador del módulo `rag`.
    *   **`embeddings/`**: Gestión de embeddings.
        *   `embedding_manager.py`: (`EmbeddingManager`) Gestiona la creación y uso de modelos de embedding.
    *   **`pdf_processor/`**: Procesamiento de PDFs.
        *   `pdf_loader.py`: (`PDFLoader`) Carga y posiblemente divide PDFs en chunks (aunque `RAGRetriever` parece hacer más de esto).
    *   **`retrieval/`**: Lógica de recuperación de documentos.
        *   `retriever.py`: (`RAGRetriever`) Componente central del RAG. Procesa PDFs, los almacena en un vector store, y recupera documentos relevantes para una consulta.
    *   **`vector_store/`**: Gestión del vector store.
        *   `vector_store.py`: (`VectorStore`) Abstracción para interactuar con el vector store (ej. Chroma).

*   **`tools/`**: Define herramientas personalizadas que el agente puede usar.
    *   **`__init__.py`**: Inicializador del módulo `tools`.
    *   **`serp.py`**: Herramienta para interactuar con la API de Serp (búsqueda web). (Nota: `CustomSearchTool` se menciona en `bot.py`, podría estar definido aquí o ser una clase genérica).

*   **`utils/`**: Contiene utilidades diversas.
    *   **`__init__.py`**: Inicializador del módulo `utils`.
    *   **`anonymizer.py`**: (`BotAnonymizer`) Utilidad para anonimizar datos PII en los mensajes.
    *   **`chain_cache.py`**: (`ChatbotCache`, `CacheTypes`) Lógica para el cacheo de respuestas o cadenas.
    *   **`pdf_utils.py`**: (`PDFProcessor`) Utilidades para manejar archivos PDF (guardar, listar, eliminar, obtener información del vector store asociado). 