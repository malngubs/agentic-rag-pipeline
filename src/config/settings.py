"""
Fixed Configuration management for the Agentic RAG Pipeline.

This module provides centralized configuration management using Pydantic settings.
It supports environment variables, .env files, and validation.
"""

import os
from pathlib import Path
from typing import List, Optional, Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv

# Load .env file explicitly
load_dotenv()


class AppSettings(BaseSettings):
    """Main application settings."""
    
    # Basic app configuration
    environment: Literal["development", "staging", "production"] = Field(
        default="development", 
        env="ENVIRONMENT"
    )
    debug: bool = Field(default=False, env="DEBUG")
    app_name: str = Field(default="Agentic RAG Pipeline", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    api_host: str = Field(default="localhost", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    
    # Security settings - these are required
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    encryption_key: str = Field(..., env="ENCRYPTION_KEY")
    
    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v):
        """Ensure JWT secret key is secure."""
        if len(v) < 32:
            raise ValueError("JWT secret key must be at least 32 characters long")
        return v
    
    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, v):
        """Ensure encryption key is valid length."""
        if len(v) != 32:
            raise ValueError("Encryption key must be exactly 32 characters long")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # This allows extra environment variables without errors


class OllamaSettings(BaseSettings):
    """Ollama LLM configuration."""
    
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    primary_model: str = Field(default="llama3.2:3b-instruct-q4_K_M", env="PRIMARY_MODEL")
    embedding_model: str = Field(default="nomic-embed-text", env="EMBEDDING_MODEL")
    reranker_model: str = Field(default="BAAI/bge-reranker-base", env="RERANKER_MODEL")
    fallback_model: str = Field(default="mistral:7b-instruct", env="FALLBACK_MODEL")
    
    # Model performance settings
    model_temperature: float = Field(default=0.1, env="MODEL_TEMPERATURE")
    model_top_p: float = Field(default=0.9, env="MODEL_TOP_P")
    model_max_tokens: int = Field(default=2048, env="MODEL_MAX_TOKENS")
    model_timeout: int = Field(default=60, env="MODEL_TIMEOUT")

    class Config:
        env_file = ".env"
        extra = "ignore"


