# producto_repo.py
import json
import random
import string
from typing import Dict, List, Optional
from datetime import date # ✨ AÑADIDO
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import func, or_, and_, cast, String, desc
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.atributo_categoria_model import AtributoCategoria
from app.models.producto_model import Producto
from app.models.variantes_model import Variante
from app.models.localizaciones_model import Localizacion
from app.models.lotes_model import StockConfig, StockUnit  # ✨ IMPORTACIÓN CORREGIDA
from app.models.atributo_model import Atributo, ValorAtributo
from app.models.marcas_model import Marca
from app.models.categorias_model import Categoria # ✨ MOVIDO AQUÍ
from app.models.variante_imagen_model import Imagen
from app.models.ventas_model import Venta, DetalleVenta 

from app.schemas.variante_schema import VarianteSchema # ✨ ASUMIENDO QUE VarianteSchema ESTÁ AQUÍ O IMPORTADO CORRECTAMENTE
from app.services.s3_service import delete_image_from_s3, upload_image_to_s3
from app.repositories.proveedores_repo import buscar_o_crear
from app.repositories.marcas_repo import crear_marca
from app.repositories.auditoria_repo import registrar_log


# =====================================================
# HELPERS Y UTILIDADES
# =====================================================

def ordenar_tallas_logicamente(tallas):
    orden_letras = {
        'xxs': 1, 'xs': 2, 's': 3, 'm': 4, 'l': 5, 'xl': 6, 'xxl': 7, 
        'xxxl': 8, '3xl': 8, '4xl': 9, 'tu': 99, 'unica': 99, 'única': 99
    }

    def obtener_peso(t):
        t_clean = str(t).strip().lower()
        if t_clean in orden_letras:
            return (0, orden_letras[t_clean], t)
        try:
            return (1, float(t_clean), t)
        except ValueError:
            return (2, 0, t)

    return sorted(list(tallas), key=obtener_peso)

def verificar_vinculo_devolucion(db: Session, stock_unit_id: Optional[int], nuevo_estado: str):
    if nuevo_estado == 'en_camino_devolucion':
        if not stock_unit_id:
            raise HTTPException(
                status_code=400,
                detail="No se puede cambiar el estado a 'En Tránsito (Devolución)' porque esta prenda es nueva y no está vinculada a ninguna venta."
            )
        en_venta = db.query(DetalleVenta).filter(DetalleVenta.stock_unit_id == stock_unit_id).first()
        if not en_venta:
            raise HTTPException(
                status_code=400,
                detail=f"No se puede cambiar el estado de la prenda #{stock_unit_id} a 'En Tránsito (Devolución)' porque esta prenda no está vinculada a ninguna venta."
            )

def generar_sku(tipo: str, id_unico: int) -> str:
    prefijo = tipo[:3].upper() if tipo else "GEN"
    rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"{prefijo}-{rand}-{id_unico}"

def guardar_valores_stock_config(db: Session, config_obj: StockConfig, atributos_data: list):
    try:
        config_obj.valores = []
        db.flush()

        if not atributos_data:
            return

        nombres_solicitados = {a["nombre"].strip().lower() for a in atributos_data if a.get("valor")}
        atributos_existentes = db.query(Atributo).filter(Atributo.nombre.in_(nombres_solicitados)).all()
        cache_atributos = {attr.nombre: attr for attr in atributos_existentes}

        for attr in atributos_data:
            valor_raw = attr.get("valor")
            if valor_raw is None or str(valor_raw).strip() == "":
                continue

            nombre_norm = attr["nombre"].strip().lower()

            if nombre_norm in cache_atributos:
                atributo_obj = cache_atributos[nombre_norm]
            else:
                atributo_obj = Atributo(nombre=nombre_norm)
                db.add(atributo_obj)
                db.flush()
                cache_atributos[nombre_norm] = atributo_obj

            nuevo_valor = ValorAtributo(atributo_id=atributo_obj.id, valor=str(valor_raw).strip().upper())
            config_obj.valores.append(nuevo_valor)
        
        db.flush()

    except Exception as e:
        db.rollback()
        print(f"❌ Error EAV: {e}")
        raise HTTPException(status_code=500, detail=f"Error al procesar atributos: {str(e)}")

def optimizar_imagenes_variante(db: Session, variante: Variante):
    if not variante.imagenes: return
    imagenes_ordenadas = sorted(variante.imagenes, key=lambda x: x.orden or 0)
    if len(imagenes_ordenadas) > 1:
        imagenes_a_borrar = imagenes_ordenadas[1:]
        for img in imagenes_a_borrar:
            try:
                delete_image_from_s3(img.url)
            except Exception: pass
            db.delete(img)
        db.flush()


# =====================================================
# CREACIÓN DE PRODUCTO
# =====================================================

def crear_producto(
    db: Session, nombre: str, estado: str, descripcion: Optional[str], 
    categoria_id: int, tipo: str, publico_objetivo: str, variantes: str, 
    marca_id: Optional[int] = None, marca_nombre: Optional[str] = None, 
    imagenes: Optional[Dict[str, List]] = None, es_vintage: bool = False, 
    epoca: Optional[str] = None
):
    desc_final = descripcion.strip() if descripcion else ""
    if not publico_objetivo or not publico_objetivo.strip():
        raise HTTPException(status_code=400, detail="El público objetivo es obligatorio.")

    try:
        variantes_json = json.loads(variantes)
        variantes_validadas = [VarianteSchema(**v) for v in variantes_json] 
    except ValidationError as e:
        raise HTTPException(status_code=400, detail="Datos de variante inválidos")

    if not marca_id and marca_nombre:
        nombre_clean = marca_nombre.strip()
        marca_existente = db.query(Marca).filter(Marca.nombre.ilike(nombre_clean)).first()
        marca_id = marca_existente.id if marca_existente else crear_marca(db, nombre=nombre_clean).id

    producto = Producto(
        nombre=nombre.strip(), descripcion=desc_final, categoria_id=categoria_id,
        marca_id=marca_id, estado=estado, es_vintage=es_vintage, epoca=epoca,
        tipo=tipo, publico_objetivo=publico_objetivo, sku="TEMP"
    )
    db.add(producto)
    db.flush()
    producto.sku = generar_sku(tipo, producto.id)

    for v_data in variantes_validadas:
        if not v_data.descripcion or not v_data.descripcion.strip():
            raise HTTPException(status_code=400, detail="Cada variante debe tener su propia descripción.")

        nueva_variante = Variante(
            producto_id=producto.id, sku="TEMP", hex_identidad=v_data.hex_identidad,         
            identidad_variante=v_data.identidad_variante, descripcion=v_data.descripcion.strip(),
            orden=v_data.orden
        )
        db.add(nueva_variante)
        db.flush()
        nueva_variante.sku = generar_sku(tipo, nueva_variante.id)

        for config_data in v_data.stock_configs:
            p_id = config_data.proveedor_id
            propietario_id = getattr(config_data, 'propietario_id', None)

            if propietario_id:
                p_id = None 
            else:
                if not p_id and (config_data.proveedor_nombre_nuevo or config_data.proveedor):
                    nombre_p = config_data.proveedor_nombre_nuevo or config_data.proveedor
                    prov_obj = buscar_o_crear(db, nombre_p.strip(), contexto="inventario")
                    p_id = prov_obj.id if prov_obj else None

            config_obj = StockConfig(
                variante_id=nueva_variante.id,
                proveedor_id=p_id,
                propietario_id=propietario_id, 
                donar_ganancias=getattr(config_data, 'donar_ganancias', False), 
                localizacion_id=config_data.localizacion_id,
                etiqueta=config_data.etiqueta,
                precio_compra=config_data.precio_compra, 
                precio_venta=config_data.precio_venta,
                orden=getattr(config_data, 'orden', 0)
            )
            db.add(config_obj)
            db.flush()

            if config_data.atributos:
                attr_dicts = [{"nombre": a.nombre, "valor": a.valor} for a in config_data.atributos]
                guardar_valores_stock_config(db, config_obj, attr_dicts)

            # ✨ CORRECCIÓN: Procesamos las unidades físicas (StockUnits) desde su propio array
            if hasattr(config_data, 'stock_units') and config_data.stock_units:
                for u_data in config_data.stock_units:
                    verificar_vinculo_devolucion(db, None, u_data.estado_gestion)
                    unit = StockUnit(
                        stock_config_id=config_obj.id, 
                        estado_gestion=u_data.estado_gestion,
                        publicar_web=u_data.publicar_web,
                        publicar_vinted=u_data.publicar_vinted,
                        publicar_wallapop=u_data.publicar_wallapop,
                        fecha_compra=u_data.fecha_compra or date.today(), # ✨ DEFAULT TODAY
                        sku=u_data.sku if u_data.sku else "TEMP"
                    )
                    db.add(unit)
                    db.flush()
                    if unit.sku == "TEMP":
                        unit.sku = generar_sku(tipo, unit.id)

            # ✨ Y si el usuario usó el input rápido ("Cantidad de unidades físicas iniciales")
            cantidad_fisica_extra = getattr(config_data, 'cantidad_agregar', 0)
            f_val = getattr(config_data, 'fecha_compra_lote_nuevo', None)
            fecha_ingreso_nueva = f_val if f_val else date.today()
            
            for _ in range(cantidad_fisica_extra):
                unit = StockUnit(
                    stock_config_id=config_obj.id, 
                    estado_gestion='en_stock',
                    publicar_web=False,
                    publicar_vinted=False,
                    publicar_wallapop=False,
                    fecha_compra=fecha_ingreso_nueva,
                    sku="TEMP"
                )
                db.add(unit)
                db.flush()
                unit.sku = generar_sku(tipo, unit.id)

        # Imágenes
        lista_mezclada = v_data.imagenes if v_data.imagenes else []
        for indice, marcador in enumerate(lista_mezclada):
            if isinstance(marcador, str) and marcador.startswith('NUEVA_'):
                key_archivo = f"file_{v_data.temp_id}_{marcador}"
                if imagenes and key_archivo in imagenes:
                    file_to_upload = imagenes[key_archivo][0]
                    url_s3 = upload_image_to_s3(file_to_upload, folder=f"productos/{producto.id}/{nueva_variante.id}")
                    db.add(Imagen(url=url_s3, variante_id=nueva_variante.id, orden=indice))

    db.commit()
    db.refresh(producto)

    # ✨ AUDITORÍA: Registro de creación de producto
    registrar_log(
        db, accion="CREAR", entidad_tipo="PRODUCTO", entidad_id=producto.id,
        nombre_usuario="Sistema", 
        valor_nuevo={"nombre": producto.nombre, "sku": producto.sku, "tipo": producto.tipo},
        notas=f"Producto '{producto.nombre}' registrado con {len(producto.variantes)} variantes."
    )

    return producto


