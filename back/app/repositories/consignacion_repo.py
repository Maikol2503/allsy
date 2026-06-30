# consignacion_repo.py
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from sqlalchemy import or_, desc, func
from sqlalchemy.orm import joinedload, selectinload

from app.models.ventas_model import Venta, DetalleVenta
# ✨ IMPORTACIONES ACTUALIZADAS
from app.models.lotes_model import StockConfig, StockUnit
from app.models.variantes_model import Variante
from app.models.producto_model import Producto
from app.models.clientes_model import Cliente
from app.models.egresos_model import Egreso
from app.models.pagos_consignacion_model import PagoConsignacion
from app.schemas.ventas_schema import VentaCreate
from app.schemas.consignacion_schema import PagoCreate
from app.services.cliente_services import procesar_cliente_omnicanal
from app.repositories.auditoria_repo import registrar_log
import random
import string

# =====================================================
# 🧠 CEREBRO FINANCIERO: CÁLCULO DE COMISIONES
# =====================================================
def calcular_desglose_venta(
    precio_venta: float, 
    exento_tarifa_fija: bool = False,
    exento_comision: bool = False,
    donar_ganancias: bool = False
) -> dict:
    if donar_ganancias:
        return {
            "precio_venta": float(precio_venta),
            "tarifa_fija": 0.0,
            "porcentaje_aplicado": 100,
            "comision_porcentaje_eur": float(precio_venta),
            "comision_total_allsys": float(precio_venta),
            "pago_cliente": 0.0
        }

    tarifa_fija = 0.0 if exento_tarifa_fija else 1.50
    
    if exento_comision:
        porcentaje = 0.0
    elif precio_venta <= 15.00:
        porcentaje = 0.30
    elif precio_venta <= 50.00:
        porcentaje = 0.25
    else:
        porcentaje = 0.15

    comision_porcentaje_eur = precio_venta * porcentaje
    comision_total_allsys = tarifa_fija + comision_porcentaje_eur
    pago_cliente = max(0.0, precio_venta - comision_total_allsys)
    
    return {
        "precio_venta": float(precio_venta),
        "tarifa_fija": float(tarifa_fija),
        "porcentaje_aplicado": int(porcentaje * 100), 
        "comision_porcentaje_eur": float(comision_porcentaje_eur),
        "comision_total_allsys": float(comision_total_allsys),
        "pago_cliente": float(pago_cliente)
    }

