import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { VentasService } from '../../../core/services/ventas.service';
import { DateRange, DateSelectorComponent } from '../../../shared/components/selectors/date-selector/date-selector.component';
import { MarcaService } from '../../../core/services/marcas.service';
import { CategorySelectorComponent, CategorySelectionEvent } from '../../../shared/components/selectors/category-selector/category-selector.component';
import { LocationSelectorComponent } from '../../../shared/components/selectors/location-selector/location-selector.component';

import { TranslatePipe } from '@ngx-translate/core';

@Component({
  selector: 'app-sales-list',
  standalone: true,
  imports: [CommonModule, FormsModule, DateSelectorComponent, CategorySelectorComponent, LocationSelectorComponent, TranslatePipe],
  templateUrl: './sales-list.component.html',
  styleUrls: ['./sales-list.component.css']
})
export class SalesListComponent implements OnInit {
  ventas: any[] = [];
  cargando = true;
  marcas: any[] = [];
  totalItems = 0;
  page = 1;
  limit = 10;

  // ✨ VARIABLES DE BÚSQUEDA (Las 3 Cajas)
  searchProducto = '';
  tipoBusquedaProd = 'stock_unit_id'; 
  searchCodigo = '';
  searchCliente = '';
  tipoBusquedaCliente = 'nombre'; // 👈 NUEVO: Selector de cliente

  // Otros filtros
  filtroEstadoPago = ''; // ✨ REEMPALZA filtroEstado
  filtroCanal = '';
  fechaInicio: string | null = null;
  fechaFin: string | null = null;
  filtroVendedor: string = '';
  filtroMarca: string = '';
  filtroCategoria: number | null = null; 
  localizacion_id: number | null | undefined = null; // ✨ NUEVO
  showFilters: boolean = false;

  totalRecaudado = 0;
  totalBeneficio = 0;

  constructor(
    private ventasService: VentasService, 
    private marcaService: MarcaService, 
    private router: Router
  ) {}

  ngOnInit() {
    this.cargarMarcas();
    this.cargarVentas();
  }

  cargarMarcas() {
    this.marcaService.listarMarcas().subscribe({
      next: (res) => this.marcas = res,
      error: (err) => console.error('Error al cargar marcas', err)
    });
  }

  onCategoriaSeleccionada(event: CategorySelectionEvent) {
    this.filtroCategoria = event.categoriaId;
    this.buscar();
  }

  cargarVentas() {
    this.cargando = true;
    this.ventasService.listarVentas(
      this.page, this.limit,
      this.searchProducto, this.tipoBusquedaProd,         // Caja 1
      this.searchCodigo,                                  // Caja 2
      this.searchCliente, this.tipoBusquedaCliente,       // Caja 3 ✨
      undefined,                                          // cliente_id
      this.filtroEstadoPago || undefined,                 // ✨ estado_pago
      undefined,                                          // estado_envio
      this.filtroCanal, 
      this.fechaInicio || undefined, this.fechaFin || undefined, 
      this.filtroVendedor,
      this.filtroMarca || undefined,        
      this.filtroCategoria || undefined,
      'creacion',                                         // tipo_fecha
      false,                                              // solo_online
      true,                                               // ✨ include_details (Para SKU/IDs)
      undefined,                                          // estado_legado
      this.localizacion_id || undefined                   // ✨ NUEVO: localizacion_id
    ).subscribe({
      next: (res) => {
        this.ventas = res.items;
        this.totalItems = res.total;
        this.totalRecaudado = res.suma_recaudado;
        this.totalBeneficio = res.suma_beneficio;
        this.cargando = false;
      },
      error: (err) => {
        console.error(err);
        this.cargando = false;
      }
    });
  }

  onFechasCambiadas(rango: DateRange) {
    this.fechaInicio = rango.inicio;
    this.fechaFin = rango.fin;
    this.buscar(); 
  }

  toggleFilters(): void {
    this.showFilters = !this.showFilters;
  }

  buscar() {
    this.page = 1; 
    this.cargarVentas();
  }

  limpiarFiltros() {
    this.searchProducto = '';
    this.tipoBusquedaProd = 'stock_unit_id';
    this.searchCodigo = '';
    this.searchCliente = '';
    this.tipoBusquedaCliente = 'nombre';
    
    this.filtroEstadoPago = '';
    this.filtroCanal = '';
    this.filtroVendedor = ''; 
    this.fechaInicio = null; 
    this.fechaFin = null;
    this.filtroMarca = '';
    this.filtroCategoria = null; 
    this.buscar();
  }

  get hasActiveFilters(): boolean {
    return !!(this.searchProducto || this.searchCodigo || this.searchCliente || this.filtroEstadoPago || this.filtroCanal || this.filtroVendedor || this.fechaInicio || this.fechaFin || this.filtroMarca || this.filtroCategoria);
  }

  removerFiltro(tipo: string) {
    if (tipo === 'producto') this.searchProducto = '';
    if (tipo === 'codigo') this.searchCodigo = '';
    if (tipo === 'cliente') this.searchCliente = '';
    if (tipo === 'pago') this.filtroEstadoPago = '';
    if (tipo === 'canal') this.filtroCanal = '';
    if (tipo === 'vendedor') this.filtroVendedor = '';
    if (tipo === 'marca') this.filtroMarca = '';
    if (tipo === 'categoria') this.filtroCategoria = null;
    if (tipo === 'fechas') {
      this.fechaInicio = null;
      this.fechaFin = null;
    }
    this.buscar();
  }

  getLabelPago(val: string): string {
    const map: any = { 'pendiente': 'Pendiente', 'pagado': 'Pagados', 'reembolsado': 'Reembolsados' };
    return map[val] || val;
  }
  
  getLabelCanal(val: string): string {
    const map: any = { 'tienda_fisica': 'Casa', 'web': 'Web', 'vinted': 'Vinted', 'wallapop': 'Wallapop' };
    return map[val] || val;
  }

  getMarcaName(id: string): string {
    const m = this.marcas.find(x => x.id.toString() === id.toString());
    return m ? m.nombre : id;
  }

  generarDevolucion(venta: any) {
    const confirma = confirm(`¿Estás seguro de que quieres generar una DEVOLUCIÓN TOTAL para la venta ${venta.codigo_venta}?\n\n- Se reembolsará el total: ${venta.total}€\n- Todas las prendas volverán al inventario.`);
    if (!confirma) return;

    this.ventasService.editarVenta(venta.id, {
      estado_pago: 'reembolsado'
    }).subscribe({
      next: () => {
        alert('✅ Devolución procesada correctamente. El stock ha sido liberado.');
        this.cargarVentas();
      },
      error: (err) => {
        alert('❌ Error al procesar devolución: ' + (err.error?.detail || 'Desconocido'));
      }
    });
  }

  cambiarPagina(nuevaPagina: number) {
    if (nuevaPagina >= 1 && nuevaPagina <= this.totalPages) {
      this.page = nuevaPagina;
      this.cargarVentas();
    }
  }

  get totalPages(): number {
    return Math.ceil(this.totalItems / this.limit);
  }

  irAEditar(ventaId: number) {
    this.router.navigate(['/edit-sale', ventaId]);
  }
}