class QdrantSettings(BaseSettings):
    """Qdrant vector database configuration."""
    
    qdrant_host: str = Field(default="localhost", env="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, env="QDRANT_PORT")
    qdrant_path: str = Field(default="./data/qdrant", env="QDRANT_PATH")
    qdrant_collection_name: str = Field(default="documents", env="QDRANT_COLLECTION_NAME")
    
    # Vector settings
    vector_dimension: int = Field(default=384, env="VECTOR_DIMENSION")  # Default for nomic-embed-text
    distance_metric: str = Field(default="cosine", env="DISTANCE_METRIC")
    hnsw_ef_construct: int = Field(default=128, env="HNSW_EF_CONSTRUCT")
    hnsw_m: int = Field(default=16, env="HNSW_M")

    class Config:
        env_file = ".env"
        extra = "ignore"


class RedisSettings(BaseSettings):
    """Redis configuration for caching and queues."""
    
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    
    # Connection pool settings
    redis_max_connections: int = Field(default=10, env="REDIS_MAX_CONNECTIONS")
    redis_socket_timeout: int = Field(default=5, env="REDIS_SOCKET_TIMEOUT")
    redis_socket_connect_timeout: int = Field(default=5, env="REDIS_SOCKET_CONNECT_TIMEOUT")

    class Config:
        env_file = ".env"
        extra = "ignore"


class DocumentSettings(BaseSettings):
    """Document processing configuration."""
    
    documents_path: str = Field(default="./data/documents", env="DOCUMENTS_PATH")
    max_file_size_mb: int = Field(default=50, env="MAX_FILE_SIZE_MB")
    allowed_file_types: List[str] = Field(default=["pdf", "docx", "txt", "md"], env="ALLOWED_FILE_TYPES")
    
    # Chunking settings
    max_chunk_size: int = Field(default=512, env="MAX_CHUNK_SIZE")
    chunk_overlap: int = Field(default=64, env="CHUNK_OVERLAP")
    min_chunk_size: int = Field(default=50, env="MIN_CHUNK_SIZE")
    
    # Processing settings
    extract_images: bool = Field(default=False, env="EXTRACT_IMAGES")
    extract_tables: bool = Field(default=True, env="EXTRACT_TABLES")
    preserve_formatting: bool = Field(default=True, env="PRESERVE_FORMATTING")
    
    @field_validator("documents_path")
    @classmethod
    def create_documents_path(cls, v):
        """Ensure documents directory exists."""
        Path(v).mkdir(parents=True, exist_ok=True)
        return v

    class Config:
        env_file = ".env"
        extra = "ignore"


class RetrievalSettings(BaseSettings):
    """RAG retrieval configuration."""
    
    retrieval_k: int = Field(default=8, env="RETRIEVAL_K")
    rerank_top_k: int = Field(default=4, env="RERANK_TOP_K")
    bm25_weight: float = Field(default=0.4, env="BM25_WEIGHT")
    dense_weight: float = Field(default=0.6, env="DENSE_WEIGHT")
    similarity_threshold: float = Field(default=0.7, env="SIMILARITY_THRESHOLD")
    
    # Advanced retrieval settings
    enable_hybrid_search: bool = Field(default=True, env="ENABLE_HYBRID_SEARCH")
    enable_reranking: bool = Field(default=True, env="ENABLE_RERANKING")
    enable_query_expansion: bool = Field(default=False, env="ENABLE_QUERY_EXPANSION")
    max_context_length: int = Field(default=8000, env="MAX_CONTEXT_LENGTH")

    class Config:
        env_file = ".env"
        extra = "ignore"


class MonitoringSettings(BaseSettings):
    """Monitoring and observability configuration."""
    
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    
    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_path: str = Field(default="./data/logs", env="LOG_PATH")
    log_rotation: str = Field(default="1 day", env="LOG_ROTATION")
    log_retention: str = Field(default="30 days", env="LOG_RETENTION")
    
    # Structured logging
    enable_structured_logging: bool = Field(default=True, env="ENABLE_STRUCTURED_LOGGING")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    @field_validator("log_path")
    @classmethod
    def create_log_path(cls, v):
        """Ensure log directory exists."""
        Path(v).mkdir(parents=True, exist_ok=True)
        return v

    class Config:
        env_file = ".env"
        extra = "ignore"


class RateLimitSettings(BaseSettings):
    """Rate limiting configuration."""
    
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    rate_limit_per_day: int = Field(default=10000, env="RATE_LIMIT_PER_DAY")
    
    # Per-tenant limits
    tenant_rate_limit_multiplier: float = Field(default=1.0, env="TENANT_RATE_LIMIT_MULTIPLIER")
    premium_tenant_multiplier: float = Field(default=5.0, env="PREMIUM_TENANT_MULTIPLIER")

    class Config:
        env_file = ".env"
        extra = "ignore"


class WidgetSettings(BaseSettings):
    """Frontend widget configuration."""
    
    widget_enabled: bool = Field(default=True, env="WIDGET_ENABLED")
    widget_max_message_length: int = Field(default=4000, env="WIDGET_MAX_MESSAGE_LENGTH")
    widget_theme_primary: str = Field(default="#007bff", env="WIDGET_THEME_PRIMARY")
    widget_theme_accent: str = Field(default="#28a745", env="WIDGET_THEME_ACCENT")
    widget_theme_background: str = Field(default="#ffffff", env="WIDGET_THEME_BACKGROUND")
    
    # Widget features
    enable_file_upload: bool = Field(default=True, env="ENABLE_FILE_UPLOAD")
    enable_voice_input: bool = Field(default=False, env="ENABLE_VOICE_INPUT")
    enable_dark_mode: bool = Field(default=True, env="ENABLE_DARK_MODE")
    enable_export: bool = Field(default=True, env="ENABLE_EXPORT")

    class Config:
        env_file = ".env"
        extra = "ignore"


class Settings(BaseSettings):
    """Main settings class that combines all configuration sections."""
    
    app: AppSettings = AppSettings()
    ollama: OllamaSettings = OllamaSettings()
    qdrant: QdrantSettings = QdrantSettings()
    redis: RedisSettings = RedisSettings()
    documents: DocumentSettings = DocumentSettings()
    retrieval: RetrievalSettings = RetrievalSettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    rate_limiting: RateLimitSettings = RateLimitSettings()
    widget: WidgetSettings = WidgetSettings()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # This is the key fix!


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    This function uses LRU cache to ensure settings are loaded only once
    and reused throughout the application lifecycle.
    
    Returns:
        Settings: Configured settings instance
    """
    return Settings()


# Convenience functions for getting specific setting sections
def get_app_settings() -> AppSettings:
    """Get application settings."""
    return get_settings().app


def get_ollama_settings() -> OllamaSettings:
    """Get Ollama settings."""
    return get_settings().ollama


def get_qdrant_settings() -> QdrantSettings:
    """Get Qdrant settings."""
    return get_settings().qdrant


def get_redis_settings() -> RedisSettings:
    """Get Redis settings."""
    return get_settings().redis


def get_document_settings() -> DocumentSettings:
    """Get document processing settings."""
    return get_settings().documents


def get_retrieval_settings() -> RetrievalSettings:
    """Get retrieval settings."""
    return get_settings().retrieval


# Example usage and validation
if __name__ == "__main__":
    # Test settings loading
    try:
        settings = get_settings()
        print(f"Settings loaded successfully")
        print(f"   App: {settings.app.app_name} v{settings.app.app_version}")
        print(f"   Environment: {settings.app.environment}")
        print(f"   Primary Model: {settings.ollama.primary_model}")
        print(f"   Vector DB: {settings.qdrant.qdrant_collection_name}")
        
    except Exception as e:
        print(f"Settings validation failed: {e}")
        raise