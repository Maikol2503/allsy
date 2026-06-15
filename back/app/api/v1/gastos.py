from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_session
# ✨ Importamos GastoUpdate para la edición
from app.schemas.gastos_schema import GastoCreate, GastoUpdate 
from app.repositories import gastos_repo

gastos_router = APIRouter(
    prefix="/gastos",
    tags=["Gastos"]
)

@gastos_router.post("/")
def crear_gasto(
    data: GastoCreate, 
    db: Session = Depends(get_session)
):
    """
    Registra un nuevo gasto o salida de dinero.
    """
    try:
        gasto = gastos_repo.registrar_gasto(db, data)
        return {
            "success": True, 
            "mensaje": "Gasto registrado correctamente", 
            "gasto_id": gasto.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ✨ NUEVO: Endpoint para obtener UN solo gasto (Útil para rellenar el formulario al editar)
@gastos_router.get("/{gasto_id}")
def obtener_gasto(
    gasto_id: int, 
    db: Session = Depends(get_session)
):
    """
    Obtiene los detalles de un gasto específico.
    """
    try:
        gasto = gastos_repo.obtener_gasto_por_id(db, gasto_id)
        if not gasto:
            raise HTTPException(status_code=404, detail="Gasto no encontrado")
        return gasto
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el gasto: {str(e)}")


# ✨ NUEVO: Endpoint para editar un gasto
@gastos_router.put("/{gasto_id}")
def actualizar_gasto(
    gasto_id: int,
    data: GastoUpdate,
    db: Session = Depends(get_session)
):
    """
    Edita un gasto existente.
    """
    try:
        gasto_editado = gastos_repo.editar_gasto(db, gasto_id, data)
        if not gasto_editado:
            raise HTTPException(status_code=404, detail="Gasto no encontrado")
        return {
            "success": True, 
            "mensaje": "Gasto actualizado correctamente", 
            "gasto_id": gasto_editado.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar: {str(e)}")


# ✨ ACTUALIZADO: Endpoint de listar con filtros
@gastos_router.get("/")
def listar_gastos(
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
    Obtiene el historial de gastos paginado y filtrado.
    """
    try:
        return gastos_repo.obtener_gastos_paginados(
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
        raise HTTPException(status_code=500, detail=f"Error al obtener gastos: {str(e)}")