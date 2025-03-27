"""Configuration settings for the API."""

import os
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Settings for the API application."""
    
    APP_NAME: str = "API Observability Platform"
    DEBUG: bool = Field(default=False)
    API_PREFIX: str = "/api"
    VERSION: str = "0.1.0"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Environment-specific settings
    ENVIRONMENT: str = Field(default="development")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Create a global settings object
settings = Settings()
