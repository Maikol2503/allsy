import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface AuditoriaLog {
  id: number;
  fecha: string;
  usuario_id?: number;
  nombre_usuario?: string;
  localizacion_id?: number;
  accion: string;
  entidad_tipo: string;
  entidad_id?: number;
  valor_anterior?: any;
  valor_nuevo?: any;
  notas?: string;
  ip_address?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuditoriaService {
  private apiUrl = 'http://localhost:8000/api/v1/auditoria';

  constructor(private http: HttpClient) {}

  obtenerLogs(filtros: { 
    entidad_tipo?: string, 
    entidad_id?: number, 
    localizacion_id?: number,
    limit?: number 
  } = {}): Observable<AuditoriaLog[]> {
    let params = new HttpParams();
    if (filtros.entidad_tipo) params = params.set('entidad_tipo', filtros.entidad_tipo);
    if (filtros.entidad_id) params = params.set('entidad_id', filtros.entidad_id.toString());
    if (filtros.localizacion_id) params = params.set('localizacion_id', filtros.localizacion_id.toString());
    if (filtros.limit) params = params.set('limit', filtros.limit.toString());

    return this.http.get<AuditoriaLog[]>(this.apiUrl, { params });
  }
}
