# gastos_repo.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from datetime import datetime
from app.models.gastos_model import Gasto
from app.schemas.gastos_schema import GastoCreate, GastoUpdate
from sqlalchemy import desc, or_, and_

# ✨ IMPORTANTE: Importar tu helper de proveedores
from app.repositories.proveedores_repo import buscar_o_crear 
from app.repositories.auditoria_repo import registrar_log 

def registrar_gasto(db: Session, data: GastoCreate):
    # ✨ 1. LÓGICA DEL PROVEEDOR
    p_id = data.proveedor_id
    
    # Si no nos enviaron un ID, pero escribieron un nombre nuevo en el input
    if not p_id and data.proveedor_nombre_nuevo:
        # Lo buscamos o creamos diciéndole que es un GASTO
        proveedor_obj = buscar_o_crear(db, data.proveedor_nombre_nuevo.strip(), contexto="gasto")
        p_id = proveedor_obj.id if proveedor_obj else None

    # 2. Creamos la instancia del modelo
    nuevo_gasto = Gasto(
        concepto=data.concepto,
        categoria=data.categoria,
        monto=data.monto,
        metodo_pago=data.metodo_pago,
        fecha=data.fecha or datetime.utcnow(),
        notas=data.notas,
        proveedor_id=p_id  # ✨ 3. Asignamos el ID (ya sea el que mandó Angular o el nuevo)
    )
    
    # Guardamos en base de datos
    db.add(nuevo_gasto)
    db.commit()
    db.refresh(nuevo_gasto)

    # ✨ AUDITORÍA: Registro de gasto
    registrar_log(
        db, accion="CREAR", entidad_tipo="GASTO", entidad_id=nuevo_gasto.id,
        valor_nuevo={"concepto": nuevo_gasto.concepto, "monto": nuevo_gasto.monto},
        notas=f"Gasto de {nuevo_gasto.monto}€ registrado."
    )

    return nuevo_gasto



def obtener_gasto_por_id(db: Session, gasto_id: int):
    # Usamos joinedload para que devuelva también la info del proveedor
    gasto = db.query(Gasto).options(joinedload(Gasto.proveedor)).filter(Gasto.id == gasto_id).first()
    
    if not gasto:
        return None
        
    return {
        "id": gasto.id,
        "concepto": gasto.concepto,
        "categoria": gasto.categoria,
        "monto": gasto.monto,
        "metodo_pago": gasto.metodo_pago,
        "fecha": gasto.fecha.isoformat() if gasto.fecha else None,
        "notas": gasto.notas,
        "proveedor_id": gasto.proveedor_id,
        "proveedor": {"id": gasto.proveedor.id, "nombre": gasto.proveedor.nombre_proveedor} if gasto.proveedor else None
    }



# ✨ NUEVO: Función para editar
def editar_gasto(db: Session, gasto_id: int, data: GastoUpdate):
    gasto = db.query(Gasto).filter(Gasto.id == gasto_id).first()
    if not gasto:
        return None

    # Actualizamos los campos si vienen en la petición
    if data.concepto is not None: gasto.concepto = data.concepto
    if data.categoria is not None: gasto.categoria = data.categoria
    if data.monto is not None: gasto.monto = data.monto
    if data.metodo_pago is not None: gasto.metodo_pago = data.metodo_pago
    if data.notas is not None: gasto.notas = data.notas
    if data.fecha is not None: gasto.fecha = data.fecha

    # 🧠 Lógica inteligente de proveedor
    if data.proveedor_id:
        gasto.proveedor_id = data.proveedor_id
    elif data.proveedor_nombre_nuevo:
        proveedor_obj = buscar_o_crear(db, data.proveedor_nombre_nuevo.strip(), contexto="gasto")
        gasto.proveedor_id = proveedor_obj.id

    db.commit()
    db.refresh(gasto)

    # ✨ AUDITORÍA: Actualización de gasto
    registrar_log(
        db, accion="EDITAR", entidad_tipo="GASTO", entidad_id=gasto.id,
        valor_nuevo={"concepto": gasto.concepto, "monto": gasto.monto},
        notas=f"Gasto {gasto.id} actualizado."
    )

    return gasto


# ✨ ACTUALIZADO: Paginación con filtros
def obtener_gastos_paginados(
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
    query = db.query(Gasto)

    # --- APLICACIÓN DE FILTROS ---
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(or_(
            Gasto.concepto.ilike(term),
            Gasto.notas.ilike(term)
        ))
        
    if categoria:
        query = query.filter(Gasto.categoria == categoria)
        
    if metodo_pago:
        query = query.filter(Gasto.metodo_pago == metodo_pago)
        
    if proveedor_id:
        query = query.filter(Gasto.proveedor_id == proveedor_id)
        
    if fecha_inicio:
        query = query.filter(Gasto.fecha >= fecha_inicio)
        
    if fecha_fin:
        query = query.filter(Gasto.fecha <= f"{fecha_fin} 23:59:59")
    # -----------------------------

    total = query.count()
    gastos = (
        query.options(joinedload(Gasto.proveedor))
        .order_by(desc(Gasto.fecha))
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    resultados = []
    for g in gastos:
        resultados.append({
            "id": g.id,
            "concepto": g.concepto,
            "categoria": g.categoria,
            "monto": g.monto,
            "metodo_pago": g.metodo_pago,
            "fecha": g.fecha.isoformat() if g.fecha else None, # Formato seguro para Angular
            "notas": g.notas,
            "proveedor": {"id": g.proveedor.id, "nombre": g.proveedor.nombre_proveedor} if g.proveedor else None,
            "proveedor_id": g.proveedor_id # Útil para cargar el Select al editar
        })
    
    return {"total": total, "items": resultados}

# def obtener_gastos_paginados(db: Session, page: int = 1, limit: int = 20):
#     offset = (page - 1) * limit
    
#     # Consulta base
#     query = db.query(Gasto)
    
#     # Contamos el total para la paginación
#     total = query.count()
    
#     # Obtenemos los gastos ordenados por los más recientes primero
#     gastos = (
#         query
#         .options(joinedload(Gasto.proveedor)) # ✨ CARGA RÁPIDA: Trae los datos del proveedor para mostrar el nombre en el frontend
#         .order_by(desc(Gasto.fecha))
#         .offset(offset)
#         .limit(limit)
#         .all()
#     )
    
#     # Construimos la respuesta asegurando que el Frontend reciba el nombre del proveedor
#     resultados = []
#     for g in gastos:
#         resultados.append({
#             "id": g.id,
#             "concepto": g.concepto,
#             "categoria": g.categoria,
#             "monto": g.monto,
#             "metodo_pago": g.metodo_pago,
#             "fecha": g.fecha,
#             "notas": g.notas,
#             # ✨ Devolvemos el objeto proveedor estructurado
#             "proveedor": {"id": g.proveedor.id, "nombre": g.proveedor.nombre_proveedor} if g.proveedor else None
#         })
    
#     return {"total": total, "items": resultados}
