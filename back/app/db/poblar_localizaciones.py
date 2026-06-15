from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine, Base
from app.models.localizaciones_model import Localizacion

def poblar_localizaciones():
    db: Session = SessionLocal()
    
    # 1. Crear Raíz: CASA
    casa = db.query(Localizacion).filter(Localizacion.nombre == "CASA", Localizacion.parent_id == None).first()
    if not casa:
        casa = Localizacion(nombre="CASA", tipo="casa", es_principal=True)
        db.add(casa)
        db.flush() # Para obtener el ID
        print("🏠 Localización CASA creada.")
    else:
        print("🏠 Localización CASA ya existía.")

    # 2. Crear Sub-localizaciones
    sub_locs = [
        "habitacion",
        "pasillo estante blanco izquierdo",
        "pasillo estante blanco derecho",
        "sala"
    ]

    for nombre in sub_locs:
        existe = db.query(Localizacion).filter(Localizacion.nombre == nombre, Localizacion.parent_id == casa.id).first()
        if not existe:
            nueva_sub = Localizacion(nombre=nombre, tipo="casa", parent_id=casa.id)
            db.add(nueva_sub)
            print(f"📍 Sub-localización '{nombre}' creada.")
    
    db.commit()
    db.close()
    print("✅ Proceso de población de localizaciones finalizado.")

if __name__ == "__main__":
    # Asegurar que las tablas existan
    Base.metadata.create_all(bind=engine)
    poblar_localizaciones()
