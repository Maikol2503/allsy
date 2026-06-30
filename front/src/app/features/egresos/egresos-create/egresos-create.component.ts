import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { EgresosService, EgresoCreate } from '../../../core/services/egresos.service';
import { SupplierSelectorComponent, Proveedor } from "../../products/add-product/components/supplier-selector/supplier-selector.component";

@Component({
  selector: 'app-egresos-create',
  standalone: true,
  imports: [CommonModule, FormsModule, SupplierSelectorComponent],
  templateUrl: './egresos-create.component.html',
  styleUrls: ['./egresos-create.component.css']
})
export class EgresosCreateComponent implements OnInit {
  guardando = false;
  isEditMode = false;
  egresoId: number | null = null;
  
  nuevoEgreso: EgresoCreate = { 
    concepto: '', categoria: 'mercancia', monto: 0, 
    metodo_pago: 'cuenta_bancaria',
    fecha: new Date().toISOString().split('T')[0],
    notas: '', proveedor_id: null, proveedor_nombre_nuevo: null
  };

  constructor(
    private egresosService: EgresosService, 
    private router: Router,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    this.route.paramMap.subscribe(params => {
      const id = params.get('id');
      if (id) {
        this.isEditMode = true;
        this.egresoId = Number(id);
        this.cargarEgreso(this.egresoId);
      }
    });
  }

  cargarEgreso(id: number) {
    this.egresosService.obtenerEgresoPorId(id).subscribe({
      next: (data) => {
        this.nuevoEgreso = {
          concepto: data.concepto,
          categoria: data.categoria,
          monto: data.monto,
          metodo_pago: data.metodo_pago,
          fecha: data.fecha ? data.fecha.split('T')[0] : '', 
          notas: data.notas,
          proveedor_id: data.proveedor_id,
          proveedor_nombre_nuevo: null
        };
      },
      error: () => alert('Error al cargar el egreso')
    });
  }

  onSupplierChanged(prov: Proveedor) {
    if (prov.isNew) {
      this.nuevoEgreso.proveedor_id = null;
      this.nuevoEgreso.proveedor_nombre_nuevo = prov.nombre;
    } else {
      this.nuevoEgreso.proveedor_id = prov.id;
      this.nuevoEgreso.proveedor_nombre_nuevo = null;
    }
  }

  guardarEgreso() {
    if (!this.nuevoEgreso.concepto.trim() || this.nuevoEgreso.monto <= 0) {
      alert('Por favor, ingresa un concepto y monto válido.');
      return;
    }

    this.guardando = true;

    const peticion = this.isEditMode 
      ? this.egresosService.editarEgreso(this.egresoId!, this.nuevoEgreso)
      : this.egresosService.registrarEgreso(this.nuevoEgreso);

    peticion.subscribe({
      next: () => {
        alert(this.isEditMode ? '✅ Egreso actualizado' : '✅ Egreso registrado');
        this.router.navigate(['/egresos']); 
      },
      error: (err) => {
        alert('Error: ' + (err.error?.detail || 'Desconocido'));
        this.guardando = false;
      }
    });
  }

  cancelar() {
    this.router.navigate(['/egresos']);
  }
}
