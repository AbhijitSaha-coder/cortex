import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Cortex — AI Research & Knowledge Agent"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = "cortex-insecure-secret-key-change-in-production-09a8f7e6d5c4b3a2"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = "sqlite:///./cortex.db"
    
    # Redis & Background Tasks
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    TASK_ALWAYS_EAGER: bool = True  # Allows running tasks synchronously in dev/test when worker not running
    
    # AI Providers & Keys
    DEFAULT_LLM_PROVIDER: str = "mock"  # "openai", "gemini", "anthropic", "mock"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    
    OPENAI_MODEL: str = "gpt-4o-mini"
    GEMINI_MODEL: str = "gemini-1.5-flash"
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    
    # Embeddings
    DEFAULT_EMBEDDING_PROVIDER: str = "mock"  # "openai", "gemini", "mock"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536
    
    # Ingestion & Documents
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "txt", "md", "markdown"]
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    
    # Retrieval
    DEFAULT_TOP_K: int = 5
    RRF_K: int = 60
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

