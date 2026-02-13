import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # URLs de conexión a MySQL
    DB_AUDITORIA_URL = os.getenv("DB_AUDITORIA_URL")
    DB_RECURSOS_URL = os.getenv("DB_RECURSOS_URL")
    
    # Configuración de Cloud Run / Server
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Seguridad
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")