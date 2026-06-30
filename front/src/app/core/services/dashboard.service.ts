import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class DashboardService {
  private apiUrl = 'http://localhost:8000/api/v1/dashboard';

  constructor(private http: HttpClient) {}

  /**
   * Obtiene el resumen de KPIs
   * @param filtros Objeto con fecha_inicio y fecha_fin
   */
  getResumen(filtros: any = {}): Observable<any> {
    let params = new HttpParams();
    
    if (filtros.fecha_inicio) params = params.set('fecha_inicio', filtros.fecha_inicio);
    if (filtros.fecha_fin) params = params.set('fecha_fin', filtros.fecha_fin);

    return this.http.get(`${this.apiUrl}/resumen`, { params });
  }

  /**
   * Obtiene los datos para la gráfica de barras (Histórico 6 meses)
   */
  getDatosGrafica(filtros: any = {}): Observable<any[]> {
    let params = new HttpParams();
    if (filtros.fecha_inicio) params = params.set('fecha_inicio', filtros.fecha_inicio);
    if (filtros.fecha_fin) params = params.set('fecha_fin', filtros.fecha_fin);

    return this.http.get<any[]>(`${this.apiUrl}/grafica-tendencia`, { params });
  }
}