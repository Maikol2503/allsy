from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime

class AuditoriaBase(BaseModel):
    usuario_id: Optional[int] = None
    nombre_usuario: Optional[str] = None
    localizacion_id: Optional[int] = None
    accion: str
    entidad_tipo: str
    entidad_id: Optional[int] = None
    valor_anterior: Optional[Dict[str, Any]] = None
    valor_nuevo: Optional[Dict[str, Any]] = None
    notas: Optional[str] = None
    ip_address: Optional[str] = None

class AuditoriaCreate(AuditoriaBase):
    pass

class AuditoriaOut(AuditoriaBase):
    id: int
    fecha: datetime

    class Config:
        from_attributes = True
