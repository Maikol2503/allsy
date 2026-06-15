from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.db.database import Base

class Proveedor(Base):
    __tablename__ = "proveedores"

    id = Column(Integer, primary_key=True, index=True)
    nombre_proveedor = Column(String(250), nullable=False)
    
    # ✨ Banderas independientes
    es_inventario = Column(Boolean, default=False) # Para ropa, neveras, perfumes, etc.
    es_gasto = Column(Boolean, default=False)      # Para luz, alquiler, bolsas, etc.

    stock_configs = relationship("StockConfig", back_populates="proveedor")