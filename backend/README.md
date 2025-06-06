# Backend del ChatBot RAG con LangChain y FastAPI

Este directorio contiene el backend para una aplicación de ChatBot con Retrieval Augmented Generation (RAG), construido con LangChain, FastAPI y MongoDB.

## Últimas Actualizaciones

### Refactorización Mayor

- Movimiento de `utils/pdf_utils.py` a `file_system/pdf_file_manager.py`
- Inyección de `RAGRetriever` en `ChatManager`
- Simplificación de la lógica de configuración en `api/app.py`
- Mejora en la gestión de settings y variables de entorno

### Mejoras de Arquitectura

- Eliminación de duplicidad en el procesamiento de PDFs
- Clarificación de responsabilidades entre componentes
- Mejor separación de concerns en el sistema RAG
- Optimización del flujo de datos en el chat

## Patrones de Diseño y Principios

El backend ha sido diseñado siguiendo varios patrones y principios de diseño de software:

### 1. Inyección de Dependencias (DI)

- Los componentes principales (`ChatManager`, `Bot`, `RAGRetriever`, etc.) reciben sus dependencias a través del constructor.
- La inyección se realiza en el ciclo de vida de la aplicación (`lifespan` en `api/app.py`).
- Las dependencias se almacenan en `app.state` para su uso en los endpoints.

### 2. Principio de Responsabilidad Única (SRP)

Cada clase tiene una responsabilidad bien definida:

- `PDFFileManager`: Gestión de archivos PDF en el sistema de archivos.
- `PDFContentLoader`: Carga y división de contenido PDF.
- `RAGIngestor`: Orquestación del proceso de ingesta.
- `RAGRetriever`: Recuperación de documentos relevantes.
- `ChatManager`: Orquestación de conversaciones y gestión de RAG.
- `Bot`: Gestión de interacciones con LLM.
- `ChainManager`: Gestión exclusiva de cadenas LangChain.

### 3. Patrón Fachada

- `ChatManager` actúa como fachada, simplificando la interacción con múltiples subsistemas (Bot, RAG, DB).
- `RAGIngestor` es una fachada para el proceso de ingesta de documentos.

### 4. Patrón Estrategia

- Sistema de memoria configurable a través de `MemoryTypes`.
- Diferentes implementaciones de embeddings y vector stores pueden intercambiarse.

### 5. Patrón Factory (implícito en LangChain)

- `ChainManager` actúa como factory para crear y configurar cadenas LangChain.
- `Bot` crea instancias de agentes y ejecutores.

### 6. Principio de Inversión de Dependencias (DIP)

- Los componentes dependen de abstracciones (interfaces) no de implementaciones concretas.
- Ejemplo: `VectorStore` es una abstracción que puede tener diferentes implementaciones.

## Arquitectura y Componentes

### Capa de API (FastAPI)

- **Punto de Entrada**: `main.py` -> `api/app.py`
- **Configuración Centralizada**: Toda la configuración de FastAPI en `api/app.py`
- **Routers Modulares**:
  - `api/routes/chat/`: Endpoints de chat
  - `api/routes/pdf/`: Gestión de PDFs
  - `api/routes/rag/`: Operaciones RAG
  - `api/routes.py`: Health check

### Capa de Servicios

1. **Gestión de Chat**

   - `ChatManager`: Orquestador principal
   - `Bot`: Interacción con LLM
   - `ChainManager`: Gestión de cadenas LangChain

2. **Sistema RAG**

   - `RAGIngestor`: Pipeline de ingesta
   - `RAGRetriever`: Recuperación de contexto
   - `PDFContentLoader`: Procesamiento de PDFs
   - `EmbeddingManager`: Gestión de embeddings
   - `VectorStore`: Almacenamiento vectorial

3. **Gestión de Archivos**

   - `PDFFileManager`: Operaciones de archivos
   - Estructura de directorios configurable

4. **Persistencia**
   - MongoDB para historial de chat
   - Vector store para embeddings
   - Sistema de archivos para PDFs

## Funcionalidades Principales

### 1. Gestión de Documentos

- Subida de PDFs
- Listado de documentos disponibles
- Eliminación de PDFs
- Procesamiento automático para RAG

### 2. RAG (Retrieval Augmented Generation)

- Indexación automática de documentos
- Búsqueda semántica
- Recuperación de contexto relevante
- Formateo de contexto para LLM

### 3. Chat Inteligente

- Respuestas basadas en contexto
- Memoria de conversación
- Streaming de respuestas
- Persistencia de historial

### 4. Configuración Flexible

- Variables de entorno
- Configuración de modelos
- Ajustes de RAG
- Personalización de prompts

