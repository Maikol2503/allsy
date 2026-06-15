from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_session
from app.repositories.marcas_repo import listar_marcas

marcas_router = APIRouter(prefix="/marcas", tags=["Marcas"])


@marcas_router.get("/")
def listar_marcas_endpoint(db: Session = Depends(get_session)):
    return listar_marcas(db)