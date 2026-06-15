from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Variante(Base):
    __tablename__ = "variantes"
    
    id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"))
    sku = Column(String(100), unique=True)
    activo = Column(Boolean, default=True)
    identidad_variante = Column(String(100))
    hex_identidad = Column(String(50))
    descripcion = Column(String(500))
    orden = Column(Integer, default=0)
    
    # ✨ ACTUALIZADO: La relación ahora es con stock_configs
    stock_configs = relationship("StockConfig", back_populates="variante", cascade="all, delete-orphan")
    imagenes = relationship("Imagen", back_populates="variante", cascade="all, delete-orphan")
    producto = relationship("Producto", back_populates="variantes")