"""
Test del endpoint /api/insights
Verifica que los insights se generen correctamente
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json

API_URL = "http://localhost:8000/api"


def test_insights_sin_mes():
    """Test: GET /api/insights (todos los períodos)"""
    print("=" * 60)
    print("TEST 1: Insights de todos los períodos")
    print("=" * 60)

    url = f"{API_URL}/insights"
    response = requests.get(url)

    print(f"Status Code: {response.status_code}")
    assert response.status_code == 200, "Debería retornar 200 OK"

    data = response.json()
    print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")

    assert data["status"] == "success", "Status debe ser 'success'"
    assert "insights" in data, "Debe contener 'insights'"
    assert isinstance(data["insights"], list), "insights debe ser una lista"

    print(f"\nOK - Total de insights generados: {len(data['insights'])}")

    if data["insights"]:
        print("\nInsights detectados:")
        for i, insight in enumerate(data["insights"], 1):
            print(f"\n  {i}. {insight['title']}")
            print(f"     {insight['message']}")
            print(f"     Accion: {insight['action']}")

    print("\nOK - TEST 1 PASO\n")
    return data["insights"]


def test_insights_con_mes():
    """Test: GET /api/insights?mes=2024-10"""
    print("=" * 60)
    print("TEST 2: Insights de un mes específico (2024-10)")
    print("=" * 60)

    url = f"{API_URL}/insights?mes=2024-10"
    response = requests.get(url)

    print(f"Status Code: {response.status_code}")
    assert response.status_code == 200, "Debería retornar 200 OK"

    data = response.json()
    print(f"Mes: {data.get('mes')}")

    assert data["status"] == "success", "Status debe ser 'success'"
    assert data["mes"] == "2024-10", "Debe retornar el mes solicitado"

    print(f"\nOK - Total de insights generados: {len(data['insights'])}")

    if data["insights"]:
        print("\nInsights detectados:")
        for i, insight in enumerate(data["insights"], 1):
            print(f"\n  {i}. {insight['title']}")
            print(f"     {insight['message']}")
            print(f"     Accion: {insight['action']}")
    else:
        print("\nINFO - No se detectaron patrones relevantes en este periodo.")

    print("\nOK - TEST 2 PASO\n")
    return data["insights"]


def test_insights_maximo_7():
    """Test: Verificar que se limita a máximo 7 insights"""
    print("=" * 60)
    print("TEST 3: Límite de 7 insights")
    print("=" * 60)

    url = f"{API_URL}/insights"
    response = requests.get(url)
    data = response.json()

    insights_count = len(data["insights"])
    print(f"Total de insights: {insights_count}")

    assert insights_count <= 7, "No debe haber más de 7 insights"

    print("OK - TEST 3 PASO\n")


def test_insights_estructura():
    """Test: Verificar estructura de cada insight"""
    print("=" * 60)
    print("TEST 4: Estructura de insights")
    print("=" * 60)

    url = f"{API_URL}/insights"
    response = requests.get(url)
    data = response.json()

    if data["insights"]:
        insight = data["insights"][0]

        # Verificar campos requeridos
        assert "lens" in insight, "Debe tener campo 'lens'"
        assert "title" in insight, "Debe tener campo 'title'"
        assert "message" in insight, "Debe tener campo 'message'"
        assert "action" in insight, "Debe tener campo 'action'"

        # Verificar que no sean vacíos
        assert insight["title"], "title no debe estar vacío"
        assert insight["message"], "message no debe estar vacío"
        assert insight["action"], "action no debe estar vacío"

        print("Estructura del primer insight:")
        print(f"  - lens: {insight['lens']}")
        print(f"  - title: {insight['title']}")
        print(f"  - message: {insight['message'][:50]}...")
        print(f"  - action: {insight['action'][:50]}...")

        print("\nOK - TEST 4 PASO\n")
    else:
        print("WARN - No hay insights para validar estructura")


def test_insights_mes_invalido():
    """Test: Mes inválido debe retornar error 400"""
    print("=" * 60)
    print("TEST 5: Mes inválido (formato incorrecto)")
    print("=" * 60)

    url = f"{API_URL}/insights?mes=2024-13"  # Mes 13 no existe
    response = requests.get(url)

    print(f"Status Code: {response.status_code}")
    assert response.status_code == 400, "Debería retornar 400 Bad Request"

    print("OK - TEST 5 PASO\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTS DE INSIGHTS FINANCIEROS/OPERATIVOS")
    print("=" * 60 + "\n")

    try:
        test_insights_sin_mes()
        test_insights_con_mes()
        test_insights_maximo_7()
        test_insights_estructura()
        test_insights_mes_invalido()

        print("=" * 60)
        print("SUCCESS - TODOS LOS TESTS PASARON")
        print("=" * 60)

    except AssertionError as e:
        print(f"\nERROR - TEST FALLO: {e}\n")
        raise
    except Exception as e:
        print(f"\nERROR CRITICO: {e}\n")
        raise
