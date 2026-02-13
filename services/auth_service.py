from sqlalchemy.orm import Session
from ..models import DescargaAuditoria

def validar_solicitud(db: Session, request_id: str, token: str):
    """
    Verifica que el request_id exista y el token coincida.
    """
    return db.query(DescargaAuditoria).filter(
        DescargaAuditoria.request_id == request_id,
        DescargaAuditoria.token == token,
        DescargaAuditoria.estado == 'PENDIENTE'
    ).first()

def actualizar_estado_auditoria(db: Session, registro: DescargaAuditoria, estado: str, bytes_sent: int):
    """
    Actualiza el registro tras completar el streaming.
    """
    registro.estado = estado
    registro.tamano_bytes = bytes_sent
    registro.codigo_http = 200
    db.commit()