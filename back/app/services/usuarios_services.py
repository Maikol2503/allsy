from sqlalchemy.orm import Session
from app.models.usuario_model import Usuario
from app.schemas.usuarios_schema import UsuarioCreate
from app.core.security import hashear_password

def crear_usuario(db: Session, usuario_in: UsuarioCreate):
    usuario = Usuario(
        nombre=usuario_in.nombre,
        email=usuario_in.email,
        hashed_password=hashear_password(usuario_in.password),
        is_admin=usuario_in.is_admin
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario