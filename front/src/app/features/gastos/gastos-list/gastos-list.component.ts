import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { GastosService } from '../../../core/services/gastos.service';

@Component({
  selector: 'app-gastos-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './gastos-list.component.html',
  styleUrls: ['./gastos-list.component.css']
})
export class GastosListComponent implements OnInit {
  // Datos
  gastos: any[] = [];
  totalItems = 0;
  
  // Estado de la UI
  cargando = true;
  
  // Parámetros de consulta (Paginación y Filtros)
  page = 1;
  limit = 20;
  
  filtros = {
    search: '',
    categoria: '',
    metodo_pago: '',
    fecha_inicio: '',
    fecha_fin: ''
  };

  constructor(
    private gastosService: GastosService, 
    private router: Router
  ) {}

  ngOnInit(): void {
    this.cargarGastos();
  }

  cargarGastos(): void {
    this.cargando = true;
    
    // Construimos el objeto de parámetros que espera el servicio
    const parametros = {
      page: this.page,
      limit: this.limit,
      ...this.filtros
    };

    this.gastosService.getGastos(parametros).subscribe({
      next: (res: any) => {
        console.log(res)
        this.gastos = res.items;
        this.totalItems = res.total;
        this.cargando = false;
      },
      error: (err) => {
        console.error('Error al cargar la lista de gastos:', err);
        this.cargando = false;
        alert('No se pudo conectar con el servidor para obtener los gastos.');
      }
    });
  }

  // --- Lógica de Filtros ---
  aplicarFiltros(): void {
    this.page = 1; // Siempre que filtramos volvemos a la primera página
    this.cargarGastos();
  }

  limpiarFiltros(): void {
    this.filtros = {
      search: '',
      categoria: '',
      metodo_pago: '',
      fecha_inicio: '',
      fecha_fin: ''
    };
    this.aplicarFiltros();
  }

  // --- Navegación ---
  irANuevoGasto(): void {
    this.router.navigate(['/gastos/nuevo']);
  }

  editarGasto(id: number): void {
    this.router.navigate(['/gastos/editar', id]);
  }

  // --- Paginación ---
  cambiarPagina(nuevaPagina: number): void {
    if (nuevaPagina >= 1 && nuevaPagina <= Math.ceil(this.totalItems / this.limit)) {
      this.page = nuevaPagina;
      this.cargarGastos();
    }
  }

  get totalPaginas(): number {
    return Math.ceil(this.totalItems / this.limit);
  }
}