import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Localizacion {
  id?: number;
  nombre: string;
  descripcion?: string;
  tipo: string;
  es_principal: boolean;
  activo: boolean;
  parent_id?: number | null;
  hijos?: Localizacion[];
}

@Injectable({
  providedIn: 'root'
})
export class LocationsService {
  private apiUrl = 'http://localhost:8000/api/v1/localizaciones';

  constructor(private http: HttpClient) { }

  listarLocalizaciones(): Observable<Localizacion[]> {
    return this.http.get<Localizacion[]>(`${this.apiUrl}/`);
  }

  listarArbol(): Observable<Localizacion[]> {
    return this.http.get<Localizacion[]>(`${this.apiUrl}/arbol`);
  }

  crearLocalizacion(data: Localizacion): Observable<Localizacion> {
    return this.http.post<Localizacion>(`${this.apiUrl}/`, data);
  }

  actualizarLocalizacion(id: number, data: Partial<Localizacion>): Observable<Localizacion> {
    return this.http.put<Localizacion>(`${this.apiUrl}/${id}`, data);
  }

  eliminarLocalizacion(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/${id}`);
  }
}
