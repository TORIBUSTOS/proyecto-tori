"""
Migración: Agregar columna banco_origen a Movimiento
ETAPA 5.1: Detección Automática de Banco
"""

from sqlalchemy import create_engine, text
from backend.database.connection import get_database_url
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """
    Agrega la columna banco_origen a la tabla movimientos.

    Columna:
    - banco_origen (String, nullable=True): Banco de origen del movimiento
      Valores posibles: SUPERVIELLE, GALICIA, DESCONOCIDO
    """
    engine = create_engine(get_database_url())

    with engine.connect() as conn:
        try:
            # Verificar si la columna ya existe
            result = conn.execute(text("PRAGMA table_info(movimientos)"))
            columnas = [row[1] for row in result]

            if "banco_origen" in columnas:
                logger.info("✅ La columna 'banco_origen' ya existe. Migración no necesaria.")
                return

            # Agregar columna banco_origen
            logger.info("📝 Agregando columna 'banco_origen'...")
            conn.execute(text("""
                ALTER TABLE movimientos
                ADD COLUMN banco_origen TEXT
            """))
            conn.commit()

            logger.info("✅ Columna 'banco_origen' agregada exitosamente")

            # Estadísticas
            result = conn.execute(text("SELECT COUNT(*) FROM movimientos"))
            total_movimientos = result.scalar()

            logger.info(f"""
╔══════════════════════════════════════════════════╗
║  MIGRACIÓN COMPLETADA - banco_origen             ║
╠══════════════════════════════════════════════════╣
║  📊 Total movimientos: {total_movimientos:,}                   ║
║  🏦 Columna: banco_origen (TEXT, NULL)           ║
║  📝 Valores: SUPERVIELLE, GALICIA, DESCONOCIDO   ║
║  ✅ Estado: EXITOSO                              ║
╚══════════════════════════════════════════════════╝
            """)

        except Exception as e:
            logger.error(f"❌ Error en migración: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    logger.info("🚀 Iniciando migración: Agregar banco_origen")
    migrate()
    logger.info("✅ Migración completada")
