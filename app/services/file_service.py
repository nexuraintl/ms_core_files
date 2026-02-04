import sqlalchemy as sa
from sqlalchemy import create_engine
from ..config import Config

# Motor para la base de datos que contiene los binarios
engine_recursos = create_engine(Config.DB_RECURSOS_URL, pool_pre_ping=True)

def stream_binary_data(recurso_path: str):
    """
    Generador que conecta a la DB de recursos y entrega el binario por trozos (chunks).
    """
    query = sa.text("SELECT archivo_binario FROM tabla_archivos WHERE id_recurso = :path")
    
    with engine_recursos.connect() as conn:
        # Ejecutamos la consulta
        result = conn.execute(query, {"path": recurso_path})
        row = result.fetchone()
        
        if row and row[0]:
            # Suponiendo que row[0] es un BLOB
            # En drivers como PyMySQL, esto puede venir como bytes completos
            # Si el archivo es masivo, se requeriría lógica de fetchmany()
            yield row[0]