"""
Script de migración para agregar control de importación por batches
Agrega:
- Tabla import_batches
- Columna batch_id a movimientos
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from sqlalchemy import text
from backend.database.connection import engine, get_db

def migrate():
    """
    Ejecuta la migración para agregar soporte de batches
    """
    print("=" * 80)
    print("MIGRACIÓN: Agregando control de importación por batches")
    print("=" * 80)

    with engine.connect() as conn:
        # 1. Crear tabla import_batches si no existe
        print("\n[1/3] Creando tabla import_batches...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS import_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename VARCHAR NOT NULL,
                file_hash VARCHAR NOT NULL,
                imported_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                rows_inserted INTEGER DEFAULT 0 NOT NULL
            )
        """))
        conn.commit()
        print("✓ Tabla import_batches creada")

        # 2. Crear índice en file_hash
        print("\n[2/3] Creando índice en file_hash...")
        conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_import_batches_file_hash
            ON import_batches (file_hash)
        """))
        conn.commit()
        print("✓ Índice único creado en file_hash")

        # 3. Agregar columna batch_id a movimientos si no existe
        print("\n[3/3] Agregando columna batch_id a movimientos...")
        try:
            # Verificar si la columna ya existe
            result = conn.execute(text("PRAGMA table_info(movimientos)"))
            columns = [row[1] for row in result]

            if 'batch_id' not in columns:
                conn.execute(text("""
                    ALTER TABLE movimientos
                    ADD COLUMN batch_id INTEGER
                """))
                conn.commit()
                print("✓ Columna batch_id agregada")

                # Crear índice
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_movimientos_batch_id
                    ON movimientos (batch_id)
                """))
                conn.commit()
                print("✓ Índice creado en batch_id")
            else:
                print("⚠ Columna batch_id ya existe, saltando...")

        except Exception as e:
            print(f"⚠ Error agregando columna batch_id: {e}")
            print("  (Puede ser que ya exista, continuando...)")

    print("\n" + "=" * 80)
    print("✓ MIGRACIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 80)
    print("\nCambios aplicados:")
    print("  - Tabla import_batches creada")
    print("  - Restricción única en file_hash para prevenir duplicados")
    print("  - Columna batch_id agregada a movimientos")
    print("  - Índice creado en batch_id para mejor rendimiento")
    print("\nAhora puedes:")
    print("  - Subir archivos Excel sin preocuparte por duplicados")
    print("  - Usar /api/dashboard?batch_id=X para ver un batch específico")
    print("  - Usar /api/dashboard?mostrar_historico=true para ver todo el histórico")
    print("=" * 80)


if __name__ == "__main__":
    migrate()
