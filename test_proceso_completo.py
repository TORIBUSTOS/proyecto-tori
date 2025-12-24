"""
Test del endpoint POST /api/proceso-completo
Verifica que el flujo completo funciona correctamente
"""

import requests
import json
from pathlib import Path

# URL del endpoint
URL = "http://localhost:8000/api/proceso-completo"

# Archivo Excel de prueba
ARCHIVO_PRUEBA = Path("output/uploads/20251213_050953_extracto_prueba.xlsx")

def test_proceso_completo():
    """Test del endpoint proceso-completo"""

    print("\n" + "="*60)
    print("TEST: POST /api/proceso-completo")
    print("="*60)

    if not ARCHIVO_PRUEBA.exists():
        print(f"[ERROR] No se encuentra el archivo: {ARCHIVO_PRUEBA}")
        return

    print(f"\n[1] Archivo de prueba: {ARCHIVO_PRUEBA.name}")
    print(f"    Tamano: {ARCHIVO_PRUEBA.stat().st_size} bytes")

    # Preparar archivo para subir
    with open(ARCHIVO_PRUEBA, 'rb') as f:
        files = {'archivo': (ARCHIVO_PRUEBA.name, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}

        print("\n[2] Enviando peticion POST...")
        response = requests.post(URL, files=files)

    print(f"\n[3] Status code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()

        print("\n[4] Respuesta recibida:")
        print(f"    Status: {data.get('status')}")
        print(f"    Mensaje: {data.get('mensaje')}")

        # Mostrar resultados de consolidacion
        consolidar = data.get('consolidar', {})
        print(f"\n[5] CONSOLIDAR:")
        print(f"    Insertados: {consolidar.get('insertados')}")
        print(f"    Columnas detectadas: {consolidar.get('columnas_detectadas')}")
        print(f"    Archivo guardado: {consolidar.get('archivo_guardado')}")

        # Mostrar resultados de categorizacion
        categorizar = data.get('categorizar', {})
        print(f"\n[6] CATEGORIZAR:")
        print(f"    Procesados: {categorizar.get('procesados')}")
        print(f"    Categorizados: {categorizar.get('categorizados')}")
        print(f"    Sin match: {categorizar.get('sin_match')}")
        print(f"    Categorias distintas: {categorizar.get('categorias_distintas')}")

        # Mostrar resultados del reporte
        reporte = data.get('reporte', {})
        print(f"\n[7] REPORTE (periodo: {reporte.get('periodo')}):")
        kpis = reporte.get('kpis', {})
        print(f"    Ingresos total: ${kpis.get('ingresos_total'):,.2f}")
        print(f"    Egresos total: ${kpis.get('egresos_total'):,.2f}")
        print(f"    Saldo neto: ${kpis.get('saldo_neto'):,.2f}")
        print(f"    Cantidad movimientos: {kpis.get('cantidad_movimientos')}")
        print(f"    Categorias activas: {kpis.get('categorias_activas')}")

        # Top egresos
        top_egresos = reporte.get('top_egresos_por_categoria', [])
        if top_egresos:
            print(f"\n[8] TOP 5 EGRESOS:")
            for i, item in enumerate(top_egresos[:5], 1):
                print(f"    {i}. {item.get('categoria')}: ${item.get('total_egresos'):,.2f}")

        print("\n" + "="*60)
        print("[OK] TEST EXITOSO - Proceso completo funciona correctamente")
        print("="*60)

        # Guardar JSON completo para debug
        with open("test_resultado.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("\n[INFO] JSON completo guardado en: test_resultado.json\n")

    else:
        print(f"\n[ERROR] Peticion fallida")
        print(f"Respuesta: {response.text}")
        print("="*60 + "\n")

if __name__ == "__main__":
    test_proceso_completo()
