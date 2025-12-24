"""
Migración: Agregar tablas de versionado de catálogo
Crea las tablas catalog_version, catalog_upgrade_map, audit_log
"""

from backend.database.connection import engine, Base
from backend.models import CatalogVersion, CatalogUpgradeMap, AuditLog


def migrate():
    """
    Crea las nuevas tablas en la base de datos:
    - catalog_version: Versiones del catálogo
    - catalog_upgrade_map: Mapeos de upgrade
    - audit_log: Auditoría de operaciones
    """
    print("[INFO] Creando tablas de versionado de catálogo...")

    # Crear solo las tablas nuevas
    CatalogVersion.__table__.create(bind=engine, checkfirst=True)
    CatalogUpgradeMap.__table__.create(bind=engine, checkfirst=True)
    AuditLog.__table__.create(bind=engine, checkfirst=True)

    print("[OK] Tablas creadas exitosamente:")
    print("  - catalog_version")
    print("  - catalog_upgrade_map")
    print("  - audit_log")


if __name__ == "__main__":
    migrate()
