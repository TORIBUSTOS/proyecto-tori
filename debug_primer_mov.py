"""
Debug: Analizar primer movimiento de noviembre para entender saldo_inicial
"""
from backend.database.connection import SessionLocal
from backend.models.movimiento import Movimiento
from datetime import date
from sqlalchemy import and_

db = SessionLocal()

# Buscar primer movimiento de noviembre 2025
fecha_inicio = date(2025, 11, 1)
fecha_fin = date(2025, 12, 1)

primer_mov = db.query(Movimiento).filter(
    and_(
        Movimiento.fecha >= fecha_inicio,
        Movimiento.fecha < fecha_fin,
        Movimiento.saldo.isnot(None)
    )
).order_by(Movimiento.fecha.asc(), Movimiento.id.asc()).first()

print("\n" + "=" * 80)
print("ANALISIS DEL PRIMER MOVIMIENTO DE NOVIEMBRE 2025")
print("=" * 80)

if primer_mov:
    print(f"\nPrimer movimiento de noviembre:")
    print(f"  ID: {primer_mov.id}")
    print(f"  Fecha: {primer_mov.fecha}")
    print(f"  Descripcion: {primer_mov.descripcion[:80]}")
    print(f"  Monto: ${primer_mov.monto:,.2f}")
    print(f"  Saldo (DESPUES del mov): ${primer_mov.saldo:,.2f}")
    print(f"\n" + "-" * 80)
    print(f"CALCULO DE SALDO_INICIAL:")
    print(f"-" * 80)
    print(f"  Formula actual en reportes.py: saldo_inicial = primer_mov.saldo - primer_mov.monto")
    print(f"  = {primer_mov.saldo:,.2f} - ({primer_mov.monto:,.2f})")
    print(f"  = ${primer_mov.saldo - primer_mov.monto:,.2f}")
    print(f"\n  Este deberia ser el saldo ANTES del primer movimiento")
    print(f"\n" + "=" * 80)
    print(f"ESPERADO (segun usuario): $1,336,671.62")
    print(f"OBTENIDO: ${primer_mov.saldo - primer_mov.monto:,.2f}")
    print(f"DIFERENCIA: ${1336671.62 - (primer_mov.saldo - primer_mov.monto):,.2f}")
    print("=" * 80 + "\n")
else:
    print("\nERROR: No se encontro primer movimiento con saldo")

# Mostrar primeros 5 movimientos de noviembre
print("\n" + "=" * 80)
print("PRIMEROS 5 MOVIMIENTOS DE NOVIEMBRE (para contexto)")
print("=" * 80)

primeros_5 = db.query(Movimiento).filter(
    and_(
        Movimiento.fecha >= fecha_inicio,
        Movimiento.fecha < fecha_fin,
        Movimiento.saldo.isnot(None)
    )
).order_by(Movimiento.fecha.asc(), Movimiento.id.asc()).limit(5).all()

for idx, mov in enumerate(primeros_5, 1):
    print(f"\n{idx}. Fecha: {mov.fecha} | Monto: ${mov.monto:,.2f} | Saldo: ${mov.saldo:,.2f}")
    print(f"   Desc: {mov.descripcion[:70]}")

print("\n" + "=" * 80 + "\n")

db.close()
