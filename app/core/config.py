"""
Configuration module for the AI Agent application.
Manages environment variables and application settings.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application configuration settings.
    All values are loaded from environment variables.
    """
    
    # Application Settings
    APP_NAME: str = "AI Agent RAG Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_DEPLOYMENT_NAME: str = ""
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME: str = ""
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"
    
    # Azure AI Search Configuration
    AZURE_SEARCH_SERVICE_ENDPOINT: str = ""
    AZURE_SEARCH_ADMIN_KEY: str = ""
    AZURE_SEARCH_INDEX_NAME: str = "rag-index"
    
    # RAG Configuration
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K_RESULTS: int = 3
    SIMILARITY_THRESHOLD: float = 0.7
    
    # Documents Configuration
    DOCUMENTS_PATH: str = "documents"
    
    # Session Configuration
    MAX_SESSION_HISTORY: int = 10
    SESSION_TIMEOUT_MINUTES: int = 60

    # Model Parameters
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 1000
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"


# Clear cache if exists
get_settings_cached = None


def get_settings() -> Settings:
    """
    Returns settings instance.
    """
    global get_settings_cached
    if get_settings_cached is None:
        get_settings_cached = Settings()
    return get_settings_cached


# Export settings instance for convenience
settings = get_settings()
