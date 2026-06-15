import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class StatisticsService {
  private API_URL = 'http://localhost:8000/api/v1/stats';

  constructor(private http: HttpClient) {}

  obtenerEstadisticas(inicio?: string, fin?: string): Observable<any> {
    let params = new HttpParams();
    if (inicio) params = params.set('fecha_inicio', inicio);
    if (fin) params = params.set('fecha_fin', fin);

    return this.http.get(`${this.API_URL}/dashboard-completo`, { params });
  }

  // ==========================================
  // 2. ANÁLISIS DE INVERSIÓN (NUEVO)
  // ==========================================
  // Analiza el éxito de la ropa que COMPRASTE en un periodo
  obtenerRendimientoCompras(inicio?: string, fin?: string): Observable<any> {
    let params = new HttpParams();
    if (inicio) params = params.set('fecha_inicio', inicio);
    if (fin) params = params.set('fecha_fin', fin);

    return this.http.get(`${this.API_URL}/rendimiento-compras`, { params });
  }


  // ==========================================
  // 3. ANÁLISIS DE PROVEEDORES (NUEVO)
  // ==========================================
  // Evalúa qué proveedor genera más rentabilidad y mejor tasa de venta
  obtenerRendimientoProveedores(inicio?: string, fin?: string): Observable<any> {
    let params = new HttpParams();
    if (inicio) params = params.set('fecha_inicio', inicio);
    if (fin) params = params.set('fecha_fin', fin);

    return this.http.get(`${this.API_URL}/rendimiento-proveedores`, { params });
  }
}