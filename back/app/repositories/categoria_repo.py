from sqlalchemy.orm import Session
from app.models.categorias_model import Categoria
from app.schemas.categoria_schema import CategoriaCreate

def crear_categoria(db: Session, categoria_in: CategoriaCreate):
    categoria = Categoria(
        nombre=categoria_in.nombre,
        descripcion=categoria_in.descripcion,
        parent_id=categoria_in.parent_id
    )
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria

def listar_categorias(db: Session):
    return db.query(Categoria).all()

def listar_subcategorias(db: Session, categoria_id: int):
    return db.query(Categoria).filter(Categoria.parent_id == categoria_id).all()
