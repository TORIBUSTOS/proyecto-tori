"""
Test de Reglas Aprendibles (ETAPA 4 MVP)

Valida:
1. Crear regla (POST /api/reglas) => 200 y regla creada
2. Crear misma regla otra vez => veces_usada incrementa y confianza sube
3. Simular categorización: crear movimiento y verificar que se categoriza por regla aprendida
"""

import sys
import io
from pathlib import Path

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, engine, Base
from backend.models.movimiento import Movimiento
from backend.models.regla_categorizacion import ReglaCategorizacion
from backend.core.reglas_aprendidas import (
    normalizar_texto,
    generar_patron_desde_descripcion,
    obtener_o_crear_regla,
    buscar_regla_aplicable,
    aplicar_regla_a_movimiento
)
from backend.core.categorizador_cascada import categorizar_movimientos
from datetime import datetime


def test_normalizacion():
    """Test 1: Verificar normalización de texto"""
    print("\n[TEST 1] Normalización de texto")
    print("=" * 60)

    tests = [
        ("  Compra   VISA!!!  ", "COMPRA VISA"),
        ("PEDIDOS YA - Delivery #123", "PEDIDOS YA DELIVERY 123"),
        ("transferencia CBU", "TRANSFERENCIA CBU"),
    ]

    for entrada, esperado in tests:
        resultado = normalizar_texto(entrada)
        assert resultado == esperado, f"Esperado '{esperado}', obtenido '{resultado}'"
        print(f"✓ '{entrada}' => '{resultado}'")

    print("[OK] Normalización funciona correctamente")


def test_generar_patron():
    """Test 2: Verificar generación de patrones"""
    print("\n[TEST 2] Generación de patrones")
    print("=" * 60)

    tests = [
        ("COMPRA VISA DEBITO COMERCIO PEDIDOSYA ENTREGA 123", "COMPRA VISA DEBITO COMERCIO PEDIDOSYA"),
        ("Transferencia CBU 0170033220000088888888", "TRANSFERENCIA CBU 0170033220000088888888"),
        ("SUELDO MENSUAL", "SUELDO MENSUAL"),
    ]

    for descripcion, esperado in tests:
        patron = generar_patron_desde_descripcion(descripcion)
        assert patron == esperado, f"Esperado '{esperado}', obtenido '{patron}'"
        print(f"✓ '{descripcion}' => '{patron}'")

    print("[OK] Generación de patrones funciona correctamente")


def test_crear_regla():
    """Test 3: Crear regla en DB (primera vez)"""
    print("\n[TEST 3] Crear regla en DB")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Limpiar tabla
        db.query(ReglaCategorizacion).delete()
        db.commit()

        # Crear regla
        patron = "COMPRA VISA DEBITO COMERCIO"
        regla = obtener_o_crear_regla(
            patron=patron,
            categoria="EGRESOS",
            subcategoria="Prestadores_Farmacias",
            db=db
        )

        assert regla.id is not None, "Regla debe tener ID"
        assert regla.patron == patron
        assert regla.categoria == "EGRESOS"
        assert regla.subcategoria == "Prestadores_Farmacias"
        assert regla.confianza == 50  # Confianza inicial
        assert regla.veces_usada == 1  # Primera vez

        print(f"✓ Regla creada: ID={regla.id}")
        print(f"  - Patrón: {regla.patron}")
        print(f"  - Categoría: {regla.categoria} / {regla.subcategoria}")
        print(f"  - Confianza: {regla.confianza}%")
        print(f"  - Veces usada: {regla.veces_usada}")

        print("[OK] Regla creada exitosamente")
        return regla

    finally:
        db.close()


def test_actualizar_regla():
    """Test 4: Actualizar regla existente (mismo patrón)"""
    print("\n[TEST 4] Actualizar regla existente")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Obtener regla existente (debe incrementar contadores)
        patron = "COMPRA VISA DEBITO COMERCIO"
        regla = obtener_o_crear_regla(
            patron=patron,
            categoria="EGRESOS",
            subcategoria="Prestadores_Farmacias",
            db=db
        )

        assert regla.confianza == 60, f"Confianza debe ser 60 (50+10), obtenida {regla.confianza}"
        assert regla.veces_usada == 2, f"Veces usada debe ser 2, obtenida {regla.veces_usada}"

        print(f"✓ Regla actualizada: ID={regla.id}")
        print(f"  - Confianza: {regla.confianza}% (+10)")
        print(f"  - Veces usada: {regla.veces_usada} (+1)")

        print("[OK] Regla actualizada exitosamente")

    finally:
        db.close()


def test_buscar_regla_aplicable():
    """Test 5: Buscar regla aplicable para una descripción"""
    print("\n[TEST 5] Buscar regla aplicable")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Buscar regla para descripción que matchea el patrón
        descripcion = "COMPRA VISA DEBITO COMERCIO PEDIDOSYA DELIVERY #456"
        regla = buscar_regla_aplicable(descripcion, db)

        assert regla is not None, "Debe encontrar una regla"
        assert regla.patron in normalizar_texto(descripcion)

        print(f"✓ Regla encontrada para: '{descripcion}'")
        print(f"  - Patrón: {regla.patron}")
        print(f"  - Categoría: {regla.categoria} / {regla.subcategoria}")

        # Buscar regla para descripción que NO matchea
        descripcion_no_match = "SUELDO MENSUAL EMPRESA XYZ"
        regla_no_match = buscar_regla_aplicable(descripcion_no_match, db)

        assert regla_no_match is None, "No debe encontrar regla para descripción diferente"
        print(f"✓ No se encontró regla para: '{descripcion_no_match}' (esperado)")

        print("[OK] Búsqueda de reglas funciona correctamente")

    finally:
        db.close()


