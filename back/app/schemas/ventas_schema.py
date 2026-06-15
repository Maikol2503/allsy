from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DetalleVentaCreate(BaseModel):
    stock_id: int
    cantidad: int
    precio_unitario: float # El precio que se cobró realmente

class VentaCreate(BaseModel):
    fecha: Optional[datetime] = None
    canal: str 
    vendedor: str 
    metodo_pago: str 
    pais: Optional[str] = "España"
    # ✨ NUEVOS CAMPOS
    estado_pago: str = "pagado"
    estado_envio: str = "pendiente_envio"

    fecha_pago: Optional[datetime] = None  # ✨ NUEVO
    fecha_envio: Optional[datetime] = None # ✨ NUEVO
    fecha_entrega: Optional[datetime] = None
    fecha_finalizado: Optional[datetime] = None
    fecha_cancelado: Optional[datetime] = None
    fecha_devuelto: Optional[datetime] = None
    
    # Datos opcionales del cliente
    nombre_cliente: Optional[str] = None
    email_cliente: Optional[str] = None
    identificador_cliente: Optional[str] = None
    tipo_identificador: Optional[str] = "telefono" 
    prefijo_telefono: Optional[str] = "+34"
    tipo_documento: Optional[str] = "DNI"
    
    # Costos extra
    costo_envio: float = 0.0
    descuento_total: float = 0.0
    
    # Logística
    transaccion_id_externo: Optional[str] = None
    empresa_transporte: Optional[str] = None
    numero_seguimiento: Optional[str] = None
    etiqueta_url: Optional[str] = None
    etiqueta_imprimida: Optional[bool] = False
    
    detalles: List[DetalleVentaCreate]





class VentaUpdate(BaseModel):
    estado_pago: Optional[str] = None
    metodo_pago: Optional[str] = None
    nombre_cliente: Optional[str] = None
    email_cliente: Optional[str] = None
    estado_envio: Optional[str] = None
    empresa_transporte: Optional[str] = None
    numero_seguimiento: Optional[str] = None
    notas_internas: Optional[str] = None
    fecha_pago: Optional[datetime] = None  # ✨ NUEVO
    fecha_envio: Optional[datetime] = None # ✨ NUEVO
    fecha_entrega: Optional[datetime] = None
    fecha_finalizado: Optional[datetime] = None
    fecha_cancelado: Optional[datetime] = None
    fecha_devuelto: Optional[datetime] = None
    monto_reembolsado: Optional[float] = None
    total: Optional[float] = None
    subtotal: Optional[float] = None
    costo_envio: Optional[float] = None
    descuento_total: Optional[float] = None
    etiqueta_url: Optional[str] = None
    etiqueta_imprimida: Optional[bool] = None
    scanned_unit_id: Optional[int] = None # ✨ NUEVO: Para intercambio inteligente