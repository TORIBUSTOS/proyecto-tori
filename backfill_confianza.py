"""
Script de Backfill - Corregir confianza y fuente en registros existentes

Este script corrige movimientos que tienen categoría/subcategoría
pero confianza=0 o NULL, seteando valores por defecto razonables.

Uso:
    python backfill_confianza.py [--dry-run]

Opciones:
    --dry-run    Solo muestra qué haría sin modificar la base de datos
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.connection import SessionLocal
from backend.models.movimiento import Movimiento
from sqlalchemy import or_


def backfill_confianza(dry_run: bool = False):
    """
    Corrige movimientos con categoría/subcategoría pero confianza inválida.

    Args:
        dry_run: Si es True, solo muestra qué haría sin modificar la BD
    """
    db = SessionLocal()

    try:
        # Query: Movimientos con categoría/subcategoría pero confianza NULL o 0
        query = db.query(Movimiento).filter(
            Movimiento.categoria.isnot(None),
            Movimiento.categoria != "",
            Movimiento.categoria != "SIN_CATEGORIA",
            Movimiento.subcategoria.isnot(None),
            Movimiento.subcategoria != "",
            or_(
                Movimiento.confianza_porcentaje == None,
                Movimiento.confianza_porcentaje == 0
            )
        )

        movimientos = query.all()
        total = len(movimientos)

        if total == 0:
            print("✅ No hay movimientos que requieran corrección.")
            return

        print(f"📊 Encontrados {total} movimientos con categoría/subcategoría pero confianza inválida")
        print()

        if dry_run:
            print("🔍 DRY RUN - Mostrando primeros 10 registros que se corregirían:")
            print()

            for i, mov in enumerate(movimientos[:10], 1):
                print(f"{i}. ID={mov.id}, Fecha={mov.fecha}, Categoria={mov.categoria}, "
                      f"Subcategoria={mov.subcategoria}, Confianza={mov.confianza_porcentaje}")

            if total > 10:
                print(f"\n... y {total - 10} más.")

            print()
            print("💡 Acción a realizar:")
            print("   - confianza_porcentaje = 60")
            print("   - confianza_fuente = 'sin_fuente'")
            print()
            print("Para ejecutar realmente, corre: python backfill_confianza.py")
            return

        # Ejecutar corrección
        print("🔧 Aplicando correcciones...")
        actualizados = 0

        for mov in movimientos:
            mov.confianza_porcentaje = 60

            # Solo setear confianza_fuente si el modelo tiene el campo
            if hasattr(mov, 'confianza_fuente'):
                mov.confianza_fuente = "sin_fuente"

            actualizados += 1

        # Commit
        db.commit()

        print(f"✅ Corrección completada: {actualizados} movimientos actualizados")
        print()
        print("📋 Resumen:")
        print(f"   - Total procesados: {actualizados}")
        print(f"   - Confianza seteada: 60%")
        print(f"   - Fuente: 'sin_fuente'")
        print()
        print("💡 Ahora puedes ejecutar 'Aplicar Reglas' desde la UI para mejorar la confianza.")

    except Exception as e:
        db.rollback()
        print(f"❌ Error durante backfill: {e}")
        raise
    finally:
        db.close()


def main():
    """Función principal"""
    # Parsear argumentos
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("🔍 MODO DRY RUN - No se modificará la base de datos")
        print()

    backfill_confianza(dry_run=dry_run)


if __name__ == "__main__":
    main()
