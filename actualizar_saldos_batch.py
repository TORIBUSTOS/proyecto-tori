"""
Script para actualizar saldos de un batch ya consolidado

Uso:
    python actualizar_saldos_batch.py <batch_id> <ruta_excel>

Ejemplo:
    python actualizar_saldos_batch.py 18 "data/movimientos_consolidados_2025_11.xlsx"
"""

import sys
import pandas as pd
from backend.database.connection import SessionLocal
from backend.models.movimiento import Movimiento
from datetime import datetime

def actualizar_saldos_batch(batch_id: int, excel_path: str):
    """
    Actualiza los saldos de movimientos de un batch existente
    leyendo el Excel original
    """
    print("\n" + "=" * 80)
    print(f"ACTUALIZAR SALDOS - BATCH {batch_id}")
    print("=" * 80)

    # Leer Excel
    print(f"\nLeyendo Excel: {excel_path}")
    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        print(f"ERROR leyendo Excel: {e}")
        return

    # Normalizar nombres de columnas
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Validar que existe columna saldo
    if "saldo" not in df.columns:
        print("ERROR: El Excel no tiene columna 'saldo'")
        print(f"Columnas encontradas: {list(df.columns)}")
        return

    print(f"OK - Excel cargado con {len(df)} filas")

    # Conectar a DB
    db = SessionLocal()

    try:
        # Obtener movimientos del batch
        movimientos = db.query(Movimiento).filter(
            Movimiento.batch_id == batch_id
        ).order_by(Movimiento.fecha.asc(), Movimiento.id.asc()).all()

        if not movimientos:
            print(f"ERROR: No se encontraron movimientos para batch {batch_id}")
            return

        print(f"OK - Encontrados {len(movimientos)} movimientos en batch {batch_id}")

        # Validar que coinciden las cantidades
        if len(movimientos) != len(df):
            print(f"ADVERTENCIA: Excel tiene {len(df)} filas pero batch tiene {len(movimientos)} movimientos")
            print("Esto puede causar desincronización")
            confirmar = input("¿Continuar de todos modos? (s/n): ")
            if confirmar.lower() != 's':
                print("Operación cancelada")
                return

        # Actualizar saldos
        print("\nActualizando saldos...")
        actualizados = 0
        errores = 0

        for idx, row in df.iterrows():
            # Saltar filas vacías
            if pd.isna(row.get("fecha")):
                continue

            # Obtener saldo del Excel
            saldo_excel = float(row["saldo"]) if not pd.isna(row["saldo"]) else None

            if saldo_excel is None:
                continue

            # Buscar movimiento correspondiente (por índice)
            if idx < len(movimientos):
                mov = movimientos[idx]

                # Actualizar saldo
                mov.saldo = saldo_excel
                actualizados += 1

                if actualizados % 100 == 0:
                    print(f"   Procesados: {actualizados}/{len(df)}")
            else:
                errores += 1

        # Commit
        db.commit()

        print("\n" + "=" * 80)
        print("RESULTADO:")
        print("=" * 80)
        print(f"Movimientos actualizados: {actualizados}")
        print(f"Errores: {errores}")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\nERROR durante la actualización: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python actualizar_saldos_batch.py <batch_id> <ruta_excel>")
        print("Ejemplo: python actualizar_saldos_batch.py 18 'data/movimientos_consolidados_2025_11.xlsx'")
        sys.exit(1)

    batch_id = int(sys.argv[1])
    excel_path = sys.argv[2]

    actualizar_saldos_batch(batch_id, excel_path)
