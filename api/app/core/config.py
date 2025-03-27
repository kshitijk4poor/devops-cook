"""Configuration settings for the API."""

import os
from typing import Optional, Dict, Any

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
    
    # Logging settings
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="json")
    LOG_REQUEST_BODY: bool = Field(default=False)
    LOG_RESPONSE_BODY: bool = Field(default=False)
    LOG_SENSITIVE_HEADERS: list = Field(default=["Authorization", "Cookie", "X-API-Key"])
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    @property
    def log_config(self) -> Dict[str, Any]:
        """Return logging configuration dictionary."""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": "app.middleware.logging.JsonFormatter",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                },
            },
            "loggers": {
                "api": {
                    "handlers": ["console"],
                    "level": self.LOG_LEVEL,
                    "propagate": False,
                },
                "uvicorn": {
                    "handlers": ["console"],
                    "level": self.LOG_LEVEL,
                    "propagate": False,
                },
                "uvicorn.access": {
                    "handlers": ["console"],
                    "level": self.LOG_LEVEL,
                    "propagate": False,
                },
            },
            "root": {
                "handlers": ["console"],
                "level": self.LOG_LEVEL,
            },
        }


# Create a global settings object
settings = Settings()
