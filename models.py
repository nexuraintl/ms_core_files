from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class DescargaAuditoria(Base):
    __tablename__ = "tn_descargas_auditoria"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, nullable=True)
    ip = Column(String(45), index=True)
    recurso = Column(String(500))  # El path en el NFS
    estado = Column(String(20), default="PENDING") # PENDING, REDIRECTED, COMPLETED, FAILED
    duracion_ms = Column(Float, default=0.0)
    tamano_bytes = Column(BigInteger, default=0)
    dominio = Column(String(255))
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)