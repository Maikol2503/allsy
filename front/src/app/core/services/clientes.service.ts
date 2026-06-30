import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ClienteData {
  id?: number;
  email?: string;
  telefono?: string;
  usuario_vinted?: string;
  usuario_wallapop?: string;
  nombre?: string;
  apellidos?: string;
  dni_nie?: string;
  direccion?: string;
  ciudad?: string;
  codigo_postal?: string;
  provincia?: string;
  pais?: string;
  notas_internas?: string;
  // ✨ NUEVOS CAMPOS FINANCIEROS (Reemplazan a exento_gastos_gestion)
  exento_comision?: boolean;
  exento_tarifa_fija?: boolean;
  total_ventas?: number;
  deuda_pendiente?: number;
  fecha_registro?: string;
}



export interface ClienteBase {
  nombre: string;
  apellidos?: string;
  email?: string;
  telefono?: string;
  usuario_vinted?: string;
  usuario_wallapop?: string;
  dni_nie?: string;
  direccion?: string;
  ciudad?: string;
  codigo_postal?: string;
  provincia?: string;
  pais: string;
  notas_internas?: string;
  exento_gastos_gestion: boolean; // ✨ CAMBIADO AQUÍ
  exento_comision: boolean;
  exento_tarifa_fija: boolean;
}

export interface ClienteCreate extends ClienteBase {}

export interface ClienteRead extends ClienteBase {
  id: number;
  total_ventas: number;
}

@Injectable({
  providedIn: 'root'
})
export class ClientesService {
  private apiUrl = `http://localhost:8000/api/v1/clientes`;

  constructor(private http: HttpClient) {}

  obtenerClientes(filtros: any): Observable<any> {
    // ✨ CORRECCIÓN: Parseo explícito para evitar fallos de inferencia
    let params = new HttpParams()
      .set('page', (filtros.page || 1).toString())
      .set('limit', (filtros.limit || 10).toString());

    if (filtros.search) params = params.set('search', filtros.search);
    if (filtros.search_type) params = params.set('search_type', filtros.search_type); // ✨ AÑADIDO
    if (filtros.pais) params = params.set('pais', filtros.pais);
    if (filtros.fecha_inicio) params = params.set('fecha_inicio', filtros.fecha_inicio);
    if (filtros.fecha_fin) params = params.set('fecha_fin', filtros.fecha_fin);
    if (filtros.con_deuda) params = params.set('con_deuda', 'true');

    return this.http.get<any>(`${this.apiUrl}/`, { params });
  }
  
  actualizarCliente(id: number, data: ClienteData): Observable<any> {
    return this.http.put<any>(`${this.apiUrl}/${id}`, data);
  }
  crearCliente(data: ClienteData): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/`, data);
  }

  obtenerClientePorId(id: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/${id}`);
  }

  desactivarCliente(id: number): Observable<any> {
    return this.http.patch<any>(`${this.apiUrl}/${id}/desactivar`, {});
  }
}