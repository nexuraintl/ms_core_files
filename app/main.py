from fastapi import FastAPI, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from .database import get_db
from .models import DescargaAuditoria

app = FastAPI(title="PoC Auditoria Cloud Run")

@app.get("/verificar-descarga/{req_id}")
async def verificar_descarga(
    req_id: str = Path(..., title="Request ID", description="El identificador único de la solicitud"),
    db: Session = Depends(get_db)
):
    """
    Endpoint PoC: Consulta la tabla de auditoría y retorna los metadatos del archivo.
    """
    try:
        # Consulta filtrando por request_id
        registro = db.query(DescargaAuditoria).filter(
            DescargaAuditoria.request_id == req_id
        ).first()

        # Validación básica
        if not registro:
            raise HTTPException(
                status_code=404, 
                detail=f"No se encontró registro para request_id: {req_id}"
            )

        # Retorno exitoso (JSON) con los campos solicitados
        return {
            "status": "success",
            "data": {
                "request_id": registro.request_id,
                "recurso": registro.recurso,
                "mime": registro.mime,
                "estado": registro.estado,
                "db_id": registro.id # Útil para debug
            }
        }

    except Exception as e:
        # Captura errores de conexión a la BD
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno de base de datos: {str(e)}"
        )