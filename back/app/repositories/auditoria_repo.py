from sqlalchemy.orm import Session
from app.models.auditoria_model import Auditoria
from typing import Optional, Any, Dict

def registrar_log(
    db: Session, 
    accion: str, 
    entidad_tipo: str, 
    entidad_id: Optional[int] = None,
    usuario_id: Optional[int] = None,
    nombre_usuario: Optional[str] = None,
    localizacion_id: Optional[int] = None,
    valor_anterior: Optional[Dict[str, Any]] = None,
    valor_nuevo: Optional[Dict[str, Any]] = None,
    notas: Optional[str] = None,
    ip_address: Optional[str] = None
):
    """
    Función centralizada para registrar cualquier movimiento importante en el sistema.
    """
    try:
        log = Auditoria(
            accion=accion,
            entidad_tipo=entidad_tipo,
            entidad_id=entidad_id,
            usuario_id=usuario_id,
            nombre_usuario=nombre_usuario,
            localizacion_id=localizacion_id,
            valor_anterior=valor_anterior,
            valor_nuevo=valor_nuevo,
            notas=notas,
            ip_address=ip_address
        )
        db.add(log)
        db.flush() # Usamos flush para obtener el ID si fuera necesario sin hacer commit final
        return log
    except Exception as e:
        print(f"⚠️ Error al registrar log de auditoría: {e}")
        # No levantamos excepción para no bloquear la transacción principal si el log falla
        return None

def obtener_logs(
    db: Session, 
    entidad_tipo: Optional[str] = None, 
    entidad_id: Optional[int] = None,
    localizacion_id: Optional[int] = None,
    limit: int = 100
):
    query = db.query(Auditoria)
    
    if entidad_tipo:
        query = query.filter(Auditoria.entidad_tipo == entidad_tipo)
    if entidad_id:
        query = query.filter(Auditoria.entidad_id == entidad_id)
    if localizacion_id:
        query = query.filter(Auditoria.localizacion_id == localizacion_id)
        
    return query.order_by(Auditoria.fecha.desc()).limit(limit).all()
