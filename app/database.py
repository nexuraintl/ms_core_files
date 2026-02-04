from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
import os

# 1. Obtenemos las variables de entorno individuales
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT", "3306")

# 2. Validación: Asegurarnos de que todas las variables necesarias existan
if not all([DB_USER, DB_PASS, DB_HOST, DB_NAME]):
    raise RuntimeError(
        "Faltan variables de entorno obligatorias (DB_USER, DB_PASS, DB_HOST, DB_NAME)."
    )

# 3. Codificación segura: Esto transforma caracteres como '#' o '|' automáticamente
user_encoded = quote_plus(DB_USER)
pass_encoded = quote_plus(DB_PASS)

# 4. Construcción de la URL de conexión
# Formato: mysql+pymysql://user:password@host:port/dbname
DATABASE_AUDITORIA_URL = (
    f"mysql+pymysql://{user_encoded}:{pass_encoded}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# 5. Configuración del Engine
engine_auditoria = create_engine(
    DATABASE_AUDITORIA_URL, 
    pool_pre_ping=True, 
    pool_size=5, 
    max_overflow=10,
    pool_recycle=1800 
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_auditoria)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()