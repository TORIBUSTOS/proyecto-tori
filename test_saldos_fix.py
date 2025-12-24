"""
Test: Verificar que el fix de saldos funciona correctamente
"""
from backend.database.connection import SessionLocal
from backend.core.reportes import generar_reporte_ejecutivo

db = SessionLocal()

print("\n" + "=" * 80)
print("TEST: VERIFICAR FIX DE SALDOS BANCARIOS")
print("=" * 80)

# Generar reporte de noviembre 2025
reporte = generar_reporte_ejecutivo(db, mes="2025-11")

print(f"\nReporte Ejecutivo - Noviembre 2025")
print(f"-" * 80)

# Mostrar saldos
saldos = reporte["saldos"]
print(f"\nSALDOS BANCARIOS:")
print(f"  Saldo Inicial: ${saldos['saldo_inicial']:,.2f}")
print(f"  Ingresos:      +${saldos['ingresos_total']:,.2f}")
print(f"  Egresos:       -${saldos['egresos_total']:,.2f}")
print(f"  Variación:     ${saldos['variacion']:,.2f}")
print(f"  Saldo Final:   ${saldos['saldo_final']:,.2f}")

print(f"\n" + "=" * 80)
print(f"VALIDACIÓN:")
print(f"=" * 80)

# Valores esperados (según el usuario)
saldo_inicial_esperado = 1336671.62
saldo_final_esperado = 14930103.81

print(f"\nSaldo Inicial:")
print(f"  Esperado: ${saldo_inicial_esperado:,.2f}")
print(f"  Obtenido: ${saldos['saldo_inicial']:,.2f}")
diferencia_inicial = abs(saldos['saldo_inicial'] - saldo_inicial_esperado)
print(f"  Diferencia: ${diferencia_inicial:,.2f}")

if diferencia_inicial < 1.0:
    print(f"  OK - CORRECTO")
else:
    print(f"  ERROR - Diferencia: ${diferencia_inicial:,.2f}")

print(f"\nSaldo Final:")
print(f"  Esperado: ${saldo_final_esperado:,.2f}")
print(f"  Obtenido: ${saldos['saldo_final']:,.2f}")
diferencia_final = abs(saldos['saldo_final'] - saldo_final_esperado)
print(f"  Diferencia: ${diferencia_final:,.2f}")

if diferencia_final < 1.0:
    print(f"  OK - CORRECTO")
else:
    print(f"  ERROR - Diferencia: ${diferencia_final:,.2f}")

print(f"\n" + "=" * 80)

if diferencia_inicial < 1.0 and diferencia_final < 1.0:
    print(f"OK - FIX EXITOSO - Los saldos ahora coinciden con el Excel")
else:
    print(f"ERROR - FIX INCOMPLETO - Revisar logica de calculo")

print("=" * 80 + "\n")

db.close()
