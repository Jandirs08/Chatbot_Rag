# Estructura del Backend

## Estructura de Directorios

```
backend/
├── api/                    # API REST y endpoints
│   ├── routes/            # Rutas de la API
│   │   ├── chat.py       # Endpoints de chat
│   │   ├── documents.py  # Endpoints de documentos
│   │   └── rag.py        # Endpoints de RAG
│   ├── schemas/          # Esquemas Pydantic
│   │   ├── chat.py      # Esquemas de chat
│   │   ├── documents.py # Esquemas de documentos
│   │   └── rag.py       # Esquemas de RAG
│   ├── app.py           # Configuración de FastAPI
│   └── health_check_routes.py # Endpoints de salud
│
├── core/                  # Núcleo de la aplicación
│   ├── bot.py           # Lógica principal del bot
│   ├── chain.py         # Cadena de procesamiento
│   ├── prompt.py        # Gestión de prompts
│   └── gradio_ui.py     # Interfaz Gradio
│
├── rag/                  # Sistema RAG
│   ├── ingestion/       # Procesamiento de documentos
│   ├── embeddings/      # Generación de embeddings
│   ├── pdf_processor/   # Procesamiento de PDFs
│   ├── vector_store/    # Almacenamiento vectorial
│   └── retrieval/       # Recuperación de información
│
├── storage/             # Almacenamiento unificado
│   ├── documents/      # Documentos procesados
│   ├── embeddings/     # Embeddings generados
│   ├── vector_store/   # Base de datos vectorial
│   └── temp/          # Archivos temporales
│
├── file_system/         # Gestión de archivos
│   ├── pdf_file_manager.py # Gestor de PDFs
│   └── file_utils.py    # Utilidades de archivos
│
├── utils/               # Utilidades generales
│   ├── logger.py       # Sistema de logging
│   └── helpers.py      # Funciones auxiliares
│
├── models/              # Modelos de datos
│   ├── document.py     # Modelo de documento
│   └── chat.py         # Modelo de chat
│
├── memory/             # Gestión de memoria
│   └── memory_manager.py # Gestor de memoria
│
├── database/           # Base de datos
│   └── db_manager.py   # Gestor de base de datos
│
├── tools/              # Herramientas y utilidades
│   └── text_processor.py # Procesamiento de texto
│
├── common/             # Código compartido
│   └── constants.py    # Constantes globales
│
├── dev/                # Herramientas de desarrollo
│   └── test_utils.py   # Utilidades de prueba
│
├── config.py           # Configuración global
├── main.py            # Punto de entrada
└── requirements.txt    # Dependencias
```

## Descripción de Componentes

### API (`api/`)

- **routes/**: Endpoints de la API REST
  - `chat.py`: Endpoints para interacción con el chat
  - `documents.py`: Endpoints para gestión de documentos
  - `rag.py`: Endpoints para operaciones RAG
- **schemas/**: Esquemas Pydantic para validación
  - `chat.py`: Esquemas para mensajes y respuestas
  - `documents.py`: Esquemas para documentos
  - `rag.py`: Esquemas para operaciones RAG
- `app.py`: Configuración principal de FastAPI
- `health_check_routes.py`: Endpoints de monitoreo

### Core (`core/`)

- `bot.py`: Implementación principal del bot
- `chain.py`: Cadena de procesamiento de mensajes
- `prompt.py`: Gestión y templates de prompts
- `gradio_ui.py`: Interfaz de usuario Gradio

### RAG (`rag/`)

- **ingestion/**: Procesamiento de documentos
- **embeddings/**: Generación y gestión de embeddings
- **pdf_processor/**: Procesamiento específico de PDFs
- **vector_store/**: Almacenamiento y búsqueda vectorial
- **retrieval/**: Lógica de recuperación de información

### Storage (`storage/`)

- **documents/**: Almacenamiento de documentos procesados
- **embeddings/**: Almacenamiento de embeddings
- **vector_store/**: Base de datos vectorial
- **temp/**: Archivos temporales

### File System (`file_system/`)

- `pdf_file_manager.py`: Gestión de archivos PDF
- `file_utils.py`: Utilidades para manejo de archivos

### Utils (`utils/`)

- `logger.py`: Sistema de logging
- `helpers.py`: Funciones auxiliares

### Models (`models/`)

- `document.py`: Modelos de datos para documentos
- `chat.py`: Modelos de datos para chat

### Memory (`memory/`)

- `memory_manager.py`: Gestión de memoria y contexto

### Database (`database/`)

- `db_manager.py`: Gestión de base de datos

### Tools (`tools/`)

- `text_processor.py`: Procesamiento de texto

### Common (`common/`)

- `constants.py`: Constantes y configuraciones globales

### Dev (`dev/`)

- `test_utils.py`: Utilidades para pruebas

### Archivos Principales

- `config.py`: Configuración global de la aplicación
- `main.py`: Punto de entrada de la aplicación
- `requirements.txt`: Dependencias del proyecto
