"""
Test de extracción automática de metadata durante consolidación
"""

from backend.database.connection import get_db
from backend.models.movimiento import Movimiento

def test_metadata_en_bd():
    """
    Verifica que los movimientos en la BD tengan metadata extraída
    """
    db = next(get_db())

    print("="*100)
    print(" TEST: METADATA EXTRAÍDA EN MOVIMIENTOS")
    print("="*100)
    print()

    # Contar movimientos con metadata
    total = db.query(Movimiento).count()

    con_nombre = db.query(Movimiento).filter(Movimiento.persona_nombre != None).count()
    con_doc = db.query(Movimiento).filter(Movimiento.documento != None).count()
    debins = db.query(Movimiento).filter(Movimiento.es_debin == True).count()
    con_debin_id = db.query(Movimiento).filter(Movimiento.debin_id != None).count()

    print(f"[ESTADÍSTICAS]")
    print(f"  Total movimientos:        {total}")
    print(f"  Con persona_nombre:       {con_nombre} ({con_nombre/total*100:.1f}%)")
    print(f"  Con documento:            {con_doc} ({con_doc/total*100:.1f}%)")
    print(f"  Marcados como DEBIN:      {debins} ({debins/total*100:.1f}%)")
    print(f"  Con debin_id:             {con_debin_id} ({con_debin_id/total*100:.1f}%)")
    print()

    # Mostrar ejemplos de cada tipo
    print("="*100)
    print(" EJEMPLOS DE METADATA EXTRAÍDA")
    print("="*100)
    print()

    # Transferencias con nombre
    print("[1] Transferencias con nombre:")
    movs_nombre = db.query(Movimiento).filter(Movimiento.persona_nombre != None).limit(3).all()
    for m in movs_nombre:
        desc = m.descripcion[:70] + "..." if len(m.descripcion) > 70 else m.descripcion
        print(f"  ID {m.id}:")
        print(f"    Descripción: {desc}")
        print(f"    Nombre:      {m.persona_nombre}")
        print(f"    Documento:   {m.documento}")
        print()

    # DEBIN
    print("[2] Movimientos DEBIN:")
    movs_debin = db.query(Movimiento).filter(Movimiento.es_debin == True).limit(3).all()
    for m in movs_debin:
        desc = m.descripcion[:70] + "..." if len(m.descripcion) > 70 else m.descripcion
        print(f"  ID {m.id}:")
        print(f"    Descripción: {desc}")
        print(f"    Es DEBIN:    {m.es_debin}")
        print(f"    DEBIN ID:    {m.debin_id}")
        print(f"    Nombre:      {m.persona_nombre}")
        print()

    # Solo documento
    print("[3] Con documento (pero sin nombre):")
    movs_doc = db.query(Movimiento).filter(
        Movimiento.documento != None,
        Movimiento.persona_nombre == None
    ).limit(3).all()
    for m in movs_doc:
        desc = m.descripcion[:70] + "..." if len(m.descripcion) > 70 else m.descripcion
        print(f"  ID {m.id}:")
        print(f"    Descripción: {desc}")
        print(f"    Documento:   {m.documento}")
        print()

    print("="*100)
    print(" TEST COMPLETADO")
    print("="*100)

if __name__ == "__main__":
    test_metadata_en_bd()
