import { Component, Input, Output, EventEmitter, OnInit, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { ClientesService } from '../../../../../core/services/clientes.service'; 

@Component({
  selector: 'app-client-selector',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './client-selector.component.html',
  styleUrls: ['./client-selector.component.css']
})
export class ClientSelectorComponent implements OnInit, OnChanges {
  @Input() clienteInicialId: number | null | undefined = null;
  @Input() defaultLabel: string = 'Allsy (Propio)';
  @Output() clientSelected = new EventEmitter<number | null | undefined>();

  searchTerm: string = '';
  clientes: any[] = [];
  isOpen: boolean = false;
  cargando: boolean = false;
  clienteSeleccionadoId: number | null = null;
  searchType: string = 'todos'; // ✨ NUEVO

  private searchSubject = new Subject<string>();

  constructor(private clientesService: ClientesService) {}

  ngOnInit() {
    this.cargarClienteInicial();

    this.searchSubject.pipe(
      debounceTime(300),
      distinctUntilChanged()
    ).subscribe(term => {
      this.buscarClientes(term);
    });
  }

  // ✨ ESTO ES CLAVE PARA EL MODO EDICIÓN
  ngOnChanges(changes: SimpleChanges) {
    if (changes['clienteInicialId'] && !changes['clienteInicialId'].firstChange) {
      this.cargarClienteInicial();
    }
  }

  cargarClienteInicial() {
    if (this.clienteInicialId) {
      this.clienteSeleccionadoId = this.clienteInicialId;
      this.clientesService.obtenerClientePorId(this.clienteInicialId).subscribe({
        next: (c: any) => {
          this.searchTerm = `👤 ${c.nombre} ${c.apellidos || ''}`;
        },
        error: () => {
          this.searchTerm = `👤 Cliente #${this.clienteInicialId}`;
        }
      });
    } else {
      this.searchTerm = this.defaultLabel;
      this.clienteSeleccionadoId = null;
    }
  }

  onSearch(term: string) {
    this.isOpen = true;
    this.clienteSeleccionadoId = null; 
    this.searchSubject.next(term);
  }

  buscarClientes(term: string) {
    // ✨ EL ESCUDO ANTI-ERROR 500:
    const busquedaLimpia = term.includes(this.defaultLabel) ? '' : term;

    this.cargando = true;
    this.clientesService.obtenerClientes({ 
      page: 1, 
      limit: 10, 
      search: busquedaLimpia,
      search_type: this.searchType // ✨ PASAMOS EL TIPO DE BÚSQUEDA
    }).subscribe({
      next: (res: any) => {
        this.clientes = res.items || [];
        this.cargando = false;
      },
      error: () => this.cargando = false
    });
  }

  // ✨ SOLUCIÓN ROBUSTA: Guardamos el ID antes que nada
  seleccionar(cliente: any | null) {
    if (cliente === null) {
      this.clienteSeleccionadoId = null;
      this.searchTerm = this.defaultLabel;
      this.clientSelected.emit(null);
    } else {
      this.clienteSeleccionadoId = cliente.id;
      this.searchTerm = `👤 ${cliente.nombre} ${cliente.apellidos || ''}`;
      this.clientSelected.emit(cliente.id);
    }
    this.isOpen = false;
  }

  limpiarSeleccion() {
    this.seleccionar(null);
    this.isOpen = true; 
    this.searchTerm = '';
    this.buscarClientes('');
  }

  // ✨ SOLUCIÓN ROBUSTA: Damos más tiempo y comprobamos bien antes de restaurar
  onBlur() {
    setTimeout(() => {
      this.isOpen = false;
      
      if (!this.clienteSeleccionadoId) {
        if (this.searchTerm.trim() === '') {
          this.cargarClienteInicial();
        } else {
          this.cargarClienteInicial();
        }
      }
    }, 250);
  }

  // ✨ NUEVO FOCUS LIMPIO
  onInputFocus() {
    this.isOpen = true;
    
    // Si no hay ID seleccionado o el texto es Allsy, limpiamos para escribir
    if (!this.clienteSeleccionadoId || this.searchTerm.includes(this.defaultLabel)) {
      this.searchTerm = '';
    }
    
    this.buscarClientes(this.searchTerm);
  }
}