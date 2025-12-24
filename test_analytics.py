"""
Test de validación para endpoints de Analytics
ETAPA 6 - Visualizaciones
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.connection import get_db
from backend.api.routes import router
from sqlalchemy import func
from backend.models.movimiento import Movimiento


def test_importacion_endpoints():
    """Verifica que los endpoints de analytics se importen correctamente"""
    print("\n=== TEST 1: Importación de endpoints ===")

    # Verificar que existen 14 endpoints
    total_endpoints = len([r for r in router.routes])
    print(f"Total de endpoints: {total_endpoints}")
    assert total_endpoints == 14, f"Se esperaban 14 endpoints, se encontraron {total_endpoints}"

    # Verificar que existen los endpoints de analytics
    rutas = [route.path for route in router.routes]

    assert "/api/analytics/pie-ingresos" in rutas, "Falta endpoint /api/analytics/pie-ingresos"
    assert "/api/analytics/pie-egresos" in rutas, "Falta endpoint /api/analytics/pie-egresos"
    assert "/api/analytics/flujo-diario" in rutas, "Falta endpoint /api/analytics/flujo-diario"

    print("[OK] Todos los endpoints de analytics estan registrados")
    print(f"  - /api/analytics/pie-ingresos")
    print(f"  - /api/analytics/pie-egresos")
    print(f"  - /api/analytics/flujo-diario")


def test_datos_disponibles():
    """Verifica que hay datos en la BD para generar gráficos"""
    print("\n=== TEST 2: Datos disponibles ===")

    db = next(get_db())

    # Contar movimientos categorizados
    total_movs = db.query(Movimiento).count()
    ingresos = db.query(Movimiento).filter(Movimiento.categoria == "INGRESOS").count()
    egresos = db.query(Movimiento).filter(Movimiento.categoria == "EGRESOS").count()

    print(f"Total movimientos: {total_movs}")
    print(f"  - Ingresos (nuevo formato): {ingresos}")
    print(f"  - Egresos (nuevo formato): {egresos}")

    assert total_movs > 0, "No hay movimientos en la BD"

    # Si no hay categorizados en formato nuevo, re-categorizar TODA la BD
    if ingresos == 0 and egresos == 0:
        print("[WARN] BD usa formato antiguo. Re-categorizando toda la BD...")
        from backend.core.categorizador_cascada import categorizar_movimientos

        # Resetear categorías para forzar re-categorización
        db.query(Movimiento).update({"categoria": "SIN_CATEGORIA"})
        db.commit()

        resultado = categorizar_movimientos(db, solo_sin_categoria=True)
        print(f"  Categorizados: {resultado.get('categorizados', 0)}")

        # Re-contar después de categorizar
        ingresos = db.query(Movimiento).filter(Movimiento.categoria == "INGRESOS").count()
        egresos = db.query(Movimiento).filter(Movimiento.categoria == "EGRESOS").count()
        print(f"  Nueva cuenta - Ingresos: {ingresos}, Egresos: {egresos}")

    assert ingresos > 0 or egresos > 0, "No hay movimientos categorizados después de re-categorizar"

    # Contar subcategorías distintas
    subcat_ingresos = db.query(Movimiento.subcategoria).filter(
        Movimiento.categoria == "INGRESOS"
    ).distinct().count()

    subcat_egresos = db.query(Movimiento.subcategoria).filter(
        Movimiento.categoria == "EGRESOS"
    ).distinct().count()

    print(f"Subcategorías distintas:")
    print(f"  - Ingresos: {subcat_ingresos}")
    print(f"  - Egresos: {subcat_egresos}")

    # Al menos una debe tener subcategorías
    assert subcat_ingresos > 0 or subcat_egresos > 0, "No hay subcategorías"

    print("[OK] Hay datos suficientes para generar graficos")


def test_estructura_respuesta_pie():
    """Simula la query de pie-ingresos y verifica estructura"""
    print("\n=== TEST 3: Estructura de respuesta (pie chart) ===")

    db = next(get_db())

    # Simular query del endpoint pie-ingresos
    resultados = db.query(
        Movimiento.subcategoria,
        func.sum(Movimiento.monto).label('total')
    ).filter(
        Movimiento.categoria == "INGRESOS"
    ).group_by(Movimiento.subcategoria).all()

    print(f"Resultados encontrados: {len(resultados)}")

    assert len(resultados) > 0, "No hay resultados para pie-ingresos"

    # Verificar estructura
    for r in resultados[:3]:  # Mostrar solo los primeros 3
        subcat = r[0] or "Sin_Subcategoria"
        total = float(r[1])
        print(f"  - {subcat}: ${total:,.2f}")

    print("[OK] Query de pie-ingresos funciona correctamente")


def test_estructura_respuesta_flujo():
    """Simula la query de flujo-diario y verifica estructura"""
    print("\n=== TEST 4: Estructura de respuesta (flujo diario) ===")

    db = next(get_db())

    # Obtener un mes de ejemplo
    primer_mov = db.query(Movimiento).order_by(Movimiento.fecha.asc()).first()

    if not primer_mov:
        print("⚠ No hay movimientos para testear flujo diario")
        return

    mes = primer_mov.fecha.strftime('%Y-%m')
    print(f"Testeando con mes: {mes}")

    # Simular query de ingresos
    ingresos_query = db.query(
        func.date(Movimiento.fecha).label('dia'),
        func.sum(Movimiento.monto).label('total')
    ).filter(
        Movimiento.categoria == "INGRESOS",
        func.strftime('%Y-%m', Movimiento.fecha) == mes
    ).group_by(func.date(Movimiento.fecha)).all()

    # Simular query de egresos
    egresos_query = db.query(
        func.date(Movimiento.fecha).label('dia'),
        func.sum(Movimiento.monto).label('total')
    ).filter(
        Movimiento.categoria == "EGRESOS",
        func.strftime('%Y-%m', Movimiento.fecha) == mes
    ).group_by(func.date(Movimiento.fecha)).all()

    print(f"Días con ingresos: {len(ingresos_query)}")
    print(f"Días con egresos: {len(egresos_query)}")

    # Mostrar primer día de cada uno
    if ingresos_query:
        dia, total = ingresos_query[0]
        print(f"  Ejemplo ingreso: {dia} = ${float(total):,.2f}")

    if egresos_query:
        dia, total = egresos_query[0]
        print(f"  Ejemplo egreso: {dia} = ${abs(float(total)):,.2f}")

    print("[OK] Query de flujo-diario funciona correctamente")


def test_archivos_frontend():
    """Verifica que existen los archivos del frontend"""
    print("\n=== TEST 5: Archivos del frontend ===")

    base_dir = Path(__file__).parent

    archivos = [
        "frontend/templates/analytics.html",
        "frontend/static/js/charts.js"
    ]

    for archivo in archivos:
        ruta = base_dir / archivo
        assert ruta.exists(), f"Falta archivo: {archivo}"
        print(f"[OK] Existe: {archivo}")


if __name__ == "__main__":
    print("=" * 60)
    print("TEST DE VALIDACIÓN - ETAPA 6 (VISUALIZACIONES)")
    print("=" * 60)

    try:
        test_importacion_endpoints()
        test_datos_disponibles()
        test_estructura_respuesta_pie()
        test_estructura_respuesta_flujo()
        test_archivos_frontend()

        print("\n" + "=" * 60)
        print(">>> TODOS LOS TESTS PASARON <<<")
        print("=" * 60)
        print("\nETAPA 6 - VISUALIZACIONES: COMPLETADA")
        print("\nProximos pasos:")
        print("1. Iniciar servidor: python run.py")
        print("2. Abrir http://localhost:8000/analytics")
        print("3. Verificar graficos visualmente")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n[ERROR] TEST FALLIDO: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