# =====================================================
# EDICIÓN COMPLETA Y PARCIAL
# =====================================================

import json # Asegúrate de que json está importado arriba del archivo

def editar_producto_completo(
    db: Session, producto_id: int, nombre: str, descripcion: str, 
    categoria_id: int, tipo: str, estado: str, publico_objetivo: str, 
    variantes: str, es_vintage: bool = False, epoca: Optional[str] = None,
    marca_id: Optional[int] = None, marca_nombre: Optional[str] = None, 
    imagenes: Optional[Dict[str, List]] = None
):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto: return None

    producto.nombre = nombre
    producto.descripcion = descripcion
    producto.categoria_id = categoria_id
    producto.tipo = tipo
    producto.estado = estado
    producto.publico_objetivo = publico_objetivo
    producto.es_vintage = es_vintage
    producto.epoca = epoca
    
    m_id = int(marca_id) if (marca_id and str(marca_id).isdigit() and int(marca_id) > 0) else None
    if m_id:
        producto.marca_id = m_id
    elif marca_nombre and marca_nombre.strip():
        nombre_clean = marca_nombre.strip()
        marca_existente = db.query(Marca).filter(Marca.nombre.ilike(nombre_clean)).first()
        if marca_existente: producto.marca_id = marca_existente.id
        else:
            nueva_m = crear_marca(db, nombre=nombre_clean)
            producto.marca_id = nueva_m.id

    # ✨ PARCHE 1: Evitar Crash por JSON vacío o corrupto
    if not variantes or variantes.strip() == "":
        variantes_data = []
    else:
        try:
            variantes_data = json.loads(variantes)
        except json.JSONDecodeError:
            variantes_data = []

    # --- DETECCION DE DESACTIVACIONES EN EDICION ---
    unidades_a_desactivar = []
    ids_variantes_vienen = [v.get("id") for v in variantes_data if v.get("id")]
    
    # 1. Variantes enteras removidas
    for v_old in producto.variantes:
        if v_old.id not in ids_variantes_vienen:
            for c in v_old.stock_configs:
                for u in c.stock_units:
                    if u.activo:
                        unidades_a_desactivar.append(u.id)
                        
    # 2. Configs o Stock Units individuales removidos dentro de las variantes que siguen
    for v_data in variantes_data:
        v_id = v_data.get("id")
        if v_id:
            nv = db.query(Variante).filter(Variante.id == v_id).first()
            if nv:
                configs_data = v_data.get("stock_configs", [])
                ids_configs_vienen = [int(c.get("id")) for c in configs_data if c.get("id")]
                
                # Configs removidos de esta variante
                for co_old in nv.stock_configs:
                    if co_old.id not in ids_configs_vienen:
                        for u in co_old.stock_units:
                            if u.activo:
                                unidades_a_desactivar.append(u.id)
                                
                # Stock units individuales removidos de los configs que siguen
                for c_data in configs_data:
                    c_id = c_data.get("id")
                    if c_id:
                        units_data = c_data.get("stock_units", [])
                        ids_units_originales = [int(u.get("id_original", u.get("id"))) for u in units_data if u.get("id_original", u.get("id"))]
                        if ids_units_originales:
                            # Buscar unidades activas de este config que no vienen en el payload
                            unidades_omitidas = db.query(StockUnit.id).filter(
                                StockUnit.stock_config_id == c_id,
                                StockUnit.id.notin_(ids_units_originales),
                                StockUnit.activo == True
                            ).all()
                            for (uid,) in unidades_omitidas:
                                unidades_a_desactivar.append(uid)

    validar_unidades_en_proceso(db, unidades_a_desactivar)

    for v_old in producto.variantes:
        if v_old.id not in ids_variantes_vienen: 
            v_old.activo = False 

    for indice_v, v_data in enumerate(variantes_data):
        v_id = v_data.get("id")
        v_temp_id = str(v_data.get("temp_id"))
        is_v_dirty = v_data.get("is_dirty", True)
        
        if v_id:
            nv = db.query(Variante).filter(Variante.id == v_id).first()
            if nv:
                nv.activo = True
                nv.orden = indice_v # ✨ SIEMPRE actualizamos el orden si vienen en el payload
                if is_v_dirty:
                    nv.hex_identidad = v_data.get("hex_identidad")

                    lista_mezclada = v_data.get("imagenes", []) 
                    urls_permanecen = {item.strip() for item in lista_mezclada if isinstance(item, str) and item.startswith('http')}
                    
                    imagenes_en_db = db.query(Imagen).filter(Imagen.variante_id == nv.id).all()
                    for img_db in imagenes_en_db:
                        if img_db.url.strip() not in urls_permanecen:
                            try: delete_image_from_s3(img_db.url)
                            except: pass
                            db.delete(img_db)

                    for indice_img, item in enumerate(lista_mezclada):
                        item_clean = item.strip() if isinstance(item, str) else item
                        if isinstance(item_clean, str) and item_clean.startswith('http'):
                            img_existente = db.query(Imagen).filter(Imagen.url == item_clean, Imagen.variante_id == nv.id).first()
                            if img_existente: img_existente.orden = indice_img 
                        elif isinstance(item_clean, str) and item_clean.startswith('NUEVA_'):
                            key_archivo = f"file_{v_temp_id}_{item_clean}"
                            if imagenes and key_archivo in imagenes:
                                url_s3 = upload_image_to_s3(imagenes[key_archivo][0], folder=f"productos/{producto.id}/{nv.id}")
                                db.add(Imagen(url=url_s3, variante_id=nv.id, orden=indice_img)) 
        else:
            nv = Variante(
                producto_id=producto.id, sku="TEMP", hex_identidad=v_data.get("hex_identidad"),
                identidad_variante=v_data.get("identidad_variante"), descripcion=v_data.get("descripcion"), orden=indice_v 
            )
            db.add(nv)
            db.flush() 
            nv.sku = generar_sku(tipo, nv.id)

            # ✨ PARCHE: Procesar imágenes para la NUEVA variante
            lista_mezclada = v_data.get("imagenes", [])
            for indice_img, marcador in enumerate(lista_mezclada):
                if isinstance(marcador, str) and marcador.startswith('NUEVA_'):
                    key_archivo = f"file_{v_temp_id}_{marcador}"
                    if imagenes and key_archivo in imagenes:
                        file_to_upload = imagenes[key_archivo][0]
                        url_s3 = upload_image_to_s3(file_to_upload, folder=f"productos/{producto.id}/{nv.id}")
                        db.add(Imagen(url=url_s3, variante_id=nv.id, orden=indice_img))

        # GESTIÓN DE STOCK CONFIGS (Anteriormente Lotes)
        configs_data = v_data.get("stock_configs", [])
        ids_configs_vienen = [int(c.get("id")) for c in configs_data if c.get("id")]
        
        if ids_configs_vienen:
            db.query(StockConfig).filter(StockConfig.variante_id == nv.id, StockConfig.id.notin_(ids_configs_vienen)).update({"activo": False}, synchronize_session=False)
        else:
            db.query(StockConfig).filter(StockConfig.variante_id == nv.id).update({"activo": False}, synchronize_session=False)

        for indice_c, c_data in enumerate(configs_data):
            c_id = c_data.get("id")
            
            raw_p_id = c_data.get("proveedor_id")
            p_id = int(raw_p_id) if (raw_p_id and str(raw_p_id).isdigit() and int(raw_p_id) > 0) else None

            if not p_id:
                nombre_p = c_data.get("proveedor_nombre_nuevo") or c_data.get("proveedor")
                if nombre_p and nombre_p.strip():
                    prov_obj = buscar_o_crear(db, nombre_p.strip())
                    p_id = prov_obj.id if prov_obj else None

            if c_id:
                co = db.query(StockConfig).filter(StockConfig.id == c_id).first()
                if co:
                    co.activo = True
                    co.orden = indice_c # ✨ SIEMPRE actualizamos el orden si vienen en el payload
                    if c_data.get("is_dirty", True):
                        co.etiqueta = c_data.get("etiqueta")
                        co.localizacion_id = c_data.get("localizacion_id")
                        co.precio_compra = c_data.get("precio_compra", 0)
                        co.precio_venta = c_data.get("precio_venta", 0)
                        co.proveedor_id = p_id 
                        co.fecha_compra = c_data.get("fecha_compra") or None
                        co.descuento = c_data.get("descuento", 0)
                        co.donar_ganancias = c_data.get("donar_ganancias", False)
                        if c_data.get("atributos"):
                            guardar_valores_stock_config(db, co, c_data.get("atributos"))

                # Actualización de unidades físicas enviadas
                units_data = c_data.get("stock_units", [])
                
                # Usamos id_original para no perder el rastro de la unidad si cambiaron el ID en la interfaz
                ids_units_originales = [int(u.get("id_original", u.get("id"))) for u in units_data if u.get("id_original", u.get("id"))]
                
                if ids_units_originales:
                    # ✨ PARCHE 2: Proteger unidades con historial de ser desactivadas accidentalmente
                    estados_protegidos = ['vendido', 'extraviado', 'donado_a_ong', 'devuelto_dueno']
                    db.query(StockUnit).filter(
                        StockUnit.stock_config_id == c_id, 
                        StockUnit.id.notin_(ids_units_originales),
                        ~StockUnit.estado_gestion.in_(estados_protegidos) 
                    ).update({"activo": False}, synchronize_session=False)
                
                for u_data in units_data:
                    u_id_original = u_data.get("id_original", u_data.get("id"))
                    u_id_nuevo = u_data.get("id")
                    
                    unit_obj = None
                    if u_id_original:
                        unit_obj = db.query(StockUnit).filter(StockUnit.id == int(u_id_original)).first()
                        if unit_obj:
                            unit_obj.activo = True
                            
                            nuevo_est = u_data.get("estado_gestion", "en_stock")
                            verificar_vinculo_devolucion(db, unit_obj.id, nuevo_est)
                            # 🛡️ PROTECCIÓN FINANCIERA: No permitir revertir 'vendido' si hay ticket activo
                            if unit_obj.estado_gestion == 'vendido' and nuevo_est != 'vendido':
                                venta_activa = db.query(Venta).join(DetalleVenta).filter(
                                    DetalleVenta.stock_unit_id == unit_obj.id,
                                    Venta.estado_envio != 'cancelado',
                                    Venta.estado_pago != 'reembolsado',
                                    DetalleVenta.devuelto == False
                                ).first()
                                if venta_activa:
                                    raise HTTPException(
                                        status_code=400, 
                                        detail=f"No puedes reactivar la prenda #{unit_obj.id} (Venta {venta_activa.codigo_venta}). Gestiona la devolución en el módulo de Ventas para que el dinero cuadre."
                                    )

                            unit_obj.estado_gestion = nuevo_est
                            unit_obj.publicar_web = u_data.get("publicar_web", False)
                            unit_obj.publicar_vinted = u_data.get("publicar_vinted", False)
                            unit_obj.publicar_wallapop = u_data.get("publicar_wallapop", False)
                            
                            # ✨ LÓGICA ROBUSTA PARA FECHA: Si viene algo, usarlo. Si no, y la prenda no tenía fecha, usar hoy.
                            f_nueva = u_data.get("fecha_compra")
                            if f_nueva:
                                unit_obj.fecha_compra = f_nueva
                            elif not unit_obj.fecha_compra:
                                unit_obj.fecha_compra = date.today()
                                
                            # Si cambiaron el ID en el input y presionaron Guardar General en lugar de Guardar Individual
                            if u_id_nuevo and int(u_id_nuevo) != int(u_id_original):
                                # 🛡️ VERIFICACIÓN DE INTEGRIDAD: Si la prenda ya se vendió, no dejamos tocar el ID
                                en_venta = db.query(DetalleVenta).filter(DetalleVenta.stock_unit_id == int(u_id_original)).first()
                                if en_venta:
                                    raise HTTPException(
                                        status_code=400, 
                                        detail=f"No puedes cambiar el ID de la prenda #{u_id_original} porque ya está vinculada a una venta o historial financiero."
                                    )

                                existe = db.query(StockUnit).filter(StockUnit.id == int(u_id_nuevo)).first()
                                if existe:
                                    raise HTTPException(status_code=400, detail=f"El ID físico #{u_id_nuevo} ya está en uso por otra prenda o está duplicado en este formulario. Revisa los números e inténtalo de nuevo.")
                                db.query(StockUnit).filter(StockUnit.id == int(u_id_original)).update({"id": int(u_id_nuevo)})
                                db.flush()
                            
                # Agregar unidades nuevas escritas a mano
                cantidad_extra = int(c_data.get("cantidad_agregar", 0))
                fecha_ingreso_nueva = c_data.get("fecha_compra_lote_nuevo") or date.today()
                
                for _ in range(cantidad_extra):
                    su = StockUnit(
                        stock_config_id=co.id, 
                        estado_gestion="en_stock", 
                        sku="TEMP",
                        fecha_compra=fecha_ingreso_nueva
                    )
                    db.add(su)
                    db.flush()
                    su.sku = generar_sku(tipo, su.id)
            else:
                co = StockConfig(
                    variante_id=nv.id, proveedor_id=p_id, propietario_id=c_data.get("propietario_id"),
                    donar_ganancias=c_data.get("donar_ganancias", False), etiqueta=c_data.get("etiqueta", "Única"), 
                    ubicacion=c_data.get("ubicacion", ""), 
                    localizacion_id=c_data.get("localizacion_id"),
                    precio_compra=c_data.get("precio_compra", 0), 
                    precio_venta=c_data.get("precio_venta", 0),
                    orden=indice_c
                )
                db.add(co)
                db.flush()
                
                if c_data.get("atributos"):
                    guardar_valores_stock_config(db, co, c_data.get("atributos"))
                
                cantidad_total = int(c_data.get("cantidad_agregar", 1))
                fecha_ingreso_nueva = c_data.get("fecha_compra_lote_nuevo") or date.today()
                
                for _ in range(cantidad_total):
                    su = StockUnit(
                        stock_config_id=co.id, estado_gestion="en_stock", sku="TEMP", 
                        publicar_web=c_data.get("publicar_web", False), 
                        publicar_vinted=c_data.get("publicar_vinted", False), 
                        publicar_wallapop=c_data.get("publicar_wallapop", False),
                        fecha_compra=fecha_ingreso_nueva # ✨ AÑADIDO
                    )
                    db.add(su)
                    db.flush()
                    su.sku = generar_sku(tipo, su.id)

    db.commit()
    db.refresh(producto)
    return producto


