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
from app.models.gastos_model import Gasto
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
        es_invalida = (est_envio == 'cancelado' or est_pago == 'reembolsado' or item_devuelto)
        
        # Sumar contadores de estados (Aproximados ahora por estado_envio)
        if est_envio == "pendiente_envio": stats["prendas_procesando"] += 1
        elif est_envio == "enviado": stats["prendas_enviada"] += 1
        elif est_envio == "entregado": stats["prendas_entregado"] += 1
        
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
            item_data["canal_venta"] = venta.canal
            item_data["fecha_venta"] = venta.fecha
            item_data["estado_pago"] = venta.estado_pago
            item_data["monto_reembolsado"] = float(venta.monto_reembolsado or 0.0)

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
        
    nuevo_pago = PagoConsignacion(
        cliente_id=cliente_id,
        monto=data.monto,
        metodo_pago=data.metodo_pago,
        referencia=data.referencia,
        notas=data.notas
    )
    db.add(nuevo_pago)
    db.flush() # Para obtener el ID del pago antes del commit

    # ✨ VINCULACIÓN DE PRENDAS (Trazabilidad)
    if data.stock_unit_ids:
        # Buscamos las prendas que pertenecen al cliente y están marcadas como vendidas
        prendas = db.query(StockUnit).join(StockConfig).filter(
            StockUnit.id.in_(data.stock_unit_ids),
            StockConfig.propietario_id == cliente_id
        ).all()
        
        for p in prendas:
            p.pago_consignacion_id = nuevo_pago.id

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
    # 1. Obtenemos las prendas del cliente en estados de venta válidos que no tengan pago asociado
    # Unimos con ventas para asegurarnos de que la venta sea real y no solo un cambio de estado manual
    query = db.query(StockUnit).join(StockConfig).filter(
        StockConfig.propietario_id == cliente_id,
        StockUnit.estado_gestion == 'vendido',
        StockUnit.pago_consignacion_id.is_(None)
    )

    unidades = query.options(
        joinedload(StockUnit.stock_config).joinedload(StockConfig.variante).joinedload(Variante.producto),
        joinedload(StockUnit.stock_config).joinedload(StockConfig.variante).joinedload(Variante.imagenes)
    ).all()

    # Pre-cargamos las ventas para calcular el desglose financiero
    unidad_ids = [u.id for u in unidades]
    ventas_dict = {}
    if unidad_ids:
        # ✨ RESTRICCIÓN CLAVE: Solo ventas que ya hemos cobrado (estado_pago == 'pagado')
        # Esto excluye prendas que están en tránsito o con dinero retenido por la plataforma.
        ventas = db.query(DetalleVenta, Venta).join(Venta, DetalleVenta.venta_id == Venta.id).filter(
            DetalleVenta.stock_unit_id.in_(unidad_ids),
            Venta.estado_pago == 'pagado', 
            Venta.estado_envio != 'cancelado'
        ).all()
        ventas_dict = {detalle.stock_unit_id: (detalle, venta) for detalle, venta in ventas}

    cliente_db = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    exento_tarifa_fija = getattr(cliente_db, 'exento_tarifa_fija', False)
    exento_comision = getattr(cliente_db, 'exento_comision', False)

    resultados = []
    for u in unidades:
        if u.id not in ventas_dict: continue # Si no hay venta válida, no se puede pagar

        detalle, venta = ventas_dict[u.id]
        config = u.stock_config
        variante = config.variante
        producto = variante.producto
        
        img_url = None
        if variante.imagenes:
            img_sorted = sorted(variante.imagenes, key=lambda x: x.orden or 0)
            img_url = img_sorted[0].url if img_sorted else None

        desglose = calcular_desglose_venta(
            float(detalle.precio_unitario_en_venta or config.precio_venta),
            exento_tarifa_fija=exento_tarifa_fija,
            exento_comision=exento_comision,
            donar_ganancias=getattr(config, 'donar_ganancias', False)
        )

        resultados.append({
            "stock_id": u.id,
            "sku": u.sku,
            "nombre_producto": producto.nombre,
            "imagen": img_url,
            "fecha_venta": venta.fecha,
            "precio_venta": float(detalle.precio_unitario_en_venta or config.precio_venta),
            "pago_cliente": desglose["pago_cliente"]
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
            u.nombre_producto = producto.nombre
            u.precio_venta = precio_real
            u.pago_cliente = desglose["pago_cliente"]
            u.comision_allsys = desglose["comision_total_allsys"]
            
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