from pydantic import BaseModel, EmailStr
from typing import Optional

class UsuarioBase(BaseModel):
    nombre: str
    email: EmailStr
    is_admin: Optional[bool] = False

# ✅ Entrada (para registrar usuario)
class UsuarioCreate(UsuarioBase):
    password: str

# ✅ Salida (para devolver al frontend)
class UsuarioOut(UsuarioBase):
    id: int

    class Config:
        orm_mode = True




class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
