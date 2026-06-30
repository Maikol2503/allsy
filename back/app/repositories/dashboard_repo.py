# dashborad_repo.py
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, desc
from app.models.ventas_model import Venta, DetalleVenta
from app.models.lotes_model import StockConfig, StockUnit 
from app.models.variantes_model import Variante
from app.models.producto_model import Producto
from app.models.clientes_model import Cliente
from app.models.egresos_model import Egreso
from app.models.pagos_consignacion_model import PagoConsignacion
from app.models.proveedores_model import Proveedor
from datetime import datetime, timedelta, timezone 
from collections import defaultdict

# Asegúrate de importar tu función desde donde la tengas
from app.repositories.consignacion_repo import calcular_desglose_venta 

def obtener_resumen_financiero(db: Session, fecha_inicio: str = None, fecha_fin: str = None):
    # 1. Filtros Base (Ventas válidas: No canceladas ni reembolsadas)
    f_ventas = [
        Venta.estado_envio != 'cancelado',
        Venta.estado_pago != 'reembolsado'
    ]
    # Excluir Devoluciones y Reembolsos para no duplicar deducciones, pero incluir las compensaciones de Allsys ya que son pérdidas/gastos reales de la tienda
    f_gastos = [
        or_(
            Egreso.categoria != "Devoluciones y Reembolsos",
            Egreso.concepto.ilike("%Compensación Allsys%")
        )
    ]
    # Solo pagos completados
    f_pagos = [PagoConsignacion.estado == 'completado']

    if fecha_inicio:
        f_ventas.append(Venta.fecha >= fecha_inicio)
        f_gastos.append(Egreso.fecha >= fecha_inicio)
        f_pagos.append(PagoConsignacion.fecha >= fecha_inicio)
    if fecha_fin:
        fecha_fin_full = f"{fecha_fin} 23:59:59"
        f_ventas.append(Venta.fecha <= fecha_fin_full)
        f_gastos.append(Egreso.fecha <= fecha_fin_full)
        f_pagos.append(PagoConsignacion.fecha <= fecha_fin_full)

    # 2. Métricas Rápidas (Agregaciones Directas)
    egresos_ops = db.query(func.sum(Egreso.monto)).filter(*f_gastos).scalar() or 0.0
    pagos_clientes = db.query(func.sum(PagoConsignacion.monto)).filter(*f_pagos).scalar() or 0.0

    # Definición de ropa propia vs consignación alineado con estadísticas
    filtro_es_propia = or_(StockConfig.propietario_id.is_(None), Cliente.nombre.ilike('%allsy%'))
    filtro_es_consig = and_(StockConfig.propietario_id.is_not(None), or_(Cliente.nombre.is_(None), ~Cliente.nombre.ilike('%allsy%')))

    # 3. Procesamiento de Ventas mediante Proyección (EVITAR CARGA DE OBJETOS COMPLETOS)
    # Filtramos por DetalleVenta.devuelto == False para no sumar prendas devueltas
    ventas_query = db.query(
        DetalleVenta.precio_unitario_en_venta,
        StockConfig.precio_compra,
        StockConfig.propietario_id,
        StockConfig.donar_ganancias,
        Cliente.exento_tarifa_fija,
        Cliente.exento_comision,
        Venta.estado_pago,
        Cliente.nombre.label("cliente_nombre")
    ).join(StockUnit, DetalleVenta.stock_unit_id == StockUnit.id)\
     .join(StockConfig, StockUnit.stock_config_id == StockConfig.id)\
     .join(Venta, DetalleVenta.venta_id == Venta.id)\
     .outerjoin(Cliente, StockConfig.propietario_id == Cliente.id)\
     .filter(*f_ventas)\
     .filter(DetalleVenta.devuelto == False).all()

    ingresos_periodo_liquidados = 0.0
    ingresos_propios_periodo = 0.0
    ingresos_consig_periodo = 0.0
    costo_propio_liquidado = 0.0
    deuda_generada_periodo = 0.0
    
    ingresos_retenidos = 0.0
    beneficio_retenido = 0.0
    deuda_retenida_total = 0.0

    for p_venta, p_compra, prop_id, donar, ex_tarifa, ex_comision, est_pago, cliente_nombre in ventas_query:
        pv = float(p_venta or 0.0)
        pc = float(p_compra or 0.0)
        es_liquidado = est_pago in ["pagado", "reembolso_parcial", "reembolsado"]
        
        es_propia = (prop_id is None) or (cliente_nombre and 'allsy' in cliente_nombre.lower())
        
        if not es_propia: # CONSIGNACIÓN
            desglose = calcular_desglose_venta(
                pv, 
                exento_tarifa_fija=ex_tarifa or False,
                exento_comision=ex_comision or False,
                donar_ganancias=donar or False
            )
            if es_liquidado:
                ingresos_periodo_liquidados += pv
                ingresos_consig_periodo += pv
                deuda_generada_periodo += desglose["pago_cliente"]
            else:
                ingresos_retenidos += pv
                beneficio_retenido += desglose["comision_total_allsys"]
                deuda_retenida_total += desglose["pago_cliente"]
        else: # PROPIA
            if es_liquidado:
                ingresos_periodo_liquidados += pv
                ingresos_propios_periodo += pv
                costo_propio_liquidado += pc
            else:
                ingresos_retenidos += pv
                beneficio_retenido += (pv - pc)

    # 4. Stock Actual (Agregación SQL Directa)
    unidades_propias = db.query(func.count(StockUnit.id))\
        .join(StockConfig)\
        .outerjoin(Cliente, StockConfig.propietario_id == Cliente.id)\
        .filter(StockUnit.estado_gestion == 'en_stock', StockUnit.activo == True, filtro_es_propia).scalar() or 0
    
    unidades_consig = db.query(func.count(StockUnit.id))\
        .join(StockConfig)\
        .outerjoin(Cliente, StockConfig.propietario_id == Cliente.id)\
        .filter(StockUnit.estado_gestion == 'en_stock', StockUnit.activo == True, filtro_es_consig).scalar() or 0
        
    inversion_stock_propio = db.query(func.sum(StockConfig.precio_compra))\
        .join(StockUnit)\
        .outerjoin(Cliente, StockConfig.propietario_id == Cliente.id)\
        .filter(StockUnit.estado_gestion == 'en_stock', StockUnit.activo == True, filtro_es_propia).scalar() or 0.0

    # 5. Saldo Bancario Teórico (Cálculo histórico rápido, neto de reembolsos/compensaciones)
    ingresos_hist = db.query(func.sum(Venta.total - func.coalesce(Venta.monto_reembolsado, 0.0))).filter(Venta.estado_pago.in_(["pagado", "reembolso_parcial"])).scalar() or 0.0
    # Excluimos "Pérdidas y Mermas" para no duplicar las compensaciones por extravío que ya se restan en pagos_consig_hist, pero incluimos Compensaciones Allsys reales
    gastos_hist = db.query(func.sum(Egreso.monto)).filter(*f_gastos).scalar() or 0.0
    
    compras_hist = db.query(func.sum(StockConfig.precio_compra))\
        .join(StockUnit)\
        .outerjoin(Cliente, StockConfig.propietario_id == Cliente.id)\
        .filter(filtro_es_propia).scalar() or 0.0
        
    pagos_consig_hist = db.query(func.sum(PagoConsignacion.monto)).filter(PagoConsignacion.estado == 'completado').scalar() or 0.0
    
    saldo_teorico = float(ingresos_hist) - float(gastos_hist) - float(compras_hist) - float(pagos_consig_hist)

    # 6. Cálculo de Deuda Absoluta (Histórica acumulada hasta hoy)
    # Buscamos las prendas de consignación vendidas o extraviadas que aún NO han sido pagadas
    # al propietario (pago_consignacion_id es NULL) y que son elegibles para pago.
    unidades_con_venta_liquidadas = db.query(
        StockUnit.id,
        StockConfig.precio_venta,
        StockConfig.donar_ganancias,
        Cliente.exento_tarifa_fija,
        Cliente.exento_comision,
        DetalleVenta.precio_unitario_en_venta
    ).join(StockConfig, StockUnit.stock_config_id == StockConfig.id)\
     .outerjoin(Cliente, StockConfig.propietario_id == Cliente.id)\
     .join(DetalleVenta, StockUnit.id == DetalleVenta.stock_unit_id)\
     .join(Venta, DetalleVenta.venta_id == Venta.id)\
     .filter(
         filtro_es_consig,
         StockUnit.estado_gestion.in_(['vendido', 'extraviado']),
         StockUnit.pago_consignacion_id.is_(None),
         Venta.estado_pago.in_(['pagado', 'reembolso_parcial']),
         Venta.estado_envio.notin_(['cancelado', 'devuelto', 'en_devolucion']),
         DetalleVenta.devuelto == False
     ).all()

    unidades_sin_venta_extraviadas = db.query(
        StockConfig.precio_venta
    ).join(StockUnit, StockUnit.stock_config_id == StockConfig.id)\
     .outerjoin(Cliente, StockConfig.propietario_id == Cliente.id)\
     .filter(
         filtro_es_consig,
         StockUnit.estado_gestion == 'extraviado',
         StockUnit.pago_consignacion_id.is_(None),
         StockUnit.id.notin_(db.query(DetalleVenta.stock_unit_id))
     ).all()

    deuda_absoluta_real = 0.0
    for s_id, precio_config, donar, ex_tarifa, ex_comision, precio_venta_real in unidades_con_venta_liquidadas:
        precio_base = float(precio_venta_real or precio_config or 0.0)
        desglose = calcular_desglose_venta(
            precio_base,
            exento_tarifa_fija=ex_tarifa or False,
            exento_comision=ex_comision or False,
            donar_ganancias=donar or False
        )
        deuda_absoluta_real += desglose["pago_cliente"]

    for precio_config, in unidades_sin_venta_extraviadas:
        deuda_absoluta_real += float(precio_config or 0.0)

    # Deuda Retenida Histórica (en tránsito/Apps)
    # Prendas vendidas o extraviadas en consignación que están asociadas a ventas que no se han cobrado aún y no se han pagado al dueño
    ventas_consig_retenidas_hist = db.query(
        DetalleVenta.precio_unitario_en_venta,
        StockConfig.precio_venta,
        StockConfig.donar_ganancias,
        Cliente.exento_tarifa_fija,
        Cliente.exento_comision
    ).join(StockUnit, DetalleVenta.stock_unit_id == StockUnit.id)\
     .join(StockConfig, StockUnit.stock_config_id == StockConfig.id)\
     .join(Venta, DetalleVenta.venta_id == Venta.id)\
     .outerjoin(Cliente, StockConfig.propietario_id == Cliente.id)\
     .filter(
         filtro_es_consig,
         StockUnit.estado_gestion.in_(['vendido', 'extraviado']),
         Venta.estado_envio.notin_(['cancelado', 'devuelto', 'en_devolucion']),
         ~Venta.estado_pago.in_(['pagado', 'reembolso_parcial', 'reembolsado']),
         DetalleVenta.devuelto == False,
         StockUnit.pago_consignacion_id.is_(None)
     ).all()

    deuda_retenida_absoluta = 0.0
    for pv, pc_v, donar, ex_tarifa, ex_comision in ventas_consig_retenidas_hist:
        desglose = calcular_desglose_venta(
            float(pv or 0.0),
            exento_tarifa_fija=ex_tarifa or False,
            exento_comision=ex_comision or False,
            donar_ganancias=donar or False
        )
        deuda_retenida_absoluta += desglose["pago_cliente"]

    return {
        "ingresos_totales": round(ingresos_periodo_liquidados, 2),
        "ingresos_propios": round(ingresos_propios_periodo, 2),
        "ingresos_consignacion": round(ingresos_consig_periodo, 2),
        "egresos_operativos": round(float(egresos_ops), 2),
        "ganancia_real": round(ingresos_periodo_liquidados - costo_propio_liquidado - deuda_generada_periodo - float(egresos_ops), 2),
        "margen_propio": round(ingresos_propios_periodo - costo_propio_liquidado, 2),
        "margen_consignacion": round(ingresos_consig_periodo - deuda_generada_periodo, 2),
        "pagos_clientes_periodo": round(float(pagos_clientes), 2),
        "deuda_generada_periodo": round(deuda_generada_periodo, 2),
        "deuda_absoluta": round(deuda_absoluta_real, 2),
        "ingresos_retenidos": round(ingresos_retenidos, 2),
        "beneficio_retenido": round(beneficio_retenido, 2),
        "deuda_retenida_total": round(deuda_retenida_absoluta, 2),
        "inversion_en_stock": round(float(inversion_stock_propio), 2),
        "inversion_historica": round(float(compras_hist), 2),
        "unidades_propias": int(unidades_propias),
        "unidades_consignacion": int(unidades_consig),
        "saldo_teorico_banco": round(saldo_teorico, 2)
    }

