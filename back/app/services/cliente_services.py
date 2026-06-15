# app/services/cliente_service.py
import re
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.models.clientes_model import Cliente

# ==========================================
# 1. HERRAMIENTAS DE LIMPIEZA PRIVADAS
# ==========================================
def _normalizar_documento(documento: str) -> str:
    """Limpia guiones, puntos y espacios, y lo pasa a mayúsculas."""
    if not documento:
        return None
    limpio = re.sub(r'[\s\-\.\,]', '', documento)
    return limpio.upper() if limpio else None


# ==========================================
# 2. EL CEREBRO OMNICANAL
# ==========================================
def procesar_cliente_omnicanal(db: Session, data) -> int:
    """
    Analiza el objeto de venta (data), busca al cliente o lo crea, 
    y devuelve su ID. Si no hay datos, devuelve None (Cliente Anónimo).
    """
    
    # Si el vendedor no puso ningún identificador, es un cliente anónimo.
    if not getattr(data, 'identificador_cliente', None):
        return None

    identificador = data.identificador_cliente.strip()
    
    # ----------------------------------------------------
    # CANALES DE APPS (Vinted / Wallapop)
    # ----------------------------------------------------
    if data.canal in ['vinted', 'wallapop']:
        # Decide en qué columna buscar según el canal
        campo_busqueda = Cliente.usuario_vinted if data.canal == 'vinted' else Cliente.usuario_wallapop
        cliente_db = db.query(Cliente).filter(campo_busqueda == identificador).first()
        
        if not cliente_db:
            # Crea el cliente con el nombre de usuario de la app
            kwargs = {
                f"usuario_{data.canal}": identificador, 
                "nombre": data.nombre_cliente or identificador, 
                "notas_internas": f"Creado auto ({data.canal.capitalize()})"
            }
            cliente_db = Cliente(**kwargs)
            db.add(cliente_db)
            db.flush() # Genera el ID sin guardar definitivamente aún
            
        return cliente_db.id

    # ----------------------------------------------------
    # CANAL WEB
    # ----------------------------------------------------
    if data.canal == 'web':
        email = identificador.lower()
        cliente_db = db.query(Cliente).filter(Cliente.email == email).first()
        
        if not cliente_db:
            cliente_db = Cliente(
                email=email, 
                nombre=data.nombre_cliente, 
                notas_internas="Creado auto (Web)"
            )
            db.add(cliente_db)
            db.flush()
            
        return cliente_db.id

    # ----------------------------------------------------
    # CANAL TIENDA FÍSICA (Lógica Explícita del Formulario)
    # ----------------------------------------------------
    if data.canal == 'tienda_fisica':
        tipo = getattr(data, 'tipo_identificador', 'nombre_anonimo')
        
        # CASO A: Es un Teléfono
        if tipo == 'telefono':
            prefijo = getattr(data, 'prefijo_telefono', '+34')
            tel_completo = f"{prefijo}{identificador.replace(' ', '')}"
            
            cliente_db = db.query(Cliente).filter(Cliente.telefono == tel_completo).first()
            if not cliente_db:
                cliente_db = Cliente(
                    telefono=tel_completo, 
                    nombre=data.nombre_cliente, 
                    notas_internas="Creado auto (Tienda - Teléfono)"
                )
                db.add(cliente_db)
        
        # CASO B: Es un Documento (DNI, NIE, Pasaporte, Cédula...)
        elif tipo == 'documento':
            doc_norm = _normalizar_documento(identificador)
            tipo_doc = getattr(data, 'tipo_documento', 'Documento')
            
            # ✨ CAMBIADO documento_identidad POR dni_nie
            cliente_db = db.query(Cliente).filter(Cliente.dni_nie == doc_norm).first()
            if not cliente_db:
                cliente_db = Cliente(
                    dni_nie=doc_norm, # ✨ AQUÍ TAMBIÉN
                    nombre=data.nombre_cliente, 
                    notas_internas=f"Creado auto (Tienda - {tipo_doc})"
                )
                db.add(cliente_db)
                
        # CASO C: Solo nos dieron un nombre genérico (Ej: "El chico de ayer")
        else:
            cliente_db = db.query(Cliente).filter(Cliente.nombre == identificador).first()
            if not cliente_db:
                cliente_db = Cliente(
                    nombre=identificador, 
                    notas_internas="Creado auto (Tienda - Solo Nombre)"
                )
                db.add(cliente_db)

        db.flush()
        return cliente_db.id

    # Fallback por si llega un canal raro que no existe
    return None