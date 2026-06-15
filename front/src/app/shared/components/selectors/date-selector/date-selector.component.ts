import { Component, Input, Output, EventEmitter, ElementRef, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

export interface DateRange {
  inicio: string | null;
  fin: string | null;
}

@Component({
  selector: 'app-date-selector',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './date-selector.component.html',
  styleUrl: './date-selector.component.css'
})
export class DateSelectorComponent {
  @Input() fechaInicio: string | null = null;
  @Input() fechaFin: string | null = null;
  @Output() fechasCambiadas = new EventEmitter<DateRange>();

  isOpen: boolean = false;
  
  // Variables temporales para el formulario antes de aplicar
  tempInicio: string | null = null;
  tempFin: string | null = null;

  constructor(private eRef: ElementRef) {}

  toggleDropdown() {
    if (!this.isOpen) {
      // Al abrir, copiamos los valores actuales a los temporales
      this.tempInicio = this.fechaInicio;
      this.tempFin = this.fechaFin;
    }
    this.isOpen = !this.isOpen;
  }

  @HostListener('document:click', ['$event'])
  clickout(event: Event) {
    if (!this.eRef.nativeElement.contains(event.target)) {
      this.isOpen = false;
    }
  }

  aplicarFechas() {
    this.fechasCambiadas.emit({
      inicio: this.tempInicio || null,
      fin: this.tempFin || null
    });
    this.isOpen = false;
  }

  limpiarFechas() {
    this.tempInicio = null;
    this.tempFin = null;
    this.aplicarFechas();
  }

  get tieneFiltroActivo(): boolean {
    return !!this.fechaInicio || !!this.fechaFin;
  }
}