def editar_variante_individual(
    db: Session, variante_id: int, identidad_variante: str, hex_identidad: str, 
    descripcion: str, urls_sobrevivientes: list, archivos_nuevos: list
):
    variante = db.query(Variante).filter(Variante.id == variante_id).first()
    if not variante: return None

    variante.identidad_variante = identidad_variante
    variante.hex_identidad = hex_identidad
    variante.descripcion = descripcion

    for img_db in list(variante.imagenes):
        if img_db.url not in urls_sobrevivientes:
            try: delete_image_from_s3(img_db.url)
            except Exception as e: print(f"Error borrando imagen de S3: {e}")
            db.delete(img_db)

    orden_base = len([img for img in variante.imagenes if img.url in urls_sobrevivientes])
    
    for idx, file in enumerate(archivos_nuevos):
        url_s3 = upload_image_to_s3(file, folder=f"productos/{variante.producto_id}/{variante.id}")
        db.add(Imagen(url=url_s3, variante_id=variante.id, orden=orden_base + idx))

    db.commit()
    db.refresh(variante)
    imagenes_finales = [img.url for img in sorted(variante.imagenes, key=lambda x: x.orden or 0)]
    return {"mensaje": "Estilo e imágenes actualizadas correctamente", "imagenes_actualizadas": imagenes_finales}


def crear_stock_config_individual(db: Session, variante_id: int, payload: dict):
    variante = db.query(Variante).filter(Variante.id == variante_id).first()
    if not variante: return None
    
    p_id = payload.get("proveedor_id")
    if not p_id and payload.get("proveedor_nombre_nuevo"):
        prov_obj = buscar_o_crear(db, payload.get("proveedor_nombre_nuevo").strip())
        p_id = prov_obj.id if prov_obj else None
        
    config_obj = StockConfig(
        variante_id=variante.id,
        proveedor_id=p_id,
        propietario_id=payload.get("propietario_id"),
        precio_compra=payload.get("precio_compra", 0.0),
        precio_venta=payload.get("precio_venta", 0.0),
        etiqueta=payload.get("etiqueta", "Única"),
        ubicacion=payload.get("ubicacion", ""),
        localizacion_id=payload.get("localizacion_id"),
        donar_ganancias=payload.get("donar_ganancias", False)
    )
    db.add(config_obj)
    db.flush()
    
    if payload.get("atributos"):
        guardar_valores_stock_config(db, config_obj, payload.get("atributos"))
        
    cantidad = payload.get("cantidad_agregar", 1)
    fecha_ingreso = payload.get("fecha_compra") or date.today()
    
    for _ in range(cantidad):
        unit = StockUnit(
            stock_config_id=config_obj.id,
            estado_gestion="en_stock",
            sku="TEMP",
            publicar_web=payload.get("publicar_web", False),
            publicar_vinted=payload.get("publicar_vinted", False),
            publicar_wallapop=payload.get("publicar_wallapop", False),
            fecha_compra=fecha_ingreso
        )
        db.add(unit)
        db.flush()
        unit.sku = generar_sku(variante.producto.tipo, unit.id)
        
    db.commit()
    return {"mensaje": "Configuración de stock creada con éxito", "stock_config_id": config_obj.id}