# =====================================================
# 📊 ESTADÍSTICAS GLOBALES DEL CLIENTE
# =====================================================
def obtener_estadisticas_cliente(db: Session, cliente_id: int):
    cliente_db = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente_db:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
    exento_tarifa_fija = getattr(cliente_db, 'exento_tarifa_fija', False)
    exento_comision = getattr(cliente_db, 'exento_comision', False)

    # 1. Contadores logísticos básicos de stock (sin tocar ventas)
    unidades_stats = db.query(
        StockUnit.estado_gestion, func.count(StockUnit.id)
    ).join(StockConfig).filter(StockConfig.propietario_id == cliente_id).group_by(StockUnit.estado_gestion).all()
    
    total_entregadas = sum(count for _, count in unidades_stats)
    stats_dict = {estado: count for estado, count in unidades_stats}
    
    stats = {
        "total_prendas_entregadas": total_entregadas,
        "prendas_en_stock": stats_dict.get('en_stock', 0),
        "prendas_devueltas_dueno": stats_dict.get('devuelto_dueno', 0),
        "prendas_donado_a_ong": stats_dict.get('donado_a_ong', 0),
        "prendas_extraviadas": stats_dict.get('extraviado', 0),
        "prendas_procesando": 0,
        "prendas_enviada": 0,
        "prendas_entregado": 0,
        "prendas_completada": 0,
        "prendas_cancelada": 0,
        "prendas_devueltas_tienda": 0,
    }

    # 2. Obtener datos financieros ligeros usando una consulta directa de columnas
    # Esto evita cargar los pesados modelos SQLAlchemy en memoria (N+1 free)
    ventas_data = db.query(
        Venta.estado_envio,
        Venta.estado_pago,
        DetalleVenta.precio_unitario_en_venta,
        DetalleVenta.devuelto, # ✨ NUEVO
        StockConfig.precio_venta,
        StockConfig.donar_ganancias
    ).join(DetalleVenta, Venta.id == DetalleVenta.venta_id)\
     .join(StockUnit, DetalleVenta.stock_unit_id == StockUnit.id)\
     .join(StockConfig, StockUnit.stock_config_id == StockConfig.id)\
     .filter(StockConfig.propietario_id == cliente_id).all()

    dinero_generado_ventas = 0.0
    dinero_para_cliente = 0.0
    ingresos_en_transito = 0.0
    beneficio_plataforma = 0.0
    beneficio_en_transito = 0.0
    saldo_en_transito = 0.0

    for est_envio, est_pago, precio_venta_real, item_devuelto, precio_config, donar in ventas_data:
        # LÓGICA DE VALIDEZ DEDUCIDA
        # Una venta no cuenta para el dueño si el envío se canceló, se reembolsó el pago, 
        # O SI EL ÍTEM ESPECÍFICO FUE DEVUELTO.
        es_invalida = (est_envio in ['cancelado', 'devuelto', 'en_devolucion'] or est_pago == 'reembolsado' or item_devuelto)
        
        # Sumar contadores de estados (Aproximados ahora por estado_envio)
        if est_envio in ["pendiente_envio", "empaquetado", "listo_envio"]: stats["prendas_procesando"] += 1
        elif est_envio == "enviado": stats["prendas_enviada"] += 1
        elif est_envio in ["entregado", "completado", "extraviado_envio", "extraviado_devolucion"]: stats["prendas_entregado"] += 1
        
        if est_envio in ["devuelto", "en_devolucion"]: stats["prendas_devueltas_tienda"] += 1
        
        if es_invalida: stats["prendas_cancelada"] += 1

        # Calcular dinero si la venta es válida (No cancelada ni devuelta)
        if not es_invalida:
            precio_base = float(precio_venta_real or precio_config or 0.0)
            desglose = calcular_desglose_venta(
                precio_base, exento_tarifa_fija=exento_tarifa_fija,
                exento_comision=exento_comision, donar_ganancias=bool(donar)
            )
            
            if est_pago in ["pagado", "reembolso_parcial"]:
                dinero_generado_ventas += precio_base
                dinero_para_cliente += desglose["pago_cliente"]
                beneficio_plataforma += desglose["comision_total_allsys"]
            else:
                ingresos_en_transito += precio_base
                saldo_en_transito += desglose["pago_cliente"]
                beneficio_en_transito += desglose["comision_total_allsys"]

    # 3. Sumar también las prendas EXTRAVIADAS en almacén (no tienen venta, pero se pagan)
    prendas_extraviadas_almacen = db.query(
        StockConfig.precio_venta,
        StockConfig.donar_ganancias
    ).join(StockUnit).filter(
        StockConfig.propietario_id == cliente_id,
        StockUnit.estado_gestion == 'extraviado',
        StockUnit.id.notin_(db.query(DetalleVenta.stock_unit_id)) # Que no estén en una venta (extravío en almacén puro)
    ).all()

    for precio_config, donar in prendas_extraviadas_almacen:
        precio_base = float(precio_config or 0.0) # Si no hay precio, se queda en 0 para revisión manual
        
        # ✨ Allsys asume la pérdida total, el dueño cobra el 100% sin comisiones
        # Allsys NO registra beneficio por comisión ni cuenta esto como "Venta Generada".
        dinero_para_cliente += precio_base

    pagos_realizados = float(db.query(func.sum(PagoConsignacion.monto)).filter(
        PagoConsignacion.cliente_id == cliente_id,
        PagoConsignacion.estado == 'completado'
    ).scalar() or 0.0)

    return {
        **stats,
        "ingresos_en_transito": round(ingresos_en_transito, 2),
        "exento_gastos_gestion": bool(exento_comision and exento_tarifa_fija),
        "deuda_por_devoluciones": 0.0, 
        "dinero_generado_ventas": round(dinero_generado_ventas, 2),
        "dinero_para_cliente": round(dinero_para_cliente, 2),
        "beneficio_plataforma": round(beneficio_plataforma, 2),
        "beneficio_en_transito": round(beneficio_en_transito, 2),
        "dinero_ya_pagado": round(pagos_realizados, 2),
        "saldo_pendiente": round(dinero_para_cliente - pagos_realizados, 2),
        "saldo_en_transito": round(saldo_en_transito, 2)
    }







