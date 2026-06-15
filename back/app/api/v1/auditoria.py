from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_session
from app.schemas.auditoria_schema import AuditoriaOut
from app.repositories.auditoria_repo import obtener_logs

router = APIRouter(prefix="/auditoria", tags=["Auditoría"])

@router.get("/", response_model=List[AuditoriaOut])
def listar_logs(
    entidad_tipo: Optional[str] = Query(None, description="Filtrar por tipo de entidad (PRODUCTO, VENTA, etc.)"),
    entidad_id: Optional[int] = Query(None, description="Filtrar por ID de la entidad"),
    localizacion_id: Optional[int] = Query(None, description="Filtrar por tienda/localización"),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_session)
):
    """
    Lista los últimos logs de actividad del sistema con filtros opcionales.
    """
    return obtener_logs(
        db, 
        entidad_tipo=entidad_tipo, 
        entidad_id=entidad_id, 
        localizacion_id=localizacion_id, 
        limit=limit
    )
