"""
Validación de extractores con movimientos reales de la BD
"""

from backend.database.connection import get_db
from backend.models.movimiento import Movimiento
from backend.core.extractores import extraer_metadata_completa

def test_extractores_con_datos_reales():
    """
    Prueba extractores con movimientos reales de la BD
    """
    db = next(get_db())

    print("="*100)
    print(" VALIDACIÓN EXTRACTORES CON DATOS REALES")
    print("="*100)
    print()

    # Buscar diferentes tipos de movimientos
    tests = [
        ("Transferencias recibidas", "%Transferencia recibida%", 3),
        ("DEBIN recibidos", "%Credito DEBIN%", 3),
        ("Compras con débito", "%Compra Visa D_bito%", 3),
        ("Débitos automáticos", "%D_bito Autom_tico%", 3),
    ]

    total_procesados = 0
    total_con_metadata = 0

    for nombre_tipo, patron, limite in tests:
        print(f"\n{'='*100}")
        print(f" {nombre_tipo}")
        print(f"{'='*100}\n")

        movs = db.query(Movimiento).filter(Movimiento.descripcion.like(patron)).limit(limite).all()

        for mov in movs:
            total_procesados += 1

            # Extraer metadata
            metadata = extraer_metadata_completa(mov.descripcion, mov.descripcion)

            # Contar si tiene alguna metadata
            tiene_metadata = any([
                metadata['persona_nombre'],
                metadata['documento'],
                metadata['es_debin'],
                metadata['debin_id'],
                metadata['cbu'],
                metadata['terminal'],
                metadata['comercio'],
                metadata['referencia']
            ])

            if tiene_metadata:
                total_con_metadata += 1

            # Mostrar resultado
            desc_corta = mov.descripcion[:80] + "..." if len(mov.descripcion) > 80 else mov.descripcion
            print(f"[MOV #{mov.id}]")
            print(f"  Descripción: {desc_corta}")
            print(f"  Metadata extraída:")

            for key, value in metadata.items():
                if value:
                    print(f"    - {key}: {value}")

            if not tiene_metadata:
                print(f"    (sin metadata extraíble)")

            print()

    # Resumen
    print("="*100)
    print(" RESUMEN")
    print("="*100)
    print(f"  Total movimientos procesados:     {total_procesados}")
    print(f"  Con metadata extraída:            {total_con_metadata}")
    print(f"  Sin metadata:                     {total_procesados - total_con_metadata}")
    print(f"  % con metadata:                   {total_con_metadata/total_procesados*100:.1f}%")
    print()

    # Estadísticas por campo
    print("="*100)
    print(" COBERTURA POR CAMPO")
    print("="*100)

    # Contar cuántos movimientos tienen cada campo
    movs_todos = db.query(Movimiento).limit(100).all()
    campos_stats = {}

    for mov in movs_todos:
        metadata = extraer_metadata_completa(mov.descripcion, mov.descripcion)
        for campo, valor in metadata.items():
            if campo not in campos_stats:
                campos_stats[campo] = 0
            if valor:
                campos_stats[campo] += 1

    for campo, count in sorted(campos_stats.items(), key=lambda x: x[1], reverse=True):
        porcentaje = count / len(movs_todos) * 100
        print(f"  {campo:<25} {count:>3}/{len(movs_todos)} ({porcentaje:>5.1f}%)")

    print()
    print("="*100)

if __name__ == "__main__":
    test_extractores_con_datos_reales()
