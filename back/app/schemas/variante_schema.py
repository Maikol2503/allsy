from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

# ✨ IMPORTACIÓN CORREGIDA: Apunta al nuevo archivo y esquema de stock
from app.schemas.lote_schema import StockConfigSchema

# ==========================================
# ESQUEMAS BÁSICOS DE CREACIÓN (Legacy / UI)
# ==========================================
class TallaCreate(BaseModel):
    talla: str
    stock: int

class ImagenVarianteCreate(BaseModel):
    url: str

class VarianteCreate(BaseModel):
    color: str
    color_nombre: str
    precio: float | None = None
    descuento: float | None = None
    tallas: list[TallaCreate]


# ==========================================
# ESQUEMA DE VALIDACIÓN PRINCIPAL
# ==========================================
class VarianteSchema(BaseModel):
    temp_id: Optional[str] = None
    id: Optional[int] = None # Útil para la edición
    
    # Reglas estrictas:
    identidad_variante: str = Field(..., min_length=1, description="El color o material es obligatorio")
    hex_identidad: str = Field(..., min_length=1)
    
    descripcion: str
    imagenes: List[str] = []
    orden: Optional[int] = 0
    
    # ✨ CORRECCIÓN CLAVE: Renombrado a stock_configs y validado con StockConfigSchema
    stock_configs: List[StockConfigSchema] = Field(..., min_items=1)