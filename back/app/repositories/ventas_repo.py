# ventas_repo.py
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload, selectinload
from fastapi import HTTPException
from datetime import datetime
from sqlalchemy import or_, and_, desc, func
import random
import string

from app.models.ventas_model import Venta, DetalleVenta
from app.models.lotes_model import StockConfig, StockUnit
from app.models.variantes_model import Variante
from app.models.producto_model import Producto
from app.models.marcas_model import Marca
from app.models.categorias_model import Categoria
from app.models.clientes_model import Cliente
from app.models.gastos_model import Gasto
from app.schemas.ventas_schema import VentaCreate
from app.services.cliente_services import procesar_cliente_omnicanal
from app.repositories.auditoria_repo import registrar_log

def contar_compras_cliente(db: Session, identificador: str):
    identificador = identificador.strip()
    cliente = db.query(Cliente).filter(
        or_(
            Cliente.email.ilike(identificador),
            Cliente.telefono.ilike(identificador),
            Cliente.usuario_vinted.ilike(identificador.replace("@", "")),
            Cliente.usuario_wallapop.ilike(identificador.replace("@", "")),
            Cliente.dni_nie.ilike(identificador)
        )
    ).first()

    if not cliente:
        return 0
    
    total = db.query(func.count(Venta.id)).filter(Venta.cliente_id == cliente.id).scalar()
    return total

def generar_codigo_venta(db: Session) -> str:
    while True:
        fecha_str = datetime.utcnow().strftime("%y%m%d")
        rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        codigo_candidato = f"VEN-{fecha_str}-{rand}"
        if not db.query(Venta).filter(Venta.codigo_venta == codigo_candidato).first():
            return codigo_candidato

def registrar_venta(db: Session, data: VentaCreate):
    try:
        subtotal = sum(d.precio_unitario for d in data.detalles)
        total_final = (subtotal + (data.costo_envio or 0)) - (data.descuento_total or 0)

        nombre_real_estricto = data.nombre_cliente.strip() if data.nombre_cliente and data.nombre_cliente.strip() else None
        cliente_id = procesar_cliente_omnicanal(db=db, data=data)

        nueva_venta = Venta(
            codigo_venta=generar_codigo_venta(db),
            fecha=data.fecha or datetime.utcnow(),
            canal=data.canal,
            vendedor=data.vendedor,
            metodo_pago=data.metodo_pago,
            estado_venta=data.estado_venta or "abierta",
            estado_pago=data.estado_pago,
            estado_envio=data.estado_envio or "pendiente_envio",
            cliente_id=cliente_id,
            nombre_cliente=nombre_real_estricto,
            email_cliente=data.email_cliente,
            subtotal=subtotal,
            costo_envio=data.costo_envio,
            descuento_total=data.descuento_total,
            total=total_final,
            transaccion_id_externo=data.transaccion_id_externo,
            numero_seguimiento=data.numero_seguimiento,
            empresa_transporte=data.empresa_transporte,
            etiqueta_url=data.etiqueta_url,
            etiqueta_imprimida=data.etiqueta_imprimida
        )
        
        db.add(nueva_venta)
        db.flush() 
        
        for item in data.detalles:
            unidad_db = db.query(StockUnit).filter(StockUnit.id == item.stock_id).with_for_update().first()
            
            if not unidad_db:
                raise HTTPException(status_code=404, detail=f"Ítem físico ID {item.stock_id} no existe.")

            if unidad_db.estado_gestion != 'en_stock':
                raise HTTPException(status_code=400, detail=f"La prenda #{unidad_db.id} no está disponible. Estado actual: {unidad_db.estado_gestion}")

            unidad_db.estado_gestion = 'vendido'
            unidad_db.publicar_web = False
            unidad_db.publicar_vinted = False
            unidad_db.publicar_wallapop = False

            nuevo_detalle = DetalleVenta(
                venta_id=nueva_venta.id,
                stock_unit_id=unidad_db.id, 
                precio_unitario_en_venta=item.precio_unitario,
                precio_compra_snapshot=float(unidad_db.stock_config.precio_compra or 0.0), 
                nombre_producto_snapshot=unidad_db.stock_config.variante.producto.nombre, 
                talla_snapshot=unidad_db.stock_config.etiqueta, 
                color_snapshot=unidad_db.stock_config.variante.identidad_variante,
                devuelto=False
            )
            db.add(nuevo_detalle)

        db.commit()
        db.refresh(nueva_venta)

        registrar_log(
            db, accion="VENDER", entidad_tipo="VENTA", entidad_id=nueva_venta.id,
            nombre_usuario=nueva_venta.vendedor,
            valor_nuevo={"total": nueva_venta.total, "codigo": nueva_venta.codigo_venta, "canal": nueva_venta.canal},
            notas=f"Venta registrada por {nueva_venta.total}€ a través de {nueva_venta.canal}."
        )

        return nueva_venta

    except Exception as e:
        db.rollback() 
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=f"Error al registrar la venta: {str(e)}")