## Estructura del Proyecto

\`\`\` backend/ ├── api/ # Capa de API │ ├── app.py # Configuración FastAPI │ ├── routes/ # Endpoints por contexto │ │ ├── chat/ │ │ ├── pdf/ │ │ └── rag/ │ └── schemas.py # Modelos Pydantic ├── chat/ # Gestión de chat │ └── manager.py # ChatManager ├── rag/ # Sistema RAG │ ├── embeddings/ # Gestión de embeddings │ ├── ingestion/ # Proceso de ingesta │ ├── pdf_processor/ # Procesamiento de PDFs │ ├── retrieval/ # Recuperación de documentos │ └── vector_store/ # Almacenamiento vectorial ├── file_system/ # Gestión de archivos │ └── pdf_file_manager.py # Operaciones PDF ├── database/ # Capa de persistencia ├── memory/ # Sistema de memoria ├── models/ # Tipos de modelos ├── common/ # Utilidades comunes ├── config.py # Configuración centralizada ├── bot.py # Lógica del bot └── chain.py # Gestión de cadenas \`\`\`

## Configuración y Despliegue

### Variables de Entorno (.env)

\`\`\`env

# LLM

MODEL_TYPE=OPENAI OPENAI_API_KEY=tu_clave BASE_MODEL_NAME=gpt-3.5-turbo MEMORY_TYPE=MONGO

# MongoDB

MONGO_URI=mongodb://localhost:27017/ MONGO_DATABASE_NAME=chatbot_rag_db

# Server

APP_TITLE="ChatBot RAG API" APP_VERSION="1.0.0" HOST=0.0.0.0 PORT=8000 LOG_LEVEL=INFO

# RAG

BASE_DATA_DIR="./data_storage" VECTOR_STORE_PATH="./data_storage/vector_store/chroma_db" EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2" RAG_CHUNK_SIZE=700 RAG_CHUNK_OVERLAP=150 \`\`\`

## Instalación y Ejecución

### Requisitos Previos

- Python 3.10 o superior
- pip (gestor de paquetes de Python)
- MongoDB instalado y ejecutándose localmente (o acceso a una instancia remota)

### Pasos de Instalación

1. **Crear y activar el entorno virtual**:

   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # Linux/Mac
   python -m venv venv
   source venv/bin/activate
   ```

2. **Instalar dependencias**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar variables de entorno**:

   - Crea un archivo `.env` en el directorio `backend/`
   - Copia el contenido del ejemplo de variables de entorno proporcionado más arriba
   - Ajusta los valores según tu configuración

4. **Iniciar el servidor**:
   ```bash
   # Desde el directorio backend/
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8080
   ```

### Solución de Problemas Comunes

1. **Error "No module named uvicorn"**:

   ```bash
   pip install uvicorn
   ```

2. **Error de conexión a MongoDB**:

   - Verifica que MongoDB esté ejecutándose
   - Comprueba la URI de conexión en el archivo `.env`

3. **Errores de dependencias**:

   ```bash
   # Actualizar pip
   python -m pip install --upgrade pip

   # Reinstalar dependencias
   pip install -r requirements.txt --no-cache-dir
   ```

## API Endpoints

### Chat

- `POST /api/v1/chat/stream_log`: Envía mensaje y recibe respuesta en streaming
- `POST /api/v1/chat/clear/{conversation_id}`: Limpia historial

### PDFs

- `POST /api/v1/pdfs/upload`: Sube PDF
- `GET /api/v1/pdfs/list-pdfs`: Lista PDFs disponibles
- `DELETE /api/v1/pdfs/delete-pdf/{filename}`: Elimina PDF

### RAG

- `POST /api/v1/rag/clear-all-content`: Limpia vector store
- `GET /api/v1/rag/status`: Estado del sistema RAG

## Contribución

1. Fork el repositorio
2. Crear rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Flujo de Datos

### Proceso de Chat con RAG

1. Usuario envía mensaje
2. `ChatManager` recibe la solicitud
3. `RAGRetriever` busca contexto relevante
4. Contexto se antepone al mensaje del usuario
5. `Bot` genera respuesta usando el contexto
6. Respuesta se almacena en MongoDB
7. Respuesta se envía al usuario

### Proceso de Ingesta de Documentos

1. PDF se sube vía API
2. `PDFFileManager` gestiona el archivo
3. `PDFContentLoader` procesa el contenido
4. `RAGIngestor` orquesta el proceso
5. Contenido se divide en chunks
6. `EmbeddingManager` genera embeddings
7. `VectorStore` almacena los vectores
