import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuditListComponent } from '../../shared/components/audit-list/audit-list.component';

@Component({
  selector: 'app-audit-page',
  standalone: true,
  imports: [CommonModule, AuditListComponent],
  template: `
    <div class="page-container">
      <div class="header">
        <h2 class="title">🔐 Auditoría Global del Sistema</h2>
        <p class="subtitle">Historial completo de movimientos financieros e inventario de todas las tiendas.</p>
      </div>

      <div class="card-section">
        <app-audit-list [limit]="50"></app-audit-list>
      </div>
    </div>
  `,
  styles: [`
    .page-container { padding: 2rem; max-width: 1200px; margin: 0 auto; }
    .header { margin-bottom: 2rem; }
    .title { color: #007782; font-size: 1.8rem; font-weight: 700; margin-bottom: 0.5rem; }
    .subtitle { color: #7f8c8d; font-size: 1rem; }
    .card-section { background: white; border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #e0e6ed; }
  `]
})
export class AuditPageComponent {}
