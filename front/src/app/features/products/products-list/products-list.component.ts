import { Component, OnInit } from '@angular/core';
import { ProductsService } from '../../../core/services/products.service';
import { CommonModule, TitleCasePipe } from '@angular/common';
import { RouterLink } from "@angular/router";
import { FormsModule } from '@angular/forms';
import { CategorySelectionEvent, CategorySelectorComponent } from '../../../shared/components/selectors/category-selector/category-selector.component';
import { Subject, Subscription } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { ColorSelectorComponent } from "../../../shared/components/selectors/color-selector/color-selector.component";
import { Color } from '../add-product/product-form.config';
import { InventoryTableComponent } from "./components/inventory-table/inventory-table.component";
import { CatalogGridComponent } from "./components/catalog-grid/catalog-grid.component";
import { ProviderSelectorComponent } from "../components/provider-selector/provider-selector.component";
import { DateSelectorComponent } from "../../../shared/components/selectors/date-selector/date-selector.component";
import { ClientSelectorComponent } from "../add-product/components/client-selector/client-selector.component";
import { LocationSelectorComponent } from "../../../shared/components/selectors/location-selector/location-selector.component";
import { LocalizacionesService, Localizacion } from "../../../core/services/localizaciones.service";

export interface MisFiltros {
  search: string;
  tipo_busqueda: 'producto_id' | 'stock_unit_id'; // ✨ ACTUALIZADO
  categoria_id: number | null;
  marca_id: number | null;
  estado: string;
  precio_min: number | null;
  precio_max: number | null;
  ordenar_por: string;
  color: string | null;
  talla: string | null;
  proveedores_ids: number[];
  fecha_inicio: string | null;
  fecha_fin: string | null;
  disponibilidad: 'todos' | 'en_stock' | 'agotado';
  propietario_id?: number | null; // ✨ CAMBIADO A ID
  localizacion_id?: number | null; // ✨ AÑADIDO
}

@Component({
  selector: 'app-products-list',
  standalone: true,
  imports: [CommonModule, FormsModule, CategorySelectorComponent, ColorSelectorComponent, InventoryTableComponent, CatalogGridComponent, ProviderSelectorComponent, DateSelectorComponent, ClientSelectorComponent, LocationSelectorComponent],
  templateUrl: './products-list.component.html',
  styleUrl: './products-list.component.css'
})
export class ProductsListComponent implements OnInit {

  stocks: any[] = []; 
  vistaActual: 'catalogo' | 'inventario' = 'catalogo'; 
  productosPadre: any[] = []; 
  pagina: number = 1;       
  limite: number = 10;
  private querySubscription?: Subscription; 
  cargando: boolean = false;
  sinMasResultados: boolean = false;
  
  totalResultados: number = 0; 
  totalCatalogo: number = 0;    
  totalInventario: number = 0;  
  
  listaLocalizaciones: Localizacion[] = [];

  filtros: MisFiltros = {
    search: '',
    tipo_busqueda: 'producto_id', 
    color: null,
    talla: null,
    categoria_id: null,
    marca_id: null,
    estado: '',
    precio_min: null,
    precio_max: null,
    ordenar_por: 'fecha_desc',
    proveedores_ids: [],
    fecha_inicio: null,
    fecha_fin: null,
    disponibilidad: 'todos',
  };

  private searchSubject = new Subject<string>();
  listaFiltrosActivos: any[] = [];

  ngOnInit(): void {
    const savedView = localStorage.getItem('vinted_pref_vista');
    if (savedView === 'inventario' || savedView === 'catalogo') {
      this.vistaActual = savedView;
      // this.limite = this.vistaActual === 'catalogo' ? 10 : 20;
      this.filtros.tipo_busqueda = this.vistaActual === 'catalogo' ? 'producto_id' : 'stock_unit_id';
    }

    this.searchSubject.pipe(
      debounceTime(400),
      distinctUntilChanged()
    ).subscribe(texto => {
      this.filtros.search = texto;
      this.aplicarFiltros();
    });

    this.cargarLocalizaciones(); // ✨ AÑADIDO
    this.cargarDatos();
  }

