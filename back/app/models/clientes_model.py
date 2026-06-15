from typing import Optional

from sqlalchemy import Column, Float, Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    activo = Column(Boolean, default=True)
    # --- IDENTIFICADORES OMNICANAL (Todos opcionales, pero claves para buscar) ---
    email = Column(String(150), unique=True, index=True, nullable=True)
    telefono = Column(String(20), unique=True, index=True, nullable=True)
    usuario_vinted = Column(String(100), unique=True, index=True, nullable=True)
    usuario_wallapop = Column(String(100), unique=True, index=True, nullable=True)
    exento_gastos_gestion = Column(Boolean, default=False)
    exento_comision = Column(Boolean, default=False)
    exento_tarifa_fija = Column(Boolean, default=False)    # Para perdonar los 1.50€
  
    # --- DATOS PERSONALES Y FACTURACIÓN ---
    nombre = Column(String(100), nullable=True)
    apellidos = Column(String(150), nullable=True)
    dni_nie = Column(String(20), unique=True, index=True, nullable=True) # Clave para facturas en España
    
    # --- LOGÍSTICA POR DEFECTO (Para autocompletar envíos futuros) ---
    direccion = Column(Text, nullable=True)
    ciudad = Column(String(100), nullable=True)
    codigo_postal = Column(String(20), nullable=True)
    provincia = Column(String(100), nullable=True)
    pais = Column(String(50), default="España")
    
    # --- CRM Y MÉTRICAS BÁSICAS ---
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    notas_internas = Column(Text, nullable=True) # Ej: "Cliente problemático", "Le gustan las prendas Y2K"
    es_vip = Column(Boolean, default=False) # Para aplicar descuentos automáticos en el futuro
    
    # --- RELACIONES ---
    # Un cliente puede tener muchas ventas
    ventas = relationship("Venta", back_populates="cliente")