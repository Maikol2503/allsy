from sqlalchemy import Column, ForeignKey, Integer, Float, String, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class Venta(Base):
    __tablename__ = "ventas"

    id = Column(Integer, primary_key=True)
    codigo_venta = Column(String(50), unique=True, nullable=False) 
    fecha = Column(DateTime, default=datetime.utcnow)
    fecha_pago = Column(DateTime, nullable=True)                  
    fecha_envio = Column(DateTime, nullable=True)
    fecha_entrega = Column(DateTime, nullable=True) 
    fecha_finalizado = Column(DateTime, nullable=True)
    fecha_cancelado = Column(DateTime, nullable=True)
    fecha_devuelto = Column(DateTime, nullable=True)
    pais = Column(String(50), nullable=True)
    monto_reembolsado = Column(Float, default=0.0)
    
    # --- FINANZAS DETALLADAS ---
    subtotal = Column(Float, nullable=False)
    iva_monto = Column(Float, default=0.0)
    descuento_total = Column(Float, default=0.0)
    costo_envio = Column(Float, default=0.0)
    total = Column(Float, nullable=False)
    moneda = Column(String(10), default="EUR")

    # --- PAGOS Y SEGURIDAD ---
    metodo_pago = Column(String(50), nullable=False) 
    estado_pago = Column(String(50), default="pagado") 
    transaccion_id_externo = Column(String(100), nullable=True)

    # --- FLUJO DE TRABAJO ---
    estado_venta = Column(String(50), default="abierta") # abierta, completada, cancelada, devuelta_parcialmente, devuelta_totalmente
    canal = Column(String(50), nullable=False) 
    vendedor = Column(String(50), nullable=False) 

    # --- CLIENTE ---
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    nombre_cliente = Column(String(100), nullable=True)
    email_cliente = Column(String(100), nullable=True)
    notas_internas = Column(Text, nullable=True)

    # --- LOGÍSTICA ---
    estado_envio = Column(String(50), default="pendiente_envio") 
    direccion_envio = Column(Text, nullable=True)
    empresa_transporte = Column(String(50), nullable=True) 
    numero_seguimiento = Column(String(100), nullable=True)
    etiqueta_url = Column(Text, nullable=True)
    etiqueta_imprimida = Column(Boolean, default=False)

    detalles = relationship("DetalleVenta", back_populates="venta", cascade="all, delete-orphan")
    cliente = relationship("Cliente", back_populates="ventas")


class DetalleVenta(Base):
    __tablename__ = "detalles_venta"
    
    id = Column(Integer, primary_key=True)
    venta_id = Column(Integer, ForeignKey("ventas.id", ondelete="CASCADE"))
    
    # ✨ ACTUALIZADO: Ahora apunta a la unidad física individual (StockUnit), no a la configuración
    stock_unit_id = Column(Integer, ForeignKey("stock_units.id"), nullable=True) 
    
    cantidad = Column(Integer, nullable=False, default=1)
    precio_unitario_en_venta = Column(Float, nullable=False) 
    
    # 🛡️ SEGURO DE DATOS FINANCIEROS (Snapshots)
    precio_compra_snapshot = Column(Float, nullable=True) # ✨ RECOMENDADO: Guardar el costo al momento de vender
    nombre_producto_snapshot = Column(String(200)) 
    talla_snapshot = Column(String(50))
    color_snapshot = Column(String(50))
    devuelto = Column(Boolean, default=False) # ✨ NUEVO: Para devoluciones parciales

    venta = relationship("Venta", back_populates="detalles")
    # ✨ ACTUALIZADO: Relación con StockUnit
    stock_unit = relationship("StockUnit", back_populates="detalles_venta")