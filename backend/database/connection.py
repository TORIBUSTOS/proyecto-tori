"""
Conexion a la base de datos SQLite usando SQLAlchemy
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config.settings import settings

# Crear engine de SQLAlchemy
# connect_args solo para SQLite (permite multiples threads)
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Crear SessionLocal para manejar sesiones de DB
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos ORM
Base = declarative_base()


def get_db():
    """
    Dependencia para FastAPI
    Crea una sesion de DB, la usa y luego la cierra

    Uso en endpoints:
        @router.get("/ejemplo")
        def ejemplo(db: Session = Depends(get_db)):
            # usar db aqui
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
