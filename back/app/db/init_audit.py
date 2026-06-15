from app.db.database import engine, Base
import app.models # Asegurar que Auditoria esté cargada

def init_audit_table():
    try:
        # Esto creará SOLO las tablas que no existan en la DB
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas de base de datos verificadas/creadas (incluyendo Auditoría).")
    except Exception as e:
        print(f"❌ Error al crear tablas: {e}")

if __name__ == "__main__":
    init_audit_table()
