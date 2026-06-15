import { Component, Input, Output, EventEmitter, ElementRef, HostListener, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SuppliersService } from '../../../../core/services/proveedores.service';


@Component({
  selector: 'app-provider-selector',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './provider-selector.component.html',
  styleUrl: './provider-selector.component.css'
})
export class ProviderSelectorComponent implements OnInit {
  
  // ✨ Ya no es un @Input, es una variable interna del componente
  proveedores: any[] = []; 
  
  @Input() seleccionados: number[] = []; // Sigue recibiendo los marcados desde el padre
  @Output() seleccionCambiada = new EventEmitter<number[]>();

  isOpen: boolean = false;

  constructor(
    private eRef: ElementRef,
    private suppliersService: SuppliersService // ✨ Inyectamos tu servicio
  ) {}

  ngOnInit(): void {
    this.cargarProveedores();
  }

  cargarProveedores() {
    this.suppliersService.getProveedores().subscribe({
      next: (data) => {
        this.proveedores = data;
        console.log(this.proveedores)
      },
      error: (err) => {
        console.error('Error al cargar la lista de proveedores:', err);
      }
    });
  }

  toggleDropdown() {
    this.isOpen = !this.isOpen;
  }

  // Cierra el menú si el usuario hace clic fuera de él
  @HostListener('document:click', ['$event'])
  clickout(event: Event) {
    if (!this.eRef.nativeElement.contains(event.target)) {
      this.isOpen = false;
    }
  }

  toggleProveedor(id: number) {
    const nuevaSeleccion = [...this.seleccionados];
    const index = nuevaSeleccion.indexOf(id);
    
    if (index === -1) {
      nuevaSeleccion.push(id); // Seleccionar
    } else {
      nuevaSeleccion.splice(index, 1); // Deseleccionar
    }
    
    this.seleccionCambiada.emit(nuevaSeleccion);
  }
}