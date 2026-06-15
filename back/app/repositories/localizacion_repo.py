from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.localizaciones_model import Localizacion
from app.models.lotes_model import StockConfig
from app.schemas.localizacion_schema import LocalizacionCreate, LocalizacionUpdate

def obtener_localizaciones(db: Session, include_inactive: bool = False):
    query = db.query(Localizacion)
    if not include_inactive:
        query = query.filter(Localizacion.activo == True)
    return query.all()

def obtener_localizaciones_raiz(db: Session):
    return db.query(Localizacion).filter(Localizacion.activo == True, Localizacion.parent_id == None).all()

def crear_localizacion(db: Session, loc_in: LocalizacionCreate):
    db_loc = Localizacion(**loc_in.model_dump())
    db.add(db_loc)
    db.commit()
    db.refresh(db_loc)
    return db_loc

def actualizar_localizacion(db: Session, loc_id: int, datos: LocalizacionUpdate):
    db_loc = db.query(Localizacion).filter(Localizacion.id == loc_id).first()
    if not db_loc:
        raise HTTPException(status_code=404, detail="Localización no encontrada")

    update_data = datos.model_dump(exclude_unset=True)
    
    # Prevenir ciclos: un nodo no puede ser su propio padre ni hijo de sí mismo
    if "parent_id" in update_data and update_data["parent_id"] == loc_id:
        raise HTTPException(status_code=400, detail="Una localización no puede ser padre de sí misma")

    for key, value in update_data.items():
        setattr(db_loc, key, value)
        
    db.commit()
    db.refresh(db_loc)
    return db_loc

def eliminar_localizacion(db: Session, loc_id: int):
    db_loc = db.query(Localizacion).filter(Localizacion.id == loc_id).first()
    if not db_loc:
        raise HTTPException(status_code=404, detail="Localización no encontrada")

    # Verificar si tiene hijos
    hijos = db.query(Localizacion).filter(Localizacion.parent_id == loc_id).count()
    if hijos > 0:
        raise HTTPException(status_code=400, detail=f"No se puede eliminar porque contiene {hijos} sub-localizaciones. Elimina o mueve los hijos primero.")

    # Verificar si hay stock usándola
    stock_usando = db.query(StockConfig).filter(StockConfig.localizacion_id == loc_id).count()
    if stock_usando > 0:
        raise HTTPException(status_code=400, detail=f"No se puede eliminar porque hay {stock_usando} lotes de stock almacenados aquí. Mueve el stock primero.")

    db.delete(db_loc)
    db.commit()
    return {"message": "Localización eliminada correctamente"}

def buscar_localizacion_por_nombre(db: Session, nombre: str, parent_id: int = None):
    return db.query(Localizacion).filter(
        Localizacion.nombre == nombre, 
        Localizacion.parent_id == parent_id,
        Localizacion.activo == True
    ).first()
