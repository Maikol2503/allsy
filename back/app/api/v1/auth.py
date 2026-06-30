from fastapi import APIRouter, Depends, HTTPException, status, HTTPException, status, Form
from sqlalchemy.orm import Session
from app.core.security import crear_token_acceso, verificar_password
from app.db.database import get_session
from app.models.usuario_model import Usuario
from app.schemas.usuarios_schema import UsuarioCreate, UsuarioOut
from app.services.usuarios_services import crear_usuario
from app.schemas.usuarios_schema import LoginRequest, TokenResponse
from datetime import datetime, timedelta
from app.core.config import settings
from jose import jwt, JWTError


auth_routers = APIRouter(prefix="/auth", tags=["Autenticación"])

# ✅ Registro
@auth_routers.post("/register", response_model=UsuarioOut)
def register(usuario_in: UsuarioCreate, db: Session = Depends(get_session)):
    nuevo_usuario = crear_usuario(db, usuario_in)
    return nuevo_usuario


@auth_routers.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_session)):
    print(login_data)
    usuario = db.query(Usuario).filter(Usuario.email == login_data.email).first()

    if not usuario or not verificar_password(login_data.password, usuario.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email o contraseña incorrectos")

    access_token = crear_token_acceso({"sub": usuario.email, "id": usuario.id})
    refresh_token = crear_token_acceso(
        {"sub": usuario.email, "id": usuario.id}, 
        expires_delta=timedelta(days=7) # El refresh dura mucho más
    )

    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer"
    }





@auth_routers.post("/refresh")
def refresh_token(refresh_token: str = Form(...), db: Session = Depends(get_session)):
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        user_id = payload.get("id")
        # Creamos un nuevo Access Token
        nuevo_access = crear_token_acceso({"sub": email, "id": user_id})
        return {"access_token": nuevo_access, "token_type": "bearer"}
    except:
        raise HTTPException(status_code=401, detail="Refresh token inválido o expirado")