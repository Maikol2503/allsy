import traceback
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_, and_
from app.models.proveedores_model import Proveedor
from app.models.ventas_model import Venta, DetalleVenta
from app.models.lotes_model import StockConfig, StockUnit
from app.models.variantes_model import Variante
from app.models.egresos_model import Egreso
from app.models.producto_model import Producto
from app.models.categorias_model import Categoria
from app.models.clientes_model import Cliente
from collections import defaultdict
from app.repositories.consignacion_repo import calcular_desglose_venta 

# =========================================================
# INTELIGENCIA DE NEGOCIO (PESTAÑAS 1 y 2)
# =========================================================
def obtener_inteligencia_negocio(db: Session, fecha_inicio: str = None, fecha_fin: str = None):
    # Ventas válidas (No canceladas ni reembolsadas globalmente)
    f_ventas = [
        Venta.estado_envio != 'cancelado',
        Venta.estado_pago != 'reembolsado'
    ]
    f_gastos = []
    f_configs = []  

    if fecha_inicio:
        f_ventas.append(Venta.fecha >= fecha_inicio)
        f_gastos.append(Egreso.fecha >= fecha_inicio)
        f_configs.append(StockUnit.fecha_registro >= fecha_inicio)
        
    if fecha_fin:
        fecha_fin_full = f"{fecha_fin} 23:59:59"
        f_ventas.append(Venta.fecha <= fecha_fin_full)
        f_gastos.append(Egreso.fecha <= fecha_fin_full)
        f_configs.append(StockUnit.fecha_registro <= fecha_fin_full)

    detalles_query = db.query(
        DetalleVenta.precio_unitario_en_venta,
        StockConfig.precio_compra,
        StockConfig.propietario_id,
        StockConfig.donar_ganancias,
        Cliente.exento_tarifa_fija,
        Cliente.exento_comision,
        Venta.vendedor,
        Venta.canal,
        Categoria.nombre,
        Cliente.nombre.label("cliente_nombre"),
        DetalleVenta.devuelto # ✨ NUEVO
    ).join(StockUnit, DetalleVenta.stock_unit_id == StockUnit.id)\
     .join(StockConfig, StockUnit.stock_config_id == StockConfig.id)\
     .join(Variante, StockConfig.variante_id == Variante.id)\
     .join(Producto, Variante.producto_id == Producto.id)\
     .join(Categoria, Producto.categoria_id == Categoria.id)\
     .join(Venta, DetalleVenta.venta_id == Venta.id)\
     .outerjoin(Cliente, StockConfig.propietario_id == Cliente.id)\
     .filter(*f_ventas).all()

    ingresos_propios, costo_propio = 0.0, 0.0
    ingresos_consig, pago_clientes = 0.0, 0.0
    
    vendedores_propios = defaultdict(float)
    canales_propios = defaultdict(float)
    categorias_propias = defaultdict(int)
    
    vendedores_consig = defaultdict(float)
    canales_consig = defaultdict(float)
    categorias_consig = defaultdict(int)

    for row in detalles_query:
        p_venta, p_compra, propietario_id, donar, ex_tarifa, ex_comision, vendedor, canal, cat_nombre, cliente_nombre, item_devuelto = row
        if item_devuelto: continue # ✨ EXCLUIR ARTÍCULOS DEVUELTOS INDIVIDUALMENTE

        ingreso_item = float(p_venta or 0.0)
        vendedor_name = vendedor or "Desconocido"
        canal_name = canal or "Sin Canal"
        categoria_name = cat_nombre or "Sin Categoría"
        
        es_propia = (propietario_id is None) or (cliente_nombre and 'allsy' in cliente_nombre.lower())
        
        if not es_propia:
            ingresos_consig += ingreso_item
            desglose = calcular_desglose_venta(
                ingreso_item,
                exento_tarifa_fija=ex_tarifa or False,
                exento_comision=ex_comision or False,
                donar_ganancias=bool(donar)
            )
            pago_clientes += desglose["pago_cliente"]
            
            vendedores_consig[vendedor_name] += ingreso_item
            canales_consig[canal_name] += ingreso_item
            categorias_consig[categoria_name] += 1
        else:
            ingresos_propios += ingreso_item
            costo_propio += float(p_compra or 0.0)
            
            vendedores_propios[vendedor_name] += ingreso_item
            canales_propios[canal_name] += ingreso_item
            categorias_propias[categoria_name] += 1

    filtro_es_propia = or_(StockConfig.propietario_id.is_(None), Cliente.nombre.ilike('%allsy%'))
    filtro_es_consig = and_(StockConfig.propietario_id.is_not(None), or_(Cliente.nombre.is_(None), ~Cliente.nombre.ilike('%allsy%')))

    remanente_dinero_propio = float(db.query(func.sum(StockConfig.precio_compra))\
        .join(StockUnit, StockUnit.stock_config_id == StockConfig.id)\
        .outerjoin(Cliente, StockConfig.propietario_id == Cliente.id)\
        .filter(*f_configs, filtro_es_propia, StockUnit.estado_gestion == 'en_stock', StockUnit.activo == True)\
        .scalar() or 0.0)
    
    remanente_unidades_propio = db.query(func.count(StockUnit.id))\
        .join(StockConfig)\
        .outerjoin(Cliente, StockConfig.propietario_id == Cliente.id)\
        .filter(*f_configs, filtro_es_propia, StockUnit.estado_gestion == 'en_stock', StockUnit.activo == True).scalar() or 0

    remanente_unidades_consig = db.query(func.count(StockUnit.id))\
        .join(StockConfig)\
        .outerjoin(Cliente, StockConfig.propietario_id == Cliente.id)\
        .filter(*f_configs, filtro_es_consig, StockUnit.estado_gestion == 'en_stock', StockUnit.activo == True).scalar() or 0

    total_pedidos = db.query(func.count(Venta.id)).filter(*f_ventas).scalar() or 1
    total_ingresos = ingresos_propios + ingresos_consig
    ticket_medio = total_ingresos / total_pedidos if total_pedidos > 0 else 0

    roi_propio = 0
    if costo_propio > 0:
        roi_propio = ((ingresos_propios - costo_propio) / costo_propio) * 100
        
    margen_consignacion_pct = 0
    if ingresos_consig > 0:
        comision_pura = ingresos_consig - pago_clientes
        margen_consignacion_pct = (comision_pura / ingresos_consig) * 100

    def format_dict(d):
        return [{"nombre": k, "total": v} for k, v in d.items()]
        
    def format_cat(d):
        return [{"nombre": k, "cantidad": v} for k, v in sorted(d.items(), key=lambda item: item[1], reverse=True)[:5]]

    return {
        "propias": {
            "ingresos": round(ingresos_propios, 2),
            "costo": round(costo_propio, 2),
            "beneficio": round(ingresos_propios - costo_propio, 2),
            "stock_remanente_mes": round(remanente_dinero_propio, 2),
            "articulos_remanentes": remanente_unidades_propio,
            "roi": f"{round(roi_propio, 1)}%",
            "vendedores": format_dict(vendedores_propios),
            "canales": format_dict(canales_propios),
            "top_categorias": format_cat(categorias_propias)
        },
        "consignacion": {
            "label": "Dueño de la Prenda (Consignación)",
            "ingresos": round(ingresos_consig, 2),
            "pago_clientes": round(pago_clientes, 2),
            "comisiones": round(ingresos_consig - pago_clientes, 2),
            "articulos_remanentes": remanente_unidades_consig,
            "margen_porcentual": f"{round(margen_consignacion_pct, 1)}%",
            "vendedores": format_dict(vendedores_consig),
            "canales": format_dict(canales_consig),
            "top_categorias": format_cat(categorias_consig)
        },
        "global": {
            "ticket_medio": round(ticket_medio, 2)
        }
    }


