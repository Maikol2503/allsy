from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_session
from app.repositories import proveedores_repo
from app.api.deps import get_current_admin # Si quieres proteger estas rutas

proveedores_router = APIRouter(
    prefix="/proveedores",
    tags=["Gestión de Proveedores"]
)

# --- LISTAR TODOS ---
@proveedores_router.get("/")
def listar_todos(db: Session = Depends(get_session)):
    return proveedores_repo.obtener_todos(db)

# --- CREAR UNO NUEVO ---
@proveedores_router.post("/", status_code=status.HTTP_201_CREATED)
def crear_proveedor(nombre: str, db: Session = Depends(get_session)):
    # Usamos buscar_o_crear para evitar duplicados por nombre
    proveedor = proveedores_repo.buscar_o_crear(db, nombre)
    return proveedor

# --- ACTUALIZAR ---
@proveedores_router.put("/{proveedor_id}")
def actualizar_proveedor(
    proveedor_id: int, 
    nombre: str, 
    db: Session = Depends(get_session)
):
    proveedor = proveedores_repo.actualizar_proveedor(db, proveedor_id, nombre)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return proveedor

# --- ELIMINAR ---
@proveedores_router.delete("/{proveedor_id}")
def eliminar_proveedor(proveedor_id: int, db: Session = Depends(get_session)):
    # Opcional: podrías mover esto al repo también
    from app.models.proveedores_model import Proveeedores
    proveedor = db.query(Proveeedores).filter(Proveeedores.id == proveedor_id).first()
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    db.delete(proveedor)
    db.commit()
    return {"message": "Proveedor eliminado correctamente"}