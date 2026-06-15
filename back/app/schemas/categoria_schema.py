from pydantic import BaseModel
from typing import Optional

class CategoriaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    genero: Optional[str] = None  # 👇 Añadimos el género
    parent_id: Optional[int] = None
    activo: Optional[bool] = True # 👇 Añadimos activo por defecto a True

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaOut(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    genero: Optional[str] = None  # 👇 Para que el frontend sepa el género
    parent_id: Optional[int] = None
    activo: bool                  # 👇 Para que el frontend sepa si está activa

    class Config:
        orm_mode = True
