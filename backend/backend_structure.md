# Estructura del Backend

```
backend/
├── api/                    # API REST y endpoints
│   ├── routes/            # Rutas de la API
│   │   ├── chat/         # Endpoints de chat
│   │   └── pdf/          # Endpoints de PDF
│   ├── schemas/          # Esquemas Pydantic
│   ├── app.py           # Configuración de FastAPI
│   └── __init__.py      # Inicialización de la API
│
├── core/                  # Núcleo de la aplicación
│   ├── bot.py           # Lógica principal del bot
│   ├── chain.py         # Gestión de cadenas de procesamiento
│   ├── prompt.py        # Gestión de prompts y personalidad
│   ├── README.md        # Documentación del core
│   └── __init__.py      # Inicialización del core
│
├── rag/                  # Sistema RAG
│   ├── ingestion/       # Procesamiento de documentos
│   ├── embeddings/      # Generación de embeddings
│   ├── pdf_processor/   # Procesamiento de PDFs
│   ├── vector_store/    # Almacenamiento vectorial
│   ├── retrieval/       # Recuperación de información
│   └── __init__.py      # Inicialización del RAG
│
├── storage/             # Almacenamiento unificado
│   ├── documents/      # Documentos procesados
│   └── vector_store/   # Base de datos vectorial
│
├── database/           # Base de datos
│   └── mongodb.py     # Conexión y operaciones con MongoDB
│
├── models/             # Modelos de datos
│   ├── model_types.py # Tipos de modelos soportados
│   └── __init__.py    # Inicialización de modelos
│
├── memory/            # Gestión de memoria
│   └── memory_manager.py # Gestor de memoria
│
├── utils/             # Utilidades generales
│   ├── cache.py      # Sistema de caché
│   └── __init__.py   # Inicialización de utilidades
│
├── common/            # Código compartido
│   └── constants.py   # Constantes globales
│
├── dev/               # Herramientas de desarrollo
│   └── test_utils.py  # Utilidades de prueba
│
├── config.py          # Configuración global
├── main.py           # Punto de entrada
├── requirements.txt   # Dependencias
├── setup.bat         # Script de configuración Windows
├── setup.sh          # Script de configuración Linux
└── Dockerfile        # Configuración de Docker
```

## Descripción de Componentes

### API (`api/`)

- **routes/**: Endpoints de la API REST
  - `chat/`: Endpoints para interacción con el chat
  - `pdf/`: Endpoints para gestión de PDFs
- **schemas/**: Esquemas Pydantic para validación
- `app.py`: Configuración principal de FastAPI

### Core (`core/`)

- `bot.py`: Implementación principal del bot
- `chain.py`: Gestión de cadenas de procesamiento
- `prompt.py`: Gestión de prompts y personalidad
- `README.md`: Documentación detallada del core

### RAG (`rag/`)

- **ingestion/**: Procesamiento de documentos
- **embeddings/**: Generación y gestión de embeddings
- **pdf_processor/**: Procesamiento específico de PDFs
- **vector_store/**: Almacenamiento y búsqueda vectorial
- **retrieval/**: Lógica de recuperación de información

### Storage (`storage/`)

- **documents/**: Almacenamiento de documentos procesados
- **vector_store/**: Base de datos vectorial

### Database (`database/`)

- `mongodb.py`: Gestión de conexión y operaciones con MongoDB

### Models (`models/`)

- `model_types.py`: Definición de tipos de modelos soportados

### Memory (`memory/`)

- `memory_manager.py`: Gestión de memoria y contexto

### Utils (`utils/`)

- `cache.py`: Sistema de caché para optimizar respuestas

### Common (`common/`)

- `constants.py`: Constantes y configuraciones globales

### Dev (`dev/`)

- `test_utils.py`: Utilidades para pruebas

### Archivos Principales

- `config.py`: Configuración global de la aplicación
- `main.py`: Punto de entrada de la aplicación
- `requirements.txt`: Dependencias del proyecto
- `setup.bat`: Script de configuración para Windows
- `setup.sh`: Script de configuración para Linux
- `Dockerfile`: Configuración para contenedorización

```

```
