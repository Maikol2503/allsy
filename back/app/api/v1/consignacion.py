from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_session
from app.schemas.consignacion_schema import EstadisticasConsignacion, PaginatedPrendas, PagoCreate, PagoRead, PagoUpdate, PrendaClienteDetalle
from app.repositories import consignacion_repo
from typing import List

router = APIRouter(prefix="/consignacion", tags=["Consignación"])

@router.get("/cliente/{cliente_id}/stats", response_model=EstadisticasConsignacion)
def get_stats(cliente_id: int, db: Session = Depends(get_session)):
    return consignacion_repo.obtener_estadisticas_cliente(db, cliente_id)

@router.post("/cliente/{cliente_id}/pagar", response_model=PagoRead)
def pay_client(cliente_id: int, data: PagoCreate, db: Session = Depends(get_session)):
    return consignacion_repo.registrar_pago(db, cliente_id, data)

@router.get("/cliente/{cliente_id}/pagos", response_model=list[PagoRead])
def get_payments(cliente_id: int, db: Session = Depends(get_session)):
    return consignacion_repo.listar_pagos(db, cliente_id)

@router.get("/cliente/{cliente_id}/pendientes-pago")
def get_pending_items_to_pay(cliente_id: int, db: Session = Depends(get_session)):
    """Retorna prendas vendidas que aún no se han pagado al cliente."""
    return consignacion_repo.obtener_prendas_pendientes_pago(db, cliente_id)



@router.put("/pago/{pago_id}", response_model=PagoRead)
def update_payment(pago_id: int, data: PagoUpdate, db: Session = Depends(get_session)):
    """Edita un pago existente."""
    return consignacion_repo.editar_pago(db, pago_id, data.dict(exclude_unset=True))

@router.put("/pago/{pago_id}/anular")
def void_payment(pago_id: int, motivo: str, db: Session = Depends(get_session)):
    """Anula un pago y devuelve el saldo al cliente sin borrar el registro financiero."""
    return consignacion_repo.anular_pago(db, pago_id, motivo)

from typing import Optional
from fastapi import Query

@router.get("/cliente/{cliente_id}/prendas", response_model=PaginatedPrendas)
def get_client_items_detail(
    cliente_id: int, 
    page: int = Query(1, ge=1), 
    limit: int = Query(10, ge=1), 
    estado: str = Query(None), # ✨ NUEVO FILTRO
    db: Session = Depends(get_session)
):
    return consignacion_repo.listar_prendas_detalle_cliente(db, cliente_id, page, limit, estado)