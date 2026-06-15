import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule, Router } from '@angular/router';
import { ClientesService, ClienteData } from '../../../core/services/clientes.service';
// ✨ IMPORTANTE: Ajusta la ruta a donde hayas guardado el panel de consignación
import { ConsignacionPanelComponent } from '../../consignacion/consignacion-panel/consignacion-panel.component';

@Component({
  selector: 'app-client-detail',
  standalone: true,
  imports: [CommonModule, RouterModule, ConsignacionPanelComponent],
  templateUrl: './client-detail.component.html',
  styleUrls: ['./client-detail.component.css']
})
export class ClientDetailComponent implements OnInit {
  cliente: ClienteData | null = null;
  cargando: boolean = true;
  error: string | null = null;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private clientesService: ClientesService
  ) {}

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get('id');
    if (idParam) {
      this.cargarCliente(Number(idParam));
    } else {
      this.error = 'No se proporcionó un ID de cliente válido.';
      this.cargando = false;
    }
  }

  cargarCliente(id: number) {
    this.cargando = true;
    this.clientesService.obtenerClientePorId(id).subscribe({
      next: (data) => {
        this.cliente = data;
        this.cargando = false;
      },
      error: (err) => {
        console.error('Error al cargar cliente:', err);
        this.error = 'No se pudo cargar la información del cliente.';
        this.cargando = false;
      }
    });
  }

  editarCliente() {
    if (this.cliente?.id) {
      // ✨ CORRECCIÓN: La ruta real es /clientes/editar/:id, NO /edit-client/:id
      this.router.navigate(['/clientes/editar', this.cliente.id]); 
    }
  }

  volver() {
    this.router.navigate(['/clientes']);
  }
}