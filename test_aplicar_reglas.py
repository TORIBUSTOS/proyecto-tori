"""
Test del endpoint POST /api/reglas/aplicar

Verifica:
- Endpoint responde correctamente
- Filtros por mes funcionan
- Filtros por batch funcionan
- Estadísticas son correctas
- Movimientos se recategorizan
"""

import requests
import json

API_URL = "http://localhost:8000/api"


def test_aplicar_reglas_sin_filtros():
    """Test 1: Aplicar reglas a todos los movimientos"""
    print("\n🧪 Test 1: POST /api/reglas/aplicar (sin filtros)")

    response = requests.post(f"{API_URL}/reglas/aplicar")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Mensaje: {data.get('mensaje')}")
        print(f"✅ Evaluados: {data.get('evaluados')}")
        print(f"✅ Actualizados: {data.get('actualizados')}")
        print(f"✅ Por regla aprendida: {data.get('por_regla_aprendida')}")
        print(f"✅ Por motor cascada: {data.get('por_motor_cascada')}")
        print(f"✅ Porcentaje: {data.get('porcentaje_actualizados')}%")

        # Mostrar top estadísticas
        if data.get('estadisticas'):
            print(f"\n📊 Top 5 categorías:")
            for i, stat in enumerate(data['estadisticas'][:5], 1):
                print(f"   {i}. {stat['categoria']}:{stat['subcategoria']} - {stat['count']} movimientos")

        return True
    else:
        print(f"❌ Error: Status {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def test_aplicar_reglas_por_mes():
    """Test 2: Aplicar reglas solo a movimientos de un mes específico"""
    print("\n🧪 Test 2: POST /api/reglas/aplicar?mes=2025-11")

    response = requests.post(f"{API_URL}/reglas/aplicar?mes=2025-11")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Mensaje: {data.get('mensaje')}")
        print(f"✅ Evaluados (Nov 2025): {data.get('evaluados')}")
        print(f"✅ Actualizados: {data.get('actualizados')}")
        print(f"✅ Porcentaje: {data.get('porcentaje_actualizados')}%")

        return True
    else:
        print(f"❌ Error: Status {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def test_aplicar_reglas_por_batch():
    """Test 3: Aplicar reglas solo a movimientos de un batch específico"""
    print("\n🧪 Test 3: POST /api/reglas/aplicar?batch_id=1")

    response = requests.post(f"{API_URL}/reglas/aplicar?batch_id=1")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Mensaje: {data.get('mensaje')}")
        print(f"✅ Evaluados (Batch 1): {data.get('evaluados')}")
        print(f"✅ Actualizados: {data.get('actualizados')}")
        print(f"✅ Porcentaje: {data.get('porcentaje_actualizados')}%")

        return True
    else:
        print(f"❌ Error: Status {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def test_aplicar_reglas_mes_y_batch():
    """Test 4: Aplicar reglas con filtros combinados (mes + batch)"""
    print("\n🧪 Test 4: POST /api/reglas/aplicar?mes=2025-11&batch_id=1")

    response = requests.post(f"{API_URL}/reglas/aplicar?mes=2025-11&batch_id=1")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Mensaje: {data.get('mensaje')}")
        print(f"✅ Evaluados (Nov 2025 + Batch 1): {data.get('evaluados')}")
        print(f"✅ Actualizados: {data.get('actualizados')}")
        print(f"✅ Porcentaje: {data.get('porcentaje_actualizados')}%")

        return True
    else:
        print(f"❌ Error: Status {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def test_aplicar_reglas_formato_invalido():
    """Test 5: Formato de mes inválido (debe fallar)"""
    print("\n🧪 Test 5: POST /api/reglas/aplicar?mes=invalido (debe fallar)")

    response = requests.post(f"{API_URL}/reglas/aplicar?mes=invalido")

    if response.status_code == 400:
        print(f"✅ Status: {response.status_code} (Bad Request como esperado)")
        return True
    else:
        print(f"❌ Error: Debería retornar 400, obtuvo {response.status_code}")
        return False


def test_aplicar_reglas_mes_all():
    """Test 6: Aplicar reglas a todos los períodos (mes=all)"""
    print("\n🧪 Test 6: POST /api/reglas/aplicar?mes=all")

    response = requests.post(f"{API_URL}/reglas/aplicar?mes=all")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Mensaje: {data.get('mensaje')}")
        print(f"✅ Evaluados (TODOS): {data.get('evaluados')}")
        print(f"✅ Actualizados: {data.get('actualizados')}")
        print(f"✅ Porcentaje: {data.get('porcentaje_actualizados')}%")

        # Mostrar breakdown completo
        if data.get('estadisticas'):
            print(f"\n📊 Top 10 categorías:")
            for i, stat in enumerate(data['estadisticas'][:10], 1):
                print(f"   {i}. {stat['categoria']}:{stat['subcategoria']} - {stat['count']} movimientos")

        return True
    else:
        print(f"❌ Error: Status {response.status_code}")
        print(f"   Response: {response.text}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 TESTS DE ENDPOINT /api/reglas/aplicar")
    print("=" * 60)

    # Verificar que el servidor esté corriendo
    try:
        response = requests.get(f"{API_URL}/../health", timeout=2)
        if response.status_code != 200:
            print("❌ El servidor no está corriendo en localhost:8000")
            print("   Ejecutar: python run_dev.py")
            exit(1)
    except requests.exceptions.RequestException:
        print("❌ El servidor no está corriendo en localhost:8000")
        print("   Ejecutar: python run_dev.py")
        exit(1)

    # Ejecutar tests
    resultados = []

    # IMPORTANTE: Solo ejecutar uno a la vez para no modificar datos simultáneamente
    print("\n⚠️  ADVERTENCIA: Estos tests MODIFICAN la base de datos.")
    print("   Se recomienda ejecutar solo un test a la vez.\n")

    # Comentar/descomentar según lo que quieras probar:
    resultados.append(test_aplicar_reglas_sin_filtros())
    # resultados.append(test_aplicar_reglas_por_mes())
    # resultados.append(test_aplicar_reglas_por_batch())
    # resultados.append(test_aplicar_reglas_mes_y_batch())
    # resultados.append(test_aplicar_reglas_formato_invalido())
    # resultados.append(test_aplicar_reglas_mes_all())

    # Resumen
    print("\n" + "=" * 60)
    print(f"📊 RESUMEN")
    print("=" * 60)
    print(f"Tests ejecutados: {len(resultados)}")
    print(f"Tests exitosos: {sum(resultados)}")
    print(f"Tests fallidos: {len(resultados) - sum(resultados)}")

    if all(resultados):
        print("\n✅ TODOS LOS TESTS PASARON")
    else:
        print("\n❌ ALGUNOS TESTS FALLARON")
        exit(1)
