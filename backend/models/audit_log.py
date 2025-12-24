"""
Modelo ORM para auditoría de operaciones
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
from backend.database.connection import Base


class AuditLog(Base):
    """
    Tabla de auditoría de operaciones

    Registra todas las operaciones importantes del sistema
    con información de before/after para trazabilidad.
    """
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    actor = Column(String, nullable=False, index=True)  # Usuario/sistema que ejecuta
    action = Column(String, nullable=False, index=True)  # Acción realizada
    entity = Column(String, nullable=False, index=True)  # Entidad afectada
    before = Column(JSON, nullable=True)  # Estado antes (JSON)
    after = Column(JSON, nullable=True)  # Estado después (JSON)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<AuditLog(actor={self.actor}, action={self.action}, entity={self.entity})>"
