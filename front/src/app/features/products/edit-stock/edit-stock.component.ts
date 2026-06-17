import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ProductsService } from '../../../core/services/products.service';
import { SupplierSelectorComponent, Proveedor } from "../add-product/components/supplier-selector/supplier-selector.component";
import { LocationSelectorComponent } from '../../../shared/components/selectors/location-selector/location-selector.component';
import { ClientSelectorComponent } from '../add-product/components/client-selector/client-selector.component';
import { map, switchMap } from 'rxjs/operators';
import { Observable } from 'rxjs';
import { formatLabel, getPlaceholder } from '../add-product/product-utils';

export interface UnidadLote {
  id: number;
  id_original?: number;
  sku: string;
  estado_gestion: string;
  canales?: any;
  editandoId?: boolean;
  fecha_compra?: string; // ✨ NUEVO
  publicar_web?: boolean; // ✨ NUEVO
  publicar_vinted?: boolean; // ✨ NUEVO
  publicar_wallapop?: boolean; // ✨ NUEVO
  venta_id?: number; // ✨ AÑADIDO PARA VINCULAR A VENTA
}

@Component({
  selector: 'app-edit-stock',
  standalone: true,
  imports: [CommonModule, FormsModule, SupplierSelectorComponent, LocationSelectorComponent, ClientSelectorComponent, RouterLink],
  templateUrl: './edit-stock.component.html',
  styleUrls: ['./edit-stock.component.css']
})
export class EditStockComponent implements OnInit {
  stockId: number | null = null;
  cargandoDatos = true;
  isSubmitting = false;
  tipoProducto: string = 'ropa_superior'; 
  mostrarUnidades = true; // ✨ Lo ponemos en true por defecto para ver las prendas
  unidadesLote: UnidadLote[] = [];
  unidades_a_agregar: number = 0; 
  fecha_a_agregar: string = new Date().toISOString().split('T')[0]; // ✨ DEFAULT TODAY
  isAddingUnits: boolean = false;
  
  stockData: any = {
    precio_compra: 0,
    precio_venta: 0,
    descuento: 0,
    localizacion_id: null,
    proveedor_id: null,
    publicar_web_masivo: false, // Control visual para marcar todas las unidades
    atributos: [],
    donar_ganancias: false,
    propietario_id: null
  };

  contexto: any = {};
  paginaInterna: number = 1; 
  Math = Math; 

  constructor(
    private route: ActivatedRoute,
    private productsService: ProductsService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.stockId = Number(this.route.snapshot.paramMap.get('id'));
    if (this.stockId) {
      this.cargarStock(this.stockId);
    }
  }

  hidratarAtributosDinamicos(moldeBackend: any[], extrasGuardados: any): any[] {
    const atributosAExcluir = ['talla', 'color', 'identidad_variante', 'numero', 'talla_anillo', 'capacidad_ml', 'talla_guantes'];
    
    // 1. ✨ COHERENCIA: Forzamos campos que siempre queremos ver (como en el formulario maestro)
    const camposSiempreVisibles = ['material', 'peso_kg'];
    let molde = [...moldeBackend];
    
    camposSiempreVisibles.forEach(campo => {
      if (!molde.some(a => a.nombre.toLowerCase() === campo)) {
        molde.push({ 
          nombre: campo, 
          tipo: campo === 'peso_kg' ? 'number' : 'text', 
          opciones: [], 
          valor: null 
        });
      }
    });

    // 2. Procesamos el molde y rescatamos valores de la base de datos
    let finalAttrs = molde
      .filter(attr => !atributosAExcluir.includes(attr.nombre.toLowerCase()))
      .map(attr => {
        const keyBackend = attr.nombre.toLowerCase();
        const attrLimpio = { ...attr, valor: attr.valor || null };
        if (extrasGuardados) {
          const claveExacta = Object.keys(extrasGuardados).find(k => k.toLowerCase() === keyBackend);
          if (claveExacta !== undefined) {
            let valorBackend = extrasGuardados[claveExacta];
            
            // ✨ CORRECCIÓN: Ajustamos el valor para que coincida exactamente (mayúsculas/minúsculas) con la opción del select
            if (attr.tipo === 'select' && attr.opciones && attr.opciones.length > 0 && valorBackend) {
               const valorStr = String(valorBackend).toLowerCase();
               const optionMatch = attr.opciones.find((o: string) => String(o).toLowerCase() === valorStr);
               if (optionMatch) {
                 valorBackend = optionMatch;
               }
            }
            
            attrLimpio.valor = valorBackend;
          }
        }
        return attrLimpio;
      });

    // 3. ✨ BLINDAJE EXTRA: Atributos que existen en BD pero no están en el molde (ej: campos antiguos)
    if (extrasGuardados) {
      Object.keys(extrasGuardados).forEach(key => {
        const keyLower = key.toLowerCase();
        const yaEsta = finalAttrs.some(fa => fa.nombre.toLowerCase() === keyLower);
        if (!yaEsta && !atributosAExcluir.includes(keyLower)) {
          finalAttrs.push({
            nombre: key,
            valor: extrasGuardados[key],
            tipo: 'text',
            opciones: []
          });
        }
      });
    }

    return finalAttrs;
  }

