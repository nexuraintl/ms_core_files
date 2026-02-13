from fastapi import FastAPI, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from .database import get_db
from .models import DescargaAuditoria
import os
from fastapi.responses import FileResponse
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

app = FastAPI()

# Definimos la constante de la ruta donde está montado el NFS
NFS_MOUNT_PATH = "/app/media"

@app.get("/descargar/{ruta_archivo:path}")
async def descargar_archivo(ruta_archivo: str):
    # 1. Construimos la ruta absoluta uniendo el montaje con la ruta de la DB
    # Ejemplo: /app/media/public_html/uploads/foto.jpg
    path_final = os.path.join(NFS_MOUNT_PATH, ruta_archivo)

    # 2. Validación de seguridad y existencia
    if not os.path.exists(path_final):
        raise HTTPException(status_code=404, detail=f"Archivo no encontrado en la ruta: {path_final}")

    # 3. Servir el archivo
    # 'filename' es el nombre que verá el usuario al descargar
    nombre_descarga = os.path.basename(path_final)
    
    return FileResponse(
        path=path_final, 
        filename=nombre_descarga,
        media_type='application/octet-stream'
    )