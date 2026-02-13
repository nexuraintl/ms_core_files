from fastapi import FastAPI, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from .database import get_db
from .models import DescargaAuditoria
import os
from fastapi.responses import JSONResponse
app = FastAPI(title="PoC Auditoria Cloud Run")

@app.get("/verificar-descarga/{req_id}")
async def verificar_descarga(
    req_id: str = Path(..., title="ID", description="El identificador único de la solicitud"),
    db: Session = Depends(get_db)
):
    """
    Endpoint PoC: Consulta la tabla de auditoría y retorna los metadatos del archivo.
    """
    try:
        # Consulta filtrando por request_id
        registro = db.query(DescargaAuditoria).filter(
            DescargaAuditoria.id == req_id
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

@app.get("/verificar-lectura/")
async def test_nfs_read():
    # Usamos uno de los archivos que ya sabemos que existen
    archivo_prueba = "/app/media/includes-media.txt"
    
    try:
        with open(archivo_prueba, "r") as f:
            primeras_lineas = f.readlines()[:3] # Lee solo las primeras 3 líneas
        return {
            "status": "exito",
            "archivo": archivo_prueba,
            "contenido_previa": primeras_lineas
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error_lectura", "mensaje": str(e)}
        )