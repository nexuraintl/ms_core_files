from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Solo requerimos esta URL para la PoC
DATABASE_AUDITORIA_URL = os.getenv("DATABASE_AUDITORIA_URL")

if not DATABASE_AUDITORIA_URL:
    # Fail fast: Si no hay string de conexión, no tiene sentido arrancar
    raise RuntimeError("La variable de entorno DATABASE_AUDITORIA_URL es obligatoria.")

engine_auditoria = create_engine(
    DATABASE_AUDITORIA_URL, 
    pool_pre_ping=True, 
    pool_size=5, 
    max_overflow=10,
    pool_recycle=1800 # Reiniciar conexiones cada 30 min
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_auditoria)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()