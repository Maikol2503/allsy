from sqlalchemy import Column, ForeignKey, Integer, Float, String, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class Cupon(Base):
    __tablename__ = "cupones"

    id = Column(Integer, primary_key=True)
    codigo = Column(String(50), unique=True, nullable=False) # Ej: BIENVENIDA10
    tipo = Column(String(20)) # "porcentaje" o "fijo"
    valor = Column(Float, nullable=False) # 15.0 o 10.0
    
    fecha_expiracion = Column(DateTime, nullable=True)
    uso_maximo = Column(Integer, default=100) # Cuántas veces se puede usar en total
    usos_actuales = Column(Integer, default=0)
    
    monto_minimo_compra = Column(Float, default=0.0) # Ej: Solo si gastas más de 50€
    activo = Column(Boolean, default=True)

    fecha_creacion = Column(DateTime, default=datetime.utcnow)