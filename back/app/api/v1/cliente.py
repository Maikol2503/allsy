from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_session
from app.schemas.clientes_schema import ClienteCreate, ClienteUpdate
from app.repositories.cliente_repo import obtener_cliente_por_id, obtener_clientes_paginados, crear_cliente, actualizar_cliente, desactivar_cliente

router = APIRouter(
    prefix="/clientes",
    tags=["Clientes CRM"]
)

@router.post("/")
def crear_nuevo_cliente(data: ClienteCreate, db: Session = Depends(get_session)):
    """Registra un nuevo cliente manualmente en el CRM."""
    # Ahora Python sabe que esta es la función del repositorio que importaste
    return crear_cliente(db, data)


@router.get("/")
def listar_clientes(
    page: int = 1, 
    limit: int = 10,
    search: Optional[str] = None,
    search_type: Optional[str] = "todos",
    pais: Optional[str] = None,
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    con_deuda: Optional[bool] = False,
    db: Session = Depends(get_session)
):
    """Obtiene el listado de clientes con filtros y el total de compras de cada uno."""
    try:
        return obtener_clientes_paginados(
            db=db, 
            page=page, 
            limit=limit, 
            search=search, 
            search_type=search_type,
            pais=pais, 
            fecha_inicio=fecha_inicio, 
            fecha_fin=fecha_fin,
            con_deuda=con_deuda
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno al listar clientes: {str(e)}")


@router.put("/{cliente_id}")
def editar_cliente(cliente_id: int, data: ClienteUpdate, db: Session = Depends(get_session)):
    """Actualiza la ficha de un cliente existente."""
    try:
        return actualizar_cliente(db, cliente_id, data.dict(exclude_unset=True))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    
    
@router.get("/{cliente_id}")
def obtener_cliente(cliente_id: int, db: Session = Depends(get_session)):
    """Obtiene los datos de un cliente específico por su ID para editarlo."""
    try:
        return obtener_cliente_por_id(db, cliente_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    



@router.patch("/{cliente_id}/desactivar")
def desactivar_cliente_endpoint(cliente_id: int, db: Session = Depends(get_session)):
    """
    Marca a un cliente como inactivo. 
    Mantiene la integridad de las ventas pero lo quita de la vista principal.
    """
    return desactivar_cliente(db, cliente_id)
