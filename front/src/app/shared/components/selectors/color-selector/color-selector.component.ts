import { Component, Input, Output, EventEmitter, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

// ✨ IMPORTA AMBOS DESDE EL CONFIG (Asegúrate de que la ruta sea correcta)
import { COLORES_PALETA, Color } from '../../../../features/products/add-product/product-form.config';

@Component({
  selector: 'app-color-selector',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './color-selector.component.html',
  styleUrl: './color-selector.component.css'
})
export class ColorSelectorComponent implements OnInit {
  listaColores: Color[] = COLORES_PALETA;

  @Input() set initialHex(hex: string | null | undefined) {
    if (!hex || hex === '#FFFFFF') {
      this.coloresSeleccionados = [];
    } else {
      const hexes = hex.split(',');
      this.coloresSeleccionados = hexes.map(h => {
        const hClean = h.trim();
        return this.listaColores.find(c => c.hex.toLowerCase() === hClean.toLowerCase()) || { hex: hClean, nombre: 'Personalizado' };
      });
    }
  }

  @Output() colorChanged = new EventEmitter<Color>();

  coloresSeleccionados: Color[] = [];
  dropdownOpen = false;

  ngOnInit() { }

  selectColor(color: Color) {
    const idx = this.coloresSeleccionados.findIndex(c => c.hex === color.hex);
    if (idx >= 0) {
      this.coloresSeleccionados.splice(idx, 1);
    } else {
      if (this.coloresSeleccionados.length >= 3) {
        alert("Puedes seleccionar un máximo de 3 colores.");
        return;
      }
      this.coloresSeleccionados.push(color);
    }

    const combinedName = this.coloresSeleccionados.map(c => c.nombre).join(' / ');
    const combinedHex = this.coloresSeleccionados.map(c => c.hex).join(',');
    
    // Si quitó todos, devolvemos blanco
    if (this.coloresSeleccionados.length === 0) {
      this.colorChanged.emit({ hex: '#FFFFFF', nombre: '' });
    } else {
      this.colorChanged.emit({ hex: combinedHex, nombre: combinedName });
    }
  }

  isColorSelected(hex: string): boolean {
    return this.coloresSeleccionados.some(c => c.hex === hex);
  }

  getCombinedBackground(): string {
    if (this.coloresSeleccionados.length === 0) return '#f2f2f2';
    const hexes = this.coloresSeleccionados.map(c => c.hex);
    if (hexes.length === 1) return hexes[0];
    if (hexes.length === 2) return `linear-gradient(90deg, ${hexes[0]} 50%, ${hexes[1]} 50%)`;
    if (hexes.length === 3) return `linear-gradient(90deg, ${hexes[0]} 33.3%, ${hexes[1]} 33.3%, ${hexes[1]} 66.6%, ${hexes[2]} 66.6%)`;
    return '#f2f2f2';
  }

  getCombinedLabel(): string {
    if (this.coloresSeleccionados.length === 0) return 'Seleccionar Color (Max 3)';
    return this.coloresSeleccionados.map(c => c.nombre).join(' / ');
  }

  toggleDropdown() { this.dropdownOpen = !this.dropdownOpen; }
  
  // Modificamos el blur para que no cierre instantáneamente si se quiere hacer click múltiple
  closeDropdown() { 
    // Comentamos el timeout automático para permitir clics múltiples
    // setTimeout(() => { this.dropdownOpen = false; }, 200); 
  }
}