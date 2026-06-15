import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ProductsService, PaginatedResponse } from '../../../core/services/products.service';

@Component({
  selector: 'app-papelera',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './papelera.component.html',
  styleUrls: ['./papelera.component.css']
})
export class PapeleraComponent implements OnInit {
  productos: any[] = [];
  cargando = true;
  expandedProducts: Set<number> = new Set();
  expandedVariants: Set<number> = new Set();

  constructor(private productsService: ProductsService) {}

  ngOnInit(): void {
    this.cargarPapelera();
  }

  cargarPapelera(): void {
    this.cargando = true;
    // Por ahora traemos la página 1. Luego puedes añadir el paginador.
    this.productsService.obtenerPapelera(1, 50).subscribe({
      next: (res: PaginatedResponse) => {
        console.log('📦 Datos llegando a la papelera:', res);
        this.productos = res.items;
        this.cargando = false;
      },
      error: (err) => {
        console.error('Error al cargar papelera', err);
        this.cargando = false;
      }
    });
  }

  // --- CONTROL DE TABLA EXPANDIBLE ---
  toggleProduct(id: number): void {
    this.expandedProducts.has(id) ? this.expandedProducts.delete(id) : this.expandedProducts.add(id);
  }

  toggleVariant(id: number): void {
    this.expandedVariants.has(id) ? this.expandedVariants.delete(id) : this.expandedVariants.add(id);
  }

  // --- ACCIONES: RESTAURAR ---
  restaurar(tipo: 'producto' | 'variante' | 'stock-config' | 'stock-unit', id: number): void {
    const confirmacion = confirm(`¿Seguro que quieres restaurar este ${tipo}?`);
    if (!confirmacion) return;

    this.cargando = true;
    let request$;

    if (tipo === 'producto') request$ = this.productsService.restaurarProducto(id);
    else if (tipo === 'variante') request$ = this.productsService.restaurarVariante(id);
    else if (tipo === 'stock-config') request$ = this.productsService.restaurarStockConfig(id);
    else request$ = this.productsService.restaurarStockUnit(id);

    request$.subscribe({
      next: (res) => {
        alert(res.mensaje);
        this.cargarPapelera(); // Recargamos para que desaparezca de la papelera
      },
      error: (err) => {
        alert('Error: ' + (err.error?.detail || 'No se pudo restaurar.'));
        this.cargando = false;
      }
    });
  }

  // --- ACCIONES: DESTRUIR ---
  destruir(tipo: 'producto' | 'variante' | 'stock-unit', id: number): void {
    const confirmacion = confirm(`⚠️ CUIDADO: Vas a eliminar permanentemente este ${tipo}. Esta acción NO se puede deshacer. ¿Continuar?`);
    if (!confirmacion) return;

    this.cargando = true;
    let request$;

    if (tipo === 'producto') request$ = this.productsService.destruirProducto(id);
    else if (tipo === 'variante') request$ = this.productsService.destruirVariante(id);
    else request$ = this.productsService.destruirStockUnit(id);

    request$.subscribe({
      next: (res) => {
        alert(res.mensaje);
        this.cargarPapelera(); 
      },
      error: (err) => {
        // Aquí atrapamos el error 400 si tiene facturas asociadas
        alert('⛔ No se puede eliminar: ' + (err.error?.detail || 'Error desconocido.'));
        this.cargando = false;
      }
    });
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
}