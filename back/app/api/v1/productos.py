import json
import traceback
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.database import get_session
from app.api.deps import get_current_admin

# ✨ IMPORTACIONES ACTUALIZADAS A LA NUEVA NOMENCLATURA
from app.schemas.producto_schema import PaginatedProductosResponse
from app.schemas.lote_schema import PaginatedStockConfigsResponse, StockConfigEditPayload, AddStockUnitsRequest
from app.repositories.producto_repo import *

producto_routers = APIRouter(tags=["Productos"])

@producto_routers.get("/papelera")
def listar_papelera_endpoint(page: int = 1, limit: int = 10, db: Session = Depends(get_session)):
    return obtener_productos_papelera(db, page=page, limit=limit)

@producto_routers.get("/inventario-individual", response_model=PaginatedStockConfigsResponse)
def listar_inventario_individual_endpoint(
    page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None), tipo_busqueda: str = Query("stock_config_id"), # ✨ ACTUALIZADO
    categoria_id: Optional[int] = Query(None), marca_id: Optional[int] = Query(None),
    color: Optional[str] = Query(None), talla: Optional[str] = Query(None),
    estado: Optional[str] = Query(None), precio_min: Optional[float] = Query(None),
    precio_max: Optional[float] = Query(None), solo_vendidos: bool = Query(False),
    ordenar_por: str = Query("fecha_desc"), proveedores_ids: List[int] = Query(default=[]),
    fecha_inicio: Optional[str] = Query(None), fecha_fin: Optional[str] = Query(None),
    disponibilidad: Optional[str] = Query("todos"), 
    localizacion_id: Optional[int] = Query(None), propietario_id: Optional[int] = Query(None),
    db: Session = Depends(get_session)
):
    return obtener_stock_configs_individuales_paginados( # ✨ ACTUALIZADO
        db=db, page=page, limit=limit, search=search, tipo_busqueda=tipo_busqueda,
        categoria_id=categoria_id, marca_id=marca_id, color=color, talla=talla, estado=estado,
        precio_min=precio_min, precio_max=precio_max, solo_vendidos=solo_vendidos,
        ordenar_por=ordenar_por, proveedores_ids=proveedores_ids, fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin, disponibilidad=disponibilidad, localizacion_id=localizacion_id,
        propietario_id=propietario_id
    )

@producto_routers.get("/", response_model=PaginatedProductosResponse)
def listar_productos_endpoint(
    page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None), tipo_busqueda: str = Query("producto_id"),
    categoria_id: Optional[int] = Query(None), marca_id: Optional[int] = Query(None),
    color: Optional[str] = Query(None), talla: Optional[str] = Query(None),
    estado: Optional[str] = Query(None), material: Optional[str] = Query(None),
    precio_min: Optional[float] = Query(None), precio_max: Optional[float] = Query(None),
    solo_vendidos: bool = Query(False), ordenar_por: str = Query("fecha_desc"),
    proveedores_ids: List[int] = Query(default=[]), fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None), disponibilidad: Optional[str] = Query("todos"),
    localizacion_id: Optional[int] = Query(None), propietario_id: Optional[int] = Query(None),
    db: Session = Depends(get_session)
):
    return obtener_productos_paginados(
        db=db, page=page, limit=limit, search=search, tipo_busqueda=tipo_busqueda,
        categoria_id=categoria_id, marca_id=marca_id, color=color, talla=talla, estado=estado,
        material=material, precio_min=precio_min, precio_max=precio_max, solo_vendidos=solo_vendidos,
        ordenar_por=ordenar_por, proveedores_ids=proveedores_ids, fecha_inicio=fecha_inicio,
        disponibilidad=disponibilidad, fecha_fin=fecha_fin, localizacion_id=localizacion_id,
        propietario_id=propietario_id
    )

@producto_routers.get("/{producto_id}")
def obtener_producto_endpoint(producto_id: int, db: Session = Depends(get_session)):
    producto = obtener_producto_completo(db, producto_id)
    if not producto: raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto


