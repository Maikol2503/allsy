from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# ✨ IMPORTAMOS EL NUEVO ESQUEMA DE STOCK (Asegúrate de que el archivo stock_schema.py exista)
from app.schemas.lote_schema import StockConfigSchema

# ==========================================
# ESQUEMAS BÁSICOS DE CREACIÓN (Legacy / UI)
# ==========================================
class TallaCreate(BaseModel):
    talla: str
    stock: int

class VarianteCreate(BaseModel):
    color: str
    colorNombre: str
    precio: float
    descuento: float
    tallas: List[TallaCreate]

class ProductoCreate(BaseModel):
    nombre: str
    descripcion: str
    precio: float
    categoria_id: int
    marca_id: int
    variantes: List[VarianteCreate]

# ==========================================
# ESQUEMAS DE LISTADO Y REFERENCIAS
# ==========================================
class SimpleRef(BaseModel):
    """Un esquema genérico para Categoría y Marca (solo id y nombre)"""
    id: int
    nombre: str

class ProductoItemList(BaseModel):
    """El esquema de un producto individual en la lista de la tabla principal"""
    id: int
    nombre: str
    sku: str
    tipo: str
    categoria: Optional[SimpleRef] = None
    marca: Optional[SimpleRef] = None
    imagen: Optional[str] = None
    stock_total: int
    precio_compra: float  
    precio_venta: float   
    colores: List[str] = []  
    tallas: List[str] = []
    canales: Optional[dict] = None

class PaginatedProductosResponse(BaseModel):
    """El esquema final paginado para los productos"""
    total: int
    items: List[ProductoItemList]

# ==========================================
# ESQUEMAS DE EDICIÓN Y VALIDACIÓN DE JSON
# ==========================================
class VarianteSchema(BaseModel):
    """
    Esquema utilizado para validar el JSON string de variantes 
    que llega en el form-data al crear o editar productos.
    """
    temp_id: Optional[str] = None
    id: Optional[int] = None 
    identidad_variante: str = Field(..., min_length=1)
    hex_identidad: str = Field(..., min_length=1)
    descripcion: str
    imagenes: List[str] = []
    orden: Optional[int] = 0
    
    # ✨ CAMBIO CLAVE: Reemplaza "lotes" por "stock_configs"
    stock_configs: List[StockConfigSchema] = Field(..., min_items=1)