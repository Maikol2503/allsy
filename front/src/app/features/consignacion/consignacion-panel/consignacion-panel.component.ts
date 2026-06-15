import { Component, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ConsignacionService, EstadisticasConsignacion, PagoCreate, PagoRead } from '../../../core/services/consignacion.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-consignacion-panel',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './consignacion-panel.component.html',
  styleUrls: ['./consignacion-panel.component.css']
})
export class ConsignacionPanelComponent implements OnInit {
  @Input() clienteId!: number; 

  stats: EstadisticasConsignacion | null = null;
  pagos: PagoRead[] = [];
  cargando = false;
  isSubmitting = false;

  prendas: any[] = [];
  prendasCargando = false;
  prendasPage = 1;
  prendasLimit = 10;
  prendasTotal = 0;
  filtroEstado = '';

  // ✨ Modo Edición
  pagoEditandoId: number | null = null;

  // ✨ Trazabilidad de prendas
  prendasPendientes: any[] = [];
  idsSeleccionados: Set<number> = new Set();
  cargandoPendientes = false;

  nuevoPago: PagoCreate = {
    monto: 0,
    metodo_pago: 'Transferencia',
    referencia: '',
    notas: '',
    stock_unit_ids: []
  };

  metodosPago = ['Transferencia', 'Bizum', 'Efectivo', 'PayPal'];

  constructor(private consignacionService: ConsignacionService, private router: Router) {}

  ngOnInit() {
    if (this.clienteId) {
      this.cargarDatos();
      this.cargarPrendas();
      this.cargarPendientesPago();
    }
  }

  cargarDatos() {
    this.cargando = true;
    
    this.consignacionService.getStats(this.clienteId).subscribe(res => {
      this.stats = res;
      // Ya no auto-rellenamos el monto directamente desde el saldo pendiente global,
      // sino que dejaremos que la selección de prendas lo haga.
    });

    this.consignacionService.getPagos(this.clienteId).subscribe(res => {
      this.pagos = res;
      this.cargando = false;
    });
  }

  cargarPendientesPago() {
    this.cargandoPendientes = true;
    this.consignacionService.getPrendasPendientesPago(this.clienteId).subscribe(res => {
      this.prendasPendientes = res;
      this.idsSeleccionados = new Set(this.prendasPendientes.map(p => p.stock_id));
      this.recalcularMontoDesdeSeleccion();
      this.cargandoPendientes = false;
    });
  }

  recalcularMontoDesdeSeleccion() {
    if (this.pagoEditandoId) return; // No recalcular si estamos editando un monto ya fijo

    let total = 0;
    this.prendasPendientes.forEach(p => {
      if (this.idsSeleccionados.has(p.stock_id)) {
        total += p.pago_cliente;
      }
    });
    this.nuevoPago.monto = Number(total.toFixed(2));
  }

  toggleSeleccion(stockId: number) {
    if (this.idsSeleccionados.has(stockId)) {
      this.idsSeleccionados.delete(stockId);
    } else {
      this.idsSeleccionados.add(stockId);
    }
    this.recalcularMontoDesdeSeleccion();
  }

  toggleTodas(event: any) {
    const check = event.target.checked;
    if (check) {
      this.idsSeleccionados = new Set(this.prendasPendientes.map(p => p.stock_id));
    } else {
      this.idsSeleccionados.clear();
    }
    this.recalcularMontoDesdeSeleccion();
  }


  cargarPrendas() {
    this.prendasCargando = true;
    this.consignacionService.getPrendasCliente(this.clienteId, this.prendasPage, this.prendasLimit, this.filtroEstado)
      .subscribe(res => {
        this.prendas = res.items;
        this.prendasTotal = res.total;
        this.prendasCargando = false;
      });
  }


  aplicarFiltro(estado: string) {
    this.filtroEstado = estado;
    this.prendasPage = 1; // Volver a la página 1 al filtrar
    this.cargarPrendas();
  }

