"""
Test rápido de las funciones de exportación
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from backend.database.connection import get_db
from backend.core.reportes import generar_reporte_ejecutivo
from backend.api.exportacion import generar_pdf_reporte
import pandas as pd
from backend.models.movimiento import Movimiento

print("=" * 80)
print("TEST DE EXPORTACIÓN - ETAPA 7")
print("=" * 80)

db = next(get_db())

# Test 1: Generar reporte
print("\n[1/3] Generando reporte ejecutivo...")
try:
    reporte = generar_reporte_ejecutivo(db, mes="2025-10")
    print(f"[OK] Reporte generado para: {reporte['periodo']}")
    print(f"  - Ingresos: ${reporte['kpis']['ingresos_total']:,.2f}")
    print(f"  - Egresos: ${reporte['kpis']['egresos_total']:,.2f}")
    print(f"  - Saldo Neto: ${reporte['kpis']['saldo_neto']:,.2f}")
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)

# Test 2: Generar PDF
print("\n[2/3] Generando PDF...")
try:
    pdf_buffer = generar_pdf_reporte(reporte)
    pdf_size = len(pdf_buffer.getvalue())
    print(f"[OK] PDF generado: {pdf_size:,} bytes")

    # Guardar archivo de prueba
    with open("test_reporte_octubre.pdf", "wb") as f:
        f.write(pdf_buffer.getvalue())
    print("[OK] PDF guardado en: test_reporte_octubre.pdf")
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Generar Excel
print("\n[3/3] Generando Excel...")
try:
    # Obtener movimientos de octubre
    movimientos = db.query(Movimiento).filter(
        Movimiento.fecha >= '2025-10-01',
        Movimiento.fecha <= '2025-10-31'
    ).order_by(Movimiento.fecha.desc()).all()

    print(f"  - Movimientos encontrados: {len(movimientos)}")

    if len(movimientos) > 0:
        # Crear DataFrame
        data = []
        for m in movimientos:
            data.append({
                'Fecha': m.fecha.strftime('%Y-%m-%d'),
                'Descripción': m.descripcion,
                'Monto': m.monto,
                'Saldo': m.saldo if m.saldo else '',
                'Categoría': m.categoria or 'SIN_CATEGORIA',
                'Subcategoría': m.subcategoria or '',
                'Confianza (%)': m.confianza_porcentaje or 0
            })

        df = pd.DataFrame(data)

        # Guardar Excel
        df.to_excel("test_movimientos_octubre.xlsx", index=False)
        print(f"[OK] Excel generado: test_movimientos_octubre.xlsx")
        print(f"  - Filas: {len(df)}")
        print(f"  - Columnas: {len(df.columns)}")
    else:
        print("[WARN] No hay movimientos en octubre")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("[OK] TODAS LAS PRUEBAS PASARON")
print("=" * 80)
print("\nArchivos generados:")
print("  - test_reporte_octubre.pdf")
print("  - test_movimientos_octubre.xlsx")

db.close()
