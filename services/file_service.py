import os
import aiofiles
import mimetypes
import re
import asyncio
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
        """
        Iterador optimizado para descargas directas. 
        Se elimina el sleep para maximizar el throughput ahora que no dependemos del API Gateway.
        """
        # CHUNK_SIZE recomendado: 1024 * 1024 (1MB) para archivos grandes (>10MB)
        # o 64 * 1024 (64KB) para equilibrio.
        async with aiofiles.open(file_path, mode="rb") as f:
            while True:
                chunk = await f.read(settings.CHUNK_SIZE)
                if not chunk: 
                    break
                yield chunk


    @staticmethod
    def generate_friendly_filename(nombre_db: str, mime_type: str, audit_id: int) -> str:
        """
        Genera un nombre de archivo seguro para cabeceras Content-Disposition.
        """
        extension = None
        
        # 1. Determinar extensión del nombre original
        if nombre_db and "." in nombre_db:
            ext_extraida = os.path.splitext(nombre_db)[1].lower().strip()
            if 2 <= len(ext_extraida) <= 5: 
                extension = ext_extraida

        # 2. Fallback al MIME type
        if (not extension or extension == ".bin") and mime_type:
            m_type = mime_type.strip().lower()
            extension = mimetypes.guess_extension(m_type)
            
            # Ajustes manuales
            if not extension or extension == ".bin":
                if 'pdf' in m_type: extension = '.pdf'
                elif 'word' in m_type: extension = '.docx'
                elif 'excel' in m_type: extension = '.xlsx'
                elif 'zip' in m_type: extension = '.zip'
                elif 'jpeg' in m_type or 'jpg' in m_type: extension = '.jpg'

        if not extension: extension = ".bin"
        if extension == ".jpe": extension = ".jpg"

        # 3. Limpiar el nombre base
        raw_name = nombre_db if nombre_db else f"archivo_{audit_id}"
        base_name, _ = os.path.splitext(raw_name)

        # Solo caracteres seguros para headers HTTP
        base_name = re.sub(r'[^\w\s\.\-\(\)]', '', base_name)
        base_name = base_name.strip().rstrip('.')
        base_name = " ".join(base_name.split())[:150]
        
        if not base_name:
            base_name = f"archivo_{audit_id}"

        return f"{base_name}{extension}"