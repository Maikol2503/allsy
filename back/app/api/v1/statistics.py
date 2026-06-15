from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_session
from app.repositories import statistics_repo
from typing import Optional

# Nomenclatura específica para evitar conflictos en el import
router_statistics = APIRouter(prefix="/stats", tags=["Estadísticas Avanzadas"])

@router_statistics.get("/dashboard-completo")
def get_stats(
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    db: Session = Depends(get_session)
):
    return statistics_repo.obtener_inteligencia_negocio(db, fecha_inicio, fecha_fin)



@router_statistics.get("/rendimiento-compras")
def get_rendimiento_compras(
    fecha_inicio: str = Query(None, description="Fecha de compra inicial (YYYY-MM-DD)"),
    fecha_fin: str = Query(None, description="Fecha de compra final (YYYY-MM-DD)"),
    db: Session = Depends(get_session)
):
    """
    Analiza el éxito y retorno de inversión de la ropa comprada 
    en un periodo específico, sin importar cuándo se vendió.
    """
    try:
        data = statistics_repo.obtener_rendimiento_compras(db, fecha_inicio, fecha_fin)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    



@router_statistics.get("/rendimiento-proveedores")
def get_rendimiento_proveedores(
    fecha_inicio: str = Query(None, description="Fecha de compra inicial (YYYY-MM-DD)"),
    fecha_fin: str = Query(None, description="Fecha de compra final (YYYY-MM-DD)"),
    db: Session = Depends(get_session)
):
    """
    Evalúa la rentabilidad y el éxito de ventas agrupado por Proveedor.
    """
    try:
        data = statistics_repo.obtener_rendimiento_proveedores(db, fecha_inicio, fecha_fin)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))