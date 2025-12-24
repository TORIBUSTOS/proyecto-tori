"""
Test de Resumen Ejecutivo en Analytics

Valida que el endpoint /api/reportes retorne datos correctos
que se renderizarán en la página de analytics.
"""

import sys
import io
from pathlib import Path

# Fix encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal
from backend.core.reportes import generar_reporte_ejecutivo
import json


def test_reporte_ejecutivo():
    """Test del reporte ejecutivo para analytics"""
    print("=" * 70)
    print("TEST RESUMEN EJECUTIVO - ANALYTICS")
    print("=" * 70)

    db = SessionLocal()

    try:
        # Generar reporte para noviembre 2025
        print("\n[1/3] Generando reporte para Nov 2025...")
        reporte = generar_reporte_ejecutivo(db, mes="2025-11")

        print("✓ Reporte generado")

        # Validar estructura
        print("\n[2/3] Validando estructura del reporte...")

        assert "saldos" in reporte, "Debe tener sección 'saldos'"
        assert "clasificacion" in reporte, "Debe tener sección 'clasificacion'"
        assert "desglose_ingresos" in reporte, "Debe tener 'desglose_ingresos'"
        assert "desglose_egresos" in reporte, "Debe tener 'desglose_egresos'"

        print("✓ Estructura correcta")

        # Mostrar datos
        print("\n[3/3] Datos del reporte:")
        print("\n💰 SALDOS BANCARIOS:")
        saldos = reporte["saldos"]
        print(f"  Saldo Inicial: ${saldos['saldo_inicial']:,.2f}")
        print(f"  Total Ingresos: ${saldos['ingresos_total']:,.2f}")
        print(f"  Total Egresos: ${saldos['egresos_total']:,.2f}")
        print(f"  Saldo Final: ${saldos['saldo_final']:,.2f}")
        print(f"  Variación: ${saldos['variacion']:,.2f}")

        print("\n📊 CLASIFICACIÓN:")
        clasif = reporte["clasificacion"]
        print(f"  Total movimientos: {clasif['total_movimientos']}")
        print(f"  Clasificados: {clasif['clasificados']}")
        print(f"  Sin clasificar: {clasif['sin_clasificar']}")
        print(f"  % Clasificados: {clasif['pct_clasificados']}%")

        print("\n💵 DESGLOSE INGRESOS:")
        ingresos = reporte["desglose_ingresos"]
        if ingresos:
            for item in ingresos:
                print(f"  {item['categoria']}: ${item['monto']:,.2f}")
        else:
            print("  (Sin ingresos)")

        print("\n💸 DESGLOSE EGRESOS:")
        egresos = reporte["desglose_egresos"]
        if egresos:
            for item in egresos[:10]:  # Mostrar top 10
                print(f"  {item['categoria']}: ${item['monto']:,.2f}")
            if len(egresos) > 10:
                print(f"  ... y {len(egresos) - 10} más")
        else:
            print("  (Sin egresos)")

        # Validar que hay datos
        print("\n[VALIDACIÓN]")
        assert clasif['total_movimientos'] > 0, "Debe haber movimientos"
        print(f"✓ Hay {clasif['total_movimientos']} movimientos en Nov 2025")

        # Guardar JSON para inspección
        output_file = "test_reporte_analytics.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False)
        print(f"✓ Reporte guardado en {output_file}")

        print("\n" + "=" * 70)
        print("✅ TEST EXITOSO - Reporte ejecutivo listo para Analytics")
        print("=" * 70)

        print("\n📋 INSTRUCCIONES PARA VALIDACIÓN MANUAL:")
        print("1. Iniciar servidor: python run_dev.py")
        print("2. Abrir /reportes?mes=2025-11")
        print("3. Anotar valores de saldos y clasificación")
        print("4. Abrir /analytics y seleccionar 'Nov 2025'")
        print("5. Scroll abajo al 'Resumen Ejecutivo'")
        print("6. Verificar que los valores coincidan exactamente")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    test_reporte_ejecutivo()
