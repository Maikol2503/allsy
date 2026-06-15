import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SuppliersService, TipoProveedor } from '../../../../../core/services/proveedores.service';

export interface Proveedor {
  id?: number;
  nombre: string;
  isNew?: boolean;
}

@Component({
  selector: 'app-supplier-selector',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './supplier-selector.component.html',
  styleUrls: ['./supplier-selector.component.css']
})
export class SupplierSelectorComponent implements OnInit {
  @Input() tipoProveedor: TipoProveedor = 'inventario'; 

  proveedores: Proveedor[] = [];
  listaFiltrada: Proveedor[] = []; // ✨ NUEVA VARIABLE DE ESTADO

  proveedorInput: string = '';
  dropdownOpen: boolean = false;
  proveedorSeleccionado: Proveedor | null = null;
  cargandoProveedores = false;
  private idInicialPendiente: number | null = null;

  @Input() set proveedorInicialId(id: number | null | undefined) {
    if (id) {
      this.idInicialPendiente = id;
      this.vincularProveedor();
    } else {
      this.proveedorSeleccionado = null;
      this.proveedorInput = '';
    }
    this.actualizarFiltro(); // ✨ Actualizamos si cambia desde fuera
  }

  @Output() supplierChanged = new EventEmitter<Proveedor>();

  constructor(private suppliersService: SuppliersService) {}

  ngOnInit(): void {
    this.cargarProveedores();
  }

  cargarProveedores(): void {
    this.cargandoProveedores = true;
    
    this.suppliersService.getProveedores(this.tipoProveedor).subscribe({
      next: (data: any[]) => {
        this.proveedores = data.map(p => ({ 
          id: p.id, 
          nombre: p.nombre_proveedor || p.nombre 
        })).sort((a, b) => a.nombre.localeCompare(b.nombre));
        
        this.cargandoProveedores = false;
        this.vincularProveedor();
        this.actualizarFiltro(); // ✨ Llenamos la lista la primera vez
      },
      error: () => {
        this.cargandoProveedores = false;
        this.actualizarFiltro();
      }
    });
  }

  private vincularProveedor(): void {
    if (this.idInicialPendiente && this.proveedores.length > 0) {
      const provEncontrado = this.proveedores.find(p => p.id === this.idInicialPendiente);
      if (provEncontrado) {
        this.proveedorSeleccionado = provEncontrado;
        this.proveedorInput = provEncontrado.nombre; 
        this.idInicialPendiente = null; 
        this.supplierChanged.emit(provEncontrado);
      }
    }
  }

  // ✨ LA MAGIA OCURRE AQUÍ: Esta función reemplaza al "get"
  actualizarFiltro(): void {
    const input = this.proveedorInput.trim().toLowerCase();
    
    // 1. Filtramos
    let filtrados = this.proveedores.filter(p => p.nombre.toLowerCase().includes(input));
    
    // 2. SALVAVIDAS: Solo tomamos 50 para no reventar el HTML
    filtrados = filtrados.slice(0, 50);

    // 3. Posicionamos la seleccionada arriba
    if (this.proveedorSeleccionado) {
      filtrados = filtrados.filter(p => p.nombre !== this.proveedorSeleccionado!.nombre);
      filtrados.unshift(this.proveedorSeleccionado);
    }
    
    // 4. Si el usuario escribe algo que no existe, ofrece crearlo
    if (input && !this.proveedores.some(p => p.nombre.toLowerCase() === input)) {
      filtrados.unshift({ nombre: this.proveedorInput, isNew: true });
    }
    
    this.listaFiltrada = filtrados;
  }

  selectProveedor(proveedor: Proveedor): void {
    this.dropdownOpen = false;
    this.proveedorSeleccionado = proveedor;
    this.proveedorInput = proveedor.nombre;
    this.supplierChanged.emit(proveedor);
    this.actualizarFiltro(); // Recalculamos al seleccionar
  }

  onBlur(): void {
    setTimeout(() => {
      this.dropdownOpen = false;
      if (this.proveedorSeleccionado) {
        this.proveedorInput = this.proveedorSeleccionado.nombre;
      } else if (!this.proveedorInput.trim()) {
        this.proveedorInput = '';
      }
    }, 200);
  }

  onInputChange(): void { 
    this.dropdownOpen = true; 
    this.proveedorSeleccionado = null;
    this.supplierChanged.emit({ nombre: this.proveedorInput, isNew: true });
    this.actualizarFiltro(); // ✨ SOLO se filtra cuando el usuario teclea
  }

  onFocus(): void { 
    this.dropdownOpen = true; 
    this.actualizarFiltro();
  }
}