import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LocationsService, Localizacion } from '../../../core/services/locations.service';

@Component({
  selector: 'app-locations',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './locations.component.html',
  styleUrls: ['./locations.component.css']
})
export class LocationsComponent implements OnInit {
  arbol: Localizacion[] = [];
  flatList: Localizacion[] = [];
  cargando = true;
  guardando = false;

  locActual: Partial<Localizacion> | null = null;
  editandoId: number | null = null;
  
  // Nodos expandidos (Guardamos los IDs)
  expandedNodes = new Set<number>();

  constructor(private locService: LocationsService) {}

  ngOnInit() {
    this.cargarDatos();
  }

  cargarDatos() {
    this.cargando = true;
    this.locService.listarArbol().subscribe({
      next: (res) => {
        this.arbol = res;
        this.cargando = false;
        // Expandir por defecto el primer nivel o todo si es pequeño
        if (this.expandedNodes.size === 0) {
           this.expandirTodo(this.arbol);
        }
      },
      error: () => this.cargando = false
    });

    this.locService.listarLocalizaciones().subscribe(res => {
      this.flatList = res;
    });
  }

  expandirTodo(nodos: Localizacion[]) {
    for (const nodo of nodos) {
      if (nodo.hijos && nodo.hijos.length > 0) {
        this.expandedNodes.add(nodo.id!);
        // this.expandirTodo(nodo.hijos); // Descomentar si se quiere todo abierto por defecto
      }
    }
  }

  toggleExpand(id: number) {
    if (this.expandedNodes.has(id)) {
      this.expandedNodes.delete(id);
    } else {
      this.expandedNodes.add(id);
    }
  }

  isExpanded(id: number): boolean {
    return this.expandedNodes.has(id);
  }

  nuevaLocalizacion() {
    this.editandoId = null;
    this.locActual = {
      nombre: '',
      tipo: 'almacen',
      activo: true,
      es_principal: false,
      parent_id: null
    };
  }

  nuevoHijo(parent: Localizacion) {
    this.editandoId = null;
    this.locActual = {
      nombre: '',
      tipo: 'estante',
      activo: true,
      es_principal: false,
      parent_id: parent.id
    };
  }

  editar(loc: Localizacion) {
    this.editandoId = loc.id!;
    this.locActual = { ...loc };
  }

  guardar() {
    if (!this.locActual || !this.locActual.nombre) return;

    this.guardando = true;
    
    if (this.editandoId) {
      this.locService.actualizarLocalizacion(this.editandoId, this.locActual).subscribe({
        next: () => {
          this.guardando = false;
          this.locActual = null;
          this.cargarDatos();
        },
        error: (err) => {
          this.guardando = false;
          alert(err.error?.detail || 'Error al guardar');
        }
      });
    } else {
      this.locService.crearLocalizacion(this.locActual as Localizacion).subscribe({
        next: () => {
          this.guardando = false;
          this.locActual = null;
          this.cargarDatos();
        },
        error: (err) => {
          this.guardando = false;
          alert(err.error?.detail || 'Error al crear');
        }
      });
    }
  }

  eliminar(loc: Localizacion) {
    if (!confirm(`¿Eliminar la ubicación "${loc.nombre}"?`)) return;
    
    this.locService.eliminarLocalizacion(loc.id!).subscribe({
      next: () => this.cargarDatos(),
      error: (err) => alert(err.error?.detail || 'Error al eliminar')
    });
  }
}
