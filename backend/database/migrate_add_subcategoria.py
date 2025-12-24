"""
Migración: Agregar columnas subcategoria y confianza_porcentaje

Fecha: 2024-12-16
Versión: 1.3.0
Descripción: Agrega soporte para categorización en cascada de 2 niveles
"""

import sqlite3
from pathlib import Path


def migrate():
    """Aplica la migración a la base de datos"""

    # Path a la base de datos
    db_path = Path(__file__).parent.parent.parent / "toro.db"

    if not db_path.exists():
        print(f"[ERROR] Base de datos no encontrada: {db_path}")
        return False

    print(f"[INFO] Conectando a: {db_path}")

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Verificar si las columnas ya existen
        cursor.execute("PRAGMA table_info(movimientos)")
        columns = {row[1] for row in cursor.fetchall()}

        # Migración 1: Agregar columna subcategoria
        if "subcategoria" not in columns:
            print("[MIGRATE] Agregando columna 'subcategoria'...")
            cursor.execute("""
                ALTER TABLE movimientos
                ADD COLUMN subcategoria TEXT
            """)
            print("[OK] Columna 'subcategoria' agregada")

            # Crear índice para subcategoria
            print("[MIGRATE] Creando índice para 'subcategoria'...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS ix_movimientos_subcategoria
                ON movimientos(subcategoria)
            """)
            print("[OK] Índice creado")
        else:
            print("[SKIP] Columna 'subcategoria' ya existe")

        # Migración 2: Agregar columna confianza_porcentaje
        if "confianza_porcentaje" not in columns:
            print("[MIGRATE] Agregando columna 'confianza_porcentaje'...")
            cursor.execute("""
                ALTER TABLE movimientos
                ADD COLUMN confianza_porcentaje INTEGER DEFAULT 0
            """)
            print("[OK] Columna 'confianza_porcentaje' agregada")
        else:
            print("[SKIP] Columna 'confianza_porcentaje' ya existe")

        # Commit changes
        conn.commit()

        # Verificar migración
        print("\n[VERIFY] Verificando estructura de tabla...")
        cursor.execute("PRAGMA table_info(movimientos)")
        columns_after = cursor.fetchall()

        print("\nEstructura de tabla 'movimientos':")
        print("-" * 60)
        for col in columns_after:
            col_id, name, type_, notnull, default, pk = col
            print(f"  {name:<25} {type_:<10} {'NOT NULL' if notnull else 'NULLABLE':<10} {'PK' if pk else ''}")

        # Estadísticas
        cursor.execute("SELECT COUNT(*) FROM movimientos")
        total_movimientos = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM movimientos WHERE subcategoria IS NOT NULL")
        con_subcategoria = cursor.fetchone()[0]

        print("\n[STATS] Estadísticas:")
        print(f"  Total movimientos: {total_movimientos}")
        print(f"  Con subcategoría: {con_subcategoria}")
        print(f"  Pendientes de recategorizar: {total_movimientos - con_subcategoria}")

        conn.close()

        print("\n[SUCCESS] Migración completada exitosamente")
        return True

    except sqlite3.Error as e:
        print(f"\n[ERROR] Error en migración: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False


def rollback():
    """
    Revertir la migración (solo para desarrollo)

    ADVERTENCIA: Esto eliminará las columnas y sus datos.
    SQLite no soporta DROP COLUMN directamente, requiere recrear tabla.
    """
    print("[WARNING] Rollback no implementado para SQLite")
    print("[INFO] Para revertir, restaura un backup de toro.db")
    return False


if __name__ == "__main__":
    print("=" * 70)
    print("MIGRACIÓN: Agregar subcategoria y confianza_porcentaje")
    print("=" * 70)
    print()

    success = migrate()

    if success:
        print("\n" + "=" * 70)
        print("MIGRACIÓN EXITOSA")
        print("=" * 70)
        print("\nPróximos pasos:")
        print("  1. Reiniciar el servidor FastAPI")
        print("  2. Ejecutar categorización con motor cascada:")
        print("     POST /api/categorizar")
        print("  3. Verificar que los movimientos tienen subcategoría")
    else:
        print("\n" + "=" * 70)
        print("MIGRACIÓN FALLIDA")
        print("=" * 70)
        print("\nRevisa los errores arriba y vuelve a intentar")
