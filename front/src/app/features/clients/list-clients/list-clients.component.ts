import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ClientesService, ClienteData } from '../../../core/services/clientes.service';
import { Router } from '@angular/router';
// import { DateSelectorComponent } from '../../../shared/components/date-selector/date-selector.component';

@Component({
  selector: 'app-list-clients',
  imports: [CommonModule, FormsModule /*, DateSelectorComponent*/],
  templateUrl: './list-clients.component.html',
  styleUrl: './list-clients.component.css'
})
export class ListClientsComponent implements OnInit {
  clientes: ClienteData[] = [];
  cargando: boolean = false;

  // Paginación
  page: number = 1;
  limit: number = 10;
  totalItems: number = 0;

  // Filtros
  searchCliente: string = '';
  filtroPais: string = '';
  fechaInicio: string = '';
  fechaFin: string = '';

  // Lista de países para el filtro
  listaPaises = [
    { nombre: 'España', bandera: '🇪🇸' },
    { nombre: 'Francia', bandera: '🇫🇷' },
    { nombre: 'Italia', bandera: '🇮🇹' },
    { nombre: 'Portugal', bandera: '🇵🇹' },
    { nombre: 'Bélgica', bandera: '🇧🇪' },
    { nombre: 'Alemania', bandera: '🇩🇪' },
    { nombre: 'Países Bajos', bandera: '🇳🇱' },
    { nombre: 'Reino Unido', bandera: '🇬🇧' },
    { nombre: 'Luxemburgo', bandera: '🇱🇺' },
    { nombre: 'Otros', bandera: '🌍' }
  ];

  constructor(private clientesService: ClientesService, private router: Router) {}

  ngOnInit(): void {
    this.cargarClientes();
  }

  cargarClientes() {
    this.cargando = true;
    const filtros = {
      page: this.page,
      limit: this.limit,
      search: this.searchCliente,
      pais: this.filtroPais,
      fecha_inicio: this.fechaInicio,
      fecha_fin: this.fechaFin
    };

    this.clientesService.obtenerClientes(filtros).subscribe({
      next: (res) => {
        this.clientes = res.items;
        this.totalItems = res.total;
        this.cargando = false;
      },
      error: (err) => {
        console.error('Error cargando clientes', err);
        this.cargando = false;
      }
    });
  }

  buscar() {
    this.page = 1; // Volver a la primera página al buscar
    this.cargarClientes();
  }

  limpiarFiltros() {
    this.searchCliente = '';
    this.filtroPais = '';
    this.fechaInicio = '';
    this.fechaFin = '';
    this.buscar();
  }

  onFechasCambiadas(fechas: { inicio: string, fin: string }) {
    this.fechaInicio = fechas.inicio;
    this.fechaFin = fechas.fin;
    this.buscar();
  }

  cambiarPagina(nuevaPagina: number) {
    if (nuevaPagina >= 1 && nuevaPagina <= this.totalPages) {
      this.page = nuevaPagina;
      this.cargarClientes();
    }
  }

  get totalPages(): number {
    return Math.ceil(this.totalItems / this.limit);
  }

  irADetalle(id: number) {
  this.router.navigate(['/clientes/detalle', id]);
}

  irAEditar(id?: number) { 
    if (!id) {
      console.error("Error: Intentando editar un cliente sin ID");
      return;
    }
    
    // 🚀 Redirección real a la pantalla de edición
    this.router.navigate(['/clientes/editar', id]);
  }
}