# egresos_repo.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from datetime import datetime
from app.models.egresos_model import Egreso
from app.schemas.egresos_schema import EgresoCreate, EgresoUpdate
from sqlalchemy import desc, or_, and_

# ✨ IMPORTANTE: Importar tu helper de proveedores
from app.repositories.proveedores_repo import buscar_o_crear 
from app.repositories.auditoria_repo import registrar_log 

def registrar_egreso(db: Session, data: EgresoCreate):
    # ✨ 1. LÓGICA DEL PROVEEDOR
    p_id = data.proveedor_id
    
    # Si no nos enviaron un ID, pero escribieron un nombre nuevo en el input
    if not p_id and data.proveedor_nombre_nuevo:
        # Lo buscamos o creamos diciéndole que es un EGRESO
        proveedor_obj = buscar_o_crear(db, data.proveedor_nombre_nuevo.strip(), contexto="egreso")
        p_id = proveedor_obj.id if proveedor_obj else None

    # 2. Creamos la instancia del modelo
    nuevo_egreso = Egreso(
        concepto=data.concepto,
        categoria=data.categoria,
        monto=data.monto,
        metodo_pago=data.metodo_pago,
        fecha=data.fecha or datetime.utcnow(),
        notas=data.notas,
        proveedor_id=p_id  # ✨ 3. Asignamos el ID
    )
    
    # Guardamos en base de datos
    db.add(nuevo_egreso)
    db.commit()
    db.refresh(nuevo_egreso)

    # ✨ AUDITORÍA: Registro de egreso
    registrar_log(
        db, accion="CREAR", entidad_tipo="EGRESO", entidad_id=nuevo_egreso.id,
        valor_nuevo={"concepto": nuevo_egreso.concepto, "monto": nuevo_egreso.monto},
        notas=f"Egreso de {nuevo_egreso.monto}€ registrado."
    )

    return nuevo_egreso



def obtener_egreso_por_id(db: Session, egreso_id: int):
    # Usamos joinedload para que devuelva también la info del proveedor
    egreso = db.query(Egreso).options(joinedload(Egreso.proveedor)).filter(Egreso.id == egreso_id).first()
    
    if not egreso:
        return None
        
    return {
        "id": egreso.id,
        "concepto": egreso.concepto,
        "categoria": egreso.categoria,
        "monto": egreso.monto,
        "metodo_pago": egreso.metodo_pago,
        "fecha": egreso.fecha.isoformat() if egreso.fecha else None,
        "notas": egreso.notas,
        "proveedor_id": egreso.proveedor_id,
        "proveedor": {"id": egreso.proveedor.id, "nombre": egreso.proveedor.nombre_proveedor} if egreso.proveedor else None
    }



# ✨ NUEVO: Función para editar
def editar_egreso(db: Session, egreso_id: int, data: EgresoUpdate):
    egreso = db.query(Egreso).filter(Egreso.id == egreso_id).first()
    if not egreso:
        return None

    # Actualizamos los campos si vienen en la petición
    if data.concepto is not None: egreso.concepto = data.concepto
    if data.categoria is not None: egreso.categoria = data.categoria
    if data.monto is not None: egreso.monto = data.monto
    if data.metodo_pago is not None: egreso.metodo_pago = data.metodo_pago
    if data.notas is not None: egreso.notas = data.notas
    if data.fecha is not None: egreso.fecha = data.fecha

    # 🧠 Lógica inteligente de proveedor
    if data.proveedor_id:
        egreso.proveedor_id = data.proveedor_id
    elif data.proveedor_nombre_nuevo:
        proveedor_obj = buscar_o_crear(db, data.proveedor_nombre_nuevo.strip(), contexto="egreso")
        egreso.proveedor_id = proveedor_obj.id

    db.commit()
    db.refresh(egreso)

    # ✨ AUDITORÍA: Actualización de egreso
    registrar_log(
        db, accion="EDITAR", entidad_tipo="EGRESO", entidad_id=egreso.id,
        valor_nuevo={"concepto": egreso.concepto, "monto": egreso.monto},
        notas=f"Egreso {egreso.id} actualizado."
    )

    return egreso


# ✨ ACTUALIZADO: Paginación con filtros
def obtener_egresos_paginados(
    db: Session, 
    page: int = 1, 
    limit: int = 20,
    search: str = None,
    categoria: str = None,
    metodo_pago: str = None,
    proveedor_id: int = None,
    fecha_inicio: str = None,
    fecha_fin: str = None
):
    offset = (page - 1) * limit
    query = db.query(Egreso)

    # --- APLICACIÓN DE FILTROS ---
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(or_(
            Egreso.concepto.ilike(term),
            Egreso.notas.ilike(term)
        ))
        
    if categoria:
        query = query.filter(Egreso.categoria == categoria)
        
    if metodo_pago:
        query = query.filter(Egreso.metodo_pago == metodo_pago)
        
    if proveedor_id:
        query = query.filter(Egreso.proveedor_id == proveedor_id)
        
    if fecha_inicio:
        query = query.filter(Egreso.fecha >= fecha_inicio)
        
    if fecha_fin:
        query = query.filter(Egreso.fecha <= f"{fecha_fin} 23:59:59")
    # -----------------------------

    total = query.count()
    egresos = (
        query.options(joinedload(Egreso.proveedor))
        .order_by(desc(Egreso.fecha))
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    resultados = []
    for g in egresos:
        resultados.append({
            "id": g.id,
            "concepto": g.concepto,
            "categoria": g.categoria,
            "monto": g.monto,
            "metodo_pago": g.metodo_pago,
            "fecha": g.fecha.isoformat() if g.fecha else None,
            "notas": g.notas,
            "proveedor": {"id": g.proveedor.id, "nombre": g.proveedor.nombre_proveedor} if g.proveedor else None,
            "proveedor_id": g.proveedor_id
        })
    
    return {"total": total, "items": resultados}