  formatLabel(n: string): string { return formatLabel(n); }
  getPlaceholder(n: string): string { return getPlaceholder(n); }

  cargarStock(id: number) {
    // Asumimos que obtenerLoteStock ahora apunta a tu endpoint de detalle de StockConfig
    this.productsService.obtenerLoteStock(id).subscribe({
      next: (data: any) => {
        console.log("🚨 DATOS DEL STOCK CONFIG RECIBIDOS:", data);
        
        this.contexto = {
          producto_id: data.producto_id || data.variante?.producto_id,
          variante_id: data.variante_id,
          producto_nombre: data.producto_nombre,
          identidad_variante: data.identidad_variante,
          sku: data.stock_config_id,
          imagen_cover: data.imagen_cover,
          hex_identidad: data.hex_identidad,
          talla: data.talla,
          nombre_talla: data.nombre_atributo_talla || 'talla', // ✨ GUARDAMOS EL NOMBRE ORIGINAL
          categoria_id: data.categoria?.id
        };

        this.stockData = {
          precio_compra: data.precio_compra,
          precio_venta: data.precio_venta,
          descuento: data.descuento || 0,
          ubicacion: data.ubicacion_almacen || data.ubicacion || '',
          localizacion_id: (data.localizacion_id || data.localizacion?.id) ? Number(data.localizacion_id || data.localizacion?.id) : null,
          fecha_compra: data.fecha_compra ? data.fecha_compra.split('T')[0] : '', 
          proveedor_id: data.proveedor_id || data.proveedor?.id || null, 
          donar_ganancias: data.donar_ganancias || false,
          propietario_id: data.propietario_id || null,
          atributos: []
        };

        // ✨ AHORA LEEMOS stock_units DESDE EL BACKEND
        this.unidadesLote = (data.stock_units || data.unidadesLote || []).map((u: any) => ({
          ...u,
          id_original: u.id,
          editandoId: false
        }));

        if (this.contexto.categoria_id) {
          this.productsService.obtenerAtributosPorCategoria(this.contexto.categoria_id).subscribe({
            next: (atributosMolde) => {
              this.stockData.atributos = this.hidratarAtributosDinamicos(atributosMolde, data.atributos_extra);
              this.cargandoDatos = false;
            },
            error: () => {
              this.stockData.atributos = this.hidratarAtributosDinamicos([], data.atributos_extra);
              this.cargandoDatos = false;
            }
          });
        } else {
          this.stockData.atributos = this.hidratarAtributosDinamicos([], data.atributos_extra);
          this.cargandoDatos = false;
        }
      }
    });
  }

  onSupplierChanged(prov: Proveedor) { this.stockData.proveedor_id = prov.id || null; }

  onPropietarioChanged(clienteId: number | null | undefined) {
    this.stockData.propietario_id = clienteId;
    if (clienteId) {
      this.stockData.proveedor_id = null;
    }
  }

