"""
Modulo de consolidacion de extractos bancarios
Lee archivos Excel y guarda movimientos en la base de datos
"""

import re
import unicodedata
import pandas as pd
from io import BytesIO
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from backend.models.movimiento import Movimiento
from backend.models.import_batch import ImportBatch
from backend.utils.file_hash import calculate_file_hash
from backend.core.extractores import extraer_metadata_completa


def _norm_col(name: str) -> str:
    """
    Normaliza nombres de columnas de forma agresiva:
    1) strip y lowercase
    2) quitar tildes/acentos (NFKD)
    3) reemplazar todo lo no-alfanumérico por espacio
    4) colapsar espacios
    5) eliminar espacios para match más fuerte
    """
    s = str(name).strip().lower()
    # quitar tildes/acentos
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    # reemplazar cualquier cosa no alfanum por espacio
    s = re.sub(r"[^a-z0-9]+", " ", s)
    # colapsar espacios y quitar
    s = re.sub(r"\s+", " ", s).strip()
    # versión sin espacios para match más fuerte
    return s.replace(" ", "")


def consolidar_excel(file_bytes: bytes, filename: str, db: Session) -> dict:
    """
    Consolida un archivo Excel de extracto bancario y guarda en DB

    Formato esperado del Excel:
    Fecha | Concepto | Detalle | Debito | Credito | Saldo

    Args:
        file_bytes: Contenido del archivo en bytes
        filename: Nombre del archivo original
        db: Sesion de base de datos SQLAlchemy

    Returns:
        dict con:
            - insertados: cantidad de movimientos insertados
            - columnas_detectadas: lista de columnas encontradas
            - archivo_guardado: ruta donde se guardo el archivo
            - batch_id: ID del batch creado

    Raises:
        ValueError: Si el archivo ya fue importado previamente (código 409)
    """
    print("=" * 80)
    print(f"DEBUG consolidar.py: INICIO - Procesando archivo: {filename}")
    print("=" * 80)

    # 0. Calcular hash del archivo y verificar duplicados
    file_hash = calculate_file_hash(file_bytes)
    print(f"DEBUG consolidar.py: Hash del archivo: {file_hash}")

    existing_batch = db.query(ImportBatch).filter(ImportBatch.file_hash == file_hash).first()
    if existing_batch:
        raise ValueError(
            f"DUPLICATE_FILE: Este archivo ya fue importado el {existing_batch.imported_at.isoformat()} "
            f"con {existing_batch.rows_inserted} movimientos (batch_id: {existing_batch.id})"
        )

    # 1. Guardar archivo en ./output/uploads/
    output_dir = Path("./output/uploads")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{filename}"
    file_path = output_dir / safe_filename

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # 2. Leer Excel con pandas desde BytesIO
    excel_buffer = BytesIO(file_bytes)
    df = pd.read_excel(excel_buffer)

    # Guardar columnas originales para debug
    original_cols = list(df.columns)
    print(f"DEBUG consolidar.py: Columnas originales del Excel: {original_cols}")

    # Crear mapeo: columna_original -> columna_normalizada
    norm_map = {c: _norm_col(c) for c in df.columns}
    print(f"DEBUG consolidar.py: Mapeo normalizado: {norm_map}")

    # Alias -> canónico (nombres normalizados de alias a nombre canónico)
    ALIASES = {
        # fecha
        "fecha": "fecha",
        "fechayhora": "fecha",
        "date": "fecha",
        # concepto
        "concepto": "concepto",
        "descripcion": "concepto",
        "description": "concepto",
        # detalle
        "detalle": "detalle",
        "detail": "detalle",
        "observaciones": "detalle",
        # débito
        "debito": "debito",
        "debitos": "debito",
        "debit": "debito",
        "cargo": "debito",
        # crédito
        "credito": "credito",
        "creditos": "credito",
        "credit": "credito",
        "abono": "credito",
        # saldo
        "saldo": "saldo",
        "balance": "saldo",
    }

    # Renombrar a canónicos cuando matchea alias
    rename_to_canon = {}
    for col, n in norm_map.items():
        if n in ALIASES:
            rename_to_canon[col] = ALIASES[n]

    print(f"DEBUG consolidar.py: Renombrado a canónico: {rename_to_canon}")

    df = df.rename(columns=rename_to_canon)

    # Validar que tenemos todas las columnas requeridas
    columnas_requeridas = {"fecha", "concepto", "detalle", "debito", "credito", "saldo"}
    presentes = set(df.columns)
    faltantes = sorted(list(columnas_requeridas - presentes))

    if faltantes:
        # mensaje súper explícito para debug
        raise ValueError(
            "Columnas faltantes en el Excel: "
            f"{faltantes}\n"
            f"Columnas originales: {original_cols}\n"
            f"Columnas normalizadas: {list(norm_map.values())}\n"
            f"Columnas renombradas (a canónico): {list(df.columns)}"
        )

    columnas_detectadas = original_cols

    # 4. Crear batch de importación
    batch = ImportBatch(
        filename=filename,
        file_hash=file_hash,
        rows_inserted=0
    )
    db.add(batch)
    db.flush()  # Obtener el ID sin hacer commit aún

    batch_id = batch.id
    print(f"DEBUG consolidar.py: Batch creado con ID: {batch_id}")

    # 5. Transformar datos usando columnas canónicas
    movimientos_insertados = 0

    for _, row in df.iterrows():
        # Ignorar filas vacias (si fecha es NaN)
        if pd.isna(row["fecha"]):
            continue

        # Parsear fecha
        fecha_val = row["fecha"]
        if isinstance(fecha_val, str):
            fecha = pd.to_datetime(fecha_val).date()
        else:
            fecha = fecha_val.date() if hasattr(fecha_val, "date") else fecha_val

        # Concatenar concepto + detalle
        concepto = str(row["concepto"]) if not pd.isna(row["concepto"]) else ""
        detalle = str(row["detalle"]) if not pd.isna(row["detalle"]) else ""
        descripcion = f"{concepto} - {detalle}".strip(" -")

        # Calcular monto: credito - debito
        debito = float(row["debito"]) if not pd.isna(row["debito"]) else 0.0
        credito = float(row["credito"]) if not pd.isna(row["credito"]) else 0.0
        monto = credito - debito

        # Obtener saldo bancario real
        saldo = float(row["saldo"]) if not pd.isna(row["saldo"]) else None

        # 6. Extraer metadata automáticamente (ETAPA 2.1)
        try:
            metadata = extraer_metadata_completa(concepto, detalle)
        except Exception as e:
            # Si falla la extracción, continuar sin metadata (no romper el flujo)
            print(f"WARN consolidar.py: Error extrayendo metadata: {e}")
            metadata = {
                'persona_nombre': None,
                'documento': None,
                'es_debin': False,
                'debin_id': None,
                'cbu': None,
                'comercio': None,
                'terminal': None,
                'referencia': None
            }

        # 7. Insertar en DB con batch_id, saldo y metadata
        movimiento = Movimiento(
            fecha=fecha,
            descripcion=descripcion,
            monto=monto,
            saldo=saldo,  # Saldo bancario real del Excel
            categoria="SIN_CATEGORIA",
            batch_id=batch_id,
            # Metadata extraída (8 campos)
            persona_nombre=metadata.get('persona_nombre'),
            documento=metadata.get('documento'),
            es_debin=metadata.get('es_debin', False),
            debin_id=metadata.get('debin_id'),
            cbu=metadata.get('cbu'),
            comercio=metadata.get('comercio'),
            terminal=metadata.get('terminal'),
            referencia=metadata.get('referencia')
        )

        db.add(movimiento)
        movimientos_insertados += 1

    # Actualizar contador de filas en el batch
    batch.rows_inserted = movimientos_insertados

    # Commit de todos los movimientos y el batch
    db.commit()

    # 7. Retornar resultado
    return {
        "insertados": movimientos_insertados,
        "columnas_detectadas": columnas_detectadas,
        "archivo_guardado": str(file_path),
        "batch_id": batch_id
    }