# =====================================================
# 📋 LISTADO PAGINADO DE PRENDAS
# =====================================================
def listar_prendas_detalle_cliente(db: Session, cliente_id: int, page: int = 1, limit: int = 10, estado_filtro: str = None):
    offset = (page - 1) * limit
    
    query = db.query(StockUnit).join(StockConfig).filter(StockConfig.propietario_id == cliente_id)

    if estado_filtro:
        if estado_filtro == "vendida":
            # Filtrado por validez (No canceladas ni devueltas)
            query = query.join(DetalleVenta).join(Venta).filter(
                Venta.estado_envio != 'cancelado',
                Venta.estado_pago != 'reembolsado'
            )
        elif estado_filtro == "devuelto":
            query = query.join(DetalleVenta).join(Venta).filter(Venta.estado_envio == 'devuelto')
        else:
            query = query.filter(StockUnit.estado_gestion == estado_filtro)

    total_prendas = query.count()
    
    # Carga rápida de relaciones para evitar queries N+1
    unidades = query.options(
        joinedload(StockUnit.stock_config).joinedload(StockConfig.variante).joinedload(Variante.producto),
        joinedload(StockUnit.stock_config).joinedload(StockConfig.variante).joinedload(Variante.imagenes)
    ).offset(offset).limit(limit).all()

    # Pre-cargamos las ventas de estas unidades específicas
    unidad_ids = [u.id for u in unidades]
    ventas_dict = {}
    if unidad_ids:
        # ✨ CORRECCIÓN: Añadido .order_by(Venta.fecha.asc())
        ventas = db.query(DetalleVenta, Venta).join(Venta, DetalleVenta.venta_id == Venta.id).filter(DetalleVenta.stock_unit_id.in_(unidad_ids)).order_by(Venta.fecha.asc()).all()
        ventas_dict = {detalle.stock_unit_id: (detalle, venta) for detalle, venta in ventas}


    cliente_db = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    exento_tarifa_fija = getattr(cliente_db, 'exento_tarifa_fija', False)
    exento_comision = getattr(cliente_db, 'exento_comision', False)

    resultados = []
    for u in unidades:
        config = u.stock_config
        variante = config.variante
        producto = variante.producto
        
        # Obtener la primera imagen si existe
        img_url = None
        if variante.imagenes:
            img_sorted = sorted(variante.imagenes, key=lambda x: x.orden or 0)
            img_url = img_sorted[0].url if img_sorted else None

        # Estructura base requerida por PrendaClienteDetalle
        item_data = {
            "stock_id": u.id,
            "producto_id": producto.id,
            "canal_venta": None,
            "sku": u.sku,
            "nombre_producto": producto.nombre,
            "imagen": img_url,
            "estado": u.estado_gestion,
            "fecha_venta": None,
            "estado_pago": None,
            "monto_reembolsado": 0.0,
            "finanzas": {
                "precio_venta": float(config.precio_venta or 0.0),
                "tarifa_fija": 0.0,
                "porcentaje_aplicado": 0,
                "comision_porcentaje_eur": 0.0,
                "comision_total_allsys": 0.0,
                "pago_cliente": 0.0
            }
        }

        # Si la prenda se vendió, inyectamos los datos reales de la venta
        if u.id in ventas_dict:
            detalle, venta = ventas_dict[u.id]
            item_data["estado"] = venta.estado_envio # ✨ INYECTAR EL ESTADO REAL DE LA VENTA LOGÍSTICA
            item_data["canal_venta"] = venta.canal
            item_data["fecha_venta"] = venta.fecha
            
            # Lógica de estado de pago desde la perspectiva del ítem individual de consignación:
            if detalle.devuelto:
                item_data["estado_pago"] = "reembolsado"
                item_data["monto_reembolsado"] = float(detalle.precio_unitario_en_venta or 0.0)
            elif venta.estado_pago == 'reembolsado':
                item_data["estado_pago"] = "reembolsado"
                item_data["monto_reembolsado"] = float(detalle.precio_unitario_en_venta or 0.0)
            elif venta.estado_pago in ['pagado', 'reembolso_parcial']:
                item_data["estado_pago"] = "pagado"
                item_data["monto_reembolsado"] = 0.0
            else:
                item_data["estado_pago"] = venta.estado_pago
                item_data["monto_reembolsado"] = 0.0

            # Lógica de validez deducida para finanzas
            es_cancelada = (venta.estado_envio == 'cancelado' or venta.estado_pago == 'reembolsado')

            if not es_cancelada:
                desglose = calcular_desglose_venta(
                    float(detalle.precio_unitario_en_venta or config.precio_venta),
                    exento_tarifa_fija=exento_tarifa_fija,
                    exento_comision=exento_comision,
                    donar_ganancias=getattr(config, 'donar_ganancias', False)
                )
                item_data["finanzas"] = desglose
        elif u.estado_gestion == 'extraviado':
            # ✨ Extraviado en almacén sin venta: Cobra el 100% de la indemnización
            item_data["nombre_producto"] = f"{producto.nombre} (Extraviado en Almacén)"
            item_data["finanzas"]["pago_cliente"] = item_data["finanzas"]["precio_venta"]

        resultados.append(item_data)

    # Ahora sí coinciden con el esquema PaginatedPrendas
    return {
        "total": total_prendas, 
        "page": page, 
        "limit": limit, 
        "items": resultados
    }