  getLabelEstadoGestion(estado: string): string {
    const mapa: any = {
      'en_stock': '✅ En Almacén',
      'vendido': '💰 Vendido',
      'devuelto_dueno': '🔙 Devuelto al dueño',
      'donado_a_ong': '💖 Donado a ONG',
      'extraviado': '⚠️ Extraviado',
      'en_camino_devolucion': '📦 En Tránsito (Devolución)'
    };
    return mapa[estado] || estado;
  }

  irAGestionarVariante() {
    this.router.navigate(['/edit', this.contexto.producto_id], { fragment: `variante-${this.contexto.variante_id}` });
  }

  verProductoPadre() {
    this.router.navigate(['/detail-product', this.contexto.producto_id]);
  }

  // ✨ MODO EDICIÓN RESTRINGIDO
  intentarEditarId(u: any) {
    if (u.estado_gestion === 'vendido') {
      alert(`⛔ No puedes editar el ID de la prenda #${u.id_original || u.id} porque ya ha sido vendida. El ID debe permanecer intacto para mantener la integridad del historial de ventas y finanzas.`);
      return;
    }
    u.editandoId = true;
  }

  // ✨ AHORA LLAMA AL MÉTODO DEDICADO A LA UNIDAD FÍSICA
  guardarEstadoUnidad(idxUnidad: number) {
    const u = this.unidadesLote[idxUnidad];
    
    if (!u.id || u.id <= 0) {
      alert('⚠️ El ID debe ser un número positivo.');
      return;
    }

    // ✨ RESTRICCIÓN: Confirmación si el ID ha cambiado
    if (u.id_original && u.id !== u.id_original) {
      const confirmar = confirm(`¿Estás seguro de que quieres cambiar el ID de ${u.id_original} a ${u.id}? Esta es una operación sensible.`);
      if (!confirmar) {
        u.id = u.id_original; // Revertimos
        u.editandoId = false;
        return;
      }
    }

    const payload = {
      id: u.id,
      sku: u.sku,
      estado_gestion: u.estado_gestion,
      publicar_web: (u as any).publicar_web || false,
      publicar_vinted: (u as any).publicar_vinted || false,
      publicar_wallapop: (u as any).publicar_wallapop || false,
      fecha_compra: (u as any).fecha_compra ? (u as any).fecha_compra.split('T')[0] : null
    };

    // Usamos u.id_original para localizar el registro
    this.productsService.actualizarStockUnit(u.id_original || u.id, payload).subscribe({
      next: (res: any) => {
        u.editandoId = false;
        u.id_original = res.id;
        u.id = res.id;

        // ✨ Si es extraviado y tiene precio, actualizamos el stock config en paralelo
        if (u.estado_gestion === 'extraviado' && this.stockData.propietario_id && this.stockData.precio_venta !== undefined) {
          this.productsService.actualizarStockIndividual(this.stockId!, { precio_venta: this.stockData.precio_venta }).subscribe();
        }

        alert(`✅ Datos de la prenda #${u.id} actualizados.`);
      },
      error: (err) => {
        console.error(err);
        alert('❌ Error: ' + (err.error?.detail || 'No se pudo guardar los cambios.'));
      }
    });
  }

  // ✨ ELIMINAR PRENDA FÍSICA
  eliminarUnidadFisica(idxUnidad: number, stockUnitId: number) {
    if(!confirm("¿Seguro que quieres borrar esta prenda física?")) return;
    this.productsService.moverStockUnitPapelera(stockUnitId).subscribe({
      next: () => {
        this.unidadesLote.splice(idxUnidad, 1);
        alert('🗑️ Prenda eliminada.');
      }
    });
  }

  private validarFormulario(): boolean {
    if (this.stockData.precio_compra < 0) { alert('⚠️ Precio compra inválido'); return false; }
    if (!this.stockData.localizacion_id) { alert('⚠️ Ubicación obligatoria'); return false; }
    return true;
  }