def actualizar_stock_config_individual(db: Session, stock_config_id: int, datos_nuevos: dict):
    config = db.query(StockConfig).filter(StockConfig.id == stock_config_id).first()
    if not config: return None

    if datos_nuevos.get("precio_compra") is not None: config.precio_compra = datos_nuevos["precio_compra"]
    if datos_nuevos.get("precio_venta") is not None: config.precio_venta = datos_nuevos["precio_venta"]
    if datos_nuevos.get("descuento") is not None: config.descuento = datos_nuevos["descuento"]
    if datos_nuevos.get("ubicacion") is not None: config.ubicacion = datos_nuevos["ubicacion"]
    if datos_nuevos.get("localizacion_id") is not None: config.localizacion_id = datos_nuevos["localizacion_id"]
    if datos_nuevos.get("donar_ganancias") is not None: config.donar_ganancias = datos_nuevos["donar_ganancias"]

    p_id = datos_nuevos.get("proveedor_id")
    if p_id: 
        config.proveedor_id = p_id
    elif datos_nuevos.get("proveedor_nombre_nuevo"):
        nuevo_p = buscar_o_crear(db, datos_nuevos["proveedor_nombre_nuevo"])
        config.proveedor_id = nuevo_p.id

    if datos_nuevos.get("atributos") is not None:
        guardar_valores_stock_config(db, config, datos_nuevos.get("atributos"))

    # ✨ ACTUALIZACIÓN DE UNIDADES FÍSICAS (StockUnits)
    units_data = datos_nuevos.get("stock_units")
    if units_data:
        for u_data in units_data:
            u_id_original = u_data.get("id_original") or u_data.get("id")
            u_id_nuevo = u_data.get("id")
            
            if u_id_original:
                unit_obj = db.query(StockUnit).filter(StockUnit.id == int(u_id_original)).first()
                if unit_obj:
                    nuevo_est = u_data.get("estado_gestion", unit_obj.estado_gestion)
                    verificar_vinculo_devolucion(db, unit_obj.id, nuevo_est)
                    # 🛡️ PROTECCIÓN FINANCIERA: No permitir revertir 'vendido' si hay ticket activo
                    if unit_obj.estado_gestion == 'vendido' and nuevo_est != 'vendido':
                        venta_activa = db.query(Venta).join(DetalleVenta).filter(
                            DetalleVenta.stock_unit_id == unit_obj.id,
                            Venta.estado_envio != 'cancelado',
                            Venta.estado_pago != 'reembolsado',
                            DetalleVenta.devuelto == False
                            ).first()
                        if venta_activa:
                            raise HTTPException(
                                status_code=400, 
                                detail=f"No puedes reactivar la prenda #{unit_obj.id} (Venta {venta_activa.codigo_venta}). Gestiona la devolución en el módulo de Ventas para que el dinero cuadre."
                            )

                    unit_obj.estado_gestion = nuevo_est
                    unit_obj.publicar_web = u_data.get("publicar_web", unit_obj.publicar_web)
                    unit_obj.publicar_vinted = u_data.get("publicar_vinted", unit_obj.publicar_vinted)
                    unit_obj.publicar_wallapop = u_data.get("publicar_wallapop", unit_obj.publicar_wallapop)
                    
                    # ✨ LÓGICA ROBUSTA PARA FECHA: Si viene algo, usarlo. Si no, y la prenda no tenía fecha, usar hoy.
                    f_nueva = u_data.get("fecha_compra")
                    if f_nueva:
                        unit_obj.fecha_compra = f_nueva
                    elif not unit_obj.fecha_compra:
                        unit_obj.fecha_compra = date.today()
                    
                    if u_id_nuevo and int(u_id_nuevo) != int(u_id_original):
                        # 🛡️ VERIFICACIÓN DE INTEGRIDAD: Si la prenda ya se vendió, no dejamos tocar el ID
                        en_venta = db.query(DetalleVenta).filter(DetalleVenta.stock_unit_id == int(u_id_original)).first()
                        if en_venta:
                            raise HTTPException(
                                status_code=400, 
                                detail=f"No puedes cambiar el ID de la prenda #{u_id_original} porque ya está vinculada a una venta o historial financiero."
                            )

                        existe = db.query(StockUnit).filter(StockUnit.id == int(u_id_nuevo)).first()
                        if existe:
                            raise HTTPException(status_code=400, detail=f"El ID físico #{u_id_nuevo} ya está en uso por otra prenda.")
                        
                        db.query(StockUnit).filter(StockUnit.id == int(u_id_original)).update({"id": int(u_id_nuevo)})
                        db.flush()

    db.commit()
    db.refresh(config)
    return config


def agregar_unidades_al_stock_config(db: Session, stock_config_id: int, cantidad_extra: int, fecha_compra: Optional[str] = None):
    config = db.query(StockConfig).filter(StockConfig.id == stock_config_id).first()
    if not config: raise HTTPException(status_code=404, detail="Configuración de stock no encontrada")

    nuevas_unidades = []
    fecha_ingreso = fecha_compra or date.today()
    
    for _ in range(cantidad_extra):
        unidad = StockUnit(
            stock_config_id=config.id, 
            estado_gestion="en_stock", 
            sku="TEMP",
            fecha_compra=fecha_ingreso
        )
        db.add(unidad)
        db.flush()
        unidad.sku = generar_sku(config.variante.producto.tipo, unidad.id)
        nuevas_unidades.append(unidad)

    db.commit()
    return {
        "mensaje": f"Se han añadido {cantidad_extra} unidades físicas a la configuración.",
        "new_ids": [u.id for u in nuevas_unidades],
        "unidades": [{"id": u.id, "sku": u.sku, "estado_gestion": u.estado_gestion, "fecha_compra": u.fecha_compra.isoformat() if u.fecha_compra else None} for u in nuevas_unidades]
    }


def cambiar_estado_stock_unit(db: Session, stock_unit_id: int, nuevo_estado: str):
    unidad = db.query(StockUnit).filter(StockUnit.id == stock_unit_id).first()
    if not unidad: raise HTTPException(status_code=404, detail="Unidad física no encontrada")

    # 🛡️ PROTECCIÓN FINANCIERA INTELIGENTE
    if unidad.estado_gestion == 'vendido' and nuevo_estado != 'vendido':
        venta_activa = db.query(Venta).join(DetalleVenta).filter(
            DetalleVenta.stock_unit_id == stock_unit_id,
            Venta.estado_envio != 'cancelado',
            Venta.estado_pago != 'reembolsado',
            DetalleVenta.devuelto == False
            ).first()
        if venta_activa:
            raise HTTPException(
                status_code=400, 
                detail=f"Operación denegada. La prenda #{stock_unit_id} tiene una venta activa ({venta_activa.codigo_venta}). Gestiona la devolución en Ventas."
            )

    if nuevo_estado in ['vendido', 'extraviado', 'donado_a_ong', 'devuelto_dueno']:
        unidad.publicar_web = False
        unidad.publicar_vinted = False
        unidad.publicar_wallapop = False
        
    unidad.estado_gestion = nuevo_estado
    db.commit()
    return unidad


