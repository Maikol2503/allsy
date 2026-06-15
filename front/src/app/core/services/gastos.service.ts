import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface GastoCreate {
  concepto: string;
  categoria: string;
  monto: number;
  metodo_pago: string;
  fecha: string;
  notas: string;
  // ✨ Los nuevos campos
  proveedor_id?: number | null;
  proveedor_nombre_nuevo?: string | null;
}

@Injectable({
  providedIn: 'root'
})
export class GastosService {
  private apiUrl = 'http://localhost:8000/api/v1/gastos';

  constructor(private http: HttpClient) {}

  // ✨ Acepta un objeto con filtros
  getGastos(filtros: any = {}): Observable<any> {
    let params = new HttpParams();
    
    // Recorremos las llaves y añadimos las que tengan valor
    Object.keys(filtros).forEach(key => {
      if (filtros[key] !== null && filtros[key] !== undefined && filtros[key] !== '') {
        params = params.set(key, filtros[key]);
      }
    });

    return this.http.get<any>(this.apiUrl, { params });
  }

  obtenerGastoPorId(id: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/${id}`);
  }

  registrarGasto(gasto: GastoCreate): Observable<any> {
    return this.http.post(this.apiUrl, gasto);
  }

  // ✨ NUEVA FUNCIÓN
  editarGasto(id: number, gasto: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/${id}`, gasto);
  }
}