from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from datetime import datetime
from sqlalchemy.orm import relationship
from app.db.database import Base

class Egreso(Base):
    __tablename__ = "egresos"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, default=datetime.utcnow)
    concepto = Column(String(200), nullable=False) # Ej: "Lote de 50 camisetas", "Bolsas de envío"
    categoria = Column(String(50), nullable=False) # Ej: compra_mercancia, envios, publicidad, otros
    monto = Column(Float, nullable=False)
    metodo_pago = Column(String(50)) # Ej: tarjeta_empresa, efectivo_caja, cuenta_bancaria
    notas = Column(Text, nullable=True)

    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=True)
    proveedor = relationship("Proveedor")
    
    # ✨ RELACIÓN DIRECTA CON VENTAS PARA REEMBOLSOS/COMPENSACIONES
    venta_id = Column(Integer, ForeignKey("ventas.id", ondelete="SET NULL"), nullable=True)
    venta = relationship("Venta")
