import os
import aiofiles
from fastapi import HTTPException

CHUNK_SIZE = 1024 * 1024 # 1MB

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
                chunk = await f.read(CHUNK_SIZE)
                if not chunk: break
                yield chunk