from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    genero = Column(String(255), nullable=True)
    descripcion = Column(String(255), nullable=True)
    parent_id = Column(Integer, ForeignKey("categorias.id"), nullable=True)
    activo = Column(Boolean, default=True)
    # Relaciones
    subcategorias = relationship(
        "Categoria",
        backref="padre",
        remote_side=[id]
    )
    productos = relationship("Producto", back_populates="categoria", lazy="dynamic")
    