  onSubmit(): void {
    if (!this.validarFormulario()) return;

    // ✨ RESTRICCIÓN GLOBAL: Verificar si hay IDs manuales modificados en la tabla
    let idsModificados: { original: number, nuevo: number }[] = [];
    this.unidadesLote.forEach(u => {
      if (u.id_original && u.id && u.id !== u.id_original) {
        idsModificados.push({ original: u.id_original, nuevo: u.id });
      }
    });

    if (idsModificados.length > 0) {
      const listaStr = idsModificados.map(m => `#${m.original} -> #${m.nuevo}`).join(', ');
      const confirmar = confirm(`Has modificado los siguientes IDs de prendas: ${listaStr}. \n\n¿Estás seguro de que quieres aplicar estos cambios de forma global? Esta acción es irreversible.`);
      if (!confirmar) return;
    }

    this.isSubmitting = true;

    const atributosCompletos = this.stockData.atributos.map((attr: any) => ({
      nombre: attr.nombre,
      valor: attr.valor || ''
    }));

    // ✨ ASEGURAMOS QUE LA TALLA NO SE PIERDA (Ya que el back reemplaza todo el array EAV)
    if (this.contexto.nombre_talla && this.contexto.talla) {
      atributosCompletos.push({
        nombre: this.contexto.nombre_talla,
        valor: this.contexto.talla
      });
    }

    // ✨ PREPARAMOS LAS UNIDADES PARA EL BACKEND
    const unitsPayload = this.unidadesLote.map(u => ({
      id: u.id,
      id_original: u.id_original || u.id,
      sku: u.sku,
      estado_gestion: u.estado_gestion,
      fecha_compra: (u as any).fecha_compra ? (u as any).fecha_compra.split('T')[0] : null,
      publicar_web: (u as any).publicar_web || false,
      publicar_vinted: (u as any).publicar_vinted || false,
      publicar_wallapop: (u as any).publicar_wallapop || false
    }));

    // ✨ EL PAYLOAD EXACTO QUE ESPERA FASTAPI EN StockConfigEditPayload
    const payload = {
      precio_compra: this.stockData.precio_compra,
      precio_venta: this.stockData.precio_venta,
      descuento: this.stockData.descuento,
      localizacion_id: this.stockData.localizacion_id,
      proveedor_id: this.stockData.proveedor_id,
      donar_ganancias: this.stockData.donar_ganancias,
      atributos: atributosCompletos,
      stock_units: unitsPayload // ✨ AHORA ENVIAMOS LAS UNIDADES TAMBIÉN
    };

    let operacion$: Observable<any> = this.productsService.actualizarStockIndividual(this.stockId!, payload);

    // Si además escribieron un número para agregar unidades, lo encadenamos
    if (this.unidades_a_agregar > 0) {
      operacion$ = operacion$.pipe(
        switchMap(() => this.productsService.agregarUnidades(this.stockId!, this.unidades_a_agregar))
      );
    }

    operacion$.subscribe({
      next: () => {
        this.isSubmitting = false;
        this.router.navigate(['/detail-product', this.contexto.producto_id], { 
          state: { ids: [this.stockId], accion: 'editado' } 
        });
      },
      error: (err) => {
        this.isSubmitting = false;
        console.error(err);
        alert('❌ Error al guardar la configuración del lote.');
      }
    });
  }

  agregarUnidadesAlLote() {
    if (this.unidades_a_agregar <= 0) return;
    
    this.isAddingUnits = true;
    this.productsService.agregarUnidades(this.stockId!, this.unidades_a_agregar, this.fecha_a_agregar).subscribe({
      next: (res: any) => {
        const nuevas = res.unidades || []; // <-- Declarado como 'nuevas'
        nuevas.forEach((u: any) => this.unidadesLote.push(u));
        this.unidades_a_agregar = 0; 
        this.isAddingUnits = false;
        
        // ✨ CORREGIDO: Usamos 'nuevas.length'
        alert(`✅ Se han añadido ${nuevas.length} nuevas prendas al inventario.`);
      },
      error: (err) => {
        this.isAddingUnits = false;
        console.error(err);
        alert('❌ Error al agregar unidades.');
      }
    });
  }

  volver() {
    this.router.navigate(['/detail-product', this.contexto.producto_id], { 
      queryParams: { highlight: this.stockId } 
    });
  }
}