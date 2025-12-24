"""
Modelo para Reglas de Categorización Aprendibles (ETAPA 4).

Permite guardar patrones aprendidos de ediciones manuales de usuarios
para aplicarlos automáticamente en futuras categorizaciones.
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from backend.database.connection import Base


class ReglaCategorizacion(Base):
    """
    Regla aprendida para categorización automática.

    Cuando el usuario edita un movimiento y marca "Recordar regla",
    se guarda el patrón normalizado para aplicarlo automáticamente
    en futuras categorizaciones.
    """
    __tablename__ = "reglas_categorizacion"

    id = Column(Integer, primary_key=True, index=True)
    patron = Column(String, unique=True, nullable=False, index=True)  # patrón normalizado
    categoria = Column(String, nullable=False)
    subcategoria = Column(String, nullable=False)
    confianza = Column(Integer, default=50)  # 0-100
    veces_usada = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<ReglaCategorizacion(patron='{self.patron}', categoria='{self.categoria}', veces_usada={self.veces_usada})>"
