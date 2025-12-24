"""
Router Admin: Gestión de Batches

Endpoints administrativos para listar y eliminar batches.
ADVERTENCIA: La eliminación es DEFINITIVA y borra todos los movimientos.
"""

from fastapi import APIRouter, HTTPException, Depends, Path
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database.connection import get_db
from backend.core.batch_admin import list_batches, delete_batch, get_batch_info


router = APIRouter(prefix="/api/admin/batch", tags=["Admin Batch"])


# ============================================
# SCHEMAS
# ============================================

class DeleteBatchRequest(BaseModel):
    confirm: bool = False
    actor: str = "admin"


# ============================================
# ENDPOINTS
# ============================================

@router.get("")
def listar_batches(db: Session = Depends(get_db)):
    """
    Lista todos los batches importados con sus estadísticas.

    Retorna:
    - id: ID del batch
    - origen: Nombre del archivo importado
    - created_at: Fecha de importación
    - rows_inserted: Total de filas insertadas (según registro)
    - total_movimientos: Total de movimientos actuales (count real)
    """
    batches = list_batches(db)

    return JSONResponse({
        "status": "success",
        "total": len(batches),
        "batches": batches
    })


@router.get("/{batch_id}")
def obtener_batch(
    batch_id: int = Path(..., description="ID del batch"),
    db: Session = Depends(get_db)
):
    """
    Obtiene información detallada de un batch específico.
    """
    batch = get_batch_info(db, batch_id)

    if not batch:
        raise HTTPException(404, f"Batch {batch_id} no existe")

    return JSONResponse({
        "status": "success",
        "batch": batch
    })


@router.delete("/{batch_id}")
def eliminar_batch(
    batch_id: int = Path(..., description="ID del batch a eliminar"),
    req: DeleteBatchRequest = DeleteBatchRequest(),
    db: Session = Depends(get_db)
):
    """
    Elimina un batch y TODOS sus movimientos asociados.

    ⚠️ ADVERTENCIA: Esta operación es DEFINITIVA y NO reversible.

    Requiere:
    - confirm: true (obligatorio)
    - actor: usuario que ejecuta (opcional, default: "admin")

    Proceso:
    1. Valida existencia del batch
    2. Cuenta movimientos asociados
    3. Elimina movimientos del batch
    4. Elimina registro de batch
    5. Registra auditoría

    Returns:
    - batch_id: ID del batch eliminado
    - origen: Nombre del archivo
    - movimientos_eliminados: Cantidad de movimientos borrados
    - audit_id: ID del registro de auditoría
    """
    # VALIDACIÓN: confirm debe ser true
    if not req.confirm:
        raise HTTPException(
            400,
            "Se requiere confirm=true para eliminar un batch. "
            "Esta operación es DEFINITIVA y borrará todos los movimientos asociados."
        )

    try:
        resultado = delete_batch(db, batch_id, req.actor)

        return JSONResponse({
            "status": "success",
            "message": f"Batch {batch_id} eliminado exitosamente",
            **resultado
        })

    except ValueError as e:
        # Batch no existe
        raise HTTPException(404, str(e))

    except Exception as e:
        # Error inesperado
        db.rollback()
        raise HTTPException(500, f"Error al eliminar batch: {str(e)}")
