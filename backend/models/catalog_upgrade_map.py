"""
Modelo ORM para mapeos de upgrade de catálogo
"""

from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from backend.database.connection import Base


class CatalogUpgradeMap(Base):
    """
    Tabla de mapeos para upgrade de catálogo

    Define cómo migrar categorías/subcategorías de una versión a otra.
    Acciones soportadas:
    - RENAME: Solo cambia el nombre de la categoría/subcategoría
    - MOVE: Mueve subcategoría a otra categoría
    - DEACTIVATE: Marca como inactiva (no asignar más)
    """
    __tablename__ = "catalog_upgrade_map"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    from_version = Column(String, nullable=False, index=True)
    to_version = Column(String, nullable=False, index=True)
    from_cat = Column(String, nullable=False, index=True)
    from_sub = Column(String, nullable=True, index=True)
    to_cat = Column(String, nullable=False)
    to_sub = Column(String, nullable=True)
    action = Column(String, nullable=False)  # "RENAME"|"MOVE"|"DEACTIVATE"
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<CatalogUpgradeMap({self.from_version}->{self.to_version}: {self.from_cat}/{self.from_sub} -> {self.to_cat}/{self.to_sub})>"
