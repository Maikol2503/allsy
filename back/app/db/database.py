from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base  # Base para tus modelos
from app.core.config import settings  # Asegúrate de tener DATABASE_URL en settings

# Crear el engine de conexión a la base de datos
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,      # Verifica que la conexión esté viva antes de usarla
    pool_recycle=3600,       # Recicla la conexión después de 1 hora
    pool_size=10,            # Opcional: tamaño del pool de conexiones
    max_overflow=20          # Opcional: conexiones adicionales permitidas fuera del pool
)

# Crear el generador de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarar la base para los modelos
Base = declarative_base()

# Dependency para usar en FastAPI
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