def actualizar_venta(db: Session, venta_id: int, datos: dict):
    venta = db.query(Venta).filter(Venta.id == venta_id).first()
    if not venta: 
        raise HTTPException(status_code=404, detail="Venta no encontrada.")

    # 🛡️ Protección financiera
    quiere_revertir_pago = (datos.get("estado_pago") and datos["estado_pago"] != "pagado" and venta.estado_pago == "pagado")
    nuevo_est_pago = datos.get("estado_pago", venta.estado_pago)
    nuevo_est_envio = datos.get("estado_envio", venta.estado_envio)
    es_anulacion_entrante = (nuevo_est_pago == "reembolsado" or nuevo_est_envio in ["cancelado", "devuelto"])
    quiere_cancelar = es_anulacion_entrante and not (venta.estado_pago == "reembolsado" or venta.estado_envio in ["cancelado", "devuelto"])
    
    if quiere_revertir_pago or quiere_cancelar:
        for detalle in venta.detalles:
            if detalle.stock_unit and detalle.stock_unit.pago_consignacion_id is not None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Operación denegada. La prenda #{detalle.stock_unit_id} ya ha sido liquidada al dueño de la prenda. Por seguridad, anula primero el pago en Consignación."
                )

    total_anterior = venta.total
    estado_pago_anterior = venta.estado_pago
    estado_envio_anterior = venta.estado_envio

    for key, value in datos.items():
        if hasattr(venta, key):
            if key == "estado_venta": continue # Obsoleto
            if key in ["total", "subtotal", "costo_envio", "descuento_total", "monto_reembolsado"] and value is not None:
                setattr(venta, key, round(float(value), 2))
            else:
                setattr(venta, key, value)

    ahora = datetime.utcnow()
    es_anulacion_actual = (venta.estado_pago == "reembolsado" or venta.estado_envio in ["cancelado", "devuelto"])
    fue_anulacion = (estado_pago_anterior == "reembolsado" or estado_envio_anterior in ["cancelado", "devuelto"])

    # ✨ AUTOMATIZACIÓN FINANCIERA: Si se anula la venta, se fuerza el reembolso
    if es_anulacion_actual and not fue_anulacion:
        venta.estado_pago = "reembolsado"
        venta.monto_reembolsado = venta.total

    # Fechas hitos
    if venta.estado_pago == "pagado" and estado_pago_anterior != "pagado":
        if not venta.fecha_pago: venta.fecha_pago = ahora
    if venta.estado_envio in ["enviado", "entregado", "completado"] and estado_envio_anterior not in ["enviado", "entregado", "completado"]:
        if not venta.fecha_envio: venta.fecha_envio = ahora
    if venta.estado_envio in ["entregado", "completado"] and estado_envio_anterior not in ["entregado", "completado"]:
        if not venta.fecha_entrega: venta.fecha_entrega = ahora
    if venta.estado_envio == "completado" and estado_envio_anterior != "completado":
        if not venta.fecha_finalizado: venta.fecha_finalizado = ahora

    # Gestión automática de stock (Anulación total o Devolución)
    if es_anulacion_actual and not fue_anulacion:
        if venta.estado_envio == "cancelado":
            venta.fecha_cancelado = ahora
        for detalle in venta.detalles:
            if not detalle.devuelto:
                detalle.devuelto = True
                unidad_db = db.query(StockUnit).filter(StockUnit.id == detalle.stock_unit_id).first()
                if unidad_db:
                    unidad_db.estado_gestion = 'en_stock'
                    unidad_db.activo = True
    elif not es_anulacion_actual and fue_anulacion:
        for detalle in venta.detalles:
            if detalle.devuelto:
                detalle.devuelto = False
                unidad_db = db.query(StockUnit).filter(StockUnit.id == detalle.stock_unit_id).with_for_update().first()
                if unidad_db:
                    if unidad_db.estado_gestion != 'en_stock':
                        db.rollback()
                        raise HTTPException(status_code=400, detail=f"La unidad #{unidad_db.id} ya no está disponible.")
                    unidad_db.estado_gestion = 'vendido'

    # Sincronización de estados logísticos granulares a los items
    if venta.estado_envio != estado_envio_anterior:
        if venta.estado_envio == 'en_devolucion':
            for detalle in venta.detalles:
                detalle.devuelto = True
                unidad_db = db.query(StockUnit).filter(StockUnit.id == detalle.stock_unit_id).first()
                if unidad_db:
                    unidad_db.estado_gestion = 'en_camino_devolucion'
                    unidad_db.activo = True
        elif venta.estado_envio in ['extraviado_envio', 'extraviado_devolucion']:
            for detalle in venta.detalles:
                detalle.devuelto = False # Se cobra
                unidad_db = db.query(StockUnit).filter(StockUnit.id == detalle.stock_unit_id).first()
                if unidad_db:
                    unidad_db.estado_gestion = 'extraviado'

    # Registro de gasto por compensación si hay monto_reembolsado manual
    if float(venta.monto_reembolsado or 0) > 0 and not es_anulacion_actual:
        concepto_gasto = f"Compensación Allsys Venta {venta.codigo_venta}"
        gasto_existente = db.query(Gasto).filter(Gasto.concepto.like(f"%{concepto_gasto}%")).first()
        if not gasto_existente:
            db.add(Gasto(
                concepto=concepto_gasto, categoria="Devoluciones y Reembolsos",
                monto=float(venta.monto_reembolsado), metodo_pago=venta.metodo_pago,
                fecha=ahora, notas="Error asumido por la tienda Allsys. El dueño de la prenda NO se ve afectado."
            ))

    try:
        db.commit()
        db.refresh(venta)
        registrar_log(
            db, accion="EDITAR", entidad_tipo="VENTA", entidad_id=venta.id,
            valor_nuevo={"total": venta.total, "estado_pago": venta.estado_pago, "estado_envio": venta.estado_envio}
        )
        return {"venta": venta, "mensaje": "Venta actualizada correctamente."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

def obtener_ventas_paginadas(
    db: Session, page: int = 1, limit: int = 10,
    search_producto: Optional[str] = None, tipo_busqueda_prod: Optional[str] = "sku",
    search_codigo: Optional[str] = None,
    search_cliente: Optional[str] = None, tipo_busqueda_cliente: Optional[str] = "nombre",
    cliente_id: Optional[int] = None,
    estado_pago: Optional[str] = None,
    estado_envio: Optional[str] = None,
    canal: Optional[str] = None,
    fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None,
    tipo_fecha: str = "creacion",
    vendedor: Optional[str] = None, marca_id: Optional[int] = None, categoria_id: Optional[int] = None,
    include_details: bool = False, solo_online: bool = False,
    estado_venta: Optional[str] = None,
    localizacion_id: Optional[int] = None # ✨ NUEVO
):
    offset = (page - 1) * limit
    query = db.query(Venta).options(
        selectinload(Venta.cliente),
        selectinload(Venta.detalles).selectinload(DetalleVenta.stock_unit).selectinload(StockUnit.stock_config).selectinload(StockConfig.variante).selectinload(Variante.imagenes),
        selectinload(Venta.detalles).selectinload(DetalleVenta.stock_unit).selectinload(StockUnit.stock_config).selectinload(StockConfig.localizacion)
    )

    if solo_online:
        query = query.filter(Venta.canal != 'tienda_fisica')
    if search_codigo:
        query = query.filter(Venta.codigo_venta.ilike(f"%{search_codigo.strip()}%"))

    # ✨ FILTRO POR LOCALIZACIÓN (Si alguna prenda de la venta es de esa sede)
    if localizacion_id:
        query = query.filter(Venta.detalles.any(DetalleVenta.stock_unit.has(StockUnit.stock_config.has(StockConfig.localizacion_id == localizacion_id))))

    if search_cliente:
        term = f"%{search_cliente.strip()}%"
        if tipo_busqueda_cliente == "nombre": query = query.filter(Venta.nombre_cliente.ilike(term))
        elif tipo_busqueda_cliente == "email": query = query.filter(Venta.email_cliente.ilike(term))
        else: query = query.filter(or_(Venta.nombre_cliente.ilike(term), Venta.email_cliente.ilike(term)))

    if cliente_id: query = query.filter(Venta.cliente_id == cliente_id)
    if estado_pago: query = query.filter(Venta.estado_pago == estado_pago)
    if estado_envio: query = query.filter(Venta.estado_envio == estado_envio)

    if estado_venta: # Mapeo legado para compatibilidad UI
        if estado_venta == 'cancelada': query = query.filter(or_(Venta.estado_pago == 'reembolsado', Venta.estado_envio == 'cancelado'))
        elif estado_venta == 'devuelta': query = query.filter(or_(Venta.estado_pago == 'reembolso_parcial', Venta.estado_envio.in_(['devuelto', 'en_devolucion', 'extraviado_devolucion'])))
        elif estado_venta == 'completada': query = query.filter(Venta.estado_pago == 'pagado', Venta.estado_envio.in_(['entregado', 'completado', 'extraviado_envio']))

    if canal: query = query.filter(Venta.canal == canal)
    if vendedor: query = query.filter(Venta.vendedor == vendedor)

    col_fecha = Venta.fecha
    if tipo_fecha == "envio": col_fecha = Venta.fecha_envio
    elif tipo_fecha == "entrega": col_fecha = Venta.fecha_entrega
    elif tipo_fecha == "cancelado": col_fecha = Venta.fecha_cancelado

    if fecha_inicio: query = query.filter(col_fecha >= fecha_inicio)
    if fecha_fin: query = query.filter(col_fecha <= f"{fecha_fin} 23:59:59")

    if search_producto or marca_id or categoria_id:
        query = query.join(DetalleVenta).join(StockUnit).join(StockConfig).join(Variante).join(Producto)
        if search_producto:
            term = search_producto.strip()
            if tipo_busqueda_prod == "sku": query = query.filter(StockUnit.sku.ilike(f"%{term}%"))
            elif term.isdigit(): query = query.filter(or_(StockUnit.id == int(term), Producto.id == int(term)))

    total = query.distinct().count()
    subq = query.distinct().subquery()
    
    # Cálculos financieros excluyendo anulaciones (NULL-safe)
    is_valid = and_(Venta.estado_envio != 'cancelado', Venta.estado_pago != 'reembolsado')
    
    suma_recaudado = db.query(func.sum(Venta.total)).filter(Venta.id.in_(db.query(subq.c.id)), is_valid).scalar() or 0.0
    suma_subtotal = db.query(func.sum(Venta.subtotal)).filter(Venta.id.in_(db.query(subq.c.id)), is_valid).scalar() or 0.0
    
    # Costo de compra real (Excluyendo ítems devueltos)
    costo_compra = db.query(func.sum(func.coalesce(DetalleVenta.precio_compra_snapshot, 0) * DetalleVenta.cantidad))\
        .join(Venta).filter(
            Venta.id.in_(db.query(subq.c.id)), 
            Venta.estado_envio != 'cancelado', 
            Venta.estado_pago != 'reembolsado',
            DetalleVenta.devuelto == False
        ).scalar() or 0.0
    
    ventas = query.distinct().order_by(desc(Venta.fecha)).offset(offset).limit(limit).all()
    
    items_res = []
    for v in ventas:
        resumen = []
        img_cover = None
        detalles_full = []
        for d in v.detalles:
            item_img = None
            try:
                if d.stock_unit and d.stock_unit.stock_config.variante.imagenes:
                    item_img = sorted(d.stock_unit.stock_config.variante.imagenes, key=lambda x: x.orden or 0)[0].url
                    if not img_cover: img_cover = item_img
            except: pass
            resumen.append(f"{d.nombre_producto_snapshot}")
            if include_details:
                detalles_full.append({
                    "id": d.id, "stock_unit_id": d.stock_unit_id, "sku": d.stock_unit.sku if d.stock_unit else None,
                    "nombre_producto": d.nombre_producto_snapshot, "talla": d.talla_snapshot, "precio_unitario": float(d.precio_unitario_en_venta),
                    "imagen_cover": item_img, "devuelto": d.devuelto
                })
        
        nombre_comprador = v.nombre_cliente or (v.cliente.nombre if v.cliente else "Anónimo")
        items_res.append({
            "id": v.id, "codigo_venta": v.codigo_venta, "fecha": v.fecha.isoformat(),
            "nombre_cliente": nombre_comprador, "email_cliente": v.email_cliente,
            "identificador_cliente": v.cliente.usuario_vinted or v.cliente.telefono if v.cliente else "",
            "pais": v.cliente.pais if v.cliente else "", "canal": v.canal, "metodo_pago": v.metodo_pago,
            "estado_venta": v.estado_venta,
            "estado_pago": v.estado_pago, "estado_envio": v.estado_envio, "total": float(v.total),
            "resumen_productos": ", ".join(resumen), "imagen_cover": img_cover, "detalles": detalles_full if include_details else None
        })

    return {"total": total, "suma_recaudado": float(suma_recaudado), "suma_beneficio": float(suma_subtotal - costo_compra), "items": items_res}

def registrar_devolucion_fisica_item(db: Session, venta_id: int, detalle_id: int, estado_stock: str = 'en_stock'):
    venta = db.query(Venta).filter(Venta.id == venta_id).first()
    detalle = db.query(DetalleVenta).filter(DetalleVenta.id == detalle_id, DetalleVenta.venta_id == venta_id).first()
    if not venta or not detalle: raise HTTPException(status_code=404, detail="No encontrado")
    if detalle.devuelto: raise HTTPException(status_code=400, detail="Ya devuelto")

    # ✨ SEGURIDAD CONTABLE: Bloquear retorno si la prenda ya fue pagada a su dueño
    if detalle.stock_unit and detalle.stock_unit.pago_consignacion_id is not None:
        raise HTTPException(
            status_code=400, 
            detail=f"Operación denegada. La prenda #{detalle.stock_unit_id} ya ha sido liquidada al dueño. Ve a Consignación y anula o quita la prenda de ese pago antes de devolverla al stock."
        )

    if detalle.stock_unit:
        detalle.stock_unit.estado_gestion = estado_stock
        detalle.stock_unit.activo = True
        # ✨ SEGURIDAD: Si está volviendo, no debe estar publicado
        if estado_stock == 'en_camino_devolucion':
            detalle.stock_unit.publicar_web = False
            detalle.stock_unit.publicar_vinted = False
            detalle.stock_unit.publicar_wallapop = False

    detalle.devuelto = True
    monto = float(detalle.precio_unitario_en_venta)
    venta.subtotal = round(venta.subtotal - monto, 2)
    venta.total = round(venta.total - monto, 2)

    if venta.estado_pago == "pagado":
        venta.estado_pago = "reembolso_parcial"
        venta.monto_reembolsado = round(float(venta.monto_reembolsado or 0) + monto, 2)
        # Importamos Gasto localmente para evitar circulares si no está arriba
        from app.models.gastos_model import Gasto
        db.add(Gasto(
            concepto=f"Reembolso devolución #{detalle.stock_unit_id} - Venta {venta.codigo_venta}",
            categoria="Devoluciones y Reembolsos",
            monto=monto, metodo_pago=venta.metodo_pago, fecha=datetime.utcnow(),
            notas=f"Dinero devuelto al cliente. Prenda #{detalle.stock_unit_id} en estado: {estado_stock}."
        ))

    # ✨ LÓGICA DE CANCELACIÓN TOTAL
    # Verificamos si TODOS los ítems de esta venta han sido devueltos.
    todos_devueltos = all(d.devuelto for d in venta.detalles)
    if todos_devueltos:
        venta.estado_venta = "devuelta_totalmente"
        # Si todo se devolvió, el pedido logísticamente se cancela o devuelve entero.
        if estado_stock == 'en_stock':
            pass # Logistics can be managed separately
        elif estado_stock == 'en_camino_devolucion':
            pass
        elif estado_stock == 'extraviado':
            pass

        venta.estado_pago = "reembolsado"
    else:
        venta.estado_venta = "devuelta_parcialmente"

    db.commit()

    registrar_log(
        db, accion="DEVOLUCION_FISICA", entidad_tipo="VENTA", entidad_id=venta_id,
        valor_nuevo={"detalle_id": detalle_id, "estado_prenda": estado_stock},
        notas=f"Devolución del ítem #{detalle_id}. El stock pasa a: {estado_stock}"
    )

    return venta

def resolver_retorno_transito(db: Session, venta_id: int, detalle_id: int, resolucion: str):
    venta = db.query(Venta).filter(Venta.id == venta_id).first()
    detalle = db.query(DetalleVenta).filter(DetalleVenta.id == detalle_id, DetalleVenta.venta_id == venta_id).first()
    if not venta or not detalle: raise HTTPException(status_code=404, detail="No encontrado")
    if not detalle.stock_unit: raise HTTPException(status_code=400, detail="Sin stock físico")

    if resolucion == 'en_stock':
        detalle.stock_unit.estado_gestion = 'en_stock'
        registrar_log(db, "LLEGADA_DEVOLUCION", "VENTA", venta_id, notas=f"El ítem devuelto #{detalle_id} ha llegado al almacén.")
        
    elif resolucion == 'extraviado':
        detalle.stock_unit.estado_gestion = 'extraviado'
        
        # ✨ REVERTIR LA DEVOLUCIÓN: Como se perdió, Vinted paga, así que el dueño cobra.
        detalle.devuelto = False
        monto = float(detalle.precio_unitario_en_venta)
        venta.subtotal = round(venta.subtotal + monto, 2)
        venta.total = round(venta.total + monto, 2)
        
        # Restar del reembolso si lo hubo
        if venta.monto_reembolsado and venta.monto_reembolsado >= monto:
            venta.monto_reembolsado = round(float(venta.monto_reembolsado) - monto, 2)
            if venta.monto_reembolsado == 0:
                venta.estado_pago = "pagado"
        
        # Eliminar el gasto que se creó automáticamente por la devolución
        from app.models.gastos_model import Gasto
        gasto = db.query(Gasto).filter(Gasto.concepto.like(f"%Reembolso devolución #{detalle.stock_unit_id}%")).first()
        if gasto:
            db.delete(gasto)
            
        # Si la venta entera se había cancelado/devuelto, la restauramos a extraviado_devolucion
        if venta.estado_envio in ["cancelado", "devuelto", "en_devolucion"]:
            venta.estado_envio = "extraviado_devolucion"
            venta.estado_pago = "pagado"
            
        registrar_log(db, "EXTRAVIO_DEVOLUCION", "VENTA", venta_id, notas=f"Ítem #{detalle_id} extraviado en transporte. Se revierte la devolución en factura para que el dueño cobre.")

    db.commit()
    return venta

def registrar_compensacion_allsys(db: Session, venta_id: int, monto: float, motivo: str):
    venta = db.query(Venta).filter(Venta.id == venta_id).first()
    if not venta: raise HTTPException(status_code=404, detail="No encontrada")
    
    monto = round(float(monto), 2)
    venta.monto_reembolsado = round(float(venta.monto_reembolsado or 0) + monto, 2)
    db.add(Gasto(
        concepto=f"Compensación Allsys {venta.codigo_venta}: {motivo}", categoria="Devoluciones y Reembolsos",
        monto=monto, metodo_pago=venta.metodo_pago, fecha=datetime.utcnow(),
        notas="Asumido por la tienda. El dueño de la prenda cobra lo pactado."
    ))
    db.commit()
    return venta

def corregir_precio_item(db: Session, venta_id: int, detalle_id: int, nuevo_precio: float):
    venta = db.query(Venta).filter(Venta.id == venta_id).first()
    detalle = db.query(DetalleVenta).filter(DetalleVenta.id == detalle_id, DetalleVenta.venta_id == venta_id).first()
    if not venta or not detalle: raise HTTPException(status_code=404, detail="No encontrado")
    if detalle.devuelto: raise HTTPException(status_code=400, detail="No se puede cambiar el precio de un ítem devuelto")
    
    if detalle.stock_unit and detalle.stock_unit.pago_consignacion_id is not None:
        raise HTTPException(status_code=400, detail="El ítem ya fue liquidado al dueño.")

    nuevo_precio = round(float(nuevo_precio), 2)
    if nuevo_precio < 0: raise HTTPException(status_code=400, detail="El precio no puede ser negativo")

    precio_anterior = float(detalle.precio_unitario_en_venta)
    diferencia = nuevo_precio - precio_anterior

    detalle.precio_unitario_en_venta = nuevo_precio
    venta.subtotal = round(venta.subtotal + diferencia, 2)
    venta.total = round(venta.total + diferencia, 2)

    db.commit()
    db.refresh(venta)
    return venta

def obtener_venta_por_id(db: Session, venta_id: int):
    venta = db.query(Venta).options(joinedload(Venta.cliente), joinedload(Venta.detalles)).filter(Venta.id == venta_id).first()
    if not venta: return None
    df = []
    for d in venta.detalles:
        img = None
        estado_gestion = "vendido"
        try:
            if d.stock_unit:
                estado_gestion = d.stock_unit.estado_gestion
                if d.stock_unit.stock_config.variante.imagenes:
                    img = sorted(d.stock_unit.stock_config.variante.imagenes, key=lambda x: x.orden or 0)[0].url
        except: pass
        df.append({
            "id": d.id, "stock_unit_id": d.stock_unit_id, "nombre_producto": d.nombre_producto_snapshot,
            "talla": d.talla_snapshot, "color": d.color_snapshot, "cantidad": d.cantidad,
            "precio_unitario": float(d.precio_unitario_en_venta), "imagen_cover": img,
            "pago_consignacion_id": d.stock_unit.pago_consignacion_id if d.stock_unit else None,
            "devuelto": d.devuelto,
            "estado_gestion": estado_gestion, # ✨ AÑADIDO PARA SEGUIMIENTO
            "stock_config_id": d.stock_unit.stock_config_id if d.stock_unit else None 
        })
    # ✨ AÑADIDO: Obtener ajustes financieros/compensaciones ligados a esta venta
    gastos_relacionados = db.query(Gasto).filter(Gasto.concepto.ilike(f"%{venta.codigo_venta}%")).all()
    ajustes = []
    for g in gastos_relacionados:
        ajustes.append({
            "id": g.id,
            "concepto": g.concepto,
            "monto": float(g.monto),
            "fecha": g.fecha.isoformat() if g.fecha else None,
            "notas": g.notas
        })

    return {
        "id": venta.id, "codigo_venta": venta.codigo_venta, "fecha": venta.fecha.isoformat(),
        "canal": venta.canal, "vendedor": venta.vendedor, "metodo_pago": venta.metodo_pago,
        "estado_venta": venta.estado_venta,
        "estado_pago": venta.estado_pago, "estado_envio": venta.estado_envio, "total": float(venta.total),
        "monto_reembolsado": float(venta.monto_reembolsado or 0), "detalles": df,
        "ajustes_financieros": ajustes, # ✨ PASAMOS LOS AJUSTES AL FRONTEND
        "cliente": {
            "id": venta.cliente.id, "nombre": venta.cliente.nombre, "email": venta.cliente.email,
            "telefono": venta.cliente.telefono, "usuario_vinted": venta.cliente.usuario_vinted,
            "usuario_wallapop": venta.cliente.usuario_wallapop, "dni_nie": venta.cliente.dni_nie
        } if venta.cliente else None,
        "email_cliente": venta.email_cliente, "nombre_cliente": venta.nombre_cliente,
        "subtotal": float(venta.subtotal), "costo_envio": float(venta.costo_envio or 0),
        "descuento_total": float(venta.descuento_total or 0)
    }

def obtener_pedidos_pendientes_logistica(
    db: Session, page: int = 1, limit: int = 10,
    search: Optional[str] = None, tipo_busqueda: str = 'general', filtro_estado: str = 'preparacion',
    localizacion_id: Optional[int] = None # ✨ NUEVO
):
    query = db.query(Venta).filter(Venta.canal != 'tienda_fisica')
    
    # ✨ FILTRO POR SEDE
    if localizacion_id:
        query = query.filter(Venta.detalles.any(DetalleVenta.stock_unit.has(StockUnit.stock_config.has(StockConfig.localizacion_id == localizacion_id))))

    if search:
        term = search.strip()
        if tipo_busqueda == 'stock_unit_id' and term.isdigit():
            query = query.filter(Venta.detalles.any(DetalleVenta.stock_unit_id == int(term)))
        elif tipo_busqueda == 'codigo_venta':
            query = query.filter(Venta.codigo_venta.ilike(f"%{term}%"))
        else:
            query = query.filter(or_(Venta.codigo_venta.ilike(f"%{term}%"), Venta.nombre_cliente.ilike(f"%{term}%")))

    if filtro_estado == 'preparacion':
        query = query.filter(or_(Venta.estado_envio.in_(['pendiente_envio', 'empaquetado', 'listo_envio']), Venta.estado_envio.is_(None)))
    elif filtro_estado != 'todos':
        query = query.filter(Venta.estado_envio == filtro_estado)

    total = query.count()
    ventas_pendientes = query.order_by(Venta.fecha.asc()).offset((page - 1) * limit).limit(limit).all()

    resultados = []
    for v in ventas_pendientes:
        items = []
        for d in v.detalles:
            item_img = None
            loc_nombre = "Sin asignar"
            estado_gestion = "vendido"
            color_nombre = "N/A"
            color_hex = "#FFFFFF"

            try:
                if d.stock_unit:
                    estado_gestion = d.stock_unit.estado_gestion
                    variante = d.stock_unit.stock_config.variante
                    color_nombre = variante.identidad_variante
                    color_hex = variante.hex_identidad

                    if variante.imagenes:
                        item_img = sorted(variante.imagenes, key=lambda x: x.orden or 0)[0].url
                    if d.stock_unit.stock_config.localizacion:
                        loc_nombre = d.stock_unit.stock_config.localizacion.nombre
            except: pass

            items.append({
                "detalle_id": d.id, "stock_unit_id": d.stock_unit_id, 
                "nombre_producto": d.nombre_producto_snapshot, "talla": d.talla_snapshot, 
                "color": color_nombre, "color_hex": color_hex,
                "cantidad": d.cantidad, "imagen_cover": item_img,
                "pago_consignacion_id": d.stock_unit.pago_consignacion_id if d.stock_unit else None,
                "localizacion": loc_nombre,
                "estado_gestion": estado_gestion # ✨ PARA INDICAR DEVOLUCIONES
            })
        resultados.append({
            "id": v.id, "codigo_venta": v.codigo_venta, "fecha": v.fecha.isoformat(),
            "canal": v.canal, "comprador": v.nombre_cliente or "Desconocido",
            "estado_envio": v.estado_envio, "etiqueta_url": v.etiqueta_url, "items": items
        })
    return {"total": total, "items": resultados}

def cambiar_id_item_venta(db: Session, venta_id: int, detalle_id: int, nuevo_stock_id: int):
    detalle = db.query(DetalleVenta).filter(DetalleVenta.id == detalle_id, DetalleVenta.venta_id == venta_id).first()
    if not detalle: raise HTTPException(status_code=404, detail="Ítem no encontrado")
    
    nueva_unidad = db.query(StockUnit).filter(StockUnit.id == nuevo_stock_id).first()
    if not nueva_unidad or nueva_unidad.estado_gestion != 'en_stock':
        raise HTTPException(status_code=400, detail="Unidad no disponible")

    old_id = detalle.stock_unit_id
    db.query(StockUnit).filter(StockUnit.id == old_id).update({"estado_gestion": "en_stock"})
    detalle.stock_unit_id = nuevo_stock_id
    nueva_unidad.estado_gestion = "vendido"
    
    db.commit()
    return {"mensaje": f"Trueque exitoso: {old_id} por {nuevo_stock_id}"}
