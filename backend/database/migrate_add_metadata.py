"""
Migración: Agregar columnas de metadata a movimientos

Agrega 4 columnas para almacenar metadata extraída automáticamente:
- persona_nombre: Nombre de persona/empresa en transferencias
- documento: DNI/CUIL/CUIT
- es_debin: Boolean indicando si es DEBIN
- debin_id: ID único del DEBIN

Versión: 2.2.0
Fecha: 2025-12-16
"""

import sqlite3
from pathlib import Path

def migrate():
    """
    Aplica migración para agregar columnas de metadata
    """
    # Path a la BD (en raíz del proyecto)
    db_path = Path(__file__).parent.parent.parent / "toro.db"

    print("="*80)
    print(" MIGRACIÓN: Agregar columnas de metadata")
    print("="*80)
    print()
    print(f"Base de datos: {db_path}")
    print()

    # Conectar
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. Agregar columna persona_nombre
        print("[1/4] Agregando columna 'persona_nombre'...")
        try:
            cursor.execute("ALTER TABLE movimientos ADD COLUMN persona_nombre TEXT")
            print("      [OK] Columna 'persona_nombre' agregada")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("      [SKIP] Columna ya existe")
            else:
                raise

        # 2. Agregar columna documento con índice
        print("[2/4] Agregando columna 'documento' con índice...")
        try:
            cursor.execute("ALTER TABLE movimientos ADD COLUMN documento TEXT")
            print("      [OK] Columna 'documento' agregada")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("      [SKIP] Columna ya existe")
            else:
                raise

        try:
            cursor.execute("CREATE INDEX ix_movimientos_documento ON movimientos(documento)")
            print("      [OK] Índice creado")
        except sqlite3.OperationalError as e:
            if "already exists" in str(e):
                print("      [SKIP] Índice ya existe")
            else:
                raise

        # 3. Agregar columna es_debin con índice
        print("[3/4] Agregando columna 'es_debin' con índice...")
        try:
            cursor.execute("ALTER TABLE movimientos ADD COLUMN es_debin INTEGER DEFAULT 0")
            print("      [OK] Columna 'es_debin' agregada")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("      [SKIP] Columna ya existe")
            else:
                raise

        try:
            cursor.execute("CREATE INDEX ix_movimientos_es_debin ON movimientos(es_debin)")
            print("      [OK] Índice creado")
        except sqlite3.OperationalError as e:
            if "already exists" in str(e):
                print("      [SKIP] Índice ya existe")
            else:
                raise

        # 4. Agregar columna debin_id
        print("[4/4] Agregando columna 'debin_id'...")
        try:
            cursor.execute("ALTER TABLE movimientos ADD COLUMN debin_id TEXT")
            print("      [OK] Columna 'debin_id' agregada")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("      [SKIP] Columna ya existe")
            else:
                raise

        # Commit
        conn.commit()

        # Verificar estructura
        print()
        print("="*80)
        print(" VERIFICACIÓN DE ESTRUCTURA")
        print("="*80)
        cursor.execute("PRAGMA table_info(movimientos)")
        columns = cursor.fetchall()

        print(f"\nColumnas en tabla 'movimientos': {len(columns)}")
        print()
        print(f"{'ID':<5} {'Nombre':<25} {'Tipo':<15} {'Null':<6} {'Default':<10}")
        print("-"*70)
        for col in columns:
            cid, name, dtype, notnull, default, pk = col
            null_str = "NO" if notnull else "YES"
            default_str = str(default) if default else "-"
            print(f"{cid:<5} {name:<25} {dtype:<15} {null_str:<6} {default_str:<10}")

        # Estadísticas
        print()
        print("="*80)
        print(" ESTADÍSTICAS")
        print("="*80)

        cursor.execute("SELECT COUNT(*) FROM movimientos")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM movimientos WHERE persona_nombre IS NOT NULL")
        con_nombre = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM movimientos WHERE documento IS NOT NULL")
        con_doc = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM movimientos WHERE es_debin = 1")
        debins = cursor.fetchone()[0]

        print(f"\n  Total movimientos:              {total}")
        print(f"  Con persona_nombre:             {con_nombre}")
        print(f"  Con documento:                  {con_doc}")
        print(f"  Marcados como DEBIN:            {debins}")
        print(f"  Pendientes de extracción:       {total - max(con_nombre, con_doc)}")
        print()

        print("="*80)
        print(" MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("="*80)
        print()

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Migración fallida: {e}")
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