def actualizar_stock_unit_individual(db: Session, stock_unit_id: int, datos_nuevos: dict):
    unidad = db.query(StockUnit).filter(StockUnit.id == stock_unit_id).first()
    if not unidad:
        raise HTTPException(status_code=404, detail="Unidad física no encontrada")

    # GESTIÓN DE CAMBIO DE ID (PRIMARY KEY)
    nuevo_id = datos_nuevos.get("id")
    if nuevo_id is not None:
        try:
            nuevo_id_int = int(nuevo_id)
            if nuevo_id_int != stock_unit_id:
                # 🛡️ VERIFICACIÓN DE INTEGRIDAD: Si la prenda ya se vendió, no dejamos tocar el ID
                en_venta = db.query(DetalleVenta).filter(DetalleVenta.stock_unit_id == stock_unit_id).first()
                if en_venta:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"No puedes cambiar el ID de la prenda #{stock_unit_id} porque ya está vinculada a una venta o historial financiero."
                    )

                # Verificar si el nuevo ID ya existe
                existe = db.query(StockUnit).filter(StockUnit.id == nuevo_id_int).first()
                if existe:
                    raise HTTPException(status_code=400, detail=f"El ID #{nuevo_id_int} ya está en uso por otra prenda.")

                # Actualización directa del PK (Bypass session object tracking)
                db.query(StockUnit).filter(StockUnit.id == stock_unit_id).update({"id": nuevo_id_int})
                db.flush()
                # Refrescamos la referencia para seguir con el resto de campos
                unidad = db.query(StockUnit).filter(StockUnit.id == nuevo_id_int).first()
                stock_unit_id = nuevo_id_int
        except ValueError:
            raise HTTPException(status_code=400, detail="El ID debe ser un número entero.")
    nuevo_sku = datos_nuevos.get("sku")
    if nuevo_sku:
        nuevo_sku = nuevo_sku.strip()
        # Verificar si el SKU ya existe en otra unidad
        existe = db.query(StockUnit).filter(StockUnit.sku == nuevo_sku, StockUnit.id != stock_unit_id).first()
        if existe:
            raise HTTPException(status_code=400, detail=f"El SKU '{nuevo_sku}' ya está en uso por otra prenda.")
        unidad.sku = nuevo_sku

    if "estado_gestion" in datos_nuevos:
        nuevo_estado = datos_nuevos["estado_gestion"]
        verificar_vinculo_devolucion(db, stock_unit_id, nuevo_estado)
        
        # 🛡️ PROTECCIÓN FINANCIERA: No permitir revertir 'vendido' si hay ticket activo
        if unidad.estado_gestion == 'vendido' and nuevo_estado != 'vendido':
            venta_activa = db.query(Venta).join(DetalleVenta).filter(
                DetalleVenta.stock_unit_id == stock_unit_id,
                Venta.estado_envio != 'cancelado',
                Venta.estado_pago != 'reembolsado',
                DetalleVenta.devuelto == False
                ).first()
            if venta_activa:
                raise HTTPException(
                    status_code=400, 
                    detail=f"No puedes reactivar la prenda #{stock_unit_id} (Venta {venta_activa.codigo_venta}). Gestiona la devolución en el módulo de Ventas para que el dinero cuadre."
                )

        if nuevo_estado in ['vendido', 'extraviado', 'donado_a_ong', 'devuelto_dueno']:
            unidad.publicar_web = False
            unidad.publicar_vinted = False
            unidad.publicar_wallapop = False
        unidad.estado_gestion = nuevo_estado

    if "fecha_compra" in datos_nuevos:
        unidad.fecha_compra = datos_nuevos["fecha_compra"] or date.today()
    
    if "publicar_web" in datos_nuevos:
        unidad.publicar_web = datos_nuevos["publicar_web"]
    if "publicar_vinted" in datos_nuevos:
        unidad.publicar_vinted = datos_nuevos["publicar_vinted"]
    if "publicar_wallapop" in datos_nuevos:
        unidad.publicar_wallapop = datos_nuevos["publicar_wallapop"]

    db.commit()
    db.refresh(unidad)
    return unidad


# =====================================================
# LISTADOS Y PAGINACIÓN
# =====================================================

def obtener_productos_paginados(
    db: Session, page: int = 1, limit: int = 10, search: str = None, 
    tipo_busqueda: str = "producto_id", categoria_id: int = None, marca_id: int = None,
    color: str = None, talla: str = None, estado: str = None, material: str = None, 
    precio_min: float = None, precio_max: float = None, solo_vendidos: bool = False, 
    ordenar_por: str = "fecha_desc", fecha_inicio: str = None, fecha_fin: str = None,
    disponibilidad: str = "todos", proveedores_ids: List[int] = None,
    localizacion_id: int = None, propietario_id: int = None
):
    offset = (page - 1) * limit
    query = db.query(Producto).filter(Producto.activo == True)

    necesita_join_configs = talla or precio_min is not None or precio_max is not None or solo_vendidos or (search and tipo_busqueda == 'stock_config_id') or (proveedores_ids and len(proveedores_ids) > 0) or localizacion_id or propietario_id
    
    if necesita_join_configs:
        query = query.join(Producto.variantes).join(Variante.stock_configs)
    elif color or disponibilidad != "todos":
        query = query.join(Producto.variantes)

    if search and search.strip():
        term = search.strip()
        if tipo_busqueda == 'producto_id' and term.isdigit():
            query = query.filter(Producto.id == int(term))
        elif tipo_busqueda == 'stock_config_id' and term.isdigit():
            query = query.filter(StockConfig.id == int(term))
        else:
            s = f"%{term}%"
            query = query.filter(or_(
                cast(Producto.id, String).ilike(s),
                Producto.sku.ilike(s),
                Producto.nombre.ilike(s)
            ))

    if categoria_id:
        from app.models.categorias_model import Categoria
        todas_cats = db.query(Categoria.id, Categoria.parent_id).all()
        hijos_map = {}
        for c_id, p_id in todas_cats:
            if p_id not in hijos_map: hijos_map[p_id] = []
            hijos_map[p_id].append(c_id)
            
        def get_all_subcats_mem(cat_id):
            ids = [cat_id]
            if cat_id in hijos_map:
                for sub_id in hijos_map[cat_id]:
                    ids.extend(get_all_subcats_mem(sub_id))
            return ids
            
        all_cat_ids = get_all_subcats_mem(categoria_id)
        query = query.filter(Producto.categoria_id.in_(all_cat_ids))

    if marca_id: query = query.filter(Producto.marca_id == marca_id)
    if estado: query = query.filter(Producto.estado == estado)
    
    if proveedores_ids and len(proveedores_ids) > 0:
        query = query.filter(StockConfig.proveedor_id.in_(proveedores_ids))

    if color:
        colors = [c.replace('#', '').lower().strip() for c in color.split(',') if c.strip()]
        if colors:
            condiciones_color = [func.lower(Variante.hex_identidad).like(f"%#{c}%") for c in colors]
            query = query.filter(Producto.variantes.any(or_(*condiciones_color)))

    if disponibilidad == "en_stock":
        query = query.filter(Producto.variantes.any(Variante.stock_configs.any(StockConfig.stock_units.any(StockUnit.estado_gestion == 'en_stock'))))
    elif disponibilidad == "agotado":
        query = query.filter(~Producto.variantes.any(Variante.stock_configs.any(StockConfig.stock_units.any(StockUnit.estado_gestion == 'en_stock'))))
        
    if fecha_inicio: query = query.filter(Producto.fecha_registro >= fecha_inicio)
    if fecha_fin: query = query.filter(Producto.fecha_registro <= f"{fecha_fin} 23:59:59")
        
    if talla:
        query = query.join(StockConfig.valores).join(ValorAtributo.atributo).filter(
            and_(Atributo.nombre.ilike("talla"), ValorAtributo.valor == talla)
        )
        
    if precio_min is not None: query = query.filter(StockConfig.precio_venta >= precio_min)
    if precio_max is not None: query = query.filter(StockConfig.precio_venta <= precio_max)
    
    if solo_vendidos:
        query = query.filter(StockConfig.stock_units.any(StockUnit.estado_gestion == 'vendido'))

    if ordenar_por == "fecha_asc": query = query.order_by(Producto.fecha_registro.asc())
    else: query = query.order_by(desc(Producto.id))

    total = query.distinct().count()

    productos = (
        query.distinct()
        .options(
            selectinload(Producto.categoria), selectinload(Producto.marca),
            selectinload(Producto.variantes).selectinload(Variante.stock_configs).selectinload(StockConfig.stock_units),
            selectinload(Producto.variantes).selectinload(Variante.stock_configs).selectinload(StockConfig.valores).selectinload(ValorAtributo.atributo),
            selectinload(Producto.variantes).selectinload(Variante.imagenes)
        )
        .offset(offset).limit(limit).all()
    )

    resultados = []
    for p in productos:
        vars_activas = sorted([v for v in p.variantes if v.activo], key=lambda x: x.orden or 0)
        variante_principal = vars_activas[0] if vars_activas else None
        
        if color:
            c_target = f"#{color.replace('#', '').lower()}"
            v_match = next((v for v in vars_activas if v.hex_identidad and v.hex_identidad.lower() == c_target), None)
            if v_match: variante_principal = v_match

        img_url = None
        if variante_principal and variante_principal.imagenes:
            img_sorted = sorted(variante_principal.imagenes, key=lambda x: x.orden or 0)
            if img_sorted: img_url = img_sorted[0].url
        
        stock_total = sum(1 for v in vars_activas for c in v.stock_configs if c.activo for u in c.stock_units if u.activo and u.estado_gestion == 'en_stock')
        
        p_venta, p_compra = 0.0, 0.0
        if variante_principal and variante_principal.stock_configs:
            configs_activos = [c for c in variante_principal.stock_configs if c.activo]
            if configs_activos:
                p_venta, p_compra = configs_activos[0].precio_venta, configs_activos[0].precio_compra
        
        tallas_set = set()
        canales_activos = {"web": False, "vinted": False, "wallapop": False}

        for v in vars_activas:
            for config in v.stock_configs:
                if not config.activo: continue
                for val in config.valores:
                    if val.atributo and val.atributo.nombre.lower() in ['talla', 'size', 'medida']:
                        tallas_set.add(val.valor)
                for u in config.stock_units:
                    if u.activo and u.estado_gestion == 'en_stock':
                        if u.publicar_web: canales_activos["web"] = True
                        if u.publicar_vinted: canales_activos["vinted"] = True
                        if u.publicar_wallapop: canales_activos["wallapop"] = True

        resultados.append({
            "id": p.id,
            "nombre": p.nombre,
            "sku": p.sku,
            "tipo": p.tipo,
            "categoria": {"id": p.categoria.id, "nombre": p.categoria.nombre} if p.categoria else None,
            "marca": {"id": p.marca.id, "nombre": p.marca.nombre} if p.marca else None,
            "imagen": img_url,
            "stock_total": stock_total,
            "precio_compra": float(p_compra),
            "precio_venta": float(p_venta),
            "colores": list({v.hex_identidad for v in vars_activas if v.hex_identidad}),
            "tallas": ordenar_tallas_logicamente(tallas_set),
            "canales": canales_activos
        })

    return {"total": total, "items": resultados}


