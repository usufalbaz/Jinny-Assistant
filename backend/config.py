"""
Jinny Core - Global Configuration & Environment Settings
Architected & Engineered by Eng. Yousuf Albaz (AI & Systems Engineer)
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Jinny Core AI Assistant"
    VERSION: str = "2.4.0-Production"
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    DEBUG: bool = False
    
    # Security & Tokens
    AUTH_SECRET_KEY: str = os.getenv("AUTH_SECRET_KEY", "jinny_secret_production_key_92837482910")
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Persistent Memory Storage
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./jinny_memory.db")
    MEMORY_RETENTION_DAYS: int = 365
    
    # IoT & Home Automation
    MQTT_BROKER_HOST: Optional[str] = os.getenv("MQTT_BROKER_HOST", "localhost")
    MQTT_BROKER_PORT: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    MQTT_USERNAME: Optional[str] = os.getenv("MQTT_USERNAME", None)
    MQTT_PASSWORD: Optional[str] = os.getenv("MQTT_PASSWORD", None)
    HOME_ASSISTANT_URL: Optional[str] = os.getenv("HOME_ASSISTANT_URL", None)
    HOME_ASSISTANT_TOKEN: Optional[str] = os.getenv("HOME_ASSISTANT_TOKEN", None)
    
    # LLM Inference Provider
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
