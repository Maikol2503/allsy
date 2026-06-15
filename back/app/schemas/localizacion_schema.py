from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class LocalizacionBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    tipo: str = "almacen"
    es_principal: bool = False
    activo: bool = True
    parent_id: Optional[int] = None

class LocalizacionCreate(LocalizacionBase):
    pass

class LocalizacionUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    tipo: Optional[str] = None
    es_principal: Optional[bool] = None
    activo: Optional[bool] = None
    parent_id: Optional[int] = None

class LocalizacionOut(LocalizacionBase):
    id: int
    fecha_registro: datetime

    class Config:
        from_attributes = True

class LocalizacionTree(LocalizacionOut):
    hijos: List['LocalizacionTree'] = []

    class Config:
        from_attributes = True
