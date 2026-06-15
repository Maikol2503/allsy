from sqlalchemy.orm import Session
from app.models.marcas_model import Marca


def listar_marcas(db: Session):
    return db.query(Marca).order_by(Marca.nombre).all()


def obtener_marca_por_id(db: Session, marca_id: int):
    return db.query(Marca).filter(Marca.id == marca_id).first()


def crear_marca(db: Session, nombre: str, descripcion: str | None = None):
    marca = Marca(
        nombre=nombre,
        descripcion=descripcion
    )
    db.add(marca)
    db.commit()
    db.refresh(marca)
    return marca
