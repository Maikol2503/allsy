import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ProductsService } from '../../../../../core/services/products.service';

export interface Marca {
  id?: number;
  nombre: string;
  isNew?: boolean;
}

@Component({
  selector: 'app-brand-selector',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './brand-selector.component.html',
  styleUrl: './brand-selector.component.css'
})
export class BrandSelectorComponent implements OnInit {
  @Input() initialValue: string = ''; 
  @Output() brandChanged = new EventEmitter<Marca>();

  marcaInput: string = '';
  dropdownOpen: boolean = false;
  marcaSeleccionada: Marca | null = null;
  
  marcas: any[] = [];
  listaFiltrada: Marca[] = []; // ✨ NUEVA VARIABLE DE ESTADO

  constructor(private productsService: ProductsService) {}

  ngOnInit() {
      this.cargarMarcas();
  }

  cargarMarcas(): void {
    this.productsService.cargarMarcas().subscribe({
      next: (data: any[]) => {
        this.marcas = data.sort((a,b) => a.nombre.localeCompare(b.nombre));
        this.actualizarFiltro(); // Llenamos la lista la primera vez
      }
    });
  }

  @Input() set marcaInicial(marca: any | null) {
    if (marca) {
      this.marcaSeleccionada = marca;
      this.marcaInput = marca.nombre;
    } else {
      this.marcaSeleccionada = null;
      this.marcaInput = '';
    }
    this.actualizarFiltro(); // Actualizamos si cambia desde fuera
  }

  // ✨ LA MAGIA OCURRE AQUÍ: Esta función reemplaza al "get"
  actualizarFiltro(): void {
    const input = this.marcaInput.trim().toLowerCase();
    
    // 1. Filtramos
    let filtradas = this.marcas.filter(m => m.nombre.toLowerCase().includes(input));

    // 2. SALVAVIDAS: Solo tomamos 50 para no reventar el HTML
    filtradas = filtradas.slice(0, 50);

    // 3. Posicionamos la seleccionada arriba
    if (this.marcaSeleccionada) {
      filtradas = filtradas.filter(m => m.nombre !== this.marcaSeleccionada!.nombre);
      filtradas.unshift(this.marcaSeleccionada);
    }

    // 4. Opción para nueva marca
    if (input && !this.marcas.some(m => m.nombre.toLowerCase() === input)) {
      filtradas.unshift({ nombre: this.marcaInput, isNew: true });
    }
    
    this.listaFiltrada = filtradas;
  }

  selectMarca(marca: Marca): void {
    this.marcaSeleccionada = marca;
    this.marcaInput = marca.nombre;
    this.dropdownOpen = false;
    this.brandChanged.emit(marca);
    this.actualizarFiltro(); // Recalculamos al seleccionar
  }

  onInputChange(): void {
    this.dropdownOpen = true;
    this.actualizarFiltro(); // ✨ SOLO se filtra cuando el usuario teclea
  }

  onBlur(): void {
    setTimeout(() => {
      this.dropdownOpen = false;
      if (this.marcaSeleccionada) {
        this.marcaInput = this.marcaSeleccionada.nombre;
      } else if (this.marcaInput.trim()) {
        const nueva = { nombre: this.marcaInput, isNew: true };
        this.selectMarca(nueva);
      }
    }, 200);
  }

  onFocus(): void {
    this.dropdownOpen = true;
    this.actualizarFiltro();
  }
}