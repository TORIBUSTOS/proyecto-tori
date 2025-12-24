"""
Migración: Agregar columna 'saldo' a la tabla movimientos

Esta columna almacena el saldo bancario real después de cada movimiento,
tal como viene en el Excel consolidado.

Uso:
    python backend/database/migrate_add_saldo.py
"""

import sqlite3
import os

# Ruta a la base de datos
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "toro.db")

def migrate():
    """
    Agrega la columna 'saldo' a la tabla movimientos si no existe
    """
    print("\n" + "=" * 80)
    print("MIGRACIÓN: Agregar columna 'saldo' a movimientos")
    print("=" * 80)

    if not os.path.exists(DB_PATH):
        print(f"\n❌ ERROR: Base de datos no encontrada en {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Verificar si la columna ya existe
        cursor.execute("PRAGMA table_info(movimientos)")
        columns = [row[1] for row in cursor.fetchall()]

        if "saldo" in columns:
            print("\nOK - La columna 'saldo' ya existe en la tabla movimientos")
            print("   No se requiere migracion")
        else:
            print("\nAgregando columna 'saldo'...")
            cursor.execute("ALTER TABLE movimientos ADD COLUMN saldo REAL")
            conn.commit()
            print("OK - Columna 'saldo' agregada exitosamente")

            # Verificar
            cursor.execute("PRAGMA table_info(movimientos)")
            columns_after = [row[1] for row in cursor.fetchall()]

            if "saldo" in columns_after:
                print("OK - Verificacion exitosa: columna presente en tabla")
            else:
                print("ERROR - La columna no se agrego correctamente")

        # Mostrar estadísticas
        cursor.execute("SELECT COUNT(*) FROM movimientos WHERE saldo IS NULL")
        null_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM movimientos")
        total_count = cursor.fetchone()[0]

        print("\n" + "=" * 80)
        print("ESTADÍSTICAS:")
        print("=" * 80)
        print(f"Total de movimientos: {total_count}")
        print(f"Movimientos sin saldo: {null_count}")
        print(f"Movimientos con saldo: {total_count - null_count}")

        if null_count > 0:
            print("\nNOTA: Los movimientos existentes tienen saldo = NULL")
            print("   El saldo se llenara automaticamente en la proxima consolidacion")

        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\nERROR durante la migracion: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