def obtener_datos_grafica_tendencia(db: Session, fecha_inicio: str = None, fecha_fin: str = None):
    try:
        hoy = datetime.now(timezone.utc)
        
        # Procesar fechas
        dt_inicio = None
        dt_fin = hoy
        
        if fecha_inicio:
            try:
                dt_inicio = datetime.fromisoformat(fecha_inicio.replace('Z', '+00:00'))
            except:
                pass
        if fecha_fin:
            try:
                dt_fin = datetime.fromisoformat(fecha_fin.replace('Z', '+00:00'))
            except:
                pass

        if not dt_inicio:
            # Default a últimos 30 días si no hay filtro
            dt_inicio = hoy - timedelta(days=30)
            
        dias_diferencia = (dt_fin - dt_inicio).days
        agrupar_por_mes = dias_diferencia > 45

        # Query ventas
        q_ventas = db.query(Venta.fecha, Venta.total, Venta.monto_reembolsado).filter(
            Venta.fecha >= dt_inicio,
            Venta.fecha <= dt_fin,
            Venta.estado_envio != 'cancelado',
            Venta.estado_pago != 'reembolsado'
        )
        ventas = q_ventas.all()
        
        # Query gastos
        q_gastos = db.query(Egreso.fecha, Egreso.monto).filter(
            Egreso.fecha >= dt_inicio,
            Egreso.fecha <= dt_fin,
            Egreso.categoria != "Devoluciones y Reembolsos"
        )
        gastos = q_gastos.all()

        agrupado_ventas = defaultdict(float)
        agrupado_gastos = defaultdict(float)

        for f, t, r in ventas:
            if f:
                clave = (f.year, f.month) if agrupar_por_mes else (f.year, f.month, f.day)
                agrupado_ventas[clave] += float(t or 0) - float(r or 0)
                
        for f, m in gastos:
            if f:
                clave = (f.year, f.month) if agrupar_por_mes else (f.year, f.month, f.day)
                agrupado_gastos[clave] += float(m or 0)

        resultados = []
        nombres_meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        
        if agrupar_por_mes:
            # Generar meses
            meses_generados = []
            curr = dt_inicio
            while curr <= dt_fin:
                meses_generados.append((curr.year, curr.month))
                curr += timedelta(days=31)
                curr = curr.replace(day=1)
            
            # Asegurar que el último mes está
            if (dt_fin.year, dt_fin.month) not in meses_generados:
                meses_generados.append((dt_fin.year, dt_fin.month))
                
            for a, m in meses_generados:
                resultados.append({
                    "mes": f"{nombres_meses[m - 1]} {str(a)[-2:]}",
                    "ventas": round(agrupado_ventas.get((a, m), 0.0), 2),
                    "egresos": round(agrupado_gastos.get((a, m), 0.0), 2)
                })
        else:
            # Generar días
            for i in range(dias_diferencia + 1):
                target_date = dt_inicio + timedelta(days=i)
                a, m, d = target_date.year, target_date.month, target_date.day
                resultados.append({
                    "mes": f"{d} {nombres_meses[m - 1]}",
                    "ventas": round(agrupado_ventas.get((a, m, d), 0.0), 2),
                    "egresos": round(agrupado_gastos.get((a, m, d), 0.0), 2)
                })
                
        return resultados
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))