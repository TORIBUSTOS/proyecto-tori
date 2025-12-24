"""
Módulo core para gestión de batches de importación
Operaciones de anulación y rollback de batches
"""

from fastapi import HTTPException
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from backend.models.import_batch import ImportBatch
from backend.models.movimiento import Movimiento


def anular_batch(db: Session, batch_id: int) -> dict:
    """
    Anula un batch completo eliminando todos sus movimientos y el batch mismo.

    Operación ATÓMICA: todo se ejecuta dentro de una transacción.
    Si algo falla, se revierte todo (rollback automático).

    Args:
        db: Sesión de base de datos SQLAlchemy
        batch_id: ID del batch a anular

    Returns:
        dict con:
            - status: "success"
            - batch_id: ID del batch eliminado
            - movimientos_eliminados: cantidad de movimientos borrados
            - batch: info del batch (filename, imported_at)

    Raises:
        HTTPException 404: Si el batch no existe
        HTTPException 500: Si hay error en la operación
    """
    with db.begin():
        # 1. Verificar que el batch existe
        batch = db.execute(
            select(ImportBatch).where(ImportBatch.id == batch_id)
        ).scalar_one_or_none()

        if not batch:
            raise HTTPException(
                status_code=404,
                detail=f"Batch {batch_id} no existe"
            )

        # 2. Contar movimientos asociados al batch
        ids = db.execute(
            select(Movimiento.id).where(Movimiento.batch_id == batch_id)
        ).scalars().all()
        count = len(ids)

        # 3. Eliminar movimientos (hard delete)
        db.execute(
            delete(Movimiento).where(Movimiento.batch_id == batch_id)
        )

        # 4. Eliminar batch (hard delete)
        db.execute(
            delete(ImportBatch).where(ImportBatch.id == batch_id)
        )

    # 5. Retornar resultado
    return {
        "status": "success",
        "batch_id": batch_id,
        "movimientos_eliminados": count,
        "batch": {
            "filename": batch.filename,
            "imported_at": batch.imported_at.isoformat()
            if getattr(batch, "imported_at", None)
            else None
        }
    }
