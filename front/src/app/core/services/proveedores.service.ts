import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, of, tap } from 'rxjs';

// Creamos un tipo para no equivocarnos con los strings mágicos
export type TipoProveedor = 'inventario' | 'gasto' | 'todos';

@Injectable({
  providedIn: 'root'
})
export class SuppliersService {

  private apiUrl = 'http://localhost:8000/api/v1/proveedores';
  
  // ✨ MEJORA DE CACHÉ: Ahora guardamos listas separadas por tipo
  // Ej: { 'inventario': [...], 'gasto': [...] }
  private proveedoresCache: Record<string, any[]> = {};

  constructor(private http: HttpClient) {}

  /**
   * Carga la lista de proveedores filtrada por tipo (con caché inteligente)
   */
  getProveedores(tipo: TipoProveedor = 'inventario'): Observable<any[]> {
    // 1. Revisamos si ya tenemos esta lista específica en caché
    if (this.proveedoresCache[tipo] && this.proveedoresCache[tipo].length > 0) {
      return of(this.proveedoresCache[tipo]);
    }

    // 2. Si no, la pedimos al backend enviando el parámetro ?tipo=...
    const params = new HttpParams().set('tipo', tipo);

    return this.http.get<any[]>(this.apiUrl, { params }).pipe(
      tap(data => this.proveedoresCache[tipo] = data)
    );
  }

  /**
   * Fuerza la actualización de la lista (ignora caché)
   */
  refrescarProveedores(tipo: TipoProveedor = 'inventario'): Observable<any[]> {
    const params = new HttpParams().set('tipo', tipo);
    
    return this.http.get<any[]>(this.apiUrl, { params }).pipe(
      tap(data => this.proveedoresCache[tipo] = data)
    );
  }

  /**
   * Crea un nuevo proveedor
   * @param nombre Nombre del proveedor
   * @param contexto Si es para inventario o para gasto (activa la bandera correcta en el backend)
   */
  crearProveedor(nombre: string, contexto: TipoProveedor = 'inventario'): Observable<any> {
    const params = new HttpParams()
      .set('nombre', nombre)
      .set('contexto', contexto); // Le decimos al backend qué bandera encender

    return this.http.post(`${this.apiUrl}/`, null, { params }).pipe(
      tap(() => this.limpiarCacheGlobal()) // Limpiamos todo porque el nuevo proveedor afecta las listas
    );
  }

  /**
   * Actualiza un proveedor existente
   */
  actualizarProveedor(id: number, nuevoNombre: string): Observable<any> {
    return this.http.put(`${this.apiUrl}/${id}`, null, {
      params: { nombre: nuevoNombre }
    }).pipe(
      tap(() => this.limpiarCacheGlobal())
    );
  }

  /**
   * Elimina un proveedor
   */
  eliminarProveedor(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/${id}`).pipe(
      tap(() => this.limpiarCacheGlobal())
    );
  }

  /**
   * Helper privado para limpiar toda la caché cuando hay cambios
   */
  private limpiarCacheGlobal(): void {
    this.proveedoresCache = {};
  }
}