from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.database import Base

class Auditoria(Base):
    __tablename__ = "auditoria"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # ¿Quién lo hizo?
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    nombre_usuario = Column(String(100), nullable=True) # Respaldo por si el usuario es borrado
    
    # ¿Dónde ocurrió? (Relacionado con tus 10+ tiendas)
    localizacion_id = Column(Integer, ForeignKey("localizaciones.id", ondelete="SET NULL"), nullable=True)
    
    # ¿Qué acción se realizó? (CREAR, EDITAR, ELIMINAR, VENDER, TRASPASAR, PAGAR)
    accion = Column(String(50), nullable=False)
    
    # ¿Sobre qué entidad? (PRODUCTO, LOTE, UNIDAD, VENTA, GASTO, PAGO)
    entidad_tipo = Column(String(50), nullable=False)
    entidad_id = Column(Integer, nullable=True) # El ID de la prenda, venta o gasto
    
    # Detalles del cambio (Para el historial de "Antes" y "Después")
    valor_anterior = Column(JSON, nullable=True)
    valor_nuevo = Column(JSON, nullable=True)
    
    notas = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)

    usuario = relationship("Usuario")
    localizacion = relationship("Localizacion")
