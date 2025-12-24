from sqlalchemy import Column, Integer, String, DateTime, func, UniqueConstraint
from backend.database.connection import Base

class ImportBatch(Base):
    __tablename__ = "import_batches"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_hash = Column(String, nullable=False, index=True)
    imported_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    rows_inserted = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("file_hash", name="uq_import_batches_file_hash"),
    )
