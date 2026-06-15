from app.db.database import SessionLocal
import app.models
from app.repositories.producto_repo import obtener_stock_configs_individuales_paginados

db = SessionLocal()
res = obtener_stock_configs_individuales_paginados(db, limit=5, propietario_id=14)
print(f"Found: {res['total']} items. First item owner: {res['items'][0]['propietario'] if res['items'] else 'None'}")
db.close()