# =========================================================
# RENDIMIENTO DE COMPRAS (PESTAÑA 3)
# =========================================================
def obtener_rendimiento_compras(db: Session, fecha_inicio: str = None, fecha_fin: str = None):
    filtro_es_propia = or_(StockConfig.propietario_id.is_(None), Cliente.nombre.ilike('%allsy%'))

    # Extracción histórica total de compras propias
    query_compras = (
        db.query(StockUnit.id, StockConfig.precio_compra)
        .join(StockConfig, StockUnit.stock_config_id == StockConfig.id)
        .outerjoin(Cliente, StockConfig.propietario_id == Cliente.id)
        .filter(filtro_es_propia)
    )

    unidades_compradas = query_compras.all()
    
    inversion_total = 0.0
    prendas_compradas = len(unidades_compradas)
    unidad_ids = []

    for uid, p_compra in unidades_compradas:
        inversion_total += float(p_compra or 0.0)
        unidad_ids.append(uid)

    ingresos_generados = 0.0
    prendas_vendidas = 0

    if unidad_ids:
        # Extraemos lo vendido en el PERIODO SELECCIONADO
        filtros_ventas = [
            DetalleVenta.stock_unit_id.in_(unidad_ids),
            Venta.estado_envio != 'cancelado',
            Venta.estado_pago != 'reembolsado',
            DetalleVenta.devuelto == False
        ]
        
        if fecha_inicio:
            filtros_ventas.append(Venta.fecha >= fecha_inicio)
        if fecha_fin:
            filtros_ventas.append(Venta.fecha <= f"{fecha_fin} 23:59:59")

        ventas_query = (
            db.query(DetalleVenta.precio_unitario_en_venta)
            .join(Venta, DetalleVenta.venta_id == Venta.id)
            .filter(*filtros_ventas)
            .all()
        )

        prendas_vendidas = len(ventas_query)
        for p_venta in ventas_query:
            ingresos_generados += float(p_venta[0] or 0.0)

    beneficio_inversion = ingresos_generados - inversion_total
    
    tasa_venta = 0.0
    if prendas_compradas > 0:
        tasa_venta = (prendas_vendidas / prendas_compradas) * 100

    return {
        "analisis_inversion": {
            "inversion_total": round(inversion_total, 2),
            "prendas_compradas": prendas_compradas,
            "ingresos_generados": round(ingresos_generados, 2),
            "prendas_vendidas": prendas_vendidas,
            "beneficio_inversion": round(beneficio_inversion, 2),
            "tasa_venta": f"{round(tasa_venta, 1)}%"
        }
    }


