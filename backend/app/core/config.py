from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Mercator Doc Library"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT - MUST be set via environment variable
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Elasticsearch
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    
    # ChromaDB
    CHROMADB_HOST: str = "localhost"
    CHROMADB_PORT: int = 8000
    
    # MinIO/S3
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "mercator-docs"
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000", 
        "http://localhost:8000",
        "https://docs.mercator.cn",
        "https://docsapi.mercator.cn"
    ]
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # seconds
    
    @field_validator('SECRET_KEY', 'DATABASE_URL')
    @classmethod
    def validate_required_fields(cls, v: str, info) -> str:
        if not v or v.strip() == '':
            raise ValueError(f"{info.field_name} must be set in environment variables")
        return v
    
    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key_strength(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        if v in ['your-secret-key-change-in-production', 'change-me', 'default-secret']:
            raise ValueError("SECRET_KEY must be changed from default value")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'  # Ignore extra environment variables


@lru_cache()
def get_settings():
    return Settings()
