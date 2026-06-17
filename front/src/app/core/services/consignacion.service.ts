import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface EstadisticasConsignacion {
  total_prendas_entregadas: number;
  prendas_en_stock: number;
  
  // Desglose logístico exacto
  prendas_procesando: number;
  prendas_enviada: number;
  prendas_entregado: number;
  prendas_completada: number;
  prendas_cancelada: number;
  prendas_devueltas_tienda: number;
  prendas_devueltas_dueno: number; 
  prendas_donado_a_ong: number;
  prendas_extraviadas: number;
  ingresos_en_transito: number;
  // Finanzas
  exento_gastos_gestion: boolean;
  deuda_por_devoluciones: number;
  dinero_generado_ventas: number;
  dinero_para_cliente: number;
  beneficio_plataforma: number;
  beneficio_en_transito: number;
  dinero_ya_pagado: number;
  saldo_pendiente: number;
  saldo_en_transito: number;
}

export interface PagoCreate {
  monto: number;
  metodo_pago: string;
  referencia?: string | null;
  notas?: string | null;
  stock_unit_ids?: number[]; // ✨ TRAZABILIDAD
}

export interface PagoRead extends PagoCreate {
  id: number;
  fecha: string;
  estado: string; // ✨ NUEVO
  motivo_anulacion?: string; // ✨ NUEVO
  items_pagados?: any[]; 
  items_anulados?: any[]; // ✨ NUEVO PARA HISTORIAL FANTASMA
}

@Injectable({
  providedIn: 'root'
})
export class ConsignacionService {
  private apiUrl = 'http://localhost:8000/api/v1/consignacion'; 

  constructor(private http: HttpClient) {}

  getStats(clienteId: number): Observable<EstadisticasConsignacion> {
    return this.http.get<EstadisticasConsignacion>(`${this.apiUrl}/cliente/${clienteId}/stats`);
  }

  registrarPago(clienteId: number, data: PagoCreate): Observable<PagoRead> {
    return this.http.post<PagoRead>(`${this.apiUrl}/cliente/${clienteId}/pagar`, data);
  }

  getPagos(clienteId: number): Observable<PagoRead[]> {
    return this.http.get<PagoRead[]>(`${this.apiUrl}/cliente/${clienteId}/pagos`);
  }

  actualizarPago(pagoId: number, pago: Partial<PagoCreate>) {
    return this.http.put<PagoRead>(`${this.apiUrl}/pago/${pagoId}`, pago);
  }

  anularPago(pagoId: number, motivo: string) {
    return this.http.put(`${this.apiUrl}/pago/${pagoId}/anular?motivo=${encodeURIComponent(motivo)}`, {});
  }

  quitarItemDePago(pagoId: number, stockUnitId: number, motivo: string) {
    return this.http.put(`${this.apiUrl}/pago/${pagoId}/quitar-item/${stockUnitId}?motivo=${encodeURIComponent(motivo)}`, {});
  }

  getPrendasPendientesPago(clienteId: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/cliente/${clienteId}/pendientes-pago`);
  }

  // Añadir dentro de ConsignacionService
  getPrendasCliente(clienteId: number, page: number = 1, limit: number = 10, estado: string = '') {
    let url = `${this.apiUrl}/cliente/${clienteId}/prendas?page=${page}&limit=${limit}`;
    if (estado) {
      url += `&estado=${estado}`;
    }
    return this.http.get<any>(url);
  }
}