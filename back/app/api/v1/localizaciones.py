from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_session
from app.schemas.localizacion_schema import LocalizacionOut, LocalizacionTree, LocalizacionCreate, LocalizacionUpdate
from app.repositories.localizacion_repo import obtener_localizaciones, obtener_localizaciones_raiz, crear_localizacion, actualizar_localizacion, eliminar_localizacion
from app.models.localizaciones_model import Localizacion

router = APIRouter(prefix="/localizaciones", tags=["Localizaciones"])

@router.get("/", response_model=List[LocalizacionOut])
def listar_localizaciones(db: Session = Depends(get_session)):
    return obtener_localizaciones(db)

@router.get("/arbol", response_model=List[LocalizacionTree])
def listar_localizaciones_arbol(db: Session = Depends(get_session)):
    raices = obtener_localizaciones_raiz(db)
    return raices

@router.post("/", response_model=LocalizacionOut)
def crear_nueva_localizacion(data: LocalizacionCreate, db: Session = Depends(get_session)):
    try:
        return crear_localizacion(db, data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{loc_id}", response_model=LocalizacionOut)
def actualizar_localizacion_endpoint(loc_id: int, data: LocalizacionUpdate, db: Session = Depends(get_session)):
    try:
        return actualizar_localizacion(db, loc_id, data)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{loc_id}")
def eliminar_localizacion_endpoint(loc_id: int, db: Session = Depends(get_session)):
    try:
        return eliminar_localizacion(db, loc_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