  constructor(private productsService: ProductsService, private localizacionesService: LocalizacionesService) {} // ✨ AÑADIDO

  cargarLocalizaciones(): void {
    this.localizacionesService.obtenerLocalizaciones().subscribe({
      next: (data) => {
        const flat: Localizacion[] = [];
        const flatten = (nodes: Localizacion[]) => {
          nodes.forEach(n => {
            flat.push(n);
            if (n.hijos && n.hijos.length > 0) {
              flatten(n.hijos);
            }
          });
        };
        flatten(data);
        this.listaLocalizaciones = flat;
      }
    });
  }

  onPropietarioSelected(clienteId: number | null | undefined): void {
    this.filtros.propietario_id = clienteId;
    this.aplicarFiltros();
  }

  cargarDatos() {
    if (this.querySubscription) {
      this.querySubscription.unsubscribe();
    }

    if (this.sinMasResultados) return; 
    this.cargando = true;

    if (this.vistaActual === 'inventario') {
      this.querySubscription = this.productsService.obtenerInventarioIndividual(this.pagina, this.limite, this.filtros)
        .subscribe({
          next: (res: any) => this.procesarRespuesta(res.items, res.total, this.stocks),
          error: () => this.cargando = false
        });
    } else {
      this.querySubscription = this.productsService.obtenerProductos(this.pagina, this.limite, this.filtros)
        .subscribe({
          next: (res: any) => this.procesarRespuesta(res.items, res.total, this.productosPadre),
          error: () => this.cargando = false
        });
    }
  }

  private procesarRespuesta(nuevosItems: any[], total: number, arrayDestino: any[]) {
    this.totalResultados = total;
    if (this.vistaActual === 'catalogo') {
      this.totalCatalogo = total;
    } else {
      this.totalInventario = total;
    }
    
    if (nuevosItems.length === 0) {
      this.sinMasResultados = true;
    } else {
      arrayDestino.push(...nuevosItems); 
      if (nuevosItems.length < this.limite) this.sinMasResultados = true;
      else this.pagina += 1;
    }
    this.cargando = false;
  }

  onProveedoresSelected(ids: number[]) {
    this.filtros.proveedores_ids = ids;
    this.aplicarFiltros();
  }

  actualizarChipsDeFiltros() {
    const activos = [];
    if (this.filtros.search) {
      let labelBusqueda = `Búsqueda: ${this.filtros.search}`;
      if (this.filtros.tipo_busqueda === 'producto_id') labelBusqueda = `ID Prod: #${this.filtros.search}`;
      if (this.filtros.tipo_busqueda === 'stock_unit_id') labelBusqueda = `ID Lote: #${this.filtros.search}`; // ✨ CORREGIDO
      activos.push({ id: 'search', label: labelBusqueda });
    }
    if (this.filtros.propietario_id) activos.push({ id: 'propietario_id', label: `Dueño Filtrado` });
    if (this.filtros.localizacion_id) activos.push({ id: 'localizacion_id', label: `Sede: #${this.filtros.localizacion_id}` });

    if (this.filtros.proveedores_ids && this.filtros.proveedores_ids.length > 0) {
      activos.push({ id: 'proveedores', label: `${this.filtros.proveedores_ids.length} Proveedor(es)` });
    }
    if (this.filtros.disponibilidad !== 'todos') {
      const label = this.filtros.disponibilidad === 'en_stock' ? 'Solo en Stock' : 'Solo Agotados';
      activos.push({ id: 'disponibilidad', label: label });
    }
    if (this.filtros.fecha_inicio || this.filtros.fecha_fin) {
      let label = 'Fecha: ';
      if (this.filtros.fecha_inicio && this.filtros.fecha_fin) label += `${this.filtros.fecha_inicio} al ${this.filtros.fecha_fin}`;
      else if (this.filtros.fecha_inicio) label += `Desde ${this.filtros.fecha_inicio}`;
      else label += `Hasta ${this.filtros.fecha_fin}`;
      activos.push({ id: 'fechas', label: label });
    }
    if (this.filtros.categoria_id) activos.push({ id: 'categoria_id', label: 'Categoría seleccionada' });
    if (this.filtros.precio_min) activos.push({ id: 'precio_min', label: `Desde $${this.filtros.precio_min}` });
    if (this.filtros.precio_max) activos.push({ id: 'precio_max', label: `Hasta $${this.filtros.precio_max}` });
    if (this.filtros.estado) activos.push({ id: 'estado', label: `Estado: ${this.filtros.estado}` });
    if (this.filtros.color) activos.push({ id: 'color', label: 'Color', isColor: true, hex: this.filtros.color });
    
    this.listaFiltrosActivos = activos;
  }

