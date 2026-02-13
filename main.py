import time
import os
import logging
from datetime import datetime, timedelta
from typing import Dict

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update

# Importaciones locales (asegúrate de que los archivos existan)
from models import DescargaAuditoria
from services.file_service import FileService
from database import get_config_from_secret, get_db_session, get_engine_for_domain

# Configuración de Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NFS-Service")

app = FastAPI(title="NFS Download Microservice - MultiDomain")

# Cache simple para el secreto (para no llamar a Google API en cada petición)
# Se refrescará cada vez que se reinicie el pod o podrías implementar un TTL.
CONFIG_CACHE: Dict = {}

def obtener_configuracion():
    global CONFIG_CACHE
    if not CONFIG_CACHE:
        CONFIG_CACHE = get_config_from_secret()
    return CONFIG_CACHE

# --- Lógica de Auditoría Final ---
async def finalizar_auditoria(audit_id: int, estado: str, bytes_enviados: int, start_time: float, domain: str, config: dict):
    """
    Actualiza el estado final en la base de datos específica del dominio.
    """
    duracion = (time.time() - start_time) * 1000  # ms
    
    # Obtenemos el motor específico para este dominio
    engine = get_engine_for_domain(domain, config)
    
    async with AsyncSession(engine) as session:
        try:
            stmt = (
                update(DescargaAuditoria)
                .where(DescargaAuditoria.id == audit_id)
                .values(
                    estado=estado,
                    duracion_ms=duracion,
                    tamano_bytes=bytes_enviados,
                    fecha_actualizacion=datetime.utcnow()
                )
            )
            await session.execute(stmt)
            await session.commit()
            logger.info(f"[{domain}] Auditoría {audit_id} finalizada: {estado}")
        except Exception as e:
            logger.error(f"[{domain}] Error al cerrar auditoría {audit_id}: {e}")

# --- Endpoint Principal ---
@app.get("/download/{audit_id}")
async def download_file(audit_id: int, request: Request):
    start_time = time.time()
    
    # 1. Identificar Dominio y Configuración
    domain = request.headers.get("x-forwarded-host", request.headers.get("host"))
    full_config = obtener_configuracion()
    
    if domain not in full_config:
        logger.error(f"Dominio no autorizado: {domain}")
        raise HTTPException(status_code=403, detail="Dominio no configurado.")
    
    domain_cfg = full_config[domain]
    nfs_base_path = domain_cfg["nfs_mount_path"]
    client_ip = request.client.host

    # 2. Obtener sesión de base de datos dinámica
    # Usamos el generador manual para asegurar que cerramos la conexión
    async for db in get_db_session(domain, full_config):
        
        # 3. Buscar el registro de auditoría
        result = await db.execute(select(DescargaAuditoria).where(DescargaAuditoria.id == audit_id))
        registro = result.scalars().first()

        if not registro:
            raise HTTPException(status_code=404, detail="ID de auditoría no encontrado.")

        # 4. Protección Anti-Spam / Concurrencia
        # Regla: No permitir si hay otra descarga activa para la misma IP y Recurso en los últimos 10 seg
        tiempo_limite = datetime.utcnow() - timedelta(seconds=10)
        
        query_spam = select(func.count()).where(
            and_(
                DescargaAuditoria.ip == client_ip,
                DescargaAuditoria.recurso == registro.recurso,
                DescargaAuditoria.estado.in_(['PENDING', 'REDIRECTED']),
                DescargaAuditoria.fecha_actualizacion >= tiempo_limite,
                DescargaAuditoria.id != audit_id
            )
        )
        spam_result = await db.execute(query_spam)
        if spam_result.scalar() > 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS, 
                detail="Descarga en curso. Espere unos segundos."
            )

        # 5. Validar ruta física en NFS (Usando el path dinámico del dominio)
        try:
            full_path = FileService.get_secure_path(nfs_base_path, registro.recurso)
        except HTTPException as e:
            await finalizar_auditoria(audit_id, "FAILED", 0, start_time, domain, full_config)
            raise e

        # 6. Actualizar a REDIRECTED
        registro.estado = "REDIRECTED"
        registro.ip = client_ip
        registro.fecha_actualizacion = datetime.utcnow()
        await db.commit()

        # 7. Generador de Stream con contador de bytes
        async def stream_con_auditoria():
            bytes_count = 0
            try:
                async for chunk in FileService.file_iterator(full_path):
                    bytes_count += len(chunk)
                    yield chunk
                
                # Éxito
                await finalizar_auditoria(audit_id, "COMPLETED", bytes_count, start_time, domain, full_config)
                
            except Exception as e:
                # El cliente canceló o hubo error de red
                logger.error(f"Stream interrumpido para {audit_id}: {e}")
                await finalizar_auditoria(audit_id, "FAILED", bytes_count, start_time, domain, full_config)

        # Retornamos la respuesta Streaming
        filename = os.path.basename(full_path)
        return StreamingResponse(
            stream_con_auditoria(),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Content-Type-Options": "nosniff"
            }
        )

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow()}