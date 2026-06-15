import { Component, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuditoriaLog, AuditoriaService } from '../../../core/services/auditoria.service';

@Component({
  selector: 'app-audit-list',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './audit-list.component.html',
  styleUrls: ['./audit-list.component.css']
})
export class AuditListComponent implements OnInit {
  @Input() entidadTipo?: string;
  @Input() entidadId?: number;
  @Input() limit: number = 20;

  logs: AuditoriaLog[] = [];
  cargando = false;

  constructor(private auditoriaService: AuditoriaService) {}

  ngOnInit(): void {
    this.cargarLogs();
  }

  cargarLogs(): void {
    this.cargando = true;
    this.auditoriaService.obtenerLogs({
      entidad_tipo: this.entidadTipo,
      entidad_id: this.entidadId,
      limit: this.limit
    }).subscribe({
      next: (data) => {
        this.logs = data;
        this.cargando = false;
      },
      error: () => this.cargando = false
    });
  }

  formatAccion(accion: string): string {
    const map: Record<string, string> = {
      'CREAR': '🆕 Creación',
      'EDITAR': '✏️ Edición',
      'ELIMINAR': '🗑️ Eliminación',
      'VENDER': '💰 Venta',
      'PAGAR': '💸 Pago a Dueño',
      'TRASPASAR': '🚚 Traspaso',
      'DEVOLUCION_PARCIAL': '🔙 Devolución'
    };
    return map[accion] || accion;
  }

  getDetalles(log: AuditoriaLog): string {
    if (!log.valor_nuevo && !log.valor_anterior) return log.notas || '';
    
    // Si hay notas descriptivas, las priorizamos
    if (log.notas) return log.notas;

    // Si no, intentamos resumir los cambios
    return JSON.stringify(log.valor_nuevo);
  }
}