# =========================================================
# RANKING B2B DE PROVEEDORES (PESTAÑA 4)
# =========================================================
def obtener_rendimiento_proveedores(db: Session, fecha_inicio: str = None, fecha_fin: str = None):
    filtro_es_propia = or_(StockConfig.propietario_id.is_(None), Cliente.nombre.ilike('%allsy%'))

    query_compras = (
        db.query(StockUnit.id, StockUnit.estado_gestion, StockConfig.precio_compra, Proveedor.id, Proveedor.nombre_proveedor)
        .join(StockConfig, StockUnit.stock_config_id == StockConfig.id)
        .outerjoin(Cliente, StockConfig.propietario_id == Cliente.id)
        .outerjoin(Proveedor, StockConfig.proveedor_id == Proveedor.id)
        .filter(filtro_es_propia)
    )

    unidades_compradas = query_compras.all()

    stats_proveedores = defaultdict(lambda: {
        "nombre": "Desconocido", 
        "inversion": 0.0, 
        "unidades_compradas": 0, 
        "ingresos": 0.0, 
        "unidades_vendidas": 0,
        "prendas_atrapadas": 0
    })

    unidad_ids_propias = []

    for uid, est_gestion, p_compra, prov_id, prov_nombre in unidades_compradas:
        pid = prov_id or 0
        stats_proveedores[pid]["nombre"] = prov_nombre or "Sin Proveedor"
        stats_proveedores[pid]["inversion"] += float(p_compra or 0.0)
        stats_proveedores[pid]["unidades_compradas"] += 1
        
        if est_gestion == "en_stock":
            stats_proveedores[pid]["prendas_atrapadas"] += 1
            
        unidad_ids_propias.append(uid)

    if unidad_ids_propias:
        filtros_ventas = [
            DetalleVenta.stock_unit_id.in_(unidad_ids_propias),
            Venta.estado_envio != 'cancelado',
            Venta.estado_pago != 'reembolsado'
        ]
        
        if fecha_inicio:
            filtros_ventas.append(Venta.fecha >= fecha_inicio)
        if fecha_fin:
            filtros_ventas.append(Venta.fecha <= f"{fecha_fin} 23:59:59")

        ventas_query = (
            db.query(DetalleVenta.stock_unit_id, DetalleVenta.precio_unitario_en_venta, StockConfig.proveedor_id, DetalleVenta.devuelto)
            .join(StockUnit, DetalleVenta.stock_unit_id == StockUnit.id)
            .join(StockConfig, StockUnit.stock_config_id == StockConfig.id)
            .join(Venta, DetalleVenta.venta_id == Venta.id)
            .filter(*filtros_ventas)
            .all()
        )

        for su_id, p_venta, prov_id, item_devuelto in ventas_query:
            if item_devuelto: continue # ✨ EXCLUIR DEVUELTOS
            pid = prov_id or 0
            stats_proveedores[pid]["ingresos"] += float(p_venta or 0.0)
            stats_proveedores[pid]["unidades_vendidas"] += 1

    ranking_proveedores = []
    for prov_id, data in stats_proveedores.items():
        inversion = data["inversion"]
        ingresos = data["ingresos"]
        beneficio = ingresos - inversion

        roi = 0.0
        if inversion > 0:
            roi = (beneficio / inversion) * 100

        tasa_venta = 0.0
        if data["unidades_compradas"] > 0:
            tasa_venta = (data["unidades_vendidas"] / data["unidades_compradas"]) * 100

        ranking_proveedores.append({
            "proveedor_id": prov_id if prov_id != 0 else None,
            "nombre": data["nombre"],
            "inversion_total": round(inversion, 2),
            "ingresos_generados": round(ingresos, 2),
            "beneficio_neto": round(beneficio, 2),
            "unidades_compradas": data["unidades_compradas"],
            "unidades_vendidas": data["unidades_vendidas"],
            "tasa_venta_pct": round(tasa_venta, 2),
            "roi_pct": round(roi, 2),
            "prendas_atrapadas": data["prendas_atrapadas"]
        })

    ranking_proveedores.sort(key=lambda x: x["roi_pct"], reverse=True)

    return {
        "ranking_proveedores": ranking_proveedores
    }