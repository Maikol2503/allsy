import { Component, OnInit } from '@angular/core';
import { CommonModule, TitleCasePipe, KeyValuePipe, DecimalPipe, DatePipe } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ProductsService } from '../../../core/services/products.service';
import { LocationsService, Localizacion } from '../../../core/services/locations.service';

@Component({
  selector: 'app-stock-detail',
  standalone: true,
  imports: [
    CommonModule, 
    FormsModule, 
    RouterModule,
    TitleCasePipe, 
    KeyValuePipe, 
    DecimalPipe, 
    DatePipe
  ],
  templateUrl: './stock-detail.component.html',
  styleUrls: ['./stock-detail.component.css']
})
export class StockDetailComponent implements OnInit {

  stock: any = null; // Este es nuestro "Lote" (StockConfig)
  cargando = true;
  stockId: number | null = null;
  fullLocationPath: string = 'Sin asignar'; // ✨ NUEVO

  // ✨ Filtros y búsqueda
  filtroSku: string = '';
  filtroEstado: string = 'todos';

  constructor(
    private route: ActivatedRoute,
    private productsService: ProductsService,
    private locService: LocationsService,
    private router: Router
  ) {}

  ngOnInit() {
    this.stockId = Number(this.route.snapshot.paramMap.get('id'));
    if (this.stockId) {
      this.cargarDatos();
    }
  }

  cargarDatos() {
    this.cargando = true;
    this.productsService.obtenerStock(this.stockId!).subscribe({
      next: (data) => {
        console.log("🚨 DATOS DEL STOCK CONFIG RECIBIDOS:", data);
        this.stock = data;
        this.cargando = false;
        
        if (this.stock.localizacion_id) {
          this.cargarRutaLocalizacion(this.stock.localizacion_id);
        }
      },
      error: (err) => {
        console.error('Error al cargar detalle de stock:', err);
        this.cargando = false;
      }
    });
  }

  cargarRutaLocalizacion(targetId: number) {
    this.locService.listarArbol().subscribe(arbol => {
      const mapa = new Map<number, string>();
      this.construirMapaNombres(arbol, '', mapa);
      this.fullLocationPath = mapa.get(targetId) || this.stock?.localizacion?.nombre || 'Desconocido';
    });
  }

  private construirMapaNombres(nodos: Localizacion[], prefijo: string, mapa: Map<number, string>) {
    for (const n of nodos) {
      const path = prefijo ? `${prefijo} > ${n.nombre}` : n.nombre;
      mapa.set(n.id!, path);
      if (n.hijos) this.construirMapaNombres(n.hijos, path, mapa);
    }
  }

  getLabelEstadoGestion(estado: string): string {
    const mapa: any = {
      'en_stock': '✅ En Almacén',
      'vendido': '💰 Vendido',
      'devuelto_dueno': '🔙 Devuelto al dueño',
      'donado_a_ong': '💖 Donado a ONG',
      'extraviado': '⚠️ Extraviado',
      'en_camino_devolucion': '📦 En Tránsito (Devolución)'
    };
    return mapa[estado] || estado;
  }

  get unidadesFiltradas() {
    if (!this.stock?.stock_units) return [];
    return this.stock.stock_units.filter((u: any) => {
      const matchSku = u.sku.toLowerCase().includes(this.filtroSku.toLowerCase()) || String(u.id).includes(this.filtroSku);
      const matchEstado = this.filtroEstado === 'todos' || u.estado_gestion === this.filtroEstado;
      return matchSku && matchEstado;
    });
  }

  get stats() {
    if (!this.stock?.stock_units) return { total: 0, disponibles: 0, vendidos: 0 };
    const units = this.stock.stock_units;
    return {
      total: units.length,
      disponibles: units.filter((u: any) => u.estado_gestion === 'en_stock').length,
      vendidos: units.filter((u: any) => u.estado_gestion === 'vendido').length,
      otros: units.filter((u: any) => !['en_stock', 'vendido'].includes(u.estado_gestion)).length
    };
  }

  formatearEstado(estado: string): string {
    const mapa: { [key: string]: string } = {
      'en_stock': '✅ En Almacén', 
      'vendido': '💰 Vendido',
      'devuelto_dueno': '🔙 Devuelto', 
      'donado_a_ong': '💖 Donado', 
      'extraviado': '⚠️ Extraviado'
    };
    return mapa[estado] || estado.replace('_', ' ');
  }

  cambiarEstadoUnidad(u: any, nuevoEstado: string) {
    this.productsService.actualizarEstadoUnidadFisica(u.id, nuevoEstado).subscribe({
      next: () => {
        u.estado_gestion = nuevoEstado;
        // No recargamos todo para no perder el scroll
      },
      error: (err) => alert('❌ No se pudo cambiar el estado: ' + (err.error?.detail || 'Error desconocido'))
    });
  }

  eliminarUnidad(u: any, idx: number) {
    if (!confirm(`¿Estás seguro de que quieres mover la prenda #${u.id} a la papelera?`)) return;
    this.productsService.moverStockUnitPapelera(u.id).subscribe({
      next: () => {
        // La quitamos de la lista local
        this.stock.stock_units = this.stock.stock_units.filter((unit: any) => unit.id !== u.id);
      }
    });
  }

  volver() { 
    this.router.navigate(['/detail-product', this.stock.producto_id]); 
  }

  editarLote() {
    this.router.navigate(['/edit-stock', this.stockId]);
  }
}