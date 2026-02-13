from fastapi import FastAPI, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from .database import get_db
from .models import DescargaAuditoria
import os

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

@app.get("/verificar-nfs/")
async def test_nfs_access():
    nfs_path = "/app/media"
    print(f"--- Iniciando prueba de NFS en: {nfs_path} ---")
    
    # 1. ¿Existe la carpeta?
    if os.path.exists(nfs_path):
        print(f"✅ La carpeta {nfs_path} es visible.")
        
        # 2. ¿Qué hay adentro? (limitado a 5 para no saturar)
        try:
            files = os.listdir(nfs_path)
            print(f"📁 Contenido encontrado: {files[:5]}")
        except Exception as e:
            print(f"❌ Error al listar archivos: {e}")
            
        # 3. ¿Podemos escribir? (Prueba de permisos)
        try:
            test_file = os.path.join(nfs_path, "test_desde_cloudrun.txt")
            with open(test_file, "w") as f:
                f.write("Cloud Run estuvo aquí")
            print("📝 Prueba de escritura: EXITOSA")
        except Exception as e:
            print(f"❌ Error de escritura (Permisos): {e}")
    else:
        print(f"⚠️ La ruta {nfs_path} NO existe en el contenedor.")

test_nfs_access()