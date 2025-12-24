"""
Router Admin: Versionado y upgrade de catálogo de categorías

Endpoints para administración de versiones de catálogo
y aplicación de upgrades masivos.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

from backend.database.connection import get_db
from backend.models import CatalogVersion, CatalogUpgradeMap, AuditLog
from backend.core.catalog_upgrade import simular_upgrade, aplicar_upgrade
from backend.core.categorias_catalogo import get_catalog


router = APIRouter(prefix="/api/admin/catalogo", tags=["Admin Catálogo"])


# ============================================
# SCHEMAS
# ============================================

class CreateVersionRequest(BaseModel):
    version: str
    descripcion: Optional[str] = None
    created_by: Optional[str] = None


class UpgradeMapRequest(BaseModel):
    from_version: str
    to_version: str
    from_cat: str
    from_sub: Optional[str] = None
    to_cat: str
    to_sub: Optional[str] = None
    action: str  # "RENAME"|"MOVE"|"DEACTIVATE"


class BulkUpgradeMapRequest(BaseModel):
    mapeos: list[UpgradeMapRequest]


class SimularUpgradeRequest(BaseModel):
    from_version: str
    to_version: str


class ScopeFilter(BaseModel):
    batch_id: Optional[int] = None
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None


class AplicarUpgradeRequest(BaseModel):
    from_version: str
    to_version: str
    confirm: bool = False
    actor: str = "admin"
    scope: Optional[ScopeFilter] = None


# ============================================
# ENDPOINTS
# ============================================

@router.post("/version")
def crear_version(
    req: CreateVersionRequest,
    db: Session = Depends(get_db)
):
    """
    Crea una nueva versión de catálogo (solo metadata).

    No modifica el JSON, solo registra la versión en DB
    para tracking y mapeos de upgrade.
    """
    # Validar que no existe
    existing = db.query(CatalogVersion).filter(
        CatalogVersion.version == req.version
    ).first()

    if existing:
        raise HTTPException(400, f"La versión {req.version} ya existe")

    # Crear versión
    version = CatalogVersion(
        version=req.version,
        descripcion=req.descripcion,
        created_by=req.created_by
    )
    db.add(version)

    # Auditoría
    audit = AuditLog(
        actor=req.created_by or "admin",
        action="create_catalog_version",
        entity="catalog_version",
        before=None,
        after={"version": req.version, "descripcion": req.descripcion}
    )
    db.add(audit)

    db.commit()
    db.refresh(version)

    return JSONResponse({
        "status": "success",
        "version_id": version.id,
        "version": version.version,
        "created_at": version.created_at.isoformat()
    })


@router.get("/version")
def listar_versiones(db: Session = Depends(get_db)):
    """
    Lista todas las versiones de catálogo registradas.
    """
    versiones = db.query(CatalogVersion).order_by(
        CatalogVersion.created_at.desc()
    ).all()

    return JSONResponse({
        "status": "success",
        "total": len(versiones),
        "versiones": [
            {
                "id": v.id,
                "version": v.version,
                "descripcion": v.descripcion,
                "created_at": v.created_at.isoformat(),
                "created_by": v.created_by
            }
            for v in versiones
        ]
    })


@router.post("/upgrade-map")
def cargar_mapeos(
    req: BulkUpgradeMapRequest,
    db: Session = Depends(get_db)
):
    """
    Carga mapeos de upgrade en bulk.

    Permite definir múltiples mapeos para migración
    de categorías entre versiones.
    """
    if not req.mapeos:
        raise HTTPException(400, "Debe proporcionar al menos un mapeo")

    # Validar acciones
    valid_actions = {"RENAME", "MOVE", "DEACTIVATE"}
    for m in req.mapeos:
        if m.action not in valid_actions:
            raise HTTPException(
                400,
                f"Acción inválida: {m.action}. Debe ser {valid_actions}"
            )

    # Insertar mapeos
    created_count = 0
    for m in req.mapeos:
        mapeo = CatalogUpgradeMap(
            from_version=m.from_version,
            to_version=m.to_version,
            from_cat=m.from_cat,
            from_sub=m.from_sub,
            to_cat=m.to_cat,
            to_sub=m.to_sub,
            action=m.action
        )
        db.add(mapeo)
        created_count += 1

    # Auditoría
    audit = AuditLog(
        actor="admin",
        action="bulk_load_upgrade_maps",
        entity="catalog_upgrade_map",
        before=None,
        after={"count": created_count}
    )
    db.add(audit)

    db.commit()

    return JSONResponse({
        "status": "success",
        "mapeos_creados": created_count
    })


@router.post("/upgrade/simular")
def simular_upgrade_endpoint(
    req: SimularUpgradeRequest,
    db: Session = Depends(get_db)
):
    """
    Simula el impacto de un upgrade SIN aplicar cambios.

    Retorna estadísticas de movimientos afectados y mapeos.
    """
    resultado = simular_upgrade(
        db=db,
        from_version=req.from_version,
        to_version=req.to_version
    )

    if "error" in resultado:
        raise HTTPException(400, resultado["error"])

    return JSONResponse({
        "status": "success",
        "from_version": req.from_version,
        "to_version": req.to_version,
        **resultado
    })


@router.post("/upgrade/aplicar")
def aplicar_upgrade_endpoint(
    req: AplicarUpgradeRequest,
    db: Session = Depends(get_db)
):
    """
    Aplica un upgrade de catálogo a los movimientos.

    REQUIERE confirm=true para ejecutar.
    Respeta categorizaciones manuales.
    """
    # Convertir scope a dict si existe
    scope_dict = None
    if req.scope:
        scope_dict = req.scope.model_dump()

    resultado = aplicar_upgrade(
        db=db,
        from_version=req.from_version,
        to_version=req.to_version,
        confirm=req.confirm,
        actor=req.actor,
        scope=scope_dict
    )

    if "error" in resultado:
        raise HTTPException(400, resultado["error"])

    return JSONResponse({
        "status": "success",
        "from_version": req.from_version,
        "to_version": req.to_version,
        **resultado
    })