@producto_routers.post("/")
async def crear_producto_endpoint(request: Request, db: Session = Depends(get_session)):
    form = await request.form()
    archivos_dict = {k: [v] for k, v in form.multi_items() if k.startswith("file_")}
    es_vintage = str(form.get("es_vintage", "false")).lower() in ["true", "on", "1"]

    # Validación de seguridad para categoría
    cat_id_raw = form.get("categoria_id")
    if not cat_id_raw or not str(cat_id_raw).isdigit():
        raise HTTPException(status_code=400, detail="El ID de la categoría es obligatorio e inválido.")

    producto = crear_producto(
        db=db, nombre=form.get("nombre"), descripcion=form.get("descripcion"),
        tipo=form.get("tipo"), categoria_id=int(cat_id_raw),
        publico_objetivo=form.get("publico_objetivo"), marca_id=form.get("marca_id"),
        marca_nombre=form.get("marca_nombre"), variantes=form.get("variantes"),
        imagenes=archivos_dict, estado=form.get("estado"), es_vintage=es_vintage,
        epoca=form.get("epoca")
    )
    return {"mensaje": "Producto creado con éxito", "producto_id": producto.id}




@producto_routers.get("/stock-config/{stock_config_id}")
def obtener_stock_config_endpoint(stock_config_id: int, db: Session = Depends(get_session)):
    """
    Devuelve todos los detalles, atributos y prendas físicas de una configuración de stock.
    Útil para rellenar el formulario de edición de lote.
    """
    detalle = obtener_stock_config_detalle(db, stock_config_id)
    if not detalle:
        raise HTTPException(status_code=404, detail="Configuración de stock no encontrada")
    return detalle





