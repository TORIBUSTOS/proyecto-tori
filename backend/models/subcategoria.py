"""
Modelo de Subcategoria para sistema de configuración

Este modelo representa las subcategorías asociadas a categorías principales.
Migrado desde hardcode a base de datos para permitir configuración dinámica.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database.session import Base


class Subcategoria(Base):
    __tablename__ = "subcategorias"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    categoria_key = Column(String, ForeignKey("categorias.key", ondelete="CASCADE"), nullable=False, index=True)
    key = Column(String, unique=True, nullable=False, index=True)  # ej: "IMPUESTOS_DEBITOS_CREDITOS"
    label = Column(String, nullable=False)  # ej: "Débitos y créditos"
    activa = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relación con categoría padre
    categoria = relationship("Categoria", back_populates="subcategorias")

    def __repr__(self):
        return f"<Subcategoria(key={self.key}, label={self.label}, categoria_key={self.categoria_key}, activa={self.activa})>"

    def to_dict(self):
        """Serializar a dict para JSON"""
        return {
            "id": self.id,
            "categoria_key": self.categoria_key,
            "key": self.key,
            "label": self.label,
            "activa": self.activa,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