def obtener_stock_configs_individuales_paginados(
    db: Session, page: int = 1, limit: int = 10, search: str = None, 
    tipo_busqueda: str = "stock_config_id", categoria_id: int = None, marca_id: int = None,
    color: str = None, talla: str = None, estado: str = None, precio_min: float = None, 
    precio_max: float = None, solo_vendidos: bool = False, ordenar_por: str = "fecha_desc",
    fecha_inicio: str = None, fecha_fin: str = None, disponibilidad: str = "todos",
    proveedores_ids: List[int] = None, localizacion_id: int = None, propietario_id: int = None
):
    offset = (page - 1) * limit
    
    query = (
        db.query(StockConfig)
        .join(StockConfig.variante)
        .join(Variante.producto)
        .filter(StockConfig.activo == True, Variante.activo == True, Producto.activo == True)
    )

    if propietario_id:
        query = query.filter(StockConfig.propietario_id == propietario_id)
        
    if localizacion_id:
        query = query.filter(StockConfig.localizacion_id == localizacion_id)

    if search and search.strip():
        term = search.strip()
        if tipo_busqueda == 'stock_unit_id' and term.isdigit():
            query = query.filter(StockConfig.stock_units.any(StockUnit.id == int(term)))
        elif tipo_busqueda == 'producto_id' and term.isdigit():
            query = query.filter(Producto.id == int(term))
        else:
            s = f"%{term}%"
            query = query.filter(or_(
                cast(StockConfig.id, String).ilike(s), 
                Producto.sku.ilike(s), 
                Producto.nombre.ilike(s),
                StockConfig.stock_units.any(
                    or_(
                        StockUnit.sku.ilike(s),
                        cast(StockUnit.id, String).ilike(s)
                    )
                )
            ))

    if categoria_id:
        from app.models.categorias_model import Categoria
        todas_cats = db.query(Categoria.id, Categoria.parent_id).all()
        hijos_map = {}
        for c_id, p_id in todas_cats:
            if p_id not in hijos_map: hijos_map[p_id] = []
            hijos_map[p_id].append(c_id)
            
        def get_all_subcats_mem(cat_id):
            ids = [cat_id]
            if cat_id in hijos_map:
                for sub_id in hijos_map[cat_id]:
                    ids.extend(get_all_subcats_mem(sub_id))
            return ids
            
        all_cat_ids = get_all_subcats_mem(categoria_id)
        query = query.filter(Producto.categoria_id.in_(all_cat_ids))

    if marca_id: query = query.filter(Producto.marca_id == marca_id)
    if estado: query = query.filter(Producto.estado == estado)

    if disponibilidad == "en_stock":
        query = query.filter(StockConfig.stock_units.any(StockUnit.estado_gestion == 'en_stock'))
    elif disponibilidad == "agotado":
        query = query.filter(~StockConfig.stock_units.any(StockUnit.estado_gestion == 'en_stock'))
        
    if solo_vendidos:
        query = query.filter(StockConfig.stock_units.any(StockUnit.estado_gestion == 'vendido'))
        
    if proveedores_ids and len(proveedores_ids) > 0:
        query = query.filter(StockConfig.proveedor_id.in_(proveedores_ids))

    if color:
        colors = [c.replace('#', '').lower().strip() for c in color.split(',') if c.strip()]
        if colors:
            condiciones_color = [func.lower(Variante.hex_identidad).like(f"%#{c}%") for c in colors]
            query = query.filter(or_(*condiciones_color))

    if fecha_inicio: query = query.filter(Producto.fecha_registro >= fecha_inicio)
    if fecha_fin: query = query.filter(Producto.fecha_registro <= f"{fecha_fin} 23:59:59")
    
    if talla:
        query = query.join(StockConfig.valores).join(ValorAtributo.atributo).filter(
            and_(Atributo.nombre.ilike("talla"), ValorAtributo.valor == talla)
        )
        
    if precio_min is not None: query = query.filter(StockConfig.precio_venta >= precio_min)
    if precio_max is not None: query = query.filter(StockConfig.precio_venta <= precio_max)

    if ordenar_por == "precio_venta_asc": query = query.order_by(StockConfig.precio_venta.asc())
    elif ordenar_por == "precio_venta_desc": query = query.order_by(StockConfig.precio_venta.desc())
    elif ordenar_por == "precio_compra_asc": query = query.order_by(StockConfig.precio_compra.asc())
    elif ordenar_por == "precio_compra_desc": query = query.order_by(StockConfig.precio_compra.desc())
    elif ordenar_por == "fecha_asc": query = query.order_by(StockConfig.id.asc())
    else: query = query.order_by(desc(StockConfig.id))

    total_configs = query.distinct().count()
    
    configs = query.options(
        selectinload(StockConfig.variante).selectinload(Variante.producto).selectinload(Producto.categoria),
        selectinload(StockConfig.variante).selectinload(Variante.producto).selectinload(Producto.marca),
        selectinload(StockConfig.variante).selectinload(Variante.imagenes),
        selectinload(StockConfig.localizacion),
        selectinload(StockConfig.propietario),
        selectinload(StockConfig.valores).selectinload(ValorAtributo.atributo),
        selectinload(StockConfig.stock_units)
    ).offset(offset).limit(limit).all()

    resultados = []
    for c in configs:
        v = c.variante
        p = v.producto
        
        talla_val = None
        atributos_extra = {}
        for val in c.valores:
            if val.atributo:
                nombre_attr = val.atributo.nombre.lower()
                if nombre_attr in ['talla', 'size', 'medida']: talla_val = val.valor
                else: atributos_extra[nombre_attr] = val.valor

        img_url = None
        if v.imagenes:
            img_sorted = sorted(v.imagenes, key=lambda x: x.orden or 0)
            if img_sorted: img_url = img_sorted[0].url

        unidades_activas = [u for u in c.stock_units if u.activo]
        disponibles = sum(1 for u in unidades_activas if u.estado_gestion == 'en_stock')

        resultados.append({
            "stock_config_id": c.id,
            "variante_id": v.id,
            "producto_id": p.id,
            "producto_nombre": p.nombre,
            "categoria": {"id": p.categoria.id, "nombre": p.categoria.nombre} if p.categoria else None,
            "marca": {"id": p.marca.id, "nombre": p.marca.nombre} if p.marca else None,
            "hex_identidad": v.hex_identidad,
            "identidad_variante": v.identidad_variante,
            "imagen_cover": img_url,
            "etiqueta": c.etiqueta,
            "talla": talla_val,
            "atributos_extra": atributos_extra,
            "stock_disponible": disponibles,
            "precio_compra": float(c.precio_compra),
            "precio_venta": float(c.precio_venta),
            "descuento": float(c.descuento or 0),
            "localizacion_id": c.localizacion_id,
            "localizacion": {"id": c.localizacion.id, "nombre": c.localizacion.nombre} if c.localizacion else None,
            "propietario": {"id": c.propietario.id, "nombre": c.propietario.nombre, "email": c.propietario.email} if c.propietario else None,
            "fecha_registro": c.fecha_registro.strftime("%Y-%m-%d") if getattr(c, 'fecha_registro', None) else (p.fecha_registro.strftime("%Y-%m-%d") if p.fecha_registro else None),
            "stock_units": [
                {
                    "id": u.id, "sku": u.sku, "estado_gestion": u.estado_gestion,
                    "canales": {"web": u.publicar_web, "vinted": u.publicar_vinted, "wallapop": u.publicar_wallapop},
                    "venta_id": u.detalles_venta[-1].venta_id if u.detalles_venta and len(u.detalles_venta) > 0 else None
                } 
                for u in unidades_activas
            ]
        })

    return {"total": total_configs, "items": resultados}


# =====================================================
# DETALLE DEL PRODUCTO COMPLETO (Edición y Vista)
# =====================================================

