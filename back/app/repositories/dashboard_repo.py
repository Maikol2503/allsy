# dashborad_repo.py
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc
from app.models.ventas_model import Venta, DetalleVenta
from app.models.lotes_model import StockConfig, StockUnit 
from app.models.variantes_model import Variante
from app.models.producto_model import Producto
from app.models.clientes_model import Cliente
from app.models.gastos_model import Gasto
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
    f_gastos = []
    f_pagos = []

    if fecha_inicio:
        f_ventas.append(Venta.fecha >= fecha_inicio)
        f_gastos.append(Gasto.fecha >= fecha_inicio)
        f_pagos.append(PagoConsignacion.fecha >= fecha_inicio)
    if fecha_fin:
        fecha_fin_full = f"{fecha_fin} 23:59:59"
        f_ventas.append(Venta.fecha <= fecha_fin_full)
        f_gastos.append(Gasto.fecha <= fecha_fin_full)
        f_pagos.append(PagoConsignacion.fecha <= fecha_fin_full)

    # 2. Métricas Rápidas (Agregaciones Directas)
    gastos_ops = db.query(func.sum(Gasto.monto)).filter(*f_gastos).scalar() or 0.0
    pagos_clientes = db.query(func.sum(PagoConsignacion.monto)).filter(*f_pagos).scalar() or 0.0

    # 3. Procesamiento de Ventas mediante Proyección (EVITAR CARGA DE OBJETOS COMPLETOS)
    ventas_query = db.query(
        DetalleVenta.precio_unitario_en_venta,
        StockConfig.precio_compra,
        StockConfig.propietario_id,
        StockConfig.donar_ganancias,
        Cliente.exento_tarifa_fija,
        Cliente.exento_comision,
        Venta.estado_pago
    ).join(StockUnit, DetalleVenta.stock_unit_id == StockUnit.id)\
     .join(StockConfig, StockUnit.stock_config_id == StockConfig.id)\
     .join(Venta, DetalleVenta.venta_id == Venta.id)\
     .outerjoin(Cliente, StockConfig.propietario_id == Cliente.id)\
     .filter(*f_ventas).all()

    ingresos_periodo_liquidados = 0.0
    ingresos_propios_periodo = 0.0
    ingresos_consig_periodo = 0.0
    costo_propio_liquidado = 0.0
    deuda_generada_periodo = 0.0
    
    ingresos_retenidos = 0.0
    beneficio_retenido = 0.0
    deuda_retenida_total = 0.0

    for p_venta, p_compra, prop_id, donar, ex_tarifa, ex_comision, est_pago in ventas_query:
        pv = float(p_venta or 0.0)
        pc = float(p_compra or 0.0)
        es_liquidado = est_pago in ["pagado", "reembolso_parcial", "reembolsado"]
        
        if prop_id: # CONSIGNACIÓN
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
        .join(StockConfig).filter(StockUnit.estado_gestion == 'en_stock', StockUnit.activo == True, StockConfig.propietario_id.is_(None)).scalar() or 0
    
    unidades_consig = db.query(func.count(StockUnit.id))\
        .join(StockConfig).filter(StockUnit.estado_gestion == 'en_stock', StockUnit.activo == True, StockConfig.propietario_id.is_not(None)).scalar() or 0
        
    inversion_stock_propio = db.query(func.sum(StockConfig.precio_compra))\
        .join(StockUnit).filter(StockUnit.estado_gestion == 'en_stock', StockUnit.activo == True, StockConfig.propietario_id.is_(None)).scalar() or 0.0

    # 5. Saldo Bancario Teórico (Cálculo histórico rápido)
    ingresos_hist = db.query(func.sum(Venta.total)).filter(Venta.estado_pago.in_(["pagado", "reembolso_parcial", "reembolsado"])).scalar() or 0.0
    gastos_hist = db.query(func.sum(Gasto.monto)).scalar() or 0.0
    compras_hist = db.query(func.sum(StockConfig.precio_compra)).join(StockUnit).filter(StockConfig.propietario_id.is_(None)).scalar() or 0.0
    pagos_consig_hist = db.query(func.sum(PagoConsignacion.monto)).scalar() or 0.0
    
    saldo_teorico = float(ingresos_hist) - float(gastos_hist) - float(compras_hist) - float(pagos_consig_hist)

    # 6. Cálculo de Deuda Absoluta (Aproximación por velocidad)
    deuda_neta = deuda_generada_periodo - float(pagos_clientes)

    return {
        "ingresos_totales": round(ingresos_periodo_liquidados, 2),
        "ingresos_propios": round(ingresos_propios_periodo, 2),
        "ingresos_consignacion": round(ingresos_consig_periodo, 2),
        "gastos_operativos": round(float(gastos_ops), 2),
        "ganancia_real": round(ingresos_periodo_liquidados - costo_propio_liquidado - deuda_generada_periodo - float(gastos_ops), 2),
        "margen_propio": round(ingresos_propios_periodo - costo_propio_liquidado, 2),
        "margen_consignacion": round(ingresos_consig_periodo - deuda_generada_periodo, 2),
        "pagos_clientes_periodo": round(float(pagos_clientes), 2),
        "deuda_generada_periodo": round(deuda_generada_periodo, 2),
        "deuda_absoluta": round(deuda_neta, 2),
        "ingresos_retenidos": round(ingresos_retenidos, 2),
        "beneficio_retenido": round(beneficio_retenido, 2),
        "deuda_retenida_total": round(deuda_retenida_total, 2),
        "inversion_en_stock": round(float(inversion_stock_propio), 2),
        "unidades_propias": int(unidades_propias),
        "unidades_consignacion": int(unidades_consig),
        "saldo_teorico_banco": round(saldo_teorico, 2)
    }

def obtener_datos_grafica_mensual(db: Session):
    try:
        hoy = datetime.now(timezone.utc)
        hace_6_meses = hoy - timedelta(days=180)
        
        ventas = db.query(Venta.fecha, Venta.total).filter(
            Venta.fecha >= hace_6_meses,
            Venta.estado_envio != 'cancelado',
            Venta.estado_pago != 'reembolsado'
        ).all()
        
        gastos = db.query(Gasto.fecha, Gasto.monto).filter(Gasto.fecha >= hace_6_meses).all()

        agrupado_ventas = defaultdict(float)
        agrupado_gastos = defaultdict(float)

        for f, t in ventas:
            if f: agrupado_ventas[(f.year, f.month)] += float(t or 0)
        for f, m in gastos:
            if f: agrupado_gastos[(f.year, f.month)] += float(m or 0)

        resultados = []
        nombres_meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        
        for i in range(5, -1, -1):
            target_date = hoy - timedelta(days=i*30)
            m = target_date.month
            a = target_date.year
            resultados.append({
                "mes": f"{nombres_meses[m - 1]} {str(a)[-2:]}",
                "ventas": round(agrupado_ventas.get((a, m), 0.0), 2),
                "gastos": round(agrupado_gastos.get((a, m), 0.0), 2)
            })
            
        return resultados
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))