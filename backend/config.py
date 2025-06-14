"""Configuration management for the chatbot application."""
import os
from typing import Any, Dict, Optional, List
from pydantic import Field, validator, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from the correct location
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

class Settings(BaseSettings):
    """Configuraciones de la aplicación."""
    
    # Configuraciones del Servidor
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=4, env="WORKERS")
    
    # Configuraciones de Seguridad
    api_key: SecretStr = Field(default=None, env="API_KEY")
    jwt_secret: Optional[SecretStr] = Field(default=None, env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    rate_limit: int = Field(default=100, env="RATE_LIMIT")
    ssl_keyfile: Optional[str] = Field(default=None, env="SSL_KEYFILE")
    ssl_certfile: Optional[str] = Field(default=None, env="SSL_CERTFILE")
    
    # Configuraciones de la App
    app_title: str = Field(default="ChatBot RAG API")
    app_description: str = Field(default="API para el ChatBot con RAG")
    app_version: str = Field(default="1.0.0")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Configuraciones de Logging
    log_level: str = Field(default="DEBUG", env="LOG_LEVEL")
    log_file: str = Field(default="app.log", env="LOG_FILE")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # Configuraciones del Modelo
    model_type: str = Field(default="OPENAI", env="MODEL_TYPE")
    openai_api_key: SecretStr = Field(..., env="OPENAI_API_KEY")
    base_model_name: str = Field(default="gpt-3.5-turbo", env="BASE_MODEL_NAME")
    max_tokens: int = Field(default=2000, env="MAX_TOKENS")
    temperature: float = Field(default=0.7, env="TEMPERATURE")
    bot_personality_name: Optional[str] = Field(default=None, env="BOT_PERSONALITY_NAME")
    system_prompt: Optional[str] = Field(default=None, env="SYSTEM_PROMPT")
    main_prompt_name: str = Field(default="ASESOR_ACADEMICO_REACT_PROMPT", env="MAIN_PROMPT_NAME")
    ai_prefix: str = Field(default="assistant", env="AI_PREFIX")
    human_prefix: str = Field(default="user", env="HUMAN_PREFIX")
    
    # Configuraciones de MongoDB
    mongo_uri: SecretStr = Field(..., env="MONGO_URI")
    mongo_database_name: str = Field(default="chatbot_rag_db", env="MONGO_DATABASE_NAME")
    mongo_collection_name: str = Field(default="chat_history", env="MONGO_COLLECTION_NAME") # <--- AÑADIR ESTA LÍNEA
    mongo_max_pool_size: int = Field(default=100, env="MONGO_MAX_POOL_SIZE")
    mongo_timeout_ms: int = Field(default=5000, env="MONGO_TIMEOUT_MS")
    
    # Configuraciones de Redis
    redis_url: Optional[SecretStr] = Field(default=None, env="REDIS_URL")
    redis_ttl: int = Field(default=3600, env="REDIS_TTL")
    redis_max_memory: str = Field(default="2gb", env="REDIS_MAX_MEMORY")
    
    # Configuraciones de Memoria
    memory_type: str = Field(default="BASE_MEMORY", env="MEMORY_TYPE")
    max_memory_entries: int = Field(default=1000, env="MAX_MEMORY_ENTRIES")
    
    # Configuraciones de RAG - Procesamiento de PDFs
    chunk_size: int = Field(default=700, env="RAG_CHUNK_SIZE")
    chunk_overlap: int = Field(default=150, env="RAG_CHUNK_OVERLAP")
    min_chunk_length: int = Field(default=100, env="MIN_CHUNK_LENGTH")
    max_file_size_mb: int = Field(default=10, env="MAX_FILE_SIZE_MB")
    
    # Configuraciones de RAG - Recuperación
    retrieval_k: int = Field(default=4, env="RETRIEVAL_K")
    retrieval_k_multiplier: int = Field(default=3, env="RETRIEVAL_K_MULTIPLIER")
    mmr_lambda_mult: float = Field(default=0.5, env="MMR_LAMBDA_MULT")
    similarity_threshold: float = Field(default=0.5, env="SIMILARITY_THRESHOLD")
    
    # Configuraciones de RAG - Ingesta
    batch_size: int = Field(default=100, env="BATCH_SIZE")
    deduplication_threshold: float = Field(default=0.95, env="DEDUP_THRESHOLD")
    max_concurrent_tasks: int = Field(default=4, env="MAX_CONCURRENT_TASKS")
    
    # Configuraciones de RAG - Vector Store
    vector_store_path: str = Field(default="./backend/storage/vector_store/chroma_db")
    distance_strategy: str = Field(default="cosine", env="DISTANCE_STRATEGY")
    
    # Configuraciones de RAG - Embeddings
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    embedding_batch_size: int = Field(default=32, env="EMBEDDING_BATCH_SIZE")
    
    # Configuraciones de RAG - Caché
    enable_cache: bool = Field(default=False, env="ENABLE_CACHE")
    cache_type: str = Field(default="RedisCache", env="CACHE_TYPE")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    max_cache_size: int = Field(default=1000, env="MAX_CACHE_SIZE")
    
    # Configuraciones de Directorios
    storage_dir: str = Field(default="./backend/storage", env="STORAGE_DIR")
    documents_dir: str = Field(default="./backend/storage/documents", env="DOCUMENTS_DIR")
    pdfs_dir: str = Field(default="./backend/storage/documents/pdfs", env="PDFS_DIR")
    cache_dir: str = Field(default="./backend/storage/cache", env="CACHE_DIR")
    temp_dir: str = Field(default="./backend/storage/temp", env="TEMP_DIR")
    backup_dir: str = Field(default="./backend/storage/backups", env="BACKUP_DIR")
    
    # Configuraciones de Monitoreo
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    enable_tracing: bool = Field(default=False, env="ENABLE_TRACING")
    enable_anonymizer: bool = Field(default=True, env="ENABLE_ANONYMIZER")
    
    # Configuración personalizada para cantidad máxima de documentos recuperados
    max_documents: int = Field(default=5, env="MAX_DOCUMENTS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    @validator("environment")
    def validate_environment(cls, v):
        allowed = ["development", "testing", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v
        
    @validator("log_level")
    def validate_log_level(cls, v):
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return v
        
    @validator("cors_origins")
    def validate_cors_origins(cls, v, values):
        if values.get("environment") == "production" and "*" in v:
            raise ValueError("Wildcard CORS origin (*) not allowed in production")
        return v
        
    @validator("temperature")
    def validate_temperature(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Temperature must be between 0 and 1")
        return v
        
    @validator("similarity_threshold", "deduplication_threshold")
    def validate_threshold(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Threshold values must be between 0 and 1")
        return v
        
    @validator("max_file_size_mb")
    def validate_max_file_size(cls, v):
        if v <= 0 or v > 100:
            raise ValueError("Max file size must be between 1 and 100 MB")
        return v

# Create global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings.
    
    Returns:
        Application settings object.
    """
    return settings