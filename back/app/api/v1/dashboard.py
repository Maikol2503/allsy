from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_session
from app.repositories import dashboard_repo

dashboard_router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)

@dashboard_router.get("/resumen")
def get_resumen(
    fecha_inicio: Optional[str] = None, 
    fecha_fin: Optional[str] = None, 
    db: Session = Depends(get_session)
):
    return dashboard_repo.obtener_resumen_financiero(db, fecha_inicio, fecha_fin)

@dashboard_router.get("/grafica-tendencia")
def get_datos_grafica(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    db: Session = Depends(get_session)
):
    """
    Devuelve las ventas vs gastos agrupadas por día o mes según el rango.
    """
    try:
        return dashboard_repo.obtener_datos_grafica_tendencia(db, fecha_inicio, fecha_fin)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar gráfica: {str(e)}")