@producto_routers.put("/{producto_id}")
async def editar_producto_endpoint(
    producto_id: int, request: Request, db: Session = Depends(get_session),
    publico_objetivo: str = Form(...), nombre: Optional[str] = Form(None),
    descripcion: Optional[str] = Form(None), categoria_id: Optional[int] = Form(None),
    marca_id: Optional[int] = Form(None), marca_nombre: Optional[str] = Form(None),
    tipo: Optional[str] = Form(None), variantes: Optional[str] = Form(None),
    estado: str = Form(...), es_vintage: bool = Form(False), epoca: Optional[str] = Form(None)
):
    try:
        form_data = await request.form()
        es_vintage_bool = str(form_data.get("es_vintage", "false")).lower() in ["true", "on", "1"]
        imagenes_dict = {}
        for key, value in form_data.multi_items():
            if key.startswith("file_"):
                if key not in imagenes_dict: imagenes_dict[key] = []
                imagenes_dict[key].append(value)

        producto = editar_producto_completo(
            db=db, producto_id=producto_id, nombre=nombre, descripcion=descripcion,
            estado=estado, categoria_id=categoria_id, publico_objetivo=publico_objetivo,
            marca_id=marca_id, marca_nombre=marca_nombre, tipo=tipo, variantes=variantes,
            imagenes=imagenes_dict, es_vintage=es_vintage_bool, epoca=epoca
        )
        if not producto: raise HTTPException(status_code=404, detail="Producto no encontrado")
        return {"mensaje": "Producto actualizado correctamente", "producto_id": producto.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@producto_routers.put("/variante/individual/{variante_id}")
async def editar_variante_individual_endpoint(variante_id: int, request: Request, db: Session = Depends(get_session)):
    form_data = await request.form()
    urls_sobrevivientes = json.loads(form_data.get("imagenes_sobrevivientes", "[]"))
    archivos_nuevos = [v for k, v in form_data.multi_items() if k.startswith("file_NUEVA_")]

    resultado = editar_variante_individual(
        db=db, variante_id=variante_id, identidad_variante=form_data.get("identidad_variante"),
        hex_identidad=form_data.get("hex_identidad"), descripcion=form_data.get("descripcion"),
        urls_sobrevivientes=urls_sobrevivientes, archivos_nuevos=archivos_nuevos
    )
    if not resultado: raise HTTPException(status_code=404, detail="Variante no encontrada")
    return resultado

# ✨ ACTUALIZADOS ENDPOINTS INDIVIDUALES (Lote -> StockConfig / Unidad -> StockUnit)

@producto_routers.post("/variante/{variante_id}/stock-config")
def crear_stock_config_individual_endpoint(variante_id: int, payload: dict, db: Session = Depends(get_session)):
    resultado = crear_stock_config_individual(db, variante_id, payload)
    if not resultado: raise HTTPException(status_code=404, detail="El estilo/variante no existe.")
    return resultado

@producto_routers.put("/stock-config/{stock_config_id}")
def editar_stock_config_endpoint(stock_config_id: int, payload: StockConfigEditPayload, db: Session = Depends(get_session)):
    actualizado = actualizar_stock_config_individual(db, stock_config_id, payload.model_dump())
    if not actualizado: raise HTTPException(status_code=404, detail="Configuración de stock no encontrada")
    return {"mensaje": "Stock actualizado correctamente"}

@producto_routers.post("/stock-config/{stock_config_id}/unidades")
def agregar_unidades_endpoint(stock_config_id: int, request: AddStockUnitsRequest, db: Session = Depends(get_session)):
    return agregar_unidades_al_stock_config(db, stock_config_id, request.cantidad)

@producto_routers.put("/stock-unit/{stock_unit_id}/estado")
def cambiar_estado_stock_unit_endpoint(stock_unit_id: int, payload: dict, db: Session = Depends(get_session)):
    nuevo_estado = payload.get("estado_gestion")
    return cambiar_estado_stock_unit(db, stock_unit_id, nuevo_estado)


@producto_routers.put("/stock-unit/{stock_unit_id}")
def actualizar_stock_unit_endpoint(stock_unit_id: int, payload: dict, db: Session = Depends(get_session)):
    """
    Actualiza datos generales de una unidad física (SKU, estado_gestion, etc.)
    """
    return actualizar_stock_unit_individual(db, stock_unit_id, payload)


# ✨ ACTUALIZADA LA PAPELERA Y ELIMINACIÓN PERMANENTE

@producto_routers.put("/{producto_id}/papelera")
def enviar_producto_a_papelera(producto_id: int, db: Session = Depends(get_session)):
    return mover_producto_papelera(db, producto_id)

@producto_routers.put("/variante/{variante_id}/papelera")
def enviar_variante_a_papelera(variante_id: int, db: Session = Depends(get_session)):
    return mover_variante_papelera(db, variante_id)

@producto_routers.put("/stock-config/{stock_config_id}/papelera")
def enviar_stock_config_a_papelera(stock_config_id: int, db: Session = Depends(get_session)):
    return mover_stock_config_papelera(db, stock_config_id)

@producto_routers.put("/stock-unit/{stock_unit_id}/papelera")
def enviar_stock_unit_a_papelera(stock_unit_id: int, db: Session = Depends(get_session)):
    return mover_stock_unit_papelera(db, stock_unit_id)

@producto_routers.put("/{producto_id}/restaurar")
def restaurar_producto(producto_id: int, db: Session = Depends(get_session)):
    return restaurar_producto_papelera(db, producto_id)

@producto_routers.put("/variante/{variante_id}/restaurar")
def restaurar_variante(variante_id: int, db: Session = Depends(get_session)):
    return restaurar_variante_papelera(db, variante_id)

@producto_routers.put("/stock-config/{stock_config_id}/restaurar")
def restaurar_stock_config(stock_config_id: int, db: Session = Depends(get_session)):
    return restaurar_stock_config_papelera(db, stock_config_id)

@producto_routers.put("/stock-unit/{stock_unit_id}/restaurar")
def restaurar_stock_unit(stock_unit_id: int, db: Session = Depends(get_session)):
    return restaurar_stock_unit_papelera(db, stock_unit_id)

@producto_routers.delete("/papelera/{producto_id}")
def destruir_producto(producto_id: int, db: Session = Depends(get_session)):
    res = destruir_producto_total(db, producto_id)
    if not res.get("success"): raise HTTPException(status_code=400, detail=res.get("mensaje"))
    return res

@producto_routers.delete("/papelera/variante/{variante_id}")
def destruir_variante(variante_id: int, db: Session = Depends(get_session)):
    res = destruir_variante_total(db, variante_id)
    if not res.get("success"): raise HTTPException(status_code=400, detail=res.get("mensaje"))
    return res

@producto_routers.delete("/papelera/stock-unit/{stock_unit_id}")
def destruir_stock_unit(stock_unit_id: int, db: Session = Depends(get_session)):
    res = destruir_stock_unit_total(db, stock_unit_id)
    if not res.get("success"): raise HTTPException(status_code=400, detail=res.get("mensaje"))
    return res





# Pega esto justo ANTES de @producto_routers.get("/{producto_id}")
# producto_routers.py

# Asegúrate de importar la función del repositorio arriba:
# from app.repositories.producto_repo import obtener_atributos_por_categoria

@producto_routers.get("/categorias/{categoria_id}/atributos")
def obtener_atributos_por_categoria_endpoint(categoria_id: int, db: Session = Depends(get_session)):
    """
    Devuelve los atributos dinámicos (talla, material, etc.) 
    configurados en la BD para una categoría específica.
    """
    try:
        return obtener_atributos_por_categoria(db, categoria_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al cargar atributos de la categoría: {str(e)}")