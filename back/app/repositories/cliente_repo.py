from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, func
from fastapi import HTTPException
from datetime import datetime

from app.models.clientes_model import Cliente
from app.models.ventas_model import Venta
from app.schemas.clientes_schema import ClienteCreate

# =====================================================
# CREAR CLIENTE
# =====================================================
from sqlalchemy.exc import IntegrityError

def crear_cliente(db: Session, data: ClienteCreate):
    try:
        nuevo_cliente = Cliente(**data.dict(exclude_unset=True))
        db.add(nuevo_cliente)
        db.commit()
        db.refresh(nuevo_cliente)
        return nuevo_cliente
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig)
        # Detectamos qué campo causó el conflicto para avisar al usuario
        if "email" in error_msg:
            msg = "El Correo Electrónico ya está registrado."
        elif "telefono" in error_msg:
            msg = "El número de Teléfono ya está registrado."
        elif "usuario_vinted" in error_msg:
            msg = "El usuario de Vinted ya está registrado."
        elif "usuario_wallapop" in error_msg:
            msg = "El usuario de Wallapop ya está registrado."
        else:
            msg = "Uno de los identificadores ya pertenece a otro cliente."
        
        raise HTTPException(status_code=400, detail=msg)

# =====================================================
# ACTUALIZAR CLIENTE
# =====================================================
from sqlalchemy.exc import IntegrityError # 👈 Asegúrate de tener esta importación arriba

def actualizar_cliente(db: Session, cliente_id: int, datos: dict):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    try:
        # ✨ CORRECCIÓN: Iteramos sobre los datos entrantes y los asignamos incondicionalmente
        # (Esto permite cambiar True -> False y viceversa)
        for key, value in datos.items():
            if hasattr(cliente, key):
                setattr(cliente, key, value)

        db.commit()
        db.refresh(cliente)
        return cliente
        
    # ✨ AQUÍ CAPTURAMOS EL ERROR DE DUPLICADOS AL EDITAR
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig)
        
        if "email" in error_msg:
            msg = "El Correo Electrónico introducido ya pertenece a otro cliente."
        elif "telefono" in error_msg:
            msg = "El número de Teléfono introducido ya pertenece a otro cliente."
        elif "usuario_vinted" in error_msg:
            msg = "El usuario de Vinted introducido ya pertenece a otro cliente."
        elif "usuario_wallapop" in error_msg:
            msg = "El usuario de Wallapop introducido ya pertenece a otro cliente."
        else:
            msg = "Uno de los datos introducidos ya está registrado en otro cliente."
        
        raise HTTPException(status_code=400, detail=msg)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error inesperado al actualizar: {str(e)}")

# =====================================================
# LISTAR CLIENTES CON FILTROS Y CONTEO DE VENTAS
# =====================================================
def obtener_clientes_paginados(
    db: Session, 
    page: int = 1, 
    limit: int = 10,
    search: str = None, 
    search_type: str = "todos",
    pais: str = None, 
    fecha_inicio: str = None, 
    fecha_fin: str = None
):
    offset = (page - 1) * limit

    # ✨ MAGIA SQL: Seleccionamos al Cliente Y contamos sus Ventas
    query = db.query(
        Cliente, 
        func.count(Venta.id).label("total_ventas")
    ).outerjoin(Venta, Cliente.id == Venta.cliente_id) \
     .filter(Cliente.activo == True) \
     .group_by(Cliente.id)

    # 1. Filtro de Búsqueda General (Email, Usuario, Teléfono, Nombre, DNI)
    if search and search.strip():
        term = f"%{search.strip()}%"
        # Quitamos el @ por si el usuario lo escribe al buscar un nombre de Vinted
        term_clean = f"%{search.strip().replace('@', '')}%"
        
        if search_type == "nombre":
            query = query.filter(or_(Cliente.nombre.ilike(term), Cliente.apellidos.ilike(term)))
        elif search_type == "email":
            query = query.filter(Cliente.email.ilike(term))
        elif search_type == "telefono":
            query = query.filter(Cliente.telefono.ilike(term))
        elif search_type == "usuario":
            query = query.filter(or_(Cliente.usuario_vinted.ilike(term_clean), Cliente.usuario_wallapop.ilike(term_clean)))
        else:
            query = query.filter(
                or_(
                    Cliente.email.ilike(term),
                    Cliente.telefono.ilike(term),
                    Cliente.usuario_vinted.ilike(term_clean),
                    Cliente.usuario_wallapop.ilike(term_clean),
                    Cliente.nombre.ilike(term),
                    Cliente.apellidos.ilike(term),
                    Cliente.dni_nie.ilike(term)
                )
            )

    # 2. Filtro por País
    if pais and pais.strip():
        query = query.filter(Cliente.pais.ilike(pais.strip()))

    # 3. Filtros por Fecha de Registro
    if fecha_inicio:
        query = query.filter(Cliente.fecha_registro >= fecha_inicio)
    if fecha_fin:
        query = query.filter(Cliente.fecha_registro <= f"{fecha_fin} 23:59:59")

    # Contar totales para la paginación
    total_count = query.count()

    # Ejecutar la consulta con orden y paginación
    resultados_db = query.order_by(desc(Cliente.fecha_registro)).offset(offset).limit(limit).all()

    # Formatear la salida combinando el objeto Cliente y la columna calculada total_ventas
    items = []
    for cliente, total_ventas in resultados_db:
        cliente_dict = cliente.__dict__.copy()
        cliente_dict.pop("_sa_instance_state", None) # Limpieza interna de SQLAlchemy
        cliente_dict["total_ventas"] = total_ventas
        items.append(cliente_dict)

    return {
        "total": total_count,
        "items": items
    }






# =====================================================
# OBTENER UN SOLO CLIENTE POR ID
# =====================================================
def obtener_cliente_por_id(db: Session, cliente_id: int):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    return cliente








# =====================================================
# DESACTIVAR CLIENTE (BORRADO LÓGICO)
# =====================================================
def desactivar_cliente(db: Session, cliente_id: int):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # En lugar de borrar, simplemente "apagamos" al cliente
    cliente.activo = False
    
    try:
        db.commit()
        db.refresh(cliente)
        return {"status": "success", "message": f"Cliente '{cliente.nombre}' ha sido desactivado."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al desactivar: {str(e)}")