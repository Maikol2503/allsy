import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Localizacion {
  id: number;
  nombre: string;
  descripcion?: string;
  tipo: string;
  es_principal: boolean;
  parent_id?: number;
  hijos?: Localizacion[];
}

@Injectable({
  providedIn: 'root'
})
export class LocalizacionesService {
  private apiUrl = 'http://localhost:8000/api/v1/localizaciones';

  constructor(private http: HttpClient) {}

  obtenerLocalizaciones(): Observable<Localizacion[]> {
    return this.http.get<Localizacion[]>(`${this.apiUrl}/arbol`);
  }
}
