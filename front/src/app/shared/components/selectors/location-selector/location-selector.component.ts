import { Component, Input, Output, EventEmitter, OnInit, OnChanges, SimpleChanges, HostListener, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LocationsService, Localizacion } from '../../../../core/services/locations.service';

@Component({
  selector: 'app-location-selector',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="custom-dropdown" [class.disabled]="disabled">
      <div class="dropdown-header" (click)="toggleDropdown()">
        <span>{{ getNombreSeleccionado() }}</span>
        <span class="arrow">{{ isOpen ? '▲' : '▼' }}</span>
      </div>

      <div class="dropdown-menu" *ngIf="isOpen">
        <div class="search-bar">
          <input type="text" [(ngModel)]="filtro" (ngModelChange)="filtrarArbol()" placeholder="Buscar ubicación..." (click)="$event.stopPropagation()">
        </div>
        
        <div class="tree-container">
          <div class="tree-item" (click)="seleccionar(null)">
            <span class="node-name" [class.selected]="!localizacionId" style="color: #64748b;">--- Quitar selección ---</span>
          </div>
          <ng-container *ngTemplateOutlet="recursiveList; context:{ $implicit: arbolVisible, depth: 0 }"></ng-container>
        </div>
      </div>
    </div>

    <ng-template #recursiveList let-nodos let-depth="depth">
      <div *ngFor="let nodo of nodos" class="tree-node" [style.padding-left.px]="depth > 0 ? 15 : 0">
        
        <div class="node-content" [class.selected]="localizacionId === nodo.id">
          <!-- Botón de expandir/contraer -->
          <span class="toggle-btn" 
                [style.visibility]="nodo.hijos && nodo.hijos.length ? 'visible' : 'hidden'"
                (click)="toggleNodo(nodo, $event)">
            {{ isExpanded(nodo) ? '▼' : '▶' }}
          </span>
          
          <!-- Nombre y selección -->
          <div class="node-label" (click)="seleccionar(nodo)">
            <span class="node-icon">{{ getIcon(nodo.tipo) }}</span>
            <span class="node-name">{{ nodo.nombre }}</span>
          </div>
        </div>

        <!-- Hijos recursivos -->
        <div *ngIf="isExpanded(nodo) && nodo.hijos && nodo.hijos.length > 0" class="node-children">
          <ng-container *ngTemplateOutlet="recursiveList; context:{ $implicit: nodo.hijos, depth: depth + 1 }"></ng-container>
        </div>

      </div>
    </ng-template>
  `,
  styles: [`
    .custom-dropdown { position: relative; width: 100%; font-family: inherit; }
    .custom-dropdown.disabled { opacity: 0.6; pointer-events: none; }
    
    .dropdown-header {
      padding: 12px 14px;
      border: 1px solid var(--ap-border-base, #cbd5e1);
      border-radius: var(--ap-radius-md, 8px);
      font-size: 0.95rem;
      background-color: var(--ap-bg-main, #fff);
      color: var(--text-main, #1e293b);
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
      transition: border-color 0.2s;
    }
    .dropdown-header:hover { border-color: var(--primary, #007782); }
    
    .dropdown-menu {
      position: absolute;
      top: 100%;
      left: 0;
      width: 100%;
      max-height: 350px;
      background: #fff;
      border: 1px solid var(--ap-border-base, #cbd5e1);
      border-radius: var(--ap-radius-md, 8px);
      box-shadow: 0 4px 15px rgba(0,0,0,0.1);
      z-index: 1000;
      display: flex;
      flex-direction: column;
      margin-top: 5px;
      overflow: hidden;
    }

    .search-bar { padding: 10px; border-bottom: 1px solid #f1f5f9; background: #f8fafc; }
    .search-bar input { width: 100%; padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.9rem; box-sizing: border-box; outline: none; }
    .search-bar input:focus { border-color: var(--primary, #007782); }

    .tree-container { flex: 1; overflow-y: auto; padding: 10px 0; }
    
    .tree-node { display: flex; flex-direction: column; }
    
    .node-content {
      display: flex;
      align-items: center;
      padding: 6px 15px;
      cursor: pointer;
      transition: background 0.1s;
    }
    .node-content:hover { background: #f1f5f9; }
    .node-content.selected { background: #e0f2f1; font-weight: bold; color: #00796b; border-left: 3px solid #007782; }
    
    .toggle-btn {
      width: 20px;
      height: 20px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      color: #94a3b8;
      font-size: 0.7rem;
      margin-right: 5px;
      border-radius: 4px;
    }
    .toggle-btn:hover { background: #e2e8f0; color: #475569; }

    .node-label { display: flex; align-items: center; gap: 8px; flex: 1; }
    .node-icon { font-size: 1.1rem; }
    .node-name { font-size: 0.95rem; }
    
    .tree-item { padding: 8px 20px; cursor: pointer; }
    .tree-item:hover { background: #f1f5f9; }
  `]
})
export class LocationSelectorComponent implements OnInit, OnChanges {
  @Input() localizacionId: number | null | undefined = null;
  @Input() disabled: boolean = false;
  @Output() localizacionChange = new EventEmitter<number | null | undefined>();

  arbolCompleto: Localizacion[] = [];
  arbolVisible: Localizacion[] = [];
  
  isOpen = false;
  filtro = '';
  expandedNodes = new Set<number>();
  mapaNombres = new Map<number, string>(); // Para búsquedas rápidas de nombres

  constructor(private locService: LocationsService, private eRef: ElementRef) {}

  ngOnInit() {
    this.locService.listarArbol().subscribe(res => {
      this.arbolCompleto = res;
      this.arbolVisible = [...this.arbolCompleto];
      this.construirMapaNombres(this.arbolCompleto);
      this.expandirTodo(this.arbolCompleto); // ✨ MOSTRAR TODO EXPANDIDO POR DEFECTO
      this.expandirRutaHaciaSeleccion(this.localizacionId, this.arbolCompleto);
    });
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['localizacionId'] && this.arbolCompleto.length > 0) {
      this.expandirRutaHaciaSeleccion(this.localizacionId, this.arbolCompleto);
    }
  }

  @HostListener('document:click', ['$event'])
  clickout(event: Event) {
    if (!this.eRef.nativeElement.contains(event.target)) {
      this.isOpen = false;
    }
  }

  toggleDropdown() {
    if (this.disabled) return;
    this.isOpen = !this.isOpen;
    if (this.isOpen && this.filtro) {
      this.filtro = '';
      this.filtrarArbol();
    }
  }

  construirMapaNombres(nodos: Localizacion[], prefijo: string = '') {
    for (const n of nodos) {
      const path = prefijo ? `${prefijo} > ${n.nombre}` : n.nombre;
      this.mapaNombres.set(n.id!, path);
      if (n.hijos) this.construirMapaNombres(n.hijos, path);
    }
  }

  getNombreSeleccionado(): string {
    if (!this.localizacionId) return '--- Seleccionar Ubicación ---';
    return this.mapaNombres.get(this.localizacionId) || `Cargando ubicación...`;
  }

  seleccionar(nodo: Localizacion | null) {
    this.localizacionId = nodo ? nodo.id : null;
    this.localizacionChange.emit(this.localizacionId);
    this.isOpen = false;
  }

  toggleNodo(nodo: Localizacion, event: Event) {
    event.stopPropagation();
    if (this.expandedNodes.has(nodo.id!)) {
      this.expandedNodes.delete(nodo.id!);
    } else {
      this.expandedNodes.add(nodo.id!);
    }
  }

  isExpanded(nodo: Localizacion): boolean {
    return this.expandedNodes.has(nodo.id!);
  }

  expandirRutaHaciaSeleccion(targetId: number | null | undefined, nodos: Localizacion[]): boolean {
    if (!targetId) return false;
    for (const nodo of nodos) {
      if (nodo.id === targetId) return true;
      if (nodo.hijos && nodo.hijos.length > 0) {
        if (this.expandirRutaHaciaSeleccion(targetId, nodo.hijos)) {
          this.expandedNodes.add(nodo.id!);
          return true;
        }
      }
    }
    return false;
  }

  filtrarArbol() {
    if (!this.filtro.trim()) {
      this.arbolVisible = [...this.arbolCompleto];
      this.expandirTodo(this.arbolVisible);
      return;
    }

    const termino = this.filtro.toLowerCase();
    this.arbolVisible = this.filtrarRecursivo(this.arbolCompleto, termino);
    this.expandirTodo(this.arbolVisible);
  }

  filtrarRecursivo(nodos: Localizacion[], termino: string): Localizacion[] {
    let filtrados: Localizacion[] = [];
    for (const nodo of nodos) {
      const coincide = nodo.nombre.toLowerCase().includes(termino);
      let hijosFiltrados: Localizacion[] = [];
      
      if (nodo.hijos) {
        hijosFiltrados = this.filtrarRecursivo(nodo.hijos, termino);
      }

      if (coincide || hijosFiltrados.length > 0) {
        filtrados.push({ ...nodo, hijos: hijosFiltrados });
      }
    }
    return filtrados;
  }

  expandirTodo(nodos: Localizacion[]) {
    for (const nodo of nodos) {
      if (nodo.hijos && nodo.hijos.length > 0) {
        this.expandedNodes.add(nodo.id!);
        this.expandirTodo(nodo.hijos);
      }
    }
  }

  getIcon(tipo: string): string {
    const iconos: any = { 'tienda': '🏪', 'almacen': '📦', 'casa': '🏠', 'estante': '🗄️' };
    return iconos[tipo] || '📍';
  }
}