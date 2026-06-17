from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class PagoCreate(BaseModel):
    monto: float
    metodo_pago: str
    referencia: Optional[str] = None
    notas: Optional[str] = None
    # ✨ TRAZABILIDAD: Lista de IDs de prendas físicas que se están pagando
    stock_unit_ids: Optional[List[int]] = []

class ItemPagadoRead(BaseModel):
    id: int
    sku: str
    nombre_producto: Optional[str] = None
    precio_venta: Optional[float] = 0.0
    pago_cliente: Optional[float] = 0.0
    comision_allsys: Optional[float] = 0.0
    class Config:
        from_attributes = True

class PagoRead(PagoCreate):
    id: int
    fecha: datetime
    estado: str = "completado"
    motivo_anulacion: Optional[str] = None
    # ✨ TRAZABILIDAD: Desglose de qué se pagó exactamente
    items_pagados: List[ItemPagadoRead] = []
    items_anulados: Optional[List[dict]] = [] # ✨ Prendas que fueron quitadas por error
    class Config:
        from_attributes = True

class EstadisticasConsignacion(BaseModel):
    total_prendas_entregadas: int
    prendas_en_stock: int
    
    # ✨ Desglose logístico exacto
    prendas_procesando: int
    prendas_enviada: int
    prendas_entregado: int
    prendas_completada: int
    prendas_cancelada: int
    prendas_devueltas_tienda: int  # ✨ CAMBIADO
    prendas_devueltas_dueno: int
    prendas_donado_a_ong: int
    prendas_extraviadas: int
    
    ingresos_en_transito: float
    exento_gastos_gestion: bool
    deuda_por_devoluciones: float
    dinero_generado_ventas: float  
    dinero_para_cliente: float     
    beneficio_plataforma: float    
    beneficio_en_transito: float   
    dinero_ya_pagado: float        
    saldo_pendiente: float         
    saldo_en_transito: float

class DesgloseFinanciero(BaseModel):
    precio_venta: float
    tarifa_fija: float
    porcentaje_aplicado: int
    comision_porcentaje_eur: float
    comision_total_allsys: float
    pago_cliente: float

class PrendaClienteDetalle(BaseModel):
    stock_id: int
    producto_id: int
    canal_venta: Optional[str] = None
    sku: str
    nombre_producto: str
    imagen: Optional[str] = None
    estado: str  # "en_stock" o "vendida"
    fecha_venta: Optional[datetime] = None
    estado_pago: Optional[str] = None
    monto_reembolsado: Optional[float] = 0.0
    finanzas: DesgloseFinanciero


class PagoUpdate(BaseModel):
    monto: Optional[float] = None
    metodo_pago: Optional[str] = None
    referencia: Optional[str] = None
    notas: Optional[str] = None




class PaginatedPrendas(BaseModel):
    total: int
    page: int
    limit: int
    items: List[PrendaClienteDetalle]