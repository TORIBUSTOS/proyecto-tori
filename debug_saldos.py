"""
Debug script para analizar diferencia en saldos inicial/final
"""
from backend.database.connection import SessionLocal
from backend.models.movimiento import Movimiento
from sqlalchemy import func
from datetime import date

db = SessionLocal()

# Fecha de inicio noviembre 2025
fecha_inicio = date(2025, 11, 1)

print("\n" + "=" * 80)
print("ANÁLISIS DE SALDOS - NOVIEMBRE 2025")
print("=" * 80)

# Primeros 10 movimientos de agosto
primeros = db.query(Movimiento).order_by(Movimiento.fecha.asc(), Movimiento.id.asc()).limit(10).all()

print("\nPrimeros 10 movimientos en DB:")
print("-" * 80)
for m in primeros:
    print(f"{m.fecha} | {m.monto:>15,.2f} | {m.descripcion[:50]}")

# Suma por mes
print("\n" + "=" * 80)
print("SUMA POR MES:")
print("=" * 80)

# Agosto
agosto_sum = db.query(func.sum(Movimiento.monto)).filter(
    Movimiento.fecha >= date(2025, 8, 1),
    Movimiento.fecha < date(2025, 9, 1)
).scalar() or 0.0
agosto_count = db.query(func.count(Movimiento.id)).filter(
    Movimiento.fecha >= date(2025, 8, 1),
    Movimiento.fecha < date(2025, 9, 1)
).scalar() or 0
print(f"Agosto 2025: ${agosto_sum:,.2f} ({agosto_count} movimientos)")

# Septiembre
sept_sum = db.query(func.sum(Movimiento.monto)).filter(
    Movimiento.fecha >= date(2025, 9, 1),
    Movimiento.fecha < date(2025, 10, 1)
).scalar() or 0.0
sept_count = db.query(func.count(Movimiento.id)).filter(
    Movimiento.fecha >= date(2025, 9, 1),
    Movimiento.fecha < date(2025, 10, 1)
).scalar() or 0
print(f"Septiembre 2025: ${sept_sum:,.2f} ({sept_count} movimientos)")

# Octubre
oct_sum = db.query(func.sum(Movimiento.monto)).filter(
    Movimiento.fecha >= date(2025, 10, 1),
    Movimiento.fecha < date(2025, 11, 1)
).scalar() or 0.0
oct_count = db.query(func.count(Movimiento.id)).filter(
    Movimiento.fecha >= date(2025, 10, 1),
    Movimiento.fecha < date(2025, 11, 1)
).scalar() or 0
print(f"Octubre 2025: ${oct_sum:,.2f} ({oct_count} movimientos)")

# Noviembre (el mes del reporte)
nov_sum = db.query(func.sum(Movimiento.monto)).filter(
    Movimiento.fecha >= date(2025, 11, 1),
    Movimiento.fecha < date(2025, 12, 1)
).scalar() or 0.0
nov_count = db.query(func.count(Movimiento.id)).filter(
    Movimiento.fecha >= date(2025, 11, 1),
    Movimiento.fecha < date(2025, 12, 1)
).scalar() or 0
print(f"Noviembre 2025: ${nov_sum:,.2f} ({nov_count} movimientos)")

print("\n" + "=" * 80)
print("CÁLCULO DE SALDOS:")
print("=" * 80)

saldo_antes_nov = agosto_sum + sept_sum + oct_sum
print(f"Saldo ANTES de noviembre (ago+sept+oct): ${saldo_antes_nov:,.2f}")
print(f"Variación en noviembre: ${nov_sum:,.2f}")
print(f"Saldo DESPUÉS de noviembre: ${saldo_antes_nov + nov_sum:,.2f}")

print("\n" + "=" * 80)
print("COMPARACIÓN CON EXCEL:")
print("=" * 80)
excel_saldo_inicial = 1336671.62
excel_saldo_final = 14930103.81
excel_variacion = excel_saldo_final - excel_saldo_inicial

print(f"Excel Saldo Inicial: ${excel_saldo_inicial:,.2f}")
print(f"Web Saldo Inicial:   ${saldo_antes_nov:,.2f}")
print(f"DIFERENCIA:          ${excel_saldo_inicial - saldo_antes_nov:,.2f}")
print(f"")
print(f"Excel Saldo Final:   ${excel_saldo_final:,.2f}")
print(f"Web Saldo Final:     ${saldo_antes_nov + nov_sum:,.2f}")
print(f"DIFERENCIA:          ${excel_saldo_final - (saldo_antes_nov + nov_sum):,.2f}")

print("\n" + "=" * 80)

db.close()
