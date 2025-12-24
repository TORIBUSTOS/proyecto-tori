"""
Test simple para verificar que /analytics y /reportes devuelven los mismos totales
"""

import requests

BASE_URL = "http://localhost:8000/api"

def test_analytics_vs_reportes(mes=None):
    """
    Compara los totales de ingresos y egresos entre /analytics y /reportes
    """
    print("\n" + "="*60)
    print("TEST: Comparando /analytics con /reportes")
    if mes:
        print(f"Periodo: {mes}")
    else:
        print("Periodo: Mes actual")
    print("="*60 + "\n")

    # 1. Obtener datos del reporte ejecutivo
    url_reporte = f"{BASE_URL}/reportes"
    if mes:
        url_reporte += f"?mes={mes}"

    print("Obteniendo datos de /reportes...")
    try:
        resp_reporte = requests.get(url_reporte)
        resp_reporte.raise_for_status()
        reporte = resp_reporte.json()["reporte"]

        total_ingresos_reporte = reporte["saldos"]["ingresos_total"]
        total_egresos_reporte = reporte["saldos"]["egresos_total"]

        print(f"   OK - Total Ingresos (reporte): ${total_ingresos_reporte:,.2f}")
        print(f"   OK - Total Egresos (reporte):  ${total_egresos_reporte:,.2f}")
    except Exception as e:
        print(f"   ERROR obteniendo reporte: {e}")
        return False

    # 2. Obtener datos de /analytics/pie-ingresos
    url_ingresos = f"{BASE_URL}/analytics/pie-ingresos"
    if mes:
        url_ingresos += f"?mes={mes}"

    print("\nObteniendo datos de /analytics/pie-ingresos...")
    try:
        resp_ingresos = requests.get(url_ingresos)
        resp_ingresos.raise_for_status()
        data_ingresos = resp_ingresos.json()

        total_ingresos_analytics = data_ingresos["total"]

        print(f"   OK - Total Ingresos (analytics): ${total_ingresos_analytics:,.2f}")
        print(f"   OK - Formato: status={data_ingresos.get('status')}, items={len(data_ingresos.get('data', []))}")
    except Exception as e:
        print(f"   ERROR obteniendo pie-ingresos: {e}")
        return False

    # 3. Obtener datos de /analytics/pie-egresos
    url_egresos = f"{BASE_URL}/analytics/pie-egresos"
    if mes:
        url_egresos += f"?mes={mes}"

    print("\nObteniendo datos de /analytics/pie-egresos...")
    try:
        resp_egresos = requests.get(url_egresos)
        resp_egresos.raise_for_status()
        data_egresos = resp_egresos.json()

        total_egresos_analytics = data_egresos["total"]

        print(f"   OK - Total Egresos (analytics):  ${total_egresos_analytics:,.2f}")
        print(f"   OK - Formato: status={data_egresos.get('status')}, items={len(data_egresos.get('data', []))}")
    except Exception as e:
        print(f"   ERROR obteniendo pie-egresos: {e}")
        return False

    # 4. Comparar totales
    print("\n" + "="*60)
    print("COMPARACION DE TOTALES:")
    print("="*60 + "\n")

    # Comparar ingresos
    diff_ingresos = abs(total_ingresos_reporte - total_ingresos_analytics)
    match_ingresos = diff_ingresos < 0.01  # Tolerancia de 1 centavo

    print("INGRESOS:")
    print(f"   Reporte:   ${total_ingresos_reporte:,.2f}")
    print(f"   Analytics: ${total_ingresos_analytics:,.2f}")
    print(f"   Diferencia: ${diff_ingresos:,.2f}")

    if match_ingresos:
        print("   RESULTADO: OK - COINCIDEN")
    else:
        print("   RESULTADO: FALLO - NO COINCIDEN")

    # Comparar egresos
    diff_egresos = abs(total_egresos_reporte - total_egresos_analytics)
    match_egresos = diff_egresos < 0.01  # Tolerancia de 1 centavo

    print("\nEGRESOS:")
    print(f"   Reporte:   ${total_egresos_reporte:,.2f}")
    print(f"   Analytics: ${total_egresos_analytics:,.2f}")
    print(f"   Diferencia: ${diff_egresos:,.2f}")

    if match_egresos:
        print("   RESULTADO: OK - COINCIDEN")
    else:
        print("   RESULTADO: FALLO - NO COINCIDEN")

    # 5. Verificar formato de respuesta
    print("\n" + "="*60)
    print("VERIFICACION DE FORMATO:")
    print("="*60 + "\n")

    print("Estructura de /analytics/pie-ingresos:")
    print(f"   - status: {data_ingresos.get('status')}")
    print(f"   - total: {data_ingresos.get('total')}")
    print(f"   - data (primeros 3 items):")
    for item in data_ingresos.get('data', [])[:3]:
        print(f"       - {item['label']}: ${item['value']:,.2f}")

    print("\nEstructura de /analytics/pie-egresos:")
    print(f"   - status: {data_egresos.get('status')}")
    print(f"   - total: {data_egresos.get('total')}")
    print(f"   - data (primeros 3 items):")
    for item in data_egresos.get('data', [])[:3]:
        print(f"       - {item['label']}: ${item['value']:,.2f}")

    # 6. Resultado final
    print("\n" + "="*60)
    if match_ingresos and match_egresos:
        print("RESULTADO FINAL: TEST EXITOSO - Todos los totales coinciden")
    else:
        print("RESULTADO FINAL: TEST FALLIDO - Los totales no coinciden")
    print("="*60 + "\n")

    return match_ingresos and match_egresos


if __name__ == "__main__":
    # Test 1: Sin filtro de mes (mes actual)
    print("\n" + "="*60)
    print("TEST 1: Sin filtro de mes (mes actual)")
    print("="*60)
    test_analytics_vs_reportes()

    # Test 2: Con un mes específico (ajustar según tus datos)
    print("\n" + "="*60)
    print("TEST 2: Con mes especifico (2024-10)")
    print("="*60)
    test_analytics_vs_reportes(mes="2024-10")

    print("\nTests completados\n")