def obtener_producto_completo(db: Session, p_id: int):
    producto = (
        db.query(Producto)
        .options(
            joinedload(Producto.categoria),
            joinedload(Producto.marca),
            joinedload(Producto.variantes).joinedload(Variante.stock_configs).joinedload(StockConfig.stock_units),
            joinedload(Producto.variantes).joinedload(Variante.stock_configs).joinedload(StockConfig.localizacion),
            joinedload(Producto.variantes).joinedload(Variante.stock_configs).joinedload(StockConfig.valores).joinedload(ValorAtributo.atributo),
            joinedload(Producto.variantes).joinedload(Variante.imagenes)
        )
        .filter(Producto.id == p_id)
        .first()
    )

    if not producto: return None

    variantes_formateadas = []
    for v in sorted([var for var in producto.variantes if var.activo], key=lambda x: x.orden or 0):
        
        configs_formateados = []
        for c in sorted([config for config in v.stock_configs if config.activo], key=lambda x: x.orden or 0):
            talla_val = "UNICA"
            atributos_lista = []
            for val in c.valores:
                if val.atributo:
                    nombre_attr = val.atributo.nombre.lower()
                    if nombre_attr in ['talla', 'size', 'medida', 'numero', 'talla_anillo', 'capacidad_ml']:
                        talla_val = val.valor.strip().upper()
                    atributos_lista.append({"nombre": val.atributo.nombre, "valor": val.valor})

            configs_formateados.append({
                "id": c.id,
                "etiqueta": c.etiqueta,
                "localizacion_id": c.localizacion_id,
                "localizacion": {"id": c.localizacion.id, "nombre": c.localizacion.nombre} if c.localizacion else None,
                "precio_compra": c.precio_compra,
                "precio_venta": c.precio_venta,
                "descuento": c.descuento,
                "proveedor_id": c.proveedor_id,
                "propietario_id": c.propietario_id,
                "orden": c.orden,
                "donar_ganancias": c.donar_ganancias,
                "atributos": atributos_lista,
                "talla": talla_val, 
                "stock_units": [
                    {
                        "id": u.id, "sku": u.sku, "estado_gestion": u.estado_gestion,
                        "publicar_web": u.publicar_web, "publicar_vinted": u.publicar_vinted, "publicar_wallapop": u.publicar_wallapop,
                        "fecha_compra": u.fecha_compra.strftime("%Y-%m-%d") if u.fecha_compra else None,
                        "fecha_registro": u.fecha_registro.strftime("%Y-%m-%d") if u.fecha_registro else None,
                    } 
                    for u in c.stock_units if u.activo
                ]
            })

        variantes_formateadas.append({
            "id": v.id,
            "hex_identidad": v.hex_identidad,
            "identidad_variante": v.identidad_variante,
            "descripcion": v.descripcion,
            "orden": v.orden,
            "imagenes": [img.url for img in sorted(v.imagenes, key=lambda x: x.orden or 0)],
            "stock_configs": configs_formateados
        })

    return {
        "id": producto.id,
        "nombre": producto.nombre,
        "fecha_registro": producto.fecha_registro,
        "fecha_actualizacion": producto.fecha_actualizacion,
        "descripcion": producto.descripcion,
        "tipo": producto.tipo,
        "estado": producto.estado,
        "publico_objetivo": producto.publico_objetivo,
        "categoria_id": producto.categoria_id,
        "marca": producto.marca,
        "es_vintage": producto.es_vintage, 
        "epoca": producto.epoca,
        "variantes": variantes_formateadas
    }





def obtener_stock_config_detalle(db: Session, stock_config_id: int):
    config = db.query(StockConfig).options(
        selectinload(StockConfig.variante).selectinload(Variante.producto).selectinload(Producto.categoria),
        selectinload(StockConfig.variante).selectinload(Variante.imagenes),
        selectinload(StockConfig.localizacion),
        selectinload(StockConfig.valores).selectinload(ValorAtributo.atributo),
        selectinload(StockConfig.stock_units)
    ).filter(StockConfig.id == stock_config_id).first()

    if not config: return None

    talla_val = None
    nombre_attr_talla = "talla"
    atributos_extra = {}
    
    sinonimos_talla = ['talla', 'size', 'numero', 'número', 'capacidad_ml', 'medida', 'talla_anillo', 'talla_guantes']
    
    for val in config.valores:
        nombre_lower = val.atributo.nombre.lower()
        if nombre_lower in sinonimos_talla:
            talla_val = val.valor
            nombre_attr_talla = val.atributo.nombre # Guardamos el nombre original (con acentos o mayúsculas)
        else:
            atributos_extra[nombre_lower] = val.valor

    # Formateamos todo exactamente como lo espera el EditStockComponent
    return {
        "stock_config_id": config.id,
        "variante_id": config.variante_id,
        "producto_id": config.variante.producto_id,
        "producto_nombre": config.variante.producto.nombre,
        "categoria": {"id": config.variante.producto.categoria_id} if config.variante.producto.categoria else None,
        "identidad_variante": config.variante.identidad_variante,
        "hex_identidad": config.variante.hex_identidad,
        "imagen_cover": config.variante.imagenes[0].url if config.variante.imagenes else None,
        "etiqueta": config.etiqueta,
        "talla": talla_val,
        "nombre_atributo_talla": nombre_attr_talla, 
        "precio_compra": config.precio_compra,
        "precio_venta": config.precio_venta,
        "descuento": config.descuento,
        "localizacion_id": config.localizacion_id,
        "localizacion": {"id": config.localizacion.id, "nombre": config.localizacion.nombre} if config.localizacion else None,
        "proveedor_id": config.proveedor_id,
        "propietario_id": config.propietario_id,
        "donar_ganancias": config.donar_ganancias,
        "atributos_extra": atributos_extra,
        "stock_units": [
            {
                "id": u.id, 
                "sku": u.sku, 
                "estado_gestion": u.estado_gestion, 
                "publicar_web": u.publicar_web, 
                "publicar_vinted": u.publicar_vinted, 
                "publicar_wallapop": u.publicar_wallapop,
                "fecha_compra": u.fecha_compra.isoformat() if u.fecha_compra else None,
                "fecha_registro": u.fecha_registro.isoformat() if u.fecha_registro else None,
                "venta_id": u.detalles_venta[-1].venta_id if u.detalles_venta and len(u.detalles_venta) > 0 else None
            } for u in config.stock_units if u.activo
        ]
    }






# =====================================================
# PAPELERA (SOFT DELETE)
# =====================================================

def validar_unidades_en_proceso(db: Session, unit_ids: List[int]):
    """
    Verifica si alguna de las unidades de stock está en un proceso activo de venta/envío/devolución.
    Si es así, lanza una excepción HTTP 400.
    """
    if not unit_ids:
        return
        
    # Procesos activos son aquellos que NO han finalizado
    estados_finalizados = ['cancelado', 'devuelto', 'entregado', 'completado', 'extraviado_envio', 'extraviado_devolucion']
    
    venta_activa = db.query(Venta).join(DetalleVenta).filter(
        DetalleVenta.stock_unit_id.in_(unit_ids),
        ~Venta.estado_envio.in_(estados_finalizados),
        DetalleVenta.devuelto == False
    ).first()
    
    if venta_activa:
        raise HTTPException(
            status_code=400,
            detail=f"⛔ No se puede realizar esta acción: Hay prendas en proceso de venta, envío o devolución activo (Venta {venta_activa.codigo_venta}, Estado envío: '{venta_activa.estado_envio}')."
        )

def mover_producto_papelera(db: Session, p_id: int):
    producto = db.query(Producto).filter(Producto.id == p_id).first()
    if not producto: return {"success": False, "mensaje": "Producto no encontrado."}
    
    unit_ids = []
    for v in producto.variantes:
        for c in v.stock_configs:
            for u in c.stock_units:
                if u.activo:
                    unit_ids.append(u.id)
                    
    validar_unidades_en_proceso(db, unit_ids)
    
    producto.activo = False
    for v in producto.variantes:
        v.activo = False
        optimizar_imagenes_variante(db, v)
        for c in v.stock_configs:
            c.activo = False
            for u in c.stock_units:
                u.activo = False
                u.publicar_web = False
                u.publicar_vinted = False
                u.publicar_wallapop = False
                
    db.commit()
    return {"success": True, "mensaje": "🗑️ Producto a papelera y canales desconectados."}

def mover_variante_papelera(db: Session, v_id: int):
    variante = db.query(Variante).filter(Variante.id == v_id).first()
    if not variante: return {"success": False, "mensaje": "Variante no encontrada."}
    
    unit_ids = [u.id for c in variante.stock_configs for u in c.stock_units if u.activo]
    validar_unidades_en_proceso(db, unit_ids)
    
    variante.activo = False
    optimizar_imagenes_variante(db, variante)
    
    for c in variante.stock_configs:
        c.activo = False
        for u in c.stock_units:
            u.activo = False
            u.publicar_web = False
            u.publicar_vinted = False
            u.publicar_wallapop = False
            
    db.commit()
    return {"success": True, "mensaje": "🗑️ Variante a papelera y canales desconectados."}

def mover_stock_config_papelera(db: Session, stock_config_id: int):
    config = db.query(StockConfig).filter(StockConfig.id == stock_config_id).first()
    if not config: return {"success": False, "mensaje": "Configuración de stock no encontrada."}
    
    unit_ids = [u.id for u in config.stock_units if u.activo]
    validar_unidades_en_proceso(db, unit_ids)
    
    config.activo = False
    for u in config.stock_units:
        u.activo = False
        u.publicar_web = False
        u.publicar_vinted = False
        u.publicar_wallapop = False
        
    db.commit()
    return {"success": True, "mensaje": "🗑️ Configuración de stock movida a la papelera y desconectada."}

def mover_stock_unit_papelera(db: Session, stock_unit_id: int):
    unidad = db.query(StockUnit).filter(StockUnit.id == stock_unit_id).first()
    if not unidad: return {"success": False, "mensaje": "Unidad no encontrada."}
    
    validar_unidades_en_proceso(db, [unidad.id])
    
    unidad.activo = False
    unidad.publicar_web = False
    unidad.publicar_vinted = False
    unidad.publicar_wallapop = False
    db.commit()
    return {"success": True, "mensaje": "🗑️ Unidad física a papelera."}


