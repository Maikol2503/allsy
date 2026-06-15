import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class CategoriaService {
  private apiUrl = `http://localhost:8000/api/v1/categorias`;

  constructor(private http: HttpClient) {}

  // Obtiene todas (la lista plana de 485 elementos que mostraste)
  listarTodas(): Observable<any[]> {
    return this.http.get<any[]>(this.apiUrl);
  }
}