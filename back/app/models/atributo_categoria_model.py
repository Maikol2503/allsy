from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON
from app.db.database import Base

class AtributoCategoria(Base):
    __tablename__ = "atributo_categoria"
    
    id = Column(Integer, primary_key=True, index=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id", ondelete="CASCADE"), nullable=False)
    
    # El nombre del campo que verá el usuario (ej: "talla", "material", "peso_kg")
    nombre = Column(String(100), nullable=False)
    
    # Tipo de input para Angular (ej: "select", "number", "text", "color-dropdown")
    tipo = Column(String(50), nullable=False)
    
    # Array en formato JSON con las opciones si es un select (ej: ["S", "M", "L"])
    opciones = Column(JSON, nullable=True)