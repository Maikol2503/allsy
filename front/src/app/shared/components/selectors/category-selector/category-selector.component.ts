import { Component, OnInit, Output, EventEmitter, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ProductsService } from '../../../../core/services/products.service';

export interface CategorySelectionEvent {
  categoriaId: number | null;
  rutaCategorias?: any[];
}

@Component({
  selector: 'app-category-selector',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './category-selector.component.html',
  styleUrls: ['./category-selector.component.css']
})
export class CategorySelectorComponent implements OnInit {
  todasLasCategorias: any[] = [];
  categoriaActual: any[] = [];
  rutaCategorias: any[] = [];
  dropdownAbierto = false;
  private idPendiente: number | null = null;

  // ✨ NUEVO INPUT: Por defecto en false. El padre lo activa si quiere.
  @Input() permitirSeleccionarTodo: boolean = false;

  @Input() set value(id: number | null) {
    if (id === null) {
      this.rutaCategorias = [];
      this.categoriaActual = this.todasLasCategorias.filter((c: any) => c.parent_id === null);
      this.dropdownAbierto = false;
    } else if (id) {
      // Si las categorías ya llegaron, reconstruye la ruta
      if (this.todasLasCategorias.length > 0) {
        this.reconstruirRutaDesdeId(id, false);
      } else {
        // ✨ EL CABLE QUE FALTABA: Guardar el ID en la sala de espera
        this.idPendiente = id;
      }
    }
  }

  @Input() set categoriaInicial(id: number | null) {
    if (id) this.value = id;
  }

  @Output() categorySelected = new EventEmitter<CategorySelectionEvent>();

  constructor(private productsService: ProductsService) {}

  ngOnInit(): void {
    this.cargarCategorias();
  }

  private cargarCategorias(): void {
    this.productsService.cargarCategorias().subscribe({
      next: (data) => {
        console.log('Categorías cargadas:', data);
        this.todasLasCategorias = data;
        if (this.rutaCategorias.length === 0) {
          this.categoriaActual = data.filter((c: any) => c.parent_id === null);
        }
        
        if (this.idPendiente) {
          this.reconstruirRutaDesdeId(this.idPendiente);
          this.idPendiente = null;
        }
      }
    });
  }

  private limpiarEstadoInterno() {
    this.rutaCategorias = [];
    this.categoriaActual = this.todasLasCategorias.filter((c: any) => c.parent_id === null);
    this.dropdownAbierto = false;
  }

  public reconstruirRutaDesdeId(id: number, emitir = true) {
    const ruta: any[] = [];
    let current = this.todasLasCategorias.find(c => c.id === id);
    
    while (current) {
      ruta.unshift(current);
      current = current.parent_id ? this.todasLasCategorias.find(c => c.id === current.parent_id) : null;
    }
    
    this.rutaCategorias = ruta;
    
    if (emitir) {
      this.categorySelected.emit({
        categoriaId: id,
        rutaCategorias: [...this.rutaCategorias]
      });
    }
  }

  seleccionarCategoria(cat: any): void {
    if (cat.parent_id === null) {
      this.rutaCategorias = [cat];
    } else {
      const parentIndex = this.rutaCategorias.findIndex(c => c.id === cat.parent_id);
      if (parentIndex !== -1) {
        this.rutaCategorias = this.rutaCategorias.slice(0, parentIndex + 1);
      }
      this.rutaCategorias.push(cat);
    }

    const sub = this.todasLasCategorias.filter(c => c.parent_id === cat.id);
    
    if (sub.length > 0) {
      this.categoriaActual = sub;
    } else {
      this.dropdownAbierto = false;
      this.categorySelected.emit({
        categoriaId: cat.id,
        rutaCategorias: [...this.rutaCategorias]
      });
    }
  }

  // ✨ NUEVA FUNCIÓN: Obtiene la categoría padre de los elementos que se están mostrando actualmente
  getCategoriaNavegacion(): any {
    if (this.categoriaActual.length > 0) {
      const parentId = this.categoriaActual[0].parent_id;
      if (parentId) {
        return this.todasLasCategorias.find(c => c.id === parentId);
      }
    }
    return null;
  }

  // ✨ NUEVA FUNCIÓN: Para cuando el usuario hace clic en "Todo en..."
  confirmarSeleccionTodo(): void {
    const parent = this.getCategoriaNavegacion();
    if (parent) {
      this.dropdownAbierto = false;
      this.reconstruirRutaDesdeId(parent.id, true);
    }
  }

  volverCategoria(): void {
    this.rutaCategorias.pop();
    const last = this.rutaCategorias.at(-1);
    this.categoriaActual = last ? 
      this.todasLasCategorias.filter(c => c.parent_id === last.id) : 
      this.todasLasCategorias.filter(c => c.parent_id === null);
  }

  limpiarSeleccion(event: Event): void {
    event.stopPropagation();
    this.limpiarEstadoInterno();
    this.categorySelected.emit({ categoriaId: null, rutaCategorias: [] });
  }

  getNombreCategoriaSeleccionada(): string {
    return this.rutaCategorias.length ? 
      this.rutaCategorias.map(c => c.nombre).join(' / ') : 
      'Seleccionar categoría';
  }

  tieneHijos(cat: any): boolean {
    return this.todasLasCategorias.some(c => c.parent_id === cat.id);
  }

  abrirCategorias(): void { 
    this.dropdownAbierto = !this.dropdownAbierto; 
  }
}