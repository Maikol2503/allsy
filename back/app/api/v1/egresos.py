from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_session
from app.schemas.egresos_schema import EgresoCreate, EgresoUpdate 
from app.repositories import egresos_repo

egresos_router = APIRouter(
    prefix="/egresos",
    tags=["Egresos"]
)

@egresos_router.post("/")
def crear_egreso(
    data: EgresoCreate, 
    db: Session = Depends(get_session)
):
    """
    Registra un nuevo egreso o salida de dinero.
    """
    try:
        egreso = egresos_repo.registrar_egreso(db, data)
        return {
            "success": True, 
            "mensaje": "Egreso registrado correctamente", 
            "egreso_id": egreso.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@egresos_router.get("/{egreso_id}")
def obtener_egreso(
    egreso_id: int, 
    db: Session = Depends(get_session)
):
    """
    Obtiene los detalles de un egreso específico.
    """
    try:
        egreso = egresos_repo.obtener_egreso_por_id(db, egreso_id)
        if not egreso:
            raise HTTPException(status_code=404, detail="Egreso no encontrado")
        return egreso
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el egreso: {str(e)}")


@egresos_router.put("/{egreso_id}")
def actualizar_egreso(
    egreso_id: int,
    data: EgresoUpdate,
    db: Session = Depends(get_session)
):
    """
    Edita un egreso existente.
    """
    try:
        egreso_editado = egresos_repo.editar_egreso(db, egreso_id, data)
        if not egreso_editado:
            raise HTTPException(status_code=404, detail="Egreso no encontrado")
        return {
            "success": True, 
            "mensaje": "Egreso actualizado correctamente", 
            "egreso_id": egreso_editado.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar: {str(e)}")


@egresos_router.get("/")
def listar_egresos(
    page: int = Query(1, ge=1), 
    limit: int = Query(20, ge=1), 
    search: Optional[str] = Query(None),
    categoria: Optional[str] = Query(None),
    metodo_pago: Optional[str] = Query(None),
    proveedor_id: Optional[int] = Query(None),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    db: Session = Depends(get_session)
):
    """
    Obtiene el historial de egresos paginado y filtrado.
    """
    try:
        return egresos_repo.obtener_egresos_paginados(
            db=db, 
            page=page, 
            limit=limit,
            search=search,
            categoria=categoria,
            metodo_pago=metodo_pago,
            proveedor_id=proveedor_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener egresos: {str(e)}")
