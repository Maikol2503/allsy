from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import date
from .atributo_schema import AtributoSchema


class StockUnitSchema(BaseModel):
    id: Optional[int] = None
    id_original: Optional[int] = None
    sku: Optional[str] = None
    estado_gestion: str = "en_stock"
    publicar_web: bool = False
    publicar_vinted: bool = False
    publicar_wallapop: bool = False
    fecha_compra: Optional[date] = None

class StockConfigSchema(BaseModel):
    id: Optional[int] = None
    temp_id: Optional[str] = None
    propietario_id: Optional[int] = None
    donar_ganancias: Optional[bool] = False
    cantidad_agregar: int = 0
    fecha_compra_lote_nuevo: Optional[date] = None # ✨ NUEVO
    precio_compra: float = Field(..., ge=0)
    precio_venta: float = Field(default=0.0)
    descuento: int = 0
    proveedor: Optional[str] = ""
    proveedor_id: Optional[int] = None
    proveedor_nombre_nuevo: Optional[str] = None
    localizacion_id: Optional[int] = None
    etiqueta: str = "Única"
    orden: Optional[int] = 0
    atributos: List[AtributoSchema] = []
    stock_units: List[StockUnitSchema] = []

class StockConfigEditPayload(BaseModel):
    precio_compra: Optional[float] = None
    precio_venta: Optional[float] = None
    descuento: Optional[float] = None
    localizacion_id: Optional[int] = None
    proveedor_id: Optional[int] = None
    proveedor_nombre_nuevo: Optional[str] = None
    atributos: Optional[List[Dict[str, Any]]] = None
    donar_ganancias: Optional[bool] = None
    stock_units: Optional[List[StockUnitSchema]] = None

class AddStockUnitsRequest(BaseModel):
    cantidad: int
    fecha_compra: Optional[date] = None

class StockConfigIndividualItemList(BaseModel):
    stock_config_id: int
    variante_id: int
    producto_id: int
    producto_nombre: str
    categoria: Optional[Dict[str, Any]]
    marca: Optional[Dict[str, Any]]
    hex_identidad: str
    identidad_variante: str
    imagen_cover: Optional[str]
    etiqueta: Optional[str]
    talla: Optional[str]
    atributos_extra: Dict[str, str]
    stock_disponible: int
    precio_compra: float
    precio_venta: float
    descuento: float
    localizacion_id: Optional[int] = None
    localizacion: Optional[Dict[str, Any]] = None
    propietario: Optional[Dict[str, Any]] = None
    fecha_registro: Optional[str] = None
    stock_units: List[Dict[str, Any]]

class PaginatedStockConfigsResponse(BaseModel):
    total: int
    items: List[StockConfigIndividualItemList]