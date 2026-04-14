import os
from pydantic_settings import BaseSettings
from typing import Optional
from urllib.parse import quote_plus

class Settings(BaseSettings):

    # Datos de la DB de Gestión (Maestra)
    DB_GESTION_HOST: str = os.getenv("DB_GESTION_HOST")
    DB_GESTION_USER: str = os.getenv("DB_GESTION_USER")
    DB_GESTION_PASS: str = os.getenv("DB_GESTION_PASS")
    DB_GESTION_NAME: str = os.getenv("DB_GESTION_NAME", "gestion_clientes")
    DB_GESTION_PORT: int = int(os.getenv("DB_GESTION_PORT", 3306))

    @property
    def DATABASE_URL_GESTION(self) -> str:

        user_safe = quote_plus(self.DB_GESTION_USER) if self.DB_GESTION_USER else ""
        pass_safe = quote_plus(self.DB_GESTION_PASS) if self.DB_GESTION_PASS else ""

        return (
            f"mysql+aiomysql://{user_safe}:{pass_safe}@"
            f"{self.DB_GESTION_HOST}:{self.DB_GESTION_PORT}/{self.DB_GESTION_NAME}"
        )

    # Configuración del Microservicio
    APP_TITLE: str = "NFS Download Microservice"
    LOG_LEVEL: str = "INFO"
    
    # Parámetros de Performance
    # 1MB por chunk es ideal para no saturar la RAM en descargas grandes
    CHUNK_SIZE: int = 1024 * 1024 #256KB
    
    # Seguridad
    # Tiempo en segundos para el bloqueo anti-spam
    ANTI_SPAM_SECONDS: int = 10

    class Config:
        case_sensitive = True

# Instancia global para ser importada en otros archivos
settings = Settings()