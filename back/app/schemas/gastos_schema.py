from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class GastoCreate(BaseModel):
    concepto: str
    categoria: str
    monto: float
    metodo_pago: str
    notas: Optional[str] = None
    fecha: Optional[datetime] = None
    
    # ✨ NUEVO: Los datos del proveedor que vendrán de Angular
    proveedor_id: Optional[int] = None
    proveedor_nombre_nuevo: Optional[str] = None


class GastoUpdate(BaseModel):
    concepto: Optional[str] = None
    categoria: Optional[str] = None
    monto: Optional[float] = None
    metodo_pago: Optional[str] = None
    notas: Optional[str] = None
    fecha: Optional[datetime] = None
    
    proveedor_id: Optional[int] = None
    proveedor_nombre_nuevo: Optional[str] = None