  onFechasSelected(fechas: {inicio: string | null, fin: string | null}) {
    this.filtros.fecha_inicio = fechas.inicio;
    this.filtros.fecha_fin = fechas.fin;
    this.aplicarFiltros();
  }

  cambiarVista(nuevaVista: 'catalogo' | 'inventario') {
    if (this.vistaActual === nuevaVista) return;
    this.vistaActual = nuevaVista;
    this.cargando = false; 
    this.filtros.search = '';
    // Limpiamos los filtros no compatibles con el catálogo
    if (nuevaVista === 'catalogo') {
      if (this.filtros.ordenar_por.includes('precio_compra')) {
        this.filtros.ordenar_por = 'fecha_desc';
      }
    }
    localStorage.setItem('vinted_pref_vista', nuevaVista);
    this.aplicarFiltros(); 
  }

  onSearchInput(event: any): void {
    this.searchSubject.next(event.target.value);
  }

  aplicarFiltros() {
    this.actualizarChipsDeFiltros();
    this.querySubscription?.unsubscribe();
    this.filtros.tipo_busqueda = this.vistaActual === 'catalogo' ? 'producto_id' : 'stock_unit_id'; // ✨ CORREGIDO

    this.pagina = 1;
    this.stocks = [];
    this.productosPadre = [];
    this.sinMasResultados = false;
    this.limite = this.vistaActual === 'catalogo' ? 10 : 20;
    
    this.cargarDatos();
  }

  limpiarFiltros() {
    const tipoBusquedaActual = this.vistaActual === 'catalogo' ? 'producto_id' : 'stock_unit_id'; // ✨ CORREGIDO
    this.filtros = {
      search: '',
      tipo_busqueda: tipoBusquedaActual,
      color: null, talla: null, categoria_id: null,
      marca_id: null, estado: '', precio_min: null, precio_max: null,
      ordenar_por: 'fecha_desc',
      proveedores_ids: [],
      fecha_inicio: null,
      fecha_fin: null,
      disponibilidad: 'todos',
      propietario_id: null,
      localizacion_id: null
    };
    this.aplicarFiltros();
  }

  onCategorySelected(event: CategorySelectionEvent): void {
    this.filtros.categoria_id = event.categoriaId;
    this.aplicarFiltros();
  }
  
  onColorSelected(event: Color | null): void {
    if (event) {
      this.filtros.color = event.hex.replace('#', '').toUpperCase();
    } else {
      this.filtros.color = null;
    }
    this.aplicarFiltros(); 
  }

  eliminarFiltro(id: string) {
    if (id === 'search') {
      this.filtros.search = '';
      this.filtros.tipo_busqueda = this.vistaActual === 'catalogo' ? 'producto_id' : 'stock_unit_id';
    }
    if (id === 'propietario_id') this.filtros.propietario_id = null;
    if (id === 'localizacion_id') this.filtros.localizacion_id = null;
    if (id === 'proveedores') this.filtros.proveedores_ids = [];
    if (id === 'fechas') {
      this.filtros.fecha_inicio = null;
      this.filtros.fecha_fin = null;
    }
    if (id === 'categoria_id') this.filtros.categoria_id = null;
    if (id === 'precio_min') this.filtros.precio_min = null;
    if (id === 'precio_max') this.filtros.precio_max = null;
    if (id === 'estado') this.filtros.estado = '';
    if (id === 'color') this.filtros.color = null;
    if (id === 'disponibilidad') this.filtros.disponibilidad = 'todos';

    this.aplicarFiltros();
  }
}