  cambiarPagina(direccion: number) {
    const nuevaPagina = this.prendasPage + direccion;
    const paginasTotales = Math.ceil(this.prendasTotal / this.prendasLimit);
    
    if (nuevaPagina >= 1 && nuevaPagina <= paginasTotales) {
      this.prendasPage = nuevaPagina;
      this.cargarPrendas();
    }
  }

  verProducto(productoId: number) {
    // ✨ CORRECCIÓN: La ruta correcta para ver producto es /detail-product/:id
    this.router.navigate(['/detail-product', productoId]);
  }

  // ✨ Botón para iniciar la edición de un pago
  iniciarEdicion(pago: PagoRead) {
    this.pagoEditandoId = pago.id;
    this.nuevoPago = {
      monto: pago.monto,
      metodo_pago: pago.metodo_pago,
      referencia: pago.referencia || '',
      notas: pago.notas || ''
    };
    // Hace scroll automático hacia arriba para ver el formulario
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // ✨ Cancelar edición y limpiar formulario
  cancelarEdicion() {
    this.pagoEditandoId = null;
    this.nuevoPago = {
      monto: this.stats ? this.stats.saldo_pendiente : 0,
      metodo_pago: 'Transferencia',
      referencia: '',
      notas: ''
    };
  }

  procesarPago() {
    if (this.nuevoPago.monto <= 0) {
      alert('⚠️ El monto debe ser mayor a 0');
      return;
    }

    this.isSubmitting = true;
    
    // ✨ Incluimos la trazabilidad en el envío
    const payload = { 
      ...this.nuevoPago, 
      stock_unit_ids: Array.from(this.idsSeleccionados) 
    };

    // Si estamos en modo edición:
    if (this.pagoEditandoId) {
      this.consignacionService.actualizarPago(this.pagoEditandoId, payload).subscribe({
        next: () => {
          alert('✅ Pago actualizado con éxito');
          this.finalizarOperacionPago();
        },
        error: (err) => {
          this.isSubmitting = false;
          alert('❌ Error al actualizar: ' + (err.error?.detail || 'Inténtalo de nuevo'));
        }
      });
    } 
    // Si es un pago nuevo:
    else {
      this.consignacionService.registrarPago(this.clienteId, payload).subscribe({
        next: () => {
          alert('✅ Pago registrado con éxito');
          this.finalizarOperacionPago();
        },
        error: (err) => {
          this.isSubmitting = false;
          alert('❌ Error al registrar el pago: ' + (err.error?.detail || 'Inténtalo de nuevo'));
        }
      });
    }
  }

  private finalizarOperacionPago() {
    this.isSubmitting = false;
    this.cancelarEdicion();
    this.cargarDatos(); 
    this.cargarPendientesPago(); // ✨ Fundamental para refrescar la lista de trazabilidad
  }

  // ✨ Función para anular
  anularPago(pagoId: number) {
    const motivo = prompt("⚠️ Vas a ANULAR este pago. \n\n- El monto se descontará de los pagos realizados.\n- El saldo volverá a estar pendiente para el dueño.\n- Las prendas asociadas se liberarán.\n\nEscribe el motivo de la anulación:");
    
    if (motivo === null) return; // Canceló
    if (motivo.trim() === '') {
      alert("Debes escribir un motivo para anular el pago.");
      return;
    }

    this.isSubmitting = true;
    this.consignacionService.anularPago(pagoId, motivo).subscribe({
      next: () => {
        alert('🚫 Pago anulado');
        this.isSubmitting = false;
        if (this.pagoEditandoId === pagoId) this.cancelarEdicion();
        this.cargarDatos(); 
        this.cargarPendientesPago();
      },
      error: (err) => {
        this.isSubmitting = false;
        alert('❌ Error al anular: ' + (err.error?.detail || 'Inténtalo de nuevo'));
      }
    });
  }
}