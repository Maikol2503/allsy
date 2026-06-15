import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { GastosService, GastoCreate } from '../../../core/services/gastos.service';
import { SupplierSelectorComponent, Proveedor } from "../../products/add-product/components/supplier-selector/supplier-selector.component";

@Component({
  selector: 'app-gastos-create',
  standalone: true,
  imports: [CommonModule, FormsModule, SupplierSelectorComponent],
  templateUrl: './gastos-create.component.html',
  styleUrls: ['./gastos-create.component.css']
})
export class GastosCreateComponent implements OnInit {
  guardando = false;
  isEditMode = false;
  gastoId: number | null = null;
  
  nuevoGasto: GastoCreate = { 
    concepto: '', categoria: 'mercancia', monto: 0, 
    metodo_pago: 'cuenta_bancaria',
    fecha: new Date().toISOString().split('T')[0],
    notas: '', proveedor_id: null, proveedor_nombre_nuevo: null
  };

  constructor(
    private gastosService: GastosService, 
    private router: Router,
    private route: ActivatedRoute // ✨ Inyectamos la ruta
  ) {}

  ngOnInit(): void {
    // ✨ Detectamos si estamos en modo edición (ej: /gastos/editar/5)
    this.route.paramMap.subscribe(params => {
      const id = params.get('id');
      if (id) {
        this.isEditMode = true;
        this.gastoId = Number(id);
        this.cargarGasto(this.gastoId);
      }
    });
  }

  cargarGasto(id: number) {
    this.gastosService.obtenerGastoPorId(id).subscribe({
      next: (data) => {
        // Rellenamos el formulario con los datos de la BD
        this.nuevoGasto = {
          concepto: data.concepto,
          categoria: data.categoria,
          monto: data.monto,
          metodo_pago: data.metodo_pago,
          // Recortamos la fecha a YYYY-MM-DD para el input type="date"
          fecha: data.fecha ? data.fecha.split('T')[0] : '', 
          notas: data.notas,
          proveedor_id: data.proveedor_id,
          proveedor_nombre_nuevo: null
        };
      },
      error: () => alert('Error al cargar el gasto')
    });
  }

  onSupplierChanged(prov: Proveedor) {
    if (prov.isNew) {
      this.nuevoGasto.proveedor_id = null;
      this.nuevoGasto.proveedor_nombre_nuevo = prov.nombre;
    } else {
      this.nuevoGasto.proveedor_id = prov.id;
      this.nuevoGasto.proveedor_nombre_nuevo = null;
    }
  }

  guardarGasto() {
    if (!this.nuevoGasto.concepto.trim() || this.nuevoGasto.monto <= 0) {
      alert('Por favor, ingresa un concepto y monto válido.');
      return;
    }

    this.guardando = true;

    // ✨ Decidimos a qué función llamar según el modo
    const peticion = this.isEditMode 
      ? this.gastosService.editarGasto(this.gastoId!, this.nuevoGasto)
      : this.gastosService.registrarGasto(this.nuevoGasto);

    peticion.subscribe({
      next: () => {
        alert(this.isEditMode ? '✅ Gasto actualizado' : '✅ Gasto registrado');
        this.router.navigate(['/gastos']); 
      },
      error: (err) => {
        alert('Error: ' + (err.error?.detail || 'Desconocido'));
        this.guardando = false;
      }
    });
  }

  cancelar() {
    this.router.navigate(['/gastos']);
  }
}