import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.repositories.cliente_repo import obtener_clientes_paginados

db = SessionLocal()
try:
    print("Testing obtener_clientes_paginados...")
    res = obtener_clientes_paginados(db=db, page=1, limit=10, con_deuda=False)
    print("SUCCESS, items:", len(res["items"]))
    for item in res["items"]:
        print(f"Cliente {item['nombre']} Deuda: {item['deuda_pendiente']}")
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()