# =====================================================
# 💸 GESTIÓN DE PAGOS
# =====================================================
def registrar_pago(db: Session, cliente_id: int, data: PagoCreate):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
    stats = obtener_estadisticas_cliente(db, cliente_id)
    saldo_pendiente = stats["saldo_pendiente"]
    monto_pago = round(float(data.monto), 2)
    
    if monto_pago <= 0:
        raise HTTPException(status_code=400, detail="El monto a pagar debe ser mayor a 0.")
        
    if monto_pago > saldo_pendiente:
        raise HTTPException(
            status_code=400, 
            detail=f"Operación denegada. El monto a pagar ({monto_pago}€) supera el saldo pendiente real del cliente ({saldo_pendiente}€)."
        )
        
    nuevo_pago = PagoConsignacion(
        cliente_id=cliente_id,
        monto=monto_pago,
        metodo_pago=data.metodo_pago,
        referencia=data.referencia,
        notas=data.notas
    )
    db.add(nuevo_pago)
    db.flush() # Para obtener el ID del pago antes del commit

    # ✨ VINCULACIÓN DE PRENDAS (Trazabilidad)
    if data.stock_unit_ids:
        # Buscamos las prendas que pertenecen al cliente y están marcadas como vendidas o extraviadas
        prendas = db.query(StockUnit).join(StockConfig).filter(
            StockUnit.id.in_(data.stock_unit_ids),
            StockConfig.propietario_id == cliente_id
        ).all()
        
        monto_extraviado = 0.0

        for p in prendas:
            p.pago_consignacion_id = nuevo_pago.id
            if p.estado_gestion == 'extraviado':
                precio_base = float(p.stock_config.precio_venta or 0.0)
                # ✨ Allsys asume la pérdida total, el dueño cobra el 100% sin comisiones
                monto_extraviado += precio_base

        if monto_extraviado > 0:
            db.add(Egreso(
                concepto=f"Compensación por prendas extraviadas en almacén (Pago Consignación #{nuevo_pago.id})",
                categoria="Pérdidas y Mermas",
                monto=round(monto_extraviado, 2),
                metodo_pago=nuevo_pago.metodo_pago,
                fecha=datetime.utcnow(),
                notas=f"Pago al cliente #{cliente_id} por prendas perdidas físicamente en el almacén."
            ))

    db.commit()
    db.refresh(nuevo_pago)

    # ✨ AUDITORÍA: Registro de pago a dueño
    registrar_log(
        db, accion="PAGAR", entidad_tipo="PAGO_CONSIGNACION", entidad_id=nuevo_pago.id,
        valor_nuevo={"monto": nuevo_pago.monto, "metodo": nuevo_pago.metodo_pago, "cliente_id": cliente_id},
        notas=f"Pago de {nuevo_pago.monto}€ liquidado al cliente #{cliente_id}."
    )

    return nuevo_pago

