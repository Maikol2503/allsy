from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class PagoConsignacion(Base):
    __tablename__ = "pagos_consignacion"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"))
    monto = Column(Float, nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow)
    metodo_pago = Column(String(50)) # Transferencia, Bizum, Efectivo
    referencia = Column(String(100), nullable=True) 
    notas = Column(Text, nullable=True) 
    
    # ✨ NUEVOS CAMPOS DE SEGURIDAD FINANCIERA
    estado = Column(String(50), default="completado") # completado, anulado
    motivo_anulacion = Column(Text, nullable=True)
    fecha_anulacion = Column(DateTime, nullable=True)
    items_anulados_json = Column(Text, nullable=True) # ✨ Auditoría: Prendas que fueron quitadas de este pago por error
    
    cliente = relationship("Cliente")
    # ✨ TRAZABILIDAD: Prendas que fueron pagadas con esta transacción
    items_pagados = relationship("StockUnit", back_populates="pago_consignacion")


