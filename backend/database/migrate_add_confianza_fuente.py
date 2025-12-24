"""
Migración: Agregar columna confianza_fuente a movimientos

Agrega columna para rastrear el origen de la categorización:
- manual: Categorizado manualmente por el usuario (confianza=100)
- regla_aprendida: Aplicada por regla aprendible (confianza=95)
- cascada: Aplicada por motor cascada (confianza=70-90)
- sin_fuente: Categorizado sin fuente conocida (confianza por defecto)

Versión: 2.3.0
Fecha: 2025-12-23
"""

import sqlite3
from pathlib import Path


def migrate():
    """
    Aplica migración para agregar columna confianza_fuente
    """
    # Path a la BD (en raíz del proyecto)
    db_path = Path(__file__).parent.parent.parent / "toro.db"

    print("=" * 80)
    print(" MIGRACIÓN: Agregar columna confianza_fuente")
    print("=" * 80)
    print()
    print(f"Base de datos: {db_path}")
    print()

    if not db_path.exists():
        print(f"❌ Error: Base de datos no encontrada en {db_path}")
        print()
        print("💡 Ejecuta primero: python -m backend.database.init_db")
        return

    # Conectar
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Agregar columna confianza_fuente
        print("[1/1] Agregando columna 'confianza_fuente'...")
        try:
            cursor.execute("ALTER TABLE movimientos ADD COLUMN confianza_fuente TEXT")
            print("      ✅ Columna 'confianza_fuente' agregada exitosamente")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("      ⚠️  Columna 'confianza_fuente' ya existe (skip)")
            else:
                raise

        # Commit
        conn.commit()
        print()
        print("=" * 80)
        print(" ✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 80)
        print()
        print("📋 Próximos pasos:")
        print("   1. (Opcional) Ejecuta backfill para datos viejos:")
        print("      python backfill_confianza.py --dry-run")
        print("      python backfill_confianza.py")
        print()
        print("   2. Ejecuta validación:")
        print("      python test_fix_confianza.py")
        print()
        print("   3. Aplica reglas desde la UI:")
        print("      POST /api/reglas/aplicar")
        print()

    except Exception as e:
        conn.rollback()
        print()
        print("=" * 80)
        print(" ❌ ERROR EN MIGRACIÓN")
        print("=" * 80)
        print()
        print(f"Error: {e}")
        print()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
