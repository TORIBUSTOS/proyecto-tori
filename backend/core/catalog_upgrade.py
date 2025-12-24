"""
Lógica de simulación y aplicación de upgrades de catálogo

Este módulo maneja la migración de categorías entre versiones
siguiendo los mapeos definidos en catalog_upgrade_map.
"""

from typing import Optional
from sqlalchemy.orm import Session
from backend.models import CatalogUpgradeMap, Movimiento, AuditLog
from datetime import datetime


def simular_upgrade(
    db: Session,
    from_version: str,
    to_version: str
) -> dict:
    """
    Simula el impacto de un upgrade de catálogo SIN aplicar cambios.

    Args:
        db: Sesión de base de datos
        from_version: Versión origen
        to_version: Versión destino

    Returns:
        dict: Resumen del impacto con total_afectados y top_mapeos
    """
    # Obtener mapeos para este upgrade
    mapeos = db.query(CatalogUpgradeMap).filter(
        CatalogUpgradeMap.from_version == from_version,
        CatalogUpgradeMap.to_version == to_version
    ).all()

    if not mapeos:
        return {
            "total_afectados": 0,
            "top_mapeos": [],
            "error": f"No hay mapeos definidos para {from_version} -> {to_version}"
        }

    # Contar movimientos afectados por cada mapeo
    resultados = []
    total_afectados = 0

    for mapeo in mapeos:
        # Construir query para contar movimientos
        query = db.query(Movimiento).filter(
            Movimiento.categoria == mapeo.from_cat
        )

        # Filtrar por subcategoría si existe
        if mapeo.from_sub:
            query = query.filter(Movimiento.subcategoria == mapeo.from_sub)

        count = query.count()
        total_afectados += count

        if count > 0:
            resultados.append({
                "from_cat": mapeo.from_cat,
                "from_sub": mapeo.from_sub,
                "to_cat": mapeo.to_cat,
                "to_sub": mapeo.to_sub,
                "action": mapeo.action,
                "affected_count": count
            })

    # Ordenar por cantidad afectada (mayor a menor)
    resultados.sort(key=lambda x: x["affected_count"], reverse=True)

    return {
        "total_afectados": total_afectados,
        "top_mapeos": resultados
    }


def aplicar_upgrade(
    db: Session,
    from_version: str,
    to_version: str,
    confirm: bool,
    actor: str = "system",
    scope: Optional[dict] = None
) -> dict:
    """
    Aplica un upgrade de catálogo a los movimientos.

    REGLAS:
    - NO pisar categorizaciones manuales (confianza_fuente == "manual")
    - Set confianza=90, confianza_fuente="upgrade_catalogo"
    - Registrar auditoría

    Args:
        db: Sesión de base de datos
        from_version: Versión origen
        to_version: Versión destino
        confirm: Debe ser True para ejecutar
        actor: Usuario/sistema que ejecuta
        scope: Filtros opcionales {batch_id, fecha_desde, fecha_hasta}

    Returns:
        dict: Resumen de la operación
    """
    if not confirm:
        return {
            "error": "confirm=true requerido para aplicar upgrade"
        }

    # Obtener mapeos
    mapeos = db.query(CatalogUpgradeMap).filter(
        CatalogUpgradeMap.from_version == from_version,
        CatalogUpgradeMap.to_version == to_version
    ).all()

    if not mapeos:
        return {
            "error": f"No hay mapeos definidos para {from_version} -> {to_version}"
        }

    # Estadísticas
    total_procesados = 0
    total_actualizados = 0
    total_preservados = 0  # Manuales preservados

    # Aplicar cada mapeo
    for mapeo in mapeos:
        # Query base: filtrar por categoría origen
        query = db.query(Movimiento).filter(
            Movimiento.categoria == mapeo.from_cat
        )

        # Filtrar por subcategoría si existe
        if mapeo.from_sub:
            query = query.filter(Movimiento.subcategoria == mapeo.from_sub)

        # Aplicar scope si se especifica
        if scope:
            if "batch_id" in scope and scope["batch_id"] is not None:
                query = query.filter(Movimiento.batch_id == scope["batch_id"])
            if "fecha_desde" in scope and scope["fecha_desde"] is not None:
                query = query.filter(Movimiento.fecha >= scope["fecha_desde"])
            if "fecha_hasta" in scope and scope["fecha_hasta"] is not None:
                query = query.filter(Movimiento.fecha <= scope["fecha_hasta"])

        # Obtener movimientos
        movimientos = query.all()
        total_procesados += len(movimientos)

        # Actualizar cada movimiento
        for mov in movimientos:
            # NO pisar manuales
            if mov.confianza_fuente == "manual":
                total_preservados += 1
                continue

            # Aplicar cambio según acción
            mov.categoria = mapeo.to_cat
            mov.subcategoria = mapeo.to_sub
            mov.confianza_porcentaje = 90
            mov.confianza_fuente = "upgrade_catalogo"

            total_actualizados += 1

    # Registrar auditoría agregada
    audit = AuditLog(
        actor=actor,
        action="catalog_upgrade",
        entity="movimientos",
        before={
            "from_version": from_version,
            "scope": scope or {}
        },
        after={
            "to_version": to_version,
            "procesados": total_procesados,
            "actualizados": total_actualizados,
            "preservados": total_preservados
        }
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "total_procesados": total_procesados,
        "total_actualizados": total_actualizados,
        "total_preservados": total_preservados,
        "audit_id": audit.id
    }