# =====================================================
# RESTAURAR DE PAPELERA
# =====================================================

def restaurar_producto_papelera(db: Session, p_id: int):
    producto = db.query(Producto).filter(Producto.id == p_id).first()
    if not producto: return {"success": False, "mensaje": "No encontrado."}
    
    producto.activo = True 
    for v in producto.variantes:
        v.activo = True
        for c in v.stock_configs:
            c.activo = True
            for u in c.stock_units:
                u.activo = True
                u.publicar_web = False
                u.publicar_vinted = False
                u.publicar_wallapop = False

    db.commit()
    return {"success": True, "mensaje": "♻️ Producto restaurado por completo."}

def restaurar_variante_papelera(db: Session, v_id: int):
    variante = db.query(Variante).filter(Variante.id == v_id).first()
    if not variante: return {"success": False, "mensaje": "No encontrado."}
    variante.activo = True
    variante.producto.activo = True
    db.commit()
    return {"success": True, "mensaje": "♻️ Variante restaurada."}

def restaurar_stock_config_papelera(db: Session, stock_config_id: int):
    config = db.query(StockConfig).filter(StockConfig.id == stock_config_id).first()
    if not config: return {"success": False, "mensaje": "No encontrado."}
    config.activo = True
    config.variante.activo = True
    config.variante.producto.activo = True
    for u in config.stock_units:
        u.activo = True
        u.publicar_web = False
        u.publicar_vinted = False
        u.publicar_wallapop = False
    db.commit()
    return {"success": True, "mensaje": "♻️ Configuración de stock restaurada."}

def restaurar_stock_unit_papelera(db: Session, stock_unit_id: int):
    unidad = db.query(StockUnit).filter(StockUnit.id == stock_unit_id).first()
    if not unidad: return {"success": False, "mensaje": "No encontrado."}
    
    unidad.activo = True
    # También restauramos sus contenedores si están borrados
    unidad.stock_config.activo = True
    unidad.stock_config.variante.activo = True
    unidad.stock_config.variante.producto.activo = True
    
    db.commit()
    return {"success": True, "mensaje": "♻️ Prenda física restaurada."}


# =====================================================
# ELIMINACIÓN PERMANENTE (HARD DELETE)
# =====================================================

def destruir_producto_total(db: Session, p_id: int):
    producto = db.query(Producto).filter(Producto.id == p_id).first()
    if not producto: return {"success": False, "mensaje": "No existe."}
    
    if producto.activo == True:
        return {"success": False, "mensaje": "⚠️ Violación de seguridad: No puedes destruir un producto activo."}
    
    estados_intocables = ['donado_a_ong', 'devuelto_dueno', 'extraviado', 'vendido']
    for variante in producto.variantes:
        for config in variante.stock_configs:
            for u in config.stock_units:
                if u.estado_gestion in estados_intocables:
                    return {"success": False, "mensaje": f"⛔ Imposible borrar: El producto contiene unidades '{u.estado_gestion}'."}
    
    ventas = db.query(DetalleVenta).join(StockUnit).join(StockConfig).join(Variante).filter(Variante.producto_id == p_id).first()
    if ventas:
        return {"success": False, "mensaje": "⛔ No puedes destruir este producto porque está asociado a ventas."}

    for v in producto.variantes:
        for img in v.imagenes:
            try: delete_image_from_s3(img.url)
            except: pass

    db.delete(producto)
    db.commit()
    return {"success": True, "mensaje": "✅ Producto eliminado permanentemente."}

def destruir_variante_total(db: Session, v_id: int):
    variante = db.query(Variante).filter(Variante.id == v_id).first()
    if not variante: return {"success": False, "mensaje": "No existe."}
    if variante.activo == True: return {"success": False, "mensaje": "⚠️ No puedes destruir variante activa."}
    
    estados_intocables = ['donado_a_ong', 'devuelto_dueno', 'extraviado', 'vendido']
    for config in variante.stock_configs:
        for u in config.stock_units:
            if u.estado_gestion in estados_intocables:
                return {"success": False, "mensaje": "⛔ Conservar variante por histórico de unidades."}
            
    ventas = db.query(DetalleVenta).join(StockUnit).join(StockConfig).filter(StockConfig.variante_id == v_id).first()
    if ventas: return {"success": False, "mensaje": "⛔ Variante tiene unidades vendidas."}

    for img in variante.imagenes:
        try: delete_image_from_s3(img.url)
        except: pass

    db.delete(variante)
    db.commit()
    return {"success": True, "mensaje": "✅ Variante eliminada."}

def destruir_stock_unit_total(db: Session, stock_unit_id: int):
    unidad = db.query(StockUnit).filter(StockUnit.id == stock_unit_id).first()
    if not unidad: return {"success": False, "mensaje": "No existe."}
    
    if unidad.activo == True:
        return {"success": False, "mensaje": "⚠️ No puedes destruir stock activo."}
    
    estados_intocables = ['donado_a_ong', 'devuelto_dueno', 'extraviado', 'vendido']
    if unidad.estado_gestion in estados_intocables:
        return {"success": False, "mensaje": f"⛔ Unidad marcada como '{unidad.estado_gestion}'. Histórico necesario."}
    
    ventas = db.query(DetalleVenta).filter(DetalleVenta.stock_unit_id == stock_unit_id).first()
    if ventas:
        return {"success": False, "mensaje": "⛔ Esta prenda ya se registró en una venta."}

    db.delete(unidad)
    db.commit()
    return {"success": True, "mensaje": "✅ Unidad física eliminada de la existencia."}


# =====================================================
# LISTAR PAPELERA
# =====================================================

def obtener_productos_papelera(db: Session, page: int = 1, limit: int = 10):
    offset = (page - 1) * limit
    
    query = (
        db.query(Producto)
        .filter(
            or_(
                Producto.activo == False,
                Producto.variantes.any(Variante.activo == False),
                Producto.variantes.any(Variante.stock_configs.any(StockConfig.activo == False)),
                Producto.variantes.any(Variante.stock_configs.any(StockConfig.stock_units.any(StockUnit.activo == False)))
            )
        )
        .options(
            joinedload(Producto.categoria), joinedload(Producto.marca),
            joinedload(Producto.variantes).joinedload(Variante.stock_configs).joinedload(StockConfig.stock_units),
            joinedload(Producto.variantes).joinedload(Variante.imagenes)
        )
        .order_by(Producto.id.desc())
    )

    total = query.distinct().count()
    productos = query.distinct().offset(offset).limit(limit).all()

    resultados = []
    for p in productos:
        vars_finales = []
        for v in p.variantes:
            configs_borradas = [c for c in v.stock_configs if not c.activo]
            unidades_borradas = [u for c in v.stock_configs for u in c.stock_units if not u.activo]
            
            if not v.activo or configs_borradas or unidades_borradas:
                vars_finales.append({
                    "id": v.id, "identidad_variante": v.identidad_variante,
                    "hex_identidad": v.hex_identidad, "descripcion": v.descripcion, "activo": v.activo,
                    "stock_configs_borradas": [
                        {"id": c.id, "etiqueta": c.etiqueta, "cantidad": len(c.stock_units)}
                        for c in configs_borradas
                    ],
                    "stock_units_borradas": [
                        {"id": u.id, "sku": u.sku, "estado_gestion": u.estado_gestion}
                        for u in unidades_borradas
                    ]
                })

        stock_oculto = sum(1 for v in p.variantes for c in v.stock_configs for u in c.stock_units if not u.activo)
        precios_ocultos = [c.precio_venta for v in p.variantes for c in v.stock_configs if not c.activo]
        
        imagen_cover = None
        if p.variantes:
            v_con_img = next((v for v in p.variantes if v.imagenes), None)
            if v_con_img:
                img_sorted = sorted(v_con_img.imagenes, key=lambda x: x.orden or 0)
                if img_sorted: imagen_cover = img_sorted[0].url

        resultados.append({
            "id": p.id, "nombre": p.nombre, "sku": p.sku, "tipo": p.tipo, "activo": p.activo,
            "categoria": {"id": p.categoria.id, "nombre": p.categoria.nombre} if p.categoria else None,
            "marca": {"id": p.marca.id, "nombre": p.marca.nombre} if p.marca else None,
            "imagen": imagen_cover,
            "stock_total_oculto": stock_oculto,
            "precio_min": min(precios_ocultos) if precios_ocultos else 0,
            "precio_max": max(precios_ocultos) if precios_ocultos else 0,
            "colores": list({v.hex_identidad for v in p.variantes if v.hex_identidad}),
            "variantes": vars_finales 
        })

    return {"total": total, "items": resultados}












# producto_repo.py

def obtener_atributos_por_categoria(db: Session, categoria_id: int):
    """
    Busca los atributos dinámicos vinculados a una categoría y los formatea para Angular.
    """
    atributos = db.query(AtributoCategoria).filter(
        AtributoCategoria.categoria_id == categoria_id
    ).all()
    
    resultados = []
    for attr in atributos:
        resultados.append({
            "id": attr.id,
            "nombre": attr.nombre,
            "tipo": attr.tipo,
            "opciones": attr.opciones if attr.opciones else [] 
        })
        
    return resultados