"""
Gestión administrativa de Batches

Módulo para listar y eliminar batches de manera segura.
ADVERTENCIA: La eliminación de un batch es DEFINITIVA y borra
todos los movimientos asociados.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models import ImportBatch, Movimiento, AuditLog
from typing import Optional


def list_batches(db: Session) -> list[dict]:
    """
    Lista todos los batches importados con sus estadísticas.

    Returns:
        list[dict]: Lista de batches con:
            - id
            - filename (origen)
            - imported_at (created_at)
            - rows_inserted (total según registro)
            - total_movimientos (count real actual)
    """
    # Obtener batches con count de movimientos actuales
    query = db.query(
        ImportBatch.id,
        ImportBatch.filename,
        ImportBatch.imported_at,
        ImportBatch.rows_inserted,
        func.count(Movimiento.id).label('total_movimientos')
    ).outerjoin(
        Movimiento,
        ImportBatch.id == Movimiento.batch_id
    ).group_by(
        ImportBatch.id
    ).order_by(
        ImportBatch.imported_at.desc()
    )

    batches = query.all()

    return [
        {
            "id": b.id,
            "origen": b.filename,
            "created_at": b.imported_at.isoformat() if b.imported_at else None,
            "rows_inserted": b.rows_inserted,
            "total_movimientos": b.total_movimientos or 0
        }
        for b in batches
    ]


def delete_batch(db: Session, batch_id: int, actor: str = "admin") -> dict:
    """
    Elimina un batch y TODOS sus movimientos asociados.

    ADVERTENCIA: Esta operación es DEFINITIVA y NO reversible.

    Args:
        db: Sesión de base de datos
        batch_id: ID del batch a eliminar
        actor: Usuario que ejecuta la operación

    Returns:
        dict: Resumen del borrado con:
            - batch_id
            - origen (filename)
            - movimientos_eliminados (count)
            - audit_id

    Raises:
        ValueError: Si el batch no existe
    """
    # Validar existencia del batch
    batch = db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()

    if not batch:
        raise ValueError(f"Batch {batch_id} no existe")

    # Contar movimientos asociados
    movimientos_count = db.query(Movimiento).filter(
        Movimiento.batch_id == batch_id
    ).count()

    # Guardar info para auditoría
    batch_info = {
        "batch_id": batch.id,
        "filename": batch.filename,
        "file_hash": batch.file_hash,
        "imported_at": batch.imported_at.isoformat() if batch.imported_at else None,
        "rows_inserted": batch.rows_inserted,
        "movimientos_count": movimientos_count
    }

    # BORRADO EN TRANSACCIÓN
    # 1. Eliminar movimientos asociados
    db.query(Movimiento).filter(Movimiento.batch_id == batch_id).delete()

    # 2. Eliminar registro de batch
    db.query(ImportBatch).filter(ImportBatch.id == batch_id).delete()

    # 3. Registrar auditoría
    audit = AuditLog(
        actor=actor,
        action="DELETE_BATCH",
        entity="batch",
        before=batch_info,
        after={"deleted": True}
    )
    db.add(audit)

    # Commit transacción
    db.commit()
    db.refresh(audit)

    return {
        "batch_id": batch_id,
        "origen": batch.filename,
        "movimientos_eliminados": movimientos_count,
        "audit_id": audit.id
    }


def get_batch_info(db: Session, batch_id: int) -> Optional[dict]:
    """
    Obtiene información detallada de un batch específico.

    Args:
        db: Sesión de base de datos
        batch_id: ID del batch

    Returns:
        dict: Información del batch o None si no existe
    """
    batch = db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()

    if not batch:
        return None

    # Contar movimientos actuales
    movimientos_count = db.query(Movimiento).filter(
        Movimiento.batch_id == batch_id
    ).count()

    return {
        "id": batch.id,
        "filename": batch.filename,
        "file_hash": batch.file_hash,
        "imported_at": batch.imported_at.isoformat() if batch.imported_at else None,
        "rows_inserted": batch.rows_inserted,
        "total_movimientos": movimientos_count
    }
