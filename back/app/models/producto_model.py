from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.database import Base

class Producto(Base):
    __tablename__ = "productos"
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(String(500))
    tipo = Column(String(50))
    estado = Column(String(50), default="nuevo")
    activo = Column(Boolean, default=True)
    publico_objetivo = Column(String(50)) 
    es_vintage = Column(Boolean, default=False)
    epoca = Column(String(50), nullable=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    marca_id = Column(Integer, ForeignKey("marcas.id"))
    sku = Column(String(100), unique=True)
    fecha_registro = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    fecha_actualizacion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    variantes = relationship("Variante", back_populates="producto", cascade="all, delete-orphan")
    categoria = relationship("Categoria")
    marca = relationship("Marca")