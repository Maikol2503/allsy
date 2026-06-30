import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { EgresosService } from '../../../core/services/egresos.service';

@Component({
  selector: 'app-egresos-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './egresos-list.component.html',
  styleUrls: ['./egresos-list.component.css']
})
export class EgresosListComponent implements OnInit {
  // Datos
  egresos: any[] = [];
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
    private egresosService: EgresosService, 
    private router: Router
  ) {}

  ngOnInit(): void {
    this.cargarEgresos();
  }

  cargarEgresos(): void {
    this.cargando = true;
    
    // Construimos el objeto de parámetros que espera el servicio
    const parametros = {
      page: this.page,
      limit: this.limit,
      ...this.filtros
    };

    this.egresosService.getEgresos(parametros).subscribe({
      next: (res: any) => {
        console.log(res)
        this.egresos = res.items;
        this.totalItems = res.total;
        this.cargando = false;
      },
      error: (err) => {
        console.error('Error al cargar la lista de egresos:', err);
        this.cargando = false;
        alert('No se pudo conectar con el servidor para obtener los egresos.');
      }
    });
  }

  // --- Lógica de Filtros ---
  aplicarFiltros(): void {
    this.page = 1; // Siempre que filtramos volvemos a la primera página
    this.cargarEgresos();
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
  irANuevoEgreso(): void {
    this.router.navigate(['/egresos/nuevo']);
  }

  editarEgreso(id: number): void {
    this.router.navigate(['/egresos/editar', id]);
  }

  // --- Paginación ---
  cambiarPagina(nuevaPagina: number): void {
    if (nuevaPagina >= 1 && nuevaPagina <= Math.ceil(this.totalItems / this.limit)) {
      this.page = nuevaPagina;
      this.cargarEgresos();
    }
  }

  get totalPaginas(): number {
    return Math.ceil(this.totalItems / this.limit);
  }
}
