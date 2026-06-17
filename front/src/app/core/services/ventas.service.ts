import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

// Definimos interfaces para que tu código sea robusto y tengas autocompletado
export interface DetalleVenta {
  stock_id: number;
  cantidad: number;
  precio_unitario: number;
}

export interface VentaData {
  fecha?: string;
  canal: string;
  vendedor: string;
  metodo_pago: string;
  estado_venta?: string;
  estado_pago: string;    // 👈 NUEVO
  estado_envio?: string;  // ✨ NUEVO
  nombre_cliente?: string;
  email_cliente?: string;
  costo_envio?: number;
  descuento_total?: number;
  transaccion_id_externo?: string;
  empresa_transporte?: string; // 👈 NUEVO
  numero_seguimiento?: string; // 👈 NUEVO
  etiqueta_url?: string;       // ✨ NUEVO
  etiqueta_imprimida?: boolean; // ✨ NUEVO
  detalles: DetalleVenta[]; 
  identificador_cliente?: string; // <-- AÑADIR ESTA LÍNEA
  tipo_identificador?: string;
  prefijo_telefono?: string;
  tipo_documento?: string;
  pais?: string;
  apellidos_cliente?: string;
  monto_reembolsado?: number;
}

@Injectable({
  providedIn: 'root'
})
export class VentasService {

  // ⚠️ Corregido: Quitamos '/auth' de la URL base para ventas
  private API_URL = 'http://localhost:8000/api/v1/ventas';

  constructor(private http: HttpClient) {}

  /**
   * 🔎 Buscar producto por ID de Stock Físico (o SKU)
   * Útil para cuando escanean o buscan una prenda exacta
   */
  buscarProductoPorStock(stockId: string | number): Observable<any> {
    return this.http.get<any>(`${this.API_URL}/producto/scan/${stockId}`);
  }


  obtenerConteoCompras(identificador: string): Observable<{compras_totales: number}> {
  return this.http.get<{compras_totales: number}>(`${this.API_URL}/historial-cliente/${identificador}`);
}

  /**
   * 💰 Registrar una venta completa
   * Ahora enviamos un JSON plano, Angular se encarga del resto
   */
  registrarVenta(data: VentaData): Observable<any> {
    // Ya no hace falta crear un FormData. 
    // Enviamos el objeto 'data' directamente como segundo parámetro.
    return this.http.post<any>(`${this.API_URL}/`, data);
  }

  /**
   * 📄 Obtener historial de ventas (Opcional, para el futuro)
   */
  // listarVentas(page: number = 1, limit: number = 10): Observable<any> {
  //   return this.http.get<any>(`${this.API_URL}/?page=${page}&limit=${limit}`);
  // }


  // 📄 Obtener historial de ventas con filtros
  // 📄 Obtener historial de ventas con filtros
  // 📄 Obtener historial de ventas con filtros
  listarVentas(
    page: number, limit: number, 
    searchProducto?: string, tipoBusquedaProd?: string, 
    searchCodigo?: string, 
    searchCliente?: string, tipoBusquedaCliente?: string, // ✨ NUEVOS
    cliente_id?: number,
    estado_pago?: string, // ✨ EXPLÍCITO
    estado_envio?: string, // ✨ EXPLÍCITO
    canal?: string, fechaInicio?: string, fechaFin?: string, 
    vendedor?: string, marca_id?: string, categoria_id?: number,
    tipo_fecha: string = 'creacion',
    solo_online: boolean = false,
    include_details: boolean = false,
    estado_legado?: string, // 👈 Para no romper llamadas antiguas
    localizacion_id?: number // ✨ NUEVO
  ): Observable<any> {
    // ✨ CORRECCIÓN: Uso de HttpParams para asegurar que los parámetros se codifiquen correctamente en la URL
    let params = new HttpParams()
      .set('page', page.toString())
      .set('limit', limit.toString())
      .set('tipo_fecha', tipo_fecha);
    
    if (solo_online) params = params.set('solo_online', 'true');
    if (include_details) params = params.set('include_details', 'true');
    if (localizacion_id) params = params.set('localizacion_id', localizacion_id.toString());
    if (searchProducto) params = params.set('search_producto', searchProducto);
    if (tipoBusquedaProd) params = params.set('tipo_busqueda_prod', tipoBusquedaProd);
    if (searchCodigo) params = params.set('search_codigo', searchCodigo);
    
    if (searchCliente) params = params.set('search_cliente', searchCliente);
    if (tipoBusquedaCliente) params = params.set('tipo_busqueda_cliente', tipoBusquedaCliente);
    if (cliente_id) params = params.set('cliente_id', cliente_id.toString());

    if (estado_pago) params = params.set('estado_pago', estado_pago);
    if (estado_envio) params = params.set('estado_envio', estado_envio);
    if (estado_legado) params = params.set('estado_venta', estado_legado);

    if (canal) params = params.set('canal', canal);
    if (fechaInicio) params = params.set('fecha_inicio', fechaInicio); 
    if (fechaFin) params = params.set('fecha_fin', fechaFin);
    if (vendedor) params = params.set('vendedor', vendedor);    
    if (marca_id) params = params.set('marca_id', marca_id.toString());
    if (categoria_id) params = params.set('categoria_id', categoria_id.toString());

    return this.http.get<any>(`${this.API_URL}/`, { params });
  }

