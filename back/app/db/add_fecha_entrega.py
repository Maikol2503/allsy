from app.db.database import engine
from sqlalchemy import text

def alter_table():
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE ventas ADD COLUMN fecha_entrega DATETIME NULL;"))
            conn.commit()
            print("✅ Columna 'fecha_entrega' agregada exitosamente.")
    except Exception as e:
        if "Duplicate column name" in str(e):
            print("✅ La columna 'fecha_entrega' ya existe.")
        else:
            print(f"❌ Error al alterar la tabla: {e}")

if __name__ == "__main__":
    alter_table()
