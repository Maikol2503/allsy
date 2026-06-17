import { Component, OnInit } from '@angular/core';
import { CommonModule, TitleCasePipe } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { VentasService } from '../../../core/services/ventas.service';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-order-detail',
  standalone: true,
  imports: [CommonModule, RouterLink, TitleCasePipe, FormsModule],
  templateUrl: './order-detail.component.html',
  styleUrls: ['./order-detail.component.css']
})
export class OrderDetailComponent implements OnInit {

  ventaId: number | null = null;
  venta: any = null;
  cargando = true;

  // Paginación interna de ítems
  pageInterna = 1;
  limitInterno = 15;
  
  // Búsqueda interna
  filtroSku = '';

  constructor(
    private route: ActivatedRoute,
    private ventasService: VentasService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.ventaId = Number(this.route.snapshot.paramMap.get('id'));
    if (this.ventaId) {
      this.cargarVenta();
    }
  }

  cargarVenta() {
    this.cargando = true;
    this.ventasService.obtenerVenta(this.ventaId!).subscribe({
      next: (res: any) => {
        this.venta = res;
        this.cargando = false;
      },
      error: (err: any) => {
        console.error('Error al cargar la venta', err);
        alert('No se pudo cargar el detalle del pedido.');
        this.cargando = false;
        this.volver();
      }
    });
  }

  get itemsFiltrados() {
    if (!this.venta || !this.venta.detalles) return [];
    
    let items = this.venta.detalles;
    
    if (this.filtroSku.trim()) {
      const term = this.filtroSku.trim().toLowerCase();
      items = items.filter((i: any) => 
        (i.stock_unit_id && i.stock_unit_id.toString().includes(term)) ||
        (i.nombre_producto && i.nombre_producto.toLowerCase().includes(term))
      );
    }
    return items;
  }

  get itemsPaginados() {
    const filtrados = this.itemsFiltrados;
    const startIndex = (this.pageInterna - 1) * this.limitInterno;
    return filtrados.slice(startIndex, startIndex + this.limitInterno);
  }

  get totalPages() {
    return Math.ceil(this.itemsFiltrados.length / this.limitInterno) || 1;
  }

  cambiarPaginaInterna(dif: number) {
    const nuevaPagina = this.pageInterna + dif;
    if (nuevaPagina >= 1 && nuevaPagina <= this.totalPages) {
      this.pageInterna = nuevaPagina;
    }
  }

  volver() {
    // Vuelve a la página anterior en el historial
    window.history.back();
  }

  getEstatusInterpretado(pedido: any): string {
    const env = pedido.estado_envio;
    const pag = pedido.estado_pago;
    const ev = pedido.estado_venta;

    if (ev === 'completada' || ev === 'completado') return '🏁 Finalizado / Venta Cerrada';
    if (ev === 'cancelada') return '❌ Anulado (Venta Cancelada)';
    if (ev === 'devuelta_totalmente') return '🔄 Devuelto Totalmente';
    if (ev === 'devuelta_parcialmente') return '⚠️ Devuelta Parcialmente';

    if (env === 'extraviado_envio') return '📦 EXTRAVIADO (Envío al cliente)';
    if (env === 'extraviado_devolucion') return '⚠️ EXTRAVIADO (Durante devolución)';
    if (env === 'en_devolucion') return '↩️ Devolución en curso';
    if (env === 'devuelto') return '✅ Devuelto (En Almacén)';

    if (pag === 'reembolsado' || env === 'cancelado') {
      if (env === 'cancelado') return '❌ Anulado (En camino de vuelta)';
      return '🚫 Cancelado. (Venta anulada)';
    }

    if (env === 'entregado') return '📦 Entregado al comprador';
    if (env === 'enviado') return '🚚 Enviado (En tránsito)';
    if (env === 'listo_envio') return '📤 Listo para enviar';
    if (env === 'empaquetado') return '📦 Empaquetado (En almacén)';
    if (env === 'pendiente_envio' || !env) return '🕒 Pendiente de enviar';

    if (pag === 'reembolso_parcial') return '⚠️ Devolución parcial procesada';

    return env || 'Procesando';
  }
}
