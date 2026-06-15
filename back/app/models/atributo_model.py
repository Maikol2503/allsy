from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.database import Base

# 1. EL CATÁLOGO (Ej: "Talla", "Material", "Contenido ML")
class Atributo(Base):
    __tablename__ = "atributos"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), nullable=False, unique=True)
    
    # Relación con todos los valores que existen de este tipo
    valores = relationship("ValorAtributo", back_populates="atributo", cascade="all, delete-orphan")

# 2. EL VALOR ESPECÍFICO (Ej: StockConfig #5 -> Atributo "Talla" -> Valor "XL")
class ValorAtributo(Base):
    __tablename__ = "valores_atributo"
    
    id = Column(Integer, primary_key=True)
    
    # ✨ ACTUALIZADO: Apunta a stock_configs.id
    stock_config_id = Column(Integer, ForeignKey("stock_configs.id", ondelete="CASCADE"), nullable=False)
    
    # Conexión al tipo de atributo
    atributo_id = Column(Integer, ForeignKey("atributos.id", ondelete="CASCADE"), nullable=False)
    
    # El valor real (Ej: "XL", "Algodón", "100")
    valor = Column(String(100), nullable=False)

    # ✨ ACTUALIZADO: Relaciones apuntando a StockConfig
    stock_config = relationship("StockConfig", back_populates="valores")
    atributo = relationship("Atributo", back_populates="valores")

    # ✨ ACTUALIZADO: Regla de unicidad
    __table_args__ = (
       UniqueConstraint('stock_config_id', 'atributo_id', name='_stock_config_atributo_uc'),
    )