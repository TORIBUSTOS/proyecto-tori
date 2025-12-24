"""
Modelo ORM para Movimientos bancarios
"""

from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from backend.database.connection import Base


class Movimiento(Base):
    """
    Tabla de movimientos bancarios consolidados

    Categorización en 2 niveles:
    - categoria: Categoría principal (INGRESOS, EGRESOS, OTROS)
    - subcategoria: Subcategoría específica (Transferencias, Prestadores_Farmacias, etc.)
    - confianza_porcentaje: Nivel de confianza de la categorización (0-100)

    Metadata extraída automáticamente:
    - persona_nombre: Nombre de persona/empresa en transferencias
    - documento: DNI/CUIL/CUIT (8-11 dígitos)
    - es_debin: True si el movimiento es un DEBIN
    - debin_id: ID único del DEBIN (si aplica)
    """
    __tablename__ = "movimientos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fecha = Column(Date, nullable=False, index=True)
    descripcion = Column(String, nullable=False)
    monto = Column(Float, nullable=False)
    saldo = Column(Float, nullable=True)  # Saldo bancario real después del movimiento

    # Categorización
    categoria = Column(String, nullable=True, index=True)
    subcategoria = Column(String, nullable=True, index=True)
    confianza_porcentaje = Column(Integer, nullable=True, default=0)
    confianza_fuente = Column(String, nullable=True)  # "manual", "regla_aprendida", "cascada", "sin_fuente"

    # Metadata extraída (ETAPA 2)
    persona_nombre = Column(String, nullable=True)
    documento = Column(String, nullable=True, index=True)
    es_debin = Column(Boolean, nullable=True, default=False, index=True)
    debin_id = Column(String, nullable=True)
    cbu = Column(String, nullable=True)
    comercio = Column(String, nullable=True)
    terminal = Column(String, nullable=True)
    referencia = Column(String, nullable=True)

    # Relaciones
    batch_id = Column(Integer, ForeignKey("import_batches.id"), nullable=True, index=True)
    batch = relationship("ImportBatch")

    def __repr__(self):
        return f"<Movimiento(id={self.id}, fecha={self.fecha}, monto={self.monto}, categoria={self.categoria}, subcategoria={self.subcategoria})>"
