from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_session
from app.models.lotes_model import StockUnit
from app.schemas.ventas_schema import VentaCreate, VentaUpdate
from app.repositories import ventas_repo
# ✨ ACTUALIZADO: Importamos la nueva función del repositorio de productos
from app.repositories.producto_repo import obtener_stock_config_detalle
from app.repositories.ventas_repo import contar_compras_cliente

venta_router = APIRouter(
    prefix="/ventas",
    tags=["Ventas"]
)

# =====================================================
# 1. RUTAS RAÍZ ( / )
# =====================================================

@venta_router.post("/")
def crear_venta(
    data: VentaCreate, 
    db: Session = Depends(get_session)
):
    """Registra una venta nueva y resta stock."""
    try:
        venta = ventas_repo.registrar_venta(db, data)
        return {
            "success": True,
            "mensaje": "Venta registrada correctamente",
            "venta_id": venta.id,
            "codigo": venta.codigo_venta,
            "total": venta.total
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@venta_router.get("/")
def listar_ventas(
    page: int = 1, limit: int = 10,
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
    solo_online: bool = False,
    include_details: bool = False,
    estado_venta: Optional[str] = Query(None),
    localizacion_id: Optional[int] = Query(None),
    db: Session = Depends(get_session)
):
    try:
        resultados = ventas_repo.obtener_ventas_paginadas(
            db=db, page=page, limit=limit,
            search_producto=search_producto, tipo_busqueda_prod=tipo_busqueda_prod,
            search_codigo=search_codigo, 
            search_cliente=search_cliente, tipo_busqueda_cliente=tipo_busqueda_cliente, 
            cliente_id=cliente_id,
            estado_pago=estado_pago,
            estado_envio=estado_envio,
            canal=canal, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin,
            tipo_fecha=tipo_fecha,
            vendedor=vendedor, marca_id=marca_id, categoria_id=categoria_id,
            solo_online=solo_online,
            include_details=include_details,
            estado_venta=estado_venta,
            localizacion_id=localizacion_id
        )
        return resultados
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener ventas: {str(e)}")

# =====================================================
# 2. RUTAS ESTÁTICAS CON PARÁMETROS ( /prefijo/{id} )
# =====================================================





# Reemplaza tu ruta estática /producto/{stock_config_id} por esta:

@venta_router.get("/producto/scan/{codigo}")
def consultar_producto_para_venta(
    codigo: str,
    db: Session = Depends(get_session)
):
    """Endpoint rápido para escanear un SKU o ID de unidad física y ver disponibilidad."""
    
    # Búsqueda dual: Si meten número, busca por ID. Si meten texto, busca por SKU.
    if codigo.isdigit():
        unidad = db.query(StockUnit).filter(StockUnit.id == int(codigo)).first()
    else:
        unidad = db.query(StockUnit).filter(StockUnit.sku == codigo).first()
        
    if not unidad:
        raise HTTPException(status_code=404, detail="El artículo físico no existe en el inventario.")

    # Validar que físicamente se puede vender
    if unidad.estado_gestion != 'en_stock' or not unidad.activo:
        return {
            "alerta": f"⚠️ ARTÍCULO NO DISPONIBLE (Estado: {unidad.estado_gestion})",
            "producto": None
        }

    config = unidad.stock_config
    return {
        "stock_unit_id": unidad.id,
        "sku": unidad.sku,
        "producto_nombre": config.variante.producto.nombre,
        "color": config.variante.identidad_variante,
        "talla": config.etiqueta,
        "precio_venta": float(config.precio_venta or 0.0),
        "imagen": config.variante.imagenes[0].url if config.variante.imagenes else None
    }








@venta_router.get("/detalle/{venta_id}")
def obtener_detalle_venta(venta_id: int, db: Session = Depends(get_session)):
    """Obtiene toda la información de una venta específica."""
    venta = ventas_repo.obtener_venta_por_id(db, venta_id)
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return venta

@venta_router.get("/historial-cliente/{identificador}")
def obtener_conteo_compras(identificador: str, db: Session = Depends(get_session)):
    try:
        total = contar_compras_cliente(db, identificador)
        return {"compras_totales": total}
    except Exception as e:
        return {"compras_totales": 0}

@venta_router.get("/logistica/pendientes")
def obtener_ventas_logistica(
    page: int = 1, 
    limit: int = 10,
    search: Optional[str] = None,
    tipo_busqueda: str = 'general',
    estado: str = 'preparacion',
    localizacion_id: Optional[int] = Query(None),
    db: Session = Depends(get_session)
):
    return ventas_repo.obtener_pedidos_pendientes_logistica(
        db=db, 
        page=page, 
        limit=limit, 
        search=search, 
        tipo_busqueda=tipo_busqueda,
        filtro_estado=estado,
        localizacion_id=localizacion_id
    )

import urllib.request
from fastapi.responses import StreamingResponse

@venta_router.get("/proxy-etiqueta")
def proxy_etiqueta(url: str):
    """
    Descarga una etiqueta externa eludiendo el CORS del frontend.
    Sirve el archivo directamente desde nuestro backend.
    """
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        
        def iterfile():
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                yield chunk
                
        content_type = response.headers.get_content_type()
        return StreamingResponse(iterfile(), media_type=content_type)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al descargar la etiqueta: {str(e)}")

# =====================================================
# 3. RUTAS TOTALMENTE DINÁMICAS ( /{id} ) - Siempre al final
# =====================================================

@venta_router.put("/{venta_id}")
def editar_venta(venta_id: int, data: VentaUpdate, db: Session = Depends(get_session)):
    """Actualiza metadatos y estados de una venta existente."""
    try:
        resultado = ventas_repo.actualizar_venta(db, venta_id, data.dict(exclude_unset=True))
        return {
            "success": True, 
            "mensaje": resultado.get("mensaje", "Venta actualizada correctamente."),
            "alerta_logistica": resultado.get("alerta_logistica")
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@venta_router.put("/{venta_id}/smart-scan")
def smart_scan_logistica(venta_id: int, scanned_unit_id: int, db: Session = Depends(get_session)):
    """Verifica si una prenda escaneada pertenece al pedido, o hace un trueque inteligente."""
    try:
        resultado = ventas_repo.procesar_smart_scan(db, venta_id, scanned_unit_id)
        return resultado
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en smart scan: {str(e)}")

@venta_router.put("/{venta_id}/item/{detalle_id}/precio")
def corregir_precio_item(venta_id: int, detalle_id: int, nuevo_precio: float, db: Session = Depends(get_session)):
    """Corrige el precio de un ítem y ajusta los totales (Afecta al dueño)."""
    try:
        ventas_repo.corregir_precio_item(db, venta_id, detalle_id, nuevo_precio)
        return {"success": True, "mensaje": "Precio actualizado correctamente."}
    except HTTPException as e: raise e
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@venta_router.put("/{venta_id}/item/{detalle_id}/devolucion-fisica")
def devolver_item_fisicamente(venta_id: int, detalle_id: int, estado_stock: str = 'en_stock', db: Session = Depends(get_session)):
    """
    Marca un artículo como devuelto físicamente.
    - El stock vuelve al almacén.
    - El total del ticket baja.
    - El dueño de la prenda NO cobra.
    """
    try:
        venta = ventas_repo.registrar_devolucion_fisica_item(db, venta_id, detalle_id, estado_stock)
        return {"success": True, "mensaje": "Artículo devuelto físicamente y stock liberado."}
    except HTTPException as e: raise e
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@venta_router.put("/{venta_id}/item/{detalle_id}/resolver-retorno")
def resolver_retorno_item(venta_id: int, detalle_id: int, resolucion: str = Query(..., description="'en_stock' o 'extraviado'"), db: Session = Depends(get_session)):
    """
    Resuelve el estado de una prenda que estaba 'en_camino_devolucion'.
    Si se marca como extraviada, se revierte la devolución para que el dueño cobre.
    """
    try:
        if resolucion not in ['en_stock', 'extraviado']:
            raise HTTPException(status_code=400, detail="Resolución inválida.")
        return ventas_repo.resolver_retorno_transito(db, venta_id, detalle_id, resolucion)
    except HTTPException as e: raise e
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@venta_router.put("/{venta_id}/compensacion-allsys")
def compensacion_allsys(venta_id: int, monto: float, motivo: str, db: Session = Depends(get_session)):
    """
    Registra un reembolso asumido por Allsys.
    - El dueño de la prenda COBRA su parte original.
    - La tienda registra un GASTO.
    """
    try:
        venta = ventas_repo.registrar_compensacion_allsys(db, venta_id, monto, motivo)
        return {"success": True, "mensaje": "Compensación registrada como gasto de la tienda."}
    except HTTPException as e: raise e
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))