def obtener_prendas_pendientes_pago(db: Session, cliente_id: int):
    """
    Retorna todas las prendas vendidas de un cliente que aún NO han sido pagadas.
    Útil para el desglose en el formulario de pago de consignación.
    """
    # 1. Obtenemos las prendas del cliente en estados válidos (vendido o extraviado en almacén) que no tengan pago asociado
    query = db.query(StockUnit).join(StockConfig).filter(
        StockConfig.propietario_id == cliente_id,
        StockUnit.estado_gestion.in_(['vendido', 'extraviado']),
        StockUnit.pago_consignacion_id.is_(None)
    )

    unidades = query.options(
        joinedload(StockUnit.stock_config).joinedload(StockConfig.variante).joinedload(Variante.producto),
        joinedload(StockUnit.stock_config).joinedload(StockConfig.variante).joinedload(Variante.imagenes)
    ).all()

    # Pre-cargamos las ventas para calcular el desglose financiero
    unidad_ids = [u.id for u in unidades]
    todas_ventas_dict = {}
    ventas_pagadas_dict = {}
    if unidad_ids:
        # Buscamos todos los detalles de venta asociados a estas prendas
        ventas = db.query(DetalleVenta, Venta).join(Venta, DetalleVenta.venta_id == Venta.id).filter(
            DetalleVenta.stock_unit_id.in_(unidad_ids)
        ).all()
        for detalle, venta in ventas:
            todas_ventas_dict[detalle.stock_unit_id] = (detalle, venta)
            
            # Solo ventas que ya hemos cobrado (estado_pago == 'pagado' o 'reembolso_parcial')
            es_pagada_y_valida = (
                venta.estado_pago in ['pagado', 'reembolso_parcial'] and
                venta.estado_envio not in ['cancelado', 'devuelto', 'en_devolucion'] and
                detalle.devuelto == False
            )
            if es_pagada_y_valida:
                ventas_pagadas_dict[detalle.stock_unit_id] = (detalle, venta)

    cliente_db = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    exento_tarifa_fija = getattr(cliente_db, 'exento_tarifa_fija', False)
    exento_comision = getattr(cliente_db, 'exento_comision', False)

    resultados = []
    for u in unidades:
        config = u.stock_config
        variante = config.variante
        producto = variante.producto
        
        img_url = None
        if variante.imagenes:
            img_sorted = sorted(variante.imagenes, key=lambda x: x.orden or 0)
            img_url = img_sorted[0].url if img_sorted else None

        tiene_venta = u.id in todas_ventas_dict
        
        if tiene_venta:
            # Si tiene venta, SOLO se puede pagar si esa venta está completamente cobrada/pagada.
            if u.id not in ventas_pagadas_dict:
                continue
                
            detalle, venta = ventas_pagadas_dict[u.id]
            precio_base = float(detalle.precio_unitario_en_venta or config.precio_venta)
            fecha_ref = venta.fecha
            desglose = calcular_desglose_venta(
                precio_base,
                exento_tarifa_fija=exento_tarifa_fija,
                exento_comision=exento_comision,
                donar_ganancias=getattr(config, 'donar_ganancias', False)
            )
            pago_cliente = desglose["pago_cliente"]
        else:
            # Si NO tiene venta (extravío en almacén puro), solo se permite si el estado es extraviado
            if u.estado_gestion != 'extraviado':
                continue
                
            precio_base = float(config.precio_venta or 0.0)
            fecha_ref = datetime.utcnow() # Fecha simulada para el extravío
            pago_cliente = precio_base # ✨ Allsys asume la pérdida total, el dueño cobra el 100% sin comisiones

        resultados.append({
            "stock_id": u.id,
            "sku": u.sku,
            "nombre_producto": f"{producto.nombre} {'(Extraviado en Almacén)' if u.estado_gestion == 'extraviado' else ''}",
            "imagen": img_url,
            "fecha_venta": fecha_ref,
            "precio_venta": precio_base,
            "pago_cliente": pago_cliente
        })

    return resultados

