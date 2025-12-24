"""
Test de categorización sobre dataset de prueba - ETAPA 1.4
"""
import json
from backend.database.connection import get_db
from backend.models.movimiento import Movimiento
from backend.core.categorizador_cascada import categorizar_movimientos

def ejecutar_categorizacion_test():
    """
    Ejecuta categorización sobre el dataset de prueba y genera reporte
    """

    db = next(get_db())

    print("="*100)
    print(" TEST DE CATEGORIZACION - ETAPA 1.4")
    print("="*100)
    print()

    # Cargar dataset
    print("[1] Cargando dataset de prueba...")
    with open("tests/dataset_prueba.json", "r", encoding="utf-8") as f:
        dataset = json.load(f)

    movs_ids = [m['id'] for m in dataset['movimientos']]
    print(f"    Dataset: {len(movs_ids)} movimientos")

    # Verificar que están sin categoría
    sin_cat = db.query(Movimiento).filter(
        Movimiento.id.in_(movs_ids),
        Movimiento.categoria == None
    ).count()
    print(f"    Sin categoria: {sin_cat} movimientos")

    # Ejecutar categorización
    print("\n[2] Ejecutando motor de categorización cascada...")
    resultado = categorizar_movimientos(db, solo_sin_categoria=True)

    print(f"    Motor: {resultado.get('motor')}")
    print(f"    Procesados: {resultado.get('procesados')}")
    print(f"    Categorizados: {resultado.get('categorizados')}")
    print(f"    Sin match: {resultado.get('sin_match')}")
    print(f"    Refinados nivel 2: {resultado.get('refinados_nivel2')}")
    print(f"    Porcentaje categorizados: {resultado.get('porcentaje_categorizados'):.1f}%")
    print(f"    Porcentaje refinados: {resultado.get('porcentaje_refinados'):.1f}%")

    # Obtener movimientos categorizados
    print("\n[3] Analizando resultados...")
    movs = db.query(Movimiento).filter(Movimiento.id.in_(movs_ids)).all()

    # Preparar resultados
    resultados = []
    categorizados = 0
    refinados = 0
    sin_categoria = 0
    confianza_total = 0

    for m in movs:
        if m.categoria:
            categorizados += 1
            confianza_total += m.confianza_porcentaje or 0
            if m.subcategoria and m.subcategoria != "Sin_Clasificar":
                refinados += 1
        else:
            sin_categoria += 1

        resultados.append({
            "id": m.id,
            "descripcion": m.descripcion,
            "monto": float(m.monto),
            "categoria": m.categoria,
            "subcategoria": m.subcategoria,
            "confianza": m.confianza_porcentaje
        })

    # Calcular métricas
    cobertura = (categorizados / len(movs) * 100) if movs else 0
    tasa_refinamiento = (refinados / categorizados * 100) if categorizados else 0
    confianza_promedio = (confianza_total / categorizados) if categorizados else 0

    # Mostrar resultados detallados
    print("\n[4] Resultados detallados:")
    print()
    print(f"{'ID':<5} {'Descripcion':<55} {'Categoria':<10} {'Subcategoria':<30} {'Conf':<5}")
    print("-" * 110)

    for r in resultados:
        desc = (r['descripcion'][:52] + '...') if len(r['descripcion']) > 55 else r['descripcion']
        cat = r['categoria'] or "SIN_CAT"
        subcat = r['subcategoria'] or "-"
        conf = f"{r['confianza']}%" if r['confianza'] else "0%"
        print(f"{r['id']:<5} {desc:<55} {cat:<10} {subcat:<30} {conf:<5}")

    # Resumen
    print()
    print("="*100)
    print(" RESUMEN DE METRICAS")
    print("="*100)
    print(f"  Total movimientos:        {len(movs)}")
    print(f"  Categorizados:            {categorizados}")
    print(f"  Sin categoria:            {sin_categoria}")
    print(f"  Cobertura:                {cobertura:.1f}%")
    print(f"  Refinados nivel 2:        {refinados}")
    print(f"  Tasa refinamiento:        {tasa_refinamiento:.1f}%")
    print(f"  Confianza promedio:       {confianza_promedio:.1f}%")
    print()

    # Criterios de éxito
    print("="*100)
    print(" CRITERIOS DE EXITO ETAPA 1.4")
    print("="*100)

    criterios = [
        ("Cobertura > 90%", cobertura > 90, f"{cobertura:.1f}%"),
        ("Confianza promedio > 80%", confianza_promedio > 80, f"{confianza_promedio:.1f}%"),
        ("Tasa refinamiento > 60%", tasa_refinamiento > 60, f"{tasa_refinamiento:.1f}%"),
        ("Sin categoria < 10%", (sin_categoria / len(movs) * 100) < 10, f"{sin_categoria}/{len(movs)}")
    ]

    for criterio, cumple, valor in criterios:
        status = "[OK]" if cumple else "[FALLO]"
        print(f"  {status} {criterio:<35} -> {valor}")

    print()

    # Guardar resultados
    output = {
        "version": "1.0",
        "motor": "CategorizadorCascada v2.0",
        "fecha_test": "2025-12-16",
        "dataset": "tests/dataset_prueba.json",
        "metricas": {
            "total_movimientos": len(movs),
            "categorizados": categorizados,
            "sin_categoria": sin_categoria,
            "cobertura_porcentaje": round(cobertura, 2),
            "refinados_nivel2": refinados,
            "tasa_refinamiento_porcentaje": round(tasa_refinamiento, 2),
            "confianza_promedio": round(confianza_promedio, 2)
        },
        "criterios_exito": {
            criterio: {"cumple": cumple, "valor": valor}
            for criterio, cumple, valor in criterios
        },
        "resultados": resultados
    }

    with open("tests/resultado_test_categorizacion.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("="*100)
    print(" Resultados guardados en: tests/resultado_test_categorizacion.json")
    print("="*100)

    return output

if __name__ == "__main__":
    resultado = ejecutar_categorizacion_test()
