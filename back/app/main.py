from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.db.database import Base, engine

# =========================
# ROUTERS (Nombres actualizados)
# =========================
from app.api.v1.auth import auth_routers
from app.api.v1.productos import producto_routers
from app.api.v1.categorias import categorias_routers
from app.api.v1.marcas import marcas_router
from app.api.v1.ventas import venta_router
from app.api.v1.proveedores import proveedores_router
# from app.api.v1.analilytics import analytics_router
from app.api.v1.egresos import egresos_router
from app.api.v1.dashboard import dashboard_router
# from app.api.v1.analilytics import analytics_router
from app.api.v1.statistics import router_statistics
from app.api.v1.cliente import router as cliente_router
from app.api.v1.consignacion import router as consignacion_router
from app.api.v1.localizaciones import router as localizaciones_router
from app.api.v1.auditoria import router as auditoria_router
from app.api.deps import get_current_user
from fastapi import Depends

# from app.api.v1.analilytics import analytics_router  # Corregido el nombre
# from app.api.v1.statistics import router as stats_router

# =========================
# MODELS (Nomenclatura Limpia)
# Importarlos aquí asegura que Base.metadata.create_all los encuentre
# =========================
from app.models.producto_model import Producto  
from app.models.variantes_model import Variante
from app.models.lotes_model import StockConfig, StockUnit  
from app.models.atributo_model import Atributo, ValorAtributo   
from app.models.atributo_categoria_model import AtributoCategoria # ✨ AÑADIDO
from app.models.categorias_model import Categoria
from app.models.marcas_model import Marca
from app.models.variante_imagen_model import Imagen
from app.models.ventas_model import Venta, DetalleVenta
from app.models.proveedores_model import Proveedor          
from app.models.egresos_model import Egreso
from app.models.localizaciones_model import Localizacion
from app.models.auditoria_model import Auditoria # ✨ AÑADIDO
from app.models.clientes_model import Cliente  
from app.models.pagos_consignacion_model import PagoConsignacion # ✨ AÑADIDO
from app.models.cupon_model import Cupon # ✨ AÑADIDO POR SEGURIDAD



app = FastAPI(
    title="Bunglo API",
    version="1.1.0",
    description="E-commerce con arquitectura EAV: Producto -> Variante -> Stock -> Atributos"
)

# =========================
# STARTUP
# =========================
@app.on_event("startup")
def on_startup():
    # Esto crea las tablas con los nuevos nombres (productos, variantes, stocks, etc.)
    Base.metadata.create_all(bind=engine)

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://bunglo.vercel.app",
        "http://localhost:4200",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# ROUTERS
# =========================
# Nota: Si cambiaste los archivos de router, asegúrate que los nombres coincidan
app.include_router(auth_routers, prefix="/api/v1")
app.include_router(producto_routers, prefix="/api/v1/productos", dependencies=[Depends(get_current_user)])
app.include_router(categorias_routers, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(marcas_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(venta_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(proveedores_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(egresos_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(dashboard_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(router_statistics, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(cliente_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(consignacion_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(localizaciones_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(auditoria_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])



# app.include_router(analytics_router, prefix="/api/v1")

# app.include_router(analytics_router, prefix="/api/v1")
# ✨ AGREGAMOS EL ROUTER DE ESTADÍSTICAS
# Con este prefijo, la ruta será: /api/v1/stats/dashboard-completo
# app.include_router(stats_router, prefix="/api/v1/stats") 

# El de analytics lo dejamos solo con /api/v1 para que sea /api/v1/financiero
# app.include_router(analytics_router, prefix="/api/v1")

# =========================
# HEALTH CHECK
# =========================
@app.get("/")
def health_check():
    try:
        with engine.connect() as connection:
            # Usar .execute(text(...)) para verificar salud de DB
            connection.execute(text("SELECT 1"))
        return {
            "status": "online", 
            "mensaje": "Bunglo API funcionando correctamente 🚀",
            "arquitectura": "EAV (Entidad-Atributo-Valor)"
        }
    except Exception as e:
        return {"status": "error", "detalle": str(e)}