def listar_pagos(db: Session, cliente_id: int):
    # 1. Cargamos los pagos con sus ítems asociados proactivamente
    pagos = db.query(PagoConsignacion).filter(
        PagoConsignacion.cliente_id == cliente_id
    ).options(
        selectinload(PagoConsignacion.items_pagados).joinedload(StockUnit.stock_config).joinedload(StockConfig.variante).joinedload(Variante.producto),
        joinedload(PagoConsignacion.cliente)
    ).order_by(desc(PagoConsignacion.fecha)).all()

    # 2. Enriquecemos los ítems pagados con datos financieros para el historial
    # Como ya tenemos la lógica de comisiones aquí, la aplicamos.
    for pago in pagos:
        exento_tarifa_fija = getattr(pago.cliente, 'exento_tarifa_fija', False)
        exento_comision = getattr(pago.cliente, 'exento_comision', False)
        
        # Guardamos una lista temporal de objetos enriquecidos para que Pydantic los lea
        items_enriquecidos = []
        for u in pago.items_pagados:
            config = u.stock_config
            producto = config.variante.producto
            
            # Buscamos la venta para saber el precio real de venta
            # (En un sistema real más grande, esto se optimizaría con un batch load)
            detalle_v = db.query(DetalleVenta).filter(DetalleVenta.stock_unit_id == u.id).first()
            precio_real = float(detalle_v.precio_unitario_en_venta if detalle_v else config.precio_venta)

            desglose = calcular_desglose_venta(
                precio_real,
                exento_tarifa_fija=exento_tarifa_fija,
                exento_comision=exento_comision,
                donar_ganancias=getattr(config, 'donar_ganancias', False)
            )

            # Inyectamos atributos dinámicos al objeto para que Pydantic los encuentre
            if u.estado_gestion == 'extraviado':
                u.nombre_producto = f"{producto.nombre} (Extraviado en Almacén)"
                u.precio_venta = precio_real
                u.pago_cliente = precio_real # ✨ Allsys no cobra comisión
                u.comision_allsys = 0.0
            else:
                u.nombre_producto = producto.nombre
                u.precio_venta = precio_real
                u.pago_cliente = desglose["pago_cliente"]
                u.comision_allsys = desglose["comision_total_allsys"]
        
        # ✨ Parsear ítems anulados fantasma
        import json
        if pago.items_anulados_json:
            try:
                pago.items_anulados = json.loads(pago.items_anulados_json)
            except Exception:
                pago.items_anulados = []
        else:
            pago.items_anulados = []
            
    return pagos

def editar_pago(db: Session, pago_id: int, datos: dict):
    pago = db.query(PagoConsignacion).filter(PagoConsignacion.id == pago_id).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
        
    if pago.estado == 'anulado':
        raise HTTPException(status_code=400, detail="No se puede editar un pago anulado.")

    # 🛡️ Inmutabilidad: No permitimos cambiar el monto ni el cliente
    campos_permitidos = ["metodo_pago", "referencia", "notas"]
    
    for k, v in datos.items():
        if k in campos_permitidos and hasattr(pago, k):
            setattr(pago, k, v)
            
    db.commit()
    db.refresh(pago)
    return pago

