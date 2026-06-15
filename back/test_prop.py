from app.db.database import SessionLocal
import app.models
from app.repositories.producto_repo import obtener_stock_configs_individuales_paginados
import json

db = SessionLocal()
res = obtener_stock_configs_individuales_paginados(db, limit=5)
for item in res['items']:
    print(f"ID: {item['stock_config_id']}, Propietario: {item['propietario']}")
db.close()
