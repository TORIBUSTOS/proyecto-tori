"""
Script para crear dataset de prueba con movimientos reales variados
"""
import json
from backend.database.connection import get_db
from backend.models.movimiento import Movimiento
from sqlalchemy import func

def crear_dataset_prueba():
    """
    Extrae una muestra representativa de movimientos para testing
    - 20 movimientos variados
    - Diferentes tipos de concepto
    - Ingresos y egresos
    - Con y sin categoría previa
    """

    db = next(get_db())

    # Limpiar categorías de algunos movimientos para testing
    print("[1] Limpiando categorías de movimientos de prueba...")
    movs = db.query(Movimiento).limit(20).all()
    for m in movs:
        m.categoria = None
        m.subcategoria = None
        m.confianza_porcentaje = 0
    db.commit()
    print(f"    Limpiados: {len(movs)} movimientos")

    # Extraer muestra variada
    print("\n[2] Extrayendo muestra representativa...")

    dataset = []

    # Buscar diferentes tipos de movimientos
    tipos_busqueda = [
        ("Impuesto", 3),
        ("Compra", 5),
        ("Transferencia", 3),
        ("DEBIN", 2),
        ("Comisi", 2),
        ("Extracci", 2),
        ("Servicio", 3),
    ]

    for patron, limite in tipos_busqueda:
        movs = db.query(Movimiento)\
            .filter(Movimiento.descripcion.like(f"%{patron}%"))\
            .filter(Movimiento.categoria == None)\
            .limit(limite)\
            .all()

        for m in movs:
            dataset.append({
                "id": m.id,
                "fecha": str(m.fecha),
                "descripcion": m.descripcion,
                "monto": float(m.monto),
                "concepto": m.descripcion,  # Usamos descripción como concepto
                "detalle": m.descripcion,    # Y también como detalle (por ahora)
                "categoria_esperada": None,  # A determinar manualmente
                "subcategoria_esperada": None
            })

    print(f"    Extraídos: {len(dataset)} movimientos")

    # Guardar dataset
    output_file = "tests/dataset_prueba.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "version": "1.0",
            "motor": "CategorizadorCascada v2.0",
            "fecha_creacion": "2025-12-16",
            "total_movimientos": len(dataset),
            "descripcion": "Dataset de prueba para validación de categorización",
            "movimientos": dataset
        }, f, indent=2, ensure_ascii=False)

    print(f"\n[3] Dataset guardado en: {output_file}")
    print(f"    Total movimientos: {len(dataset)}")

    # Mostrar muestra
    print("\n[4] Muestra del dataset:")
    print(f"{'ID':<6} {'Monto':<12} {'Descripción':<70}")
    print("-" * 90)
    for m in dataset[:10]:
        desc = (m['descripcion'][:67] + '...') if len(m['descripcion']) > 70 else m['descripcion']
        print(f"{m['id']:<6} {m['monto']:<12.2f} {desc:<70}")

    if len(dataset) > 10:
        print(f"... y {len(dataset) - 10} más")

    return dataset

if __name__ == "__main__":
    print("="*90)
    print(" CREAR DATASET DE PRUEBA - ETAPA 1.4")
    print("="*90)
    print()

    dataset = crear_dataset_prueba()

    print()
    print("="*90)
    print(f" DATASET CREADO: {len(dataset)} movimientos listos para testing")
    print("="*90)
