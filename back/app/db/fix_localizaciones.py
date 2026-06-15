from sqlalchemy import text
from app.db.database import engine

def fix_localizaciones_table():
    with engine.connect() as conn:
        print("🔍 Comprobando tabla localizaciones...")
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        conn.execute(text("DROP TABLE IF EXISTS localizaciones"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        conn.commit()
        print("🗑️ Tabla localizaciones eliminada (si existía).")
        
    from app.db.database import Base
    from app.models.localizaciones_model import Localizacion
    
    Base.metadata.create_all(bind=engine)
    print("✅ Tabla localizaciones recreada con el nuevo esquema.")

if __name__ == "__main__":
    fix_localizaciones_table()
