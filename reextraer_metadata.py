"""
Re-extrae metadata de movimientos existentes en la BD
"""

from backend.database.connection import get_db
from backend.models.movimiento import Movimiento
from backend.core.extractores import extraer_metadata_completa

def reextraer_metadata():
    """
    Re-procesa todos los movimientos para extraer metadata
    """
    db = next(get_db())

    print("="*100)
    print(" RE-EXTRACCIÓN DE METADATA DE MOVIMIENTOS EXISTENTES")
    print("="*100)
    print()

    # Obtener todos los movimientos
    movs = db.query(Movimiento).all()
    total = len(movs)

    print(f"[1] Total movimientos a procesar: {total}")
    print()

    procesados = 0
    con_metadata = 0
    errores = 0

    print("[2] Procesando...")
    for i, mov in enumerate(movs, 1):
        try:
            # Extraer concepto y detalle de la descripción
            # La descripción tiene formato "Concepto - Detalle"
            parts = mov.descripcion.split(" - ", 1)
            concepto = parts[0] if len(parts) > 0 else ""
            detalle = parts[1] if len(parts) > 1 else ""

            # Extraer metadata
            metadata = extraer_metadata_completa(concepto, detalle)

            # Actualizar movimiento
            mov.persona_nombre = metadata['persona_nombre']
            mov.documento = metadata['documento']
            mov.es_debin = metadata['es_debin']
            mov.debin_id = metadata['debin_id']

            procesados += 1

            # Contar si tiene alguna metadata
            tiene_metadata = any([
                metadata['persona_nombre'],
                metadata['documento'],
                metadata['es_debin'],
                metadata['debin_id']
            ])

            if tiene_metadata:
                con_metadata += 1

            # Progress cada 100
            if i % 100 == 0:
                print(f"    Procesados: {i}/{total} ({i/total*100:.1f}%)")

        except Exception as e:
            errores += 1
            print(f"    ERROR en movimiento {mov.id}: {e}")

    # Commit
    db.commit()

    print()
    print("="*100)
    print(" RESULTADOS")
    print("="*100)
    print(f"  Total procesados:         {procesados}")
    print(f"  Con metadata extraída:    {con_metadata} ({con_metadata/procesados*100:.1f}%)")
    print(f"  Sin metadata:             {procesados - con_metadata}")
    print(f"  Errores:                  {errores}")
    print()

    # Estadísticas por campo
    print("="*100)
    print(" ESTADÍSTICAS POR CAMPO")
    print("="*100)

    con_nombre = db.query(Movimiento).filter(Movimiento.persona_nombre != None).count()
    con_doc = db.query(Movimiento).filter(Movimiento.documento != None).count()
    debins = db.query(Movimiento).filter(Movimiento.es_debin == True).count()
    con_debin_id = db.query(Movimiento).filter(Movimiento.debin_id != None).count()

    print(f"  Con persona_nombre:       {con_nombre} ({con_nombre/total*100:.1f}%)")
    print(f"  Con documento:            {con_doc} ({con_doc/total*100:.1f}%)")
    print(f"  Marcados como DEBIN:      {debins} ({debins/total*100:.1f}%)")
    print(f"  Con debin_id:             {con_debin_id} ({con_debin_id/total*100:.1f}%)")
    print()

    print("="*100)
    print(" RE-EXTRACCIÓN COMPLETADA")
    print("="*100)

if __name__ == "__main__":
    reextraer_metadata()
