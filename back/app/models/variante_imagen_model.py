from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

# app/models/variante_imagen_model.py
class Imagen(Base):
    __tablename__ = "imagenes_variante"
    id = Column(Integer, primary_key=True)
    url = Column(String(500), nullable=False)
    orden = Column(Integer, default=0)
    variante_id = Column(Integer, ForeignKey("variantes.id", ondelete="CASCADE"))
    variante = relationship("Variante", back_populates="imagenes")
    