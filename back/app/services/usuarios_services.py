from sqlalchemy.orm import Session
from app.models.usuario_model import Usuario
from app.schemas.usuarios_schema import UsuarioCreate
from app.core.security import hashear_password

def crear_usuario(db: Session, usuario_in: UsuarioCreate):
    # Validar si ya existe
    from fastapi import HTTPException, status
    if db.query(Usuario).filter(Usuario.email == usuario_in.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El email ya está registrado")

    # Solo el primer usuario registrado es admin, o requiere otra lógica
    is_first_user = db.query(Usuario).count() == 0
    
    usuario = Usuario(
        nombre=usuario_in.nombre,
        email=usuario_in.email,
        hashed_password=hashear_password(usuario_in.password),
        is_admin=is_first_user # IGNORA lo que mande el frontend por seguridad
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario