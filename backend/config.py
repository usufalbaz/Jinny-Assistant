"""
Jinny Core - Global Configuration & Environment Settings
Architected & Engineered by Eng. Yousuf Albaz (Applied AI & Systems Engineer)
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Jinny Core AI Assistant"
    VERSION: str = "4.0.0-Enterprise"
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    DEBUG: bool = False

    JINNY_API_KEY: str = os.getenv("JINNY_API_KEY", "jinny_live_sec_prod_9948201847192847")
    API_KEY_HEADER: str = "X-Jinny-Api-Key"
    ALLOWED_ORIGINS: List[str] = ["*"]

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./jinny_memory.db")
    MEMORY_RETENTION_DAYS: int = 365
    EMBEDDING_MODEL_NAME: str = "text-embedding-004"

    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    
    # Upgraded to 2026 Elite Models
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    
    GEMINI_TEMPERATURE: float = 0.3
    GEMINI_MAX_OUTPUT_TOKENS: int = 2048

    MQTT_BROKER_HOST: str = os.getenv("MQTT_BROKER_HOST", "localhost")
    MQTT_BROKER_PORT: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    MQTT_USERNAME: Optional[str] = os.getenv("MQTT_USERNAME", None)
    MQTT_PASSWORD: Optional[str] = os.getenv("MQTT_PASSWORD", None)
    MQTT_KEEPALIVE: int = 60
    MQTT_BASE_TOPIC: str = "jinny/devices"

    HOME_ASSISTANT_URL: Optional[str] = os.getenv("HOME_ASSISTANT_URL", None)
    HOME_ASSISTANT_TOKEN: Optional[str] = os.getenv("HOME_ASSISTANT_TOKEN", None)
    WOL_BROADCAST_IP: str = "255.255.255.255"
    WOL_PORT: int = 9

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore")

settings = Settings()
