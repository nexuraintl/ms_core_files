import os
import aiofiles
import mimetypes
from datetime import datetime
from fastapi import HTTPException
from core.config import settings

class FileService:
    @staticmethod
    def get_secure_path(base_nfs_path: str, relative_path: str) -> str:
        # Aseguramos que la base existe
        if not os.path.exists(base_nfs_path):
            raise HTTPException(status_code=500, detail="Error interno: Ruta NFS no montada.")

        # Construcción segura
        safe_path = os.path.normpath(os.path.join(base_nfs_path, relative_path.lstrip("/")))
        
        if not safe_path.startswith(os.path.abspath(base_nfs_path)):
            raise HTTPException(status_code=403, detail="Acceso no permitido.")
            
        if not os.path.isfile(safe_path):
            raise HTTPException(status_code=404, detail="Archivo no encontrado en el volumen.")
            
        return safe_path

    @staticmethod
    async def file_iterator(file_path: str):
        async with aiofiles.open(file_path, mode="rb") as f:
            while True:
                chunk = await f.read(settings.CHUNK_SIZE)
                if not chunk: break
                yield chunk

    @staticmethod
    def generate_friendly_filename(mime_type: str, audit_id: int) -> str:
        """
        Determina la extensión basada en el MIME y genera un nombre con la fecha actual.
        """
        # Intentar obtener la extensión (ej: .pdf, .zip)
        extension = mimetypes.guess_extension(mime_type)
        
        # Caso especial: mimetypes a veces devuelve '.jpe' para image/jpeg o None si es desconocido
        if not extension or extension == ".jpe":
            extension = ".jpg" if "jpeg" in mime_type else ".bin"

        # Generar nombre: YYYYMMDD_HHMMSS_ID.ext
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"descarga_{timestamp}_{audit_id}{extension}"