def test_categorizacion_con_regla():
    """Test 6: Categorización automática usando regla aprendida"""
    print("\n[TEST 6] Categorización automática con regla aprendida")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Limpiar movimientos de test
        db.query(Movimiento).filter(Movimiento.descripcion.like("TEST REGLA%")).delete()
        db.commit()

        # Crear movimiento de prueba SIN categoría
        mov = Movimiento(
            fecha=datetime.now(),
            descripcion="COMPRA VISA DEBITO COMERCIO PEDIDOSYA ENTREGA 789",
            monto=-2500.00,
            categoria=None,  # Sin categoría inicialmente
            subcategoria=None
        )
        db.add(mov)
        db.commit()
        db.refresh(mov)

        print(f"✓ Movimiento creado: ID={mov.id}")
        print(f"  - Descripción: {mov.descripcion}")
        print(f"  - Categoría inicial: {mov.categoria}")

        # Ejecutar categorización (debe aplicar regla aprendida)
        resultado = categorizar_movimientos(db, solo_sin_categoria=True)

        # Refrescar movimiento desde DB
        db.refresh(mov)

        print(f"\n✓ Categorización ejecutada:")
        print(f"  - Procesados: {resultado['procesados']}")
        print(f"  - Aplicados regla aprendida: {resultado['aplicados_regla_aprendida']}")

        # Verificar que se aplicó la regla
        assert resultado['aplicados_regla_aprendida'] >= 1, "Debe aplicar al menos 1 regla aprendida"
        assert mov.categoria == "EGRESOS", f"Categoría debe ser EGRESOS, obtenida {mov.categoria}"
        assert mov.subcategoria == "Prestadores_Farmacias", f"Subcategoría debe ser Prestadores_Farmacias, obtenida {mov.subcategoria}"

        print(f"\n✓ Movimiento categorizado por regla aprendida:")
        print(f"  - Categoría: {mov.categoria}")
        print(f"  - Subcategoría: {mov.subcategoria}")
        print(f"  - Confianza: {mov.confianza_porcentaje}%")

        print("[OK] Categorización con regla aprendida funciona correctamente")

        # Limpiar
        db.delete(mov)
        db.commit()

    finally:
        db.close()


def test_regla_no_rompe_cascada():
    """Test 7: Verificar que si no hay regla aprendida, sigue usando motor cascada"""
    print("\n[TEST 7] Reglas no rompen motor cascada")
    print("=" * 60)

    db = SessionLocal()

    try:
        # Limpiar movimientos de test
        db.query(Movimiento).filter(Movimiento.descripcion.like("TEST CASCADA%")).delete()
        db.commit()

        # Crear movimiento que NO matchea ninguna regla aprendida
        # pero SÍ debe matchear regla estática (transferencias)
        mov = Movimiento(
            fecha=datetime.now(),
            descripcion="TEST CASCADA TRANSFERENCIA CBU 0170033220000088888888",
            monto=-5000.00,
            categoria=None,
            subcategoria=None
        )
        db.add(mov)
        db.commit()
        db.refresh(mov)

        print(f"✓ Movimiento creado: ID={mov.id}")
        print(f"  - Descripción: {mov.descripcion}")

        # Ejecutar categorización
        resultado = categorizar_movimientos(db, solo_sin_categoria=True)
        db.refresh(mov)

        print(f"\n✓ Categorización ejecutada:")
        print(f"  - Procesados: {resultado['procesados']}")
        print(f"  - Aplicados regla aprendida: {resultado['aplicados_regla_aprendida']}")
        print(f"  - Categorizados por cascada: {resultado['categorizados'] - resultado['aplicados_regla_aprendida']}")

        # Verificar que se categorizó por motor cascada
        assert mov.categoria is not None, "Debe tener categoría (por motor cascada)"
        print(f"\n✓ Movimiento categorizado por motor cascada:")
        print(f"  - Categoría: {mov.categoria}")
        print(f"  - Subcategoría: {mov.subcategoria}")

        print("[OK] Motor cascada sigue funcionando cuando no hay regla aprendida")

        # Limpiar
        db.delete(mov)
        db.commit()

    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("TEST REGLAS APRENDIDAS - ETAPA 4 MVP")
    print("=" * 60)

    try:
        # Ejecutar tests en orden
        test_normalizacion()
        test_generar_patron()
        test_crear_regla()
        test_actualizar_regla()
        test_buscar_regla_aplicable()
        test_categorizacion_con_regla()
        test_regla_no_rompe_cascada()

        print("\n" + "=" * 60)
        print("✅ TODOS LOS TESTS PASARON")
        print("=" * 60)
        print("\n✓ ETAPA 4 MVP - REGLAS APRENDIBLES: COMPLETADA")

    except AssertionError as e:
        print(f"\n❌ TEST FALLÓ: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
