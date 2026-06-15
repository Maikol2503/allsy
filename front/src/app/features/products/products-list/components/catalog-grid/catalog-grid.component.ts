import { Component, Input } from '@angular/core';
import { CommonModule, TitleCasePipe } from '@angular/common';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-catalog-grid',
  standalone: true,
  imports: [CommonModule, RouterLink, TitleCasePipe],
  templateUrl: './catalog-grid.component.html',
  styleUrl: './catalog-grid.component.css'
})
export class CatalogGridComponent {
  // ✨ Aquí recibe los datos del padre
  @Input() productos: any[] = []; 
}