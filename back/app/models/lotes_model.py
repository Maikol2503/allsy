from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, Date
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.database import Base

class StockConfig(Base):
    __tablename__ = "stock_configs"

    id = Column(Integer, primary_key=True)
    variante_id = Column(Integer, ForeignKey("variantes.id", ondelete="CASCADE"))
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=True)
    propietario_id = Column(Integer, ForeignKey("clientes.id", ondelete="SET NULL"), nullable=True)

    activo = Column(Boolean, default=True)
    etiqueta = Column(String(100))
    orden = Column(Integer, default=0)

    precio_compra = Column(Float, nullable=False, default=0.0)
    precio_venta = Column(Float, nullable=False, default=0.0)
    descuento = Column(Float, default=0.0)
    donar_ganancias = Column(Boolean, default=False)

    variante = relationship("Variante", back_populates="stock_configs")
    proveedor = relationship("Proveedor")
    propietario = relationship("Cliente")
    valores = relationship("ValorAtributo", back_populates="stock_config", cascade="all, delete-orphan")
    stock_units = relationship("StockUnit", back_populates="stock_config", cascade="all, delete-orphan")

    # ✨ MULTI-TIENDA: Relación con la nueva tabla Localizacion
    localizacion_id = Column(Integer, ForeignKey("localizaciones.id", ondelete="SET NULL"), nullable=True)
    localizacion = relationship("Localizacion")

class StockUnit(Base):
    __tablename__ = "stock_units"

    id = Column(Integer, primary_key=True)
    stock_config_id = Column(Integer, ForeignKey("stock_configs.id", ondelete="CASCADE"))

    sku = Column(String(100), unique=True, index=True)
    estado_gestion = Column(String(50), default="en_stock")
    activo = Column(Boolean, default=True)

    publicar_web = Column(Boolean, default=False)
    publicar_vinted = Column(Boolean, default=False)
    publicar_wallapop = Column(Boolean, default=False)

    fecha_compra = Column(Date, nullable=True)
    fecha_registro = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    fecha_actualizacion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # ✨ TRAZABILIDAD DE PAGOS: Enlace al registro de pago de consignación
    pago_consignacion_id = Column(Integer, ForeignKey("pagos_consignacion.id", ondelete="SET NULL"), nullable=True)

    stock_config = relationship("StockConfig", back_populates="stock_units")
    pago_consignacion = relationship("PagoConsignacion")
    detalles_venta = relationship("DetalleVenta", back_populates="stock_unit")