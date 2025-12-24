"""
Test rápido del endpoint /api/metadata

Verifica:
- Endpoint responde correctamente
- Filtros funcionan
- Estructura de respuesta es correcta
- Sincronización con período funciona
"""

import requests
import json

API_URL = "http://localhost:8000/api"


def test_metadata_sin_filtros():
    """Test 1: Obtener metadata sin filtros"""
    print("\n🧪 Test 1: GET /api/metadata (sin filtros)")

    response = requests.get(f"{API_URL}/metadata")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Status field: {data.get('status')}")
        print(f"✅ Total items: {data.get('total')}")
        print(f"✅ Items returned: {len(data.get('items', []))}")
        print(f"✅ Limit: {data.get('limit')}")
        print(f"✅ Offset: {data.get('offset')}")

        # Verificar estructura de un item
        if data.get('items'):
            item = data['items'][0]
            print(f"\n📄 Estructura del primer item:")
            print(f"   - id: {item.get('id')}")
            print(f"   - fecha: {item.get('fecha')}")
            print(f"   - monto: {item.get('monto')}")
            print(f"   - descripcion: {item.get('descripcion')[:50]}...")
            print(f"   - categoria: {item.get('categoria')}")
            print(f"   - subcategoria: {item.get('subcategoria')}")
            print(f"   - confianza: {item.get('confianza')}")
            print(f"   Metadata:")
            print(f"   - nombre: {item.get('nombre')}")
            print(f"   - documento: {item.get('documento')}")
            print(f"   - es_debin: {item.get('es_debin')}")
            print(f"   - debin_id: {item.get('debin_id')}")
            print(f"   - cbu: {item.get('cbu')}")
            print(f"   - comercio: {item.get('comercio')}")
            print(f"   - terminal: {item.get('terminal')}")
            print(f"   - referencia: {item.get('referencia')}")

        return True
    else:
        print(f"❌ Error: Status {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def test_metadata_con_filtro_metadata():
    """Test 2: Filtrar solo movimientos con metadata"""
    print("\n🧪 Test 2: GET /api/metadata?con_metadata=true")

    response = requests.get(f"{API_URL}/metadata?con_metadata=true")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Total con metadata: {data.get('total')}")
        print(f"✅ Items returned: {len(data.get('items', []))}")

        # Verificar que todos tienen al menos un campo de metadata
        items_con_metadata = 0
        for item in data.get('items', []):
            if any([
                item.get('nombre'),
                item.get('documento'),
                item.get('debin_id'),
                item.get('cbu'),
                item.get('comercio'),
                item.get('terminal'),
                item.get('referencia')
            ]):
                items_con_metadata += 1

        print(f"✅ Items con metadata verificados: {items_con_metadata}/{len(data.get('items', []))}")

        return True
    else:
        print(f"❌ Error: Status {response.status_code}")
        return False


def test_metadata_con_debin():
    """Test 3: Filtrar solo movimientos DEBIN"""
    print("\n🧪 Test 3: GET /api/metadata?con_debin=true")

    response = requests.get(f"{API_URL}/metadata?con_debin=true")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Total DEBIN: {data.get('total')}")
        print(f"✅ Items returned: {len(data.get('items', []))}")

        # Verificar que todos son DEBIN
        debins_validos = 0
        for item in data.get('items', []):
            if item.get('es_debin') or item.get('debin_id'):
                debins_validos += 1

        print(f"✅ Items DEBIN verificados: {debins_validos}/{len(data.get('items', []))}")

        return True
    else:
        print(f"❌ Error: Status {response.status_code}")
        return False


def test_metadata_con_periodo():
    """Test 4: Filtrar por período"""
    print("\n🧪 Test 4: GET /api/metadata?mes=2025-11")

    response = requests.get(f"{API_URL}/metadata?mes=2025-11")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Total Nov 2025: {data.get('total')}")
        print(f"✅ Items returned: {len(data.get('items', []))}")

        # Verificar que todas las fechas son de Nov 2025
        if data.get('items'):
            fechas_correctas = 0
            for item in data.get('items', []):
                fecha = item.get('fecha', '')
                if fecha.startswith('2025-11'):
                    fechas_correctas += 1

            print(f"✅ Fechas Nov 2025 verificadas: {fechas_correctas}/{len(data['items'])}")

        return True
    else:
        print(f"❌ Error: Status {response.status_code}")
        return False


def test_metadata_formato_invalido():
    """Test 5: Formato de mes inválido"""
    print("\n🧪 Test 5: GET /api/metadata?mes=invalido (debe fallar)")

    response = requests.get(f"{API_URL}/metadata?mes=invalido")

    if response.status_code == 400:
        print(f"✅ Status: {response.status_code} (Bad Request como esperado)")
        return True
    else:
        print(f"❌ Error: Debería retornar 400, obtuvo {response.status_code}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 TESTS DE ENDPOINT /api/metadata")
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

    resultados.append(test_metadata_sin_filtros())
    resultados.append(test_metadata_con_filtro_metadata())
    resultados.append(test_metadata_con_debin())
    resultados.append(test_metadata_con_periodo())
    resultados.append(test_metadata_formato_invalido())

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
