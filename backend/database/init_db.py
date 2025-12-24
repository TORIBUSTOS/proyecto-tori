"""
Inicialización de la base de datos
Crea las tablas definidas en los modelos ORM
"""

from backend.database.connection import engine, Base
from backend.models import Movimiento, ImportBatch, ReglaCategorizacion  # Importar todos los modelos


def init_db():
    """
    Crea todas las tablas en la base de datos
    Si las tablas ya existen, no hace nada
    """
    print("[INFO] Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("[OK] Tablas creadas exitosamente")


if __name__ == "__main__":
    # Permite ejecutar este script directamente
    init_db()
