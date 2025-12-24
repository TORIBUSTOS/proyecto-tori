"""
Modelo de Categoria para sistema de configuración

Este modelo representa las categorías principales de movimientos financieros.
Migrado desde hardcode a base de datos para permitir configuración dinámica.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database.session import Base


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    key = Column(String, unique=True, nullable=False, index=True)  # ej: "GASTOS_OPERATIVOS"
    label = Column(String, nullable=False)  # ej: "Gastos operativos"
    tipo = Column(String, nullable=False)  # "INGRESO" | "EGRESO" | "NEUTRO"
    icon = Column(String, nullable=True)  # opcional: "💳"
    color = Column(String, nullable=True)  # opcional: "#22c55e"
    activa = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relación con subcategorías
    subcategorias = relationship("Subcategoria", back_populates="categoria", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Categoria(key={self.key}, label={self.label}, tipo={self.tipo}, activa={self.activa})>"

    def to_dict(self, include_subcategorias=False):
        """Serializar a dict para JSON"""
        result = {
            "id": self.id,
            "key": self.key,
            "label": self.label,
            "tipo": self.tipo,
            "icon": self.icon,
            "color": self.color,
            "activa": self.activa,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

        if include_subcategorias:
            result["subcategorias"] = [sub.to_dict() for sub in self.subcategorias if sub.activa]

        return result
