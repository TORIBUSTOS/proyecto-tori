"""
Configuracion del proyecto TORO Investment Manager
Usa pydantic-settings para gestionar variables de entorno
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Configuracion de la aplicacion
    Lee variables desde .env o usa valores por defecto
    """

    # Base de datos
    DATABASE_URL: str = "sqlite:///./toro.db"

    # Security
    SECRET_KEY: str = "change-this-in-production"

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Paths
    ORIGINAL_PROJECT_PATH: str = "../sanarte_financiero"
    OUTPUT_PATH: str = "./output"

    # API
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000

    # Proyecto
    PROJECT_NAME: str = "TORO Investment Manager"
    VERSION: str = "2.1.0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Instancia global de configuracion
settings = Settings()