  // 📄 Obtener detalle de una venta
  obtenerVenta(ventaId: number): Observable<any> {
    return this.http.get<any>(`${this.API_URL}/detalle/${ventaId}`);
  }

  obtenerVentaPorId(ventaId: number): Observable<any> {
    return this.obtenerVenta(ventaId);
  }

  // 📝 Editar venta
  editarVenta(ventaId: number, data: any): Observable<any> {
    return this.http.put<any>(`${this.API_URL}/${ventaId}`, data);
  }

  // 🔄 Devolución Física (Artículo vuelve a stock, total baja)
  devolverItemFisicamente(ventaId: number, detalleId: number, estadoStock: string = 'en_stock'): Observable<any> {
    return this.http.put<any>(`${this.API_URL}/${ventaId}/item/${detalleId}/devolucion-fisica?estado_stock=${estadoStock}`, {});
  }

  // ✨ Resolver retorno en tránsito (Extravío o Llegada)
  resolverRetornoTransito(ventaId: number, detalleId: number, resolucion: string): Observable<any> {
    return this.http.put<any>(`${this.API_URL}/${ventaId}/item/${detalleId}/resolver-retorno?resolucion=${resolucion}`, {});
  }

  // 💸 Compensación Allsys (Cliente se queda artículo, Allsys asume gasto, Dueño cobra)
  registrarCompensacionAllsys(ventaId: number, monto: number, motivo: string): Observable<any> {
    return this.http.put<any>(`${this.API_URL}/${ventaId}/compensacion-allsys?monto=${monto}&motivo=${encodeURIComponent(motivo)}`, {});
  }

  // ✏️ Corregir precio
  corregirPrecioItem(ventaId: number, detalleId: number, nuevoPrecio: number): Observable<any> {
    return this.http.put<any>(`${this.API_URL}/${ventaId}/item/${detalleId}/precio?nuevo_precio=${nuevoPrecio}`, {});
  }

  // 🗑️ Eliminar ítem individual (Devolución Parcial - LEGADO)
  eliminarItemVenta(ventaId: number, detalleId: number, estado_devolucion: string = 'en_stock'): Observable<any> {
    return this.http.delete<any>(`${this.API_URL}/${ventaId}/item/${detalleId}?estado_devolucion=${estado_devolucion}`);
  }

  // 🔄 Intercambiar ítem individual (Trueque Manual)
  intercambiarItemVenta(ventaId: number, detalleId: number, nuevoStockId: number): Observable<any> {
    return this.http.put<any>(`${this.API_URL}/${ventaId}/item/${detalleId}/swap?nuevo_stock_id=${nuevoStockId}`, {});
  }

  // 📦 Procesar escaneo en logística (Smart Scan)
  procesarSmartScan(ventaId: number, scannedUnitId: number): Observable<any> {
    return this.http.put<any>(`${this.API_URL}/${ventaId}/smart-scan?scanned_unit_id=${scannedUnitId}`, {});
  }

  /**
   * 📦 Obtiene una lista paginada de todas las ventas online pendientes de envío
   */
  obtenerPendientesLogistica(page: number = 1, limit: number = 10, search?: string, tipoBusqueda: string = 'general', estado?: string, localizacion_id?: number | null): Observable<any> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('limit', limit.toString())
      .set('tipo_busqueda', tipoBusqueda);
    
    if (search) params = params.set('search', search);
    if (estado) params = params.set('estado', estado);
    if (localizacion_id) params = params.set('localizacion_id', localizacion_id.toString());

    return this.http.get<any>(`${this.API_URL}/logistica/pendientes`, { params });
  }

  /**
   * 🖨️ Devuelve la URL para usar el proxy del backend y evadir restricciones de CORS en etiquetas.
   */
  obtenerUrlProxyEtiqueta(urlEtiqueta: string): string {
    return `${this.API_URL}/proxy-etiqueta?url=${encodeURIComponent(urlEtiqueta)}`;
  }
}