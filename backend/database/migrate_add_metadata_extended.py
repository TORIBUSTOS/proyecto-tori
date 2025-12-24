"""
Migración: Agregar columnas extendidas de metadata al modelo Movimiento

Columnas a agregar:
- cbu (String, nullable)
- comercio (String, nullable)
- terminal (String, nullable)
- referencia (String, nullable)

Fecha: 2025-12-21
"""

import sqlite3
import os


def migrate():
    """Ejecuta la migración para agregar columnas de metadata extendidas"""

    # Path directo a la base de datos
    db_path = "toro.db"
    if not os.path.exists(db_path):
        print("❌ No se encontró toro.db")
        return

    print(f"🔄 Conectando a: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Verificar si las columnas ya existen
        cursor.execute("PRAGMA table_info(movimientos)")
        columns = [col[1] for col in cursor.fetchall()]

        columnas_a_agregar = []

        if 'cbu' not in columns:
            columnas_a_agregar.append(('cbu', 'TEXT'))
        if 'comercio' not in columns:
            columnas_a_agregar.append(('comercio', 'TEXT'))
        if 'terminal' not in columns:
            columnas_a_agregar.append(('terminal', 'TEXT'))
        if 'referencia' not in columns:
            columnas_a_agregar.append(('referencia', 'TEXT'))

        if not columnas_a_agregar:
            print("✅ Todas las columnas de metadata extendida ya existen")
            return

        print(f"📝 Agregando {len(columnas_a_agregar)} columnas nuevas...")

        # Agregar columnas una por una
        for nombre, tipo in columnas_a_agregar:
            print(f"   - Agregando columna '{nombre}' ({tipo})...")
            cursor.execute(f"ALTER TABLE movimientos ADD COLUMN {nombre} {tipo}")

        conn.commit()
        print(f"✅ Migración completada: {len(columnas_a_agregar)} columnas agregadas")

        # Verificar
        cursor.execute("SELECT COUNT(*) FROM movimientos")
        total_movimientos = cursor.fetchone()[0]
        print(f"📊 Total de movimientos en DB: {total_movimientos}")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error durante migración: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
