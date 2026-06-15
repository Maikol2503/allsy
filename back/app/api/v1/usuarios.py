from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_session
from app.schemas.usuarios_schema import UsuarioCreate, UsuarioOut
from app.services.usuarios_services import crear_usuario
from app.models.usuario_model import Usuario

router = APIRouter()

@router.post("/", response_model=UsuarioOut)
def registrar_usuario(usuario_in: UsuarioCreate, db: Session = Depends(get_session
                                                                       )):
    # Verificar si ya existe
    existe = db.query(Usuario).filter(Usuario.email == usuario_in.email).first()
    if existe:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    usuario = crear_usuario(db, usuario_in)
    return usuario
