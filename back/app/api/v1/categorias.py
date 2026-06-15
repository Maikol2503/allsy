from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_session
from app.schemas.categoria_schema import CategoriaCreate, CategoriaOut
from app.repositories.categoria_repo import crear_categoria, listar_categorias, listar_subcategorias
from app.api.deps import get_current_admin  # proteger rutas admin
from app.models.atributo_categoria_model import AtributoCategoria 



categorias_routers = APIRouter(prefix="/categorias", tags=["Categorías"])

# Crear categoría o subcategoría
@categorias_routers.post("/", response_model=CategoriaOut)
def crear_categoria_endpoint(
    categoria_in: CategoriaCreate,
    db: Session = Depends(get_session),
    current_admin=Depends(get_current_admin)
):
    return crear_categoria(db, categoria_in)

# Listar categorías raíz
@categorias_routers.get("/", response_model=List[CategoriaOut])
def listar_categorias_endpoint(db: Session = Depends(get_session)):
    return listar_categorias(db)

# Listar subcategorías de una categoría
@categorias_routers.get("/{categoria_id}/subcategorias", response_model=List[CategoriaOut])
def listar_subcategorias_endpoint(categoria_id: int, db: Session = Depends(get_session)):
    return listar_subcategorias(db, categoria_id)


# from fastapi import APIRouter, Depends
# from sqlalchemy.orm import Session
# from app.db.database import get_session
# # Asegúrate de importar el modelo que acabamos de crear


@categorias_routers.get("/categorias/{categoria_id}/atributos")
def obtener_atributos_categoria(categoria_id: int, db: Session = Depends(get_session)):
    """
    Devuelve los inputs que Angular debe pintar cuando eligen esta categoría.
    """
    atributos = db.query(AtributoCategoria).filter(AtributoCategoria.categoria_id == categoria_id).all()
    
    # Si la categoría aún no tiene atributos configurados, devolvemos 'peso_kg' por defecto
    # ya que es el único obligatorio para los envíos.
    if not atributos:
        return [{"nombre": "peso_kg", "tipo": "number", "opciones": None}]
        
    return [
        {
            "nombre": a.nombre,
            "tipo": a.tipo,
            "opciones": a.opciones
        } for a in atributos
    ]
