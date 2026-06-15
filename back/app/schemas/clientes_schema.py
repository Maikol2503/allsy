# from pydantic import BaseModel, EmailStr
# from typing import Optional
# from datetime import datetime

# class ClienteBase(BaseModel):
#     email: Optional[EmailStr] = None
#     telefono: Optional[str] = None
#     usuario_vinted: Optional[str] = None
#     usuario_wallapop: Optional[str] = None
    
#     nombre: Optional[str] = None
#     apellidos: Optional[str] = None
#     dni_nie: Optional[str] = None
    
#     direccion: Optional[str] = None
#     ciudad: Optional[str] = None
#     codigo_postal: Optional[str] = None
#     provincia: Optional[str] = None
#     pais: Optional[str] = "España"
    
#     notas_internas: Optional[str] = None
#     es_vip: Optional[bool] = False

# class ClienteCreate(ClienteBase):
#     pass

# class ClienteUpdate(ClienteBase):
#     pass

# class ClienteOut(ClienteBase):
#     id: int
#     fecha_registro: datetime

#     class Config:
#         from_attributes = True

# class ClienteListOut(ClienteOut):
#     total_ventas: int = 0


from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional

# Para EDITAR (Todo opcional para permitir actualizaciones parciales)
class ClienteUpdate(BaseModel):
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    usuario_vinted: Optional[str] = None
    usuario_wallapop: Optional[str] = None
    dni_nie: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    codigo_postal: Optional[str] = None
    provincia: Optional[str] = None
    pais: Optional[str] = None
    notas_internas: Optional[str] = None
    es_vip: Optional[bool] = None
    comision_personalizada: Optional[float] = None
    exento_comision: Optional[bool] = None
    exento_tarifa_fija: Optional[bool] = None

# Campos comunes que comparten todos
class ClienteBase(BaseModel):
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    usuario_vinted: Optional[str] = None
    usuario_wallapop: Optional[str] = None
    dni_nie: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    codigo_postal: Optional[str] = None
    provincia: Optional[str] = None
    pais: str = "España"
    notas_internas: Optional[str] = None
    es_vip: bool = False
    # En ClienteBase y ClienteUpdate:
    exento_comision: bool = False
    exento_tarifa_fija: bool = False

    @field_validator('email', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v

# Lo que pides para CREAR (No lleva ID ni total_ventas)
class ClienteCreate(ClienteBase):
    pass

# Lo que devuelves al FRONTEND (Aquí sí incluyes ID y datos calculados)
class ClienteRead(ClienteBase):
    id: int
    total_ventas: int = 0

    class Config:
        from_attributes = True # Permite leer objetos de SQLAlchemy