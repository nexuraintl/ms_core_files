from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
# Eliminamos datetime.utcnow por compatibilidad y buenas prácticas, 
# la base de datos manejará las fechas o se consultarán tal cual vienen.

Base = declarative_base()

class DescargaAuditoria(Base):
    __tablename__ = 'tn_descargas_auditoria'

    # Mapeo exacto según tu descripción
    id = Column(Integer, primary_key=True)
    request_id = Column(String(100), nullable=False, index=True) # Index para búsqueda rápida
    recurso = Column(Text, nullable=False)
    mime = Column(String(100)) # Campo crítico para tu PoC
    estado = Column(String(50))
    
    # Otros campos de tu tabla (definidos para evitar errores si SQLAlchemy intenta mapear todo)
    fecha = Column(DateTime)
    ip = Column(String(45))
    usuario_id = Column(Integer)
    origen = Column(String(255))
    user_agent = Column(Text)
    codigo_http = Column(Integer)
    tamano_bytes = Column(Integer)
    duracion_ms = Column(Integer)
    fecha_actualizacion = Column(DateTime)