def anular_pago(db: Session, pago_id: int, motivo: str):
    pago = db.query(PagoConsignacion).filter(PagoConsignacion.id == pago_id).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    
    if pago.estado == 'anulado':
        raise HTTPException(status_code=400, detail="Este pago ya está anulado.")
    
    # ✨ 1. Marcar como anulado
    pago.estado = 'anulado'
    pago.motivo_anulacion = motivo
    pago.fecha_anulacion = datetime.utcnow()

    # ✨ 2. DESVINCULACIÓN: Liberamos las prendas asociadas a este pago
    # Volverán a aparecer como pendientes de pago
    db.query(StockUnit).filter(StockUnit.pago_consignacion_id == pago_id).update(
        {"pago_consignacion_id": None}, synchronize_session=False
    )
        
    db.commit()

    # ✨ AUDITORÍA: Anulación de pago
    registrar_log(
        db, accion="ANULAR_PAGO", entidad_tipo="PAGO_CONSIGNACION", entidad_id=pago_id,
        valor_anterior={"estado": "completado"},
        valor_nuevo={"estado": "anulado", "motivo": motivo},
        notas=f"Pago #{pago_id} anulado. Motivo: {motivo}. Las prendas asociadas vuelven a estar pendientes de liquidación."
    )

    return {"message": "Pago anulado correctamente. El saldo vuelve a estar pendiente.", "pago": pago}

def quitar_item_de_pago(db: Session, pago_id: int, stock_unit_id: int, motivo: str):
    """
    Desvincula una prenda individual de un pago de consignación.
    Recalcula el monto total del pago para mantener la integridad contable.
    """
    pago = db.query(PagoConsignacion).filter(PagoConsignacion.id == pago_id).first()
    if not pago:
        raise HTTPException(status_code=404, detail="Registro de pago no encontrado.")
    
    if pago.estado == 'anulado':
        raise HTTPException(status_code=400, detail="No se pueden quitar ítems de un pago que ya está anulado globalmente.")

    unidad = db.query(StockUnit).filter(StockUnit.id == stock_unit_id, StockUnit.pago_consignacion_id == pago_id).first()
    if not unidad:
        raise HTTPException(status_code=404, detail="La prenda no pertenece a este pago o ya fue desvinculada.")

    # 1. Calcular cuánto se le pagó al cliente por esta prenda específica para restarlo del total
    cliente = pago.cliente
    config = unidad.stock_config
    
    # Buscamos la venta
    detalle_v = db.query(DetalleVenta).filter(DetalleVenta.stock_unit_id == unidad.id).first()
    precio_real = float(detalle_v.precio_unitario_en_venta if detalle_v else config.precio_venta)

    if unidad.estado_gestion == 'extraviado':
        pago_por_esta_prenda = precio_real # 100% indemnización
    else:
        desglose = calcular_desglose_venta(
            precio_real,
            exento_tarifa_fija=getattr(cliente, 'exento_tarifa_fija', False),
            exento_comision=getattr(cliente, 'exento_comision', False),
            donar_ganancias=getattr(config, 'donar_ganancias', False)
        )
        pago_por_esta_prenda = desglose["pago_cliente"]

    # 2. Guardar el ítem en el JSON fantasma
    import json
    items_anulados = []
    if pago.items_anulados_json:
        try:
            items_anulados = json.loads(pago.items_anulados_json)
        except Exception:
            pass
            
    items_anulados.append({
        "id": unidad.id,
        "sku": unidad.sku,
        "nombre_producto": f"{config.variante.producto.nombre} (Anulado de este pago)",
        "precio_venta": precio_real,
        "pago_cliente": pago_por_esta_prenda,
        "comision_allsys": desglose["comision_total_allsys"] if unidad.estado_gestion != 'extraviado' else 0.0,
        "fecha_anulacion": datetime.utcnow().isoformat(),
        "motivo": motivo
    })
    pago.items_anulados_json = json.dumps(items_anulados)

    # 3. Actualizar el pago global
    monto_anterior = pago.monto
    pago.monto = max(0.0, float(pago.monto) - pago_por_esta_prenda)
    
    # 4. Desvincular la prenda
    unidad.pago_consignacion_id = None
    
    # 5. Auditoría detallada
    registrar_log(
        db, accion="QUITAR_ITEM_PAGO", entidad_tipo="PAGO_CONSIGNACION", entidad_id=pago_id,
        valor_anterior={"monto": monto_anterior, "item_id": stock_unit_id},
        valor_nuevo={"monto": pago.monto},
        notas=f"Se retiró la prenda #{stock_unit_id} del pago #{pago_id} por error. Motivo: {motivo}. Se restaron {pago_por_esta_prenda}€ del total del pago."
    )

    db.commit()
    db.refresh(pago)
    return pago