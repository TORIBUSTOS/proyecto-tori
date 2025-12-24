"""
Modelo ORM para versionado de catálogo de categorías
"""

from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from backend.database.connection import Base


class CatalogVersion(Base):
    """
    Tabla de versiones de catálogo

    Registra las distintas versiones del catálogo de categorías
    para auditoría y control de cambios.
    """
    __tablename__ = "catalog_version"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    version = Column(String, unique=True, nullable=False, index=True)
    descripcion = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String, nullable=True)

    def __repr__(self):
        return f"<CatalogVersion(version={self.version}, created_at={self.created_at})>"
