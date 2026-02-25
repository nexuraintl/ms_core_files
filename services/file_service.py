import os
import aiofiles
import mimetypes
import re
from datetime import datetime
from fastapi import HTTPException
from core.config import settings

# Registramos tipos MIME comunes que suelen no estar en la base estándar
mimetypes.add_type('application/x-zip-compressed', '.zip')
mimetypes.add_type('application/x-7z-compressed', '.7z')
mimetypes.add_type('application/vnd.rar', '.rar')

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
    def generate_friendly_filename(nombre_db: str, mime_type: str, audit_id: int) -> str:
        """
        Usa el nombre de la BD, limpia caracteres extraños y asegura la extensión correcta.
        """
        # 1. Determinar extensión
        extension = ".bin"
        if mime_type:
            mime_type = mime_type.strip().lower()
            extension = mimetypes.guess_extension(mime_type) or ".bin"
            
            # Ajustes manuales
            if not extension or extension == ".bin":
                if 'zip' in mime_type: extension = '.zip'
                elif 'pdf' in mime_type: extension = '.pdf'
                elif 'excel' in mime_type or 'spreadsheet' in mime_type: extension = '.xlsx'
            
            if extension == ".jpe": extension = ".jpg"

        # 2. Limpiar el nombre que viene de la BD (quitar caracteres no permitidos en archivos)
        # Si no hay nombre, usamos un fallback
        base_name = nombre_db if nombre_db else f"archivo_{audit_id}"
        
        # Eliminar cualquier cosa que no sea letras, números, puntos o guiones
        base_name = re.sub(r'[^\w\s\.-]', '', base_name)
        # Reemplazar espacios por guiones bajos
        base_name = base_name.replace(" ", "_")

        # 3. Retornar nombre final (asegurando que no se repita la extensión si el nombre ya la trae)
        if base_name.lower().endswith(extension.lower()):
            return base_name
            
        return f"{base_name}{extension}"