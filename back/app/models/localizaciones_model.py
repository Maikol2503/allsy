from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.database import Base

class Localizacion(Base):
    __tablename__ = "localizaciones"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False) # Ej: "CASA", "Tienda Madrid"
    descripcion = Column(String(255), nullable=True) 
    parent_id = Column(Integer, ForeignKey("localizaciones.id", ondelete="CASCADE"), nullable=True)
    
    tipo = Column(String(50), nullable=False, default="almacen") # tienda, almacen, casa
    es_principal = Column(Boolean, default=False)
    activo = Column(Boolean, default=True)
    fecha_registro = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    parent = relationship("Localizacion", remote_side=[id], backref="hijos")
