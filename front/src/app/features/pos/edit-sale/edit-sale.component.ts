import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute, Router } from '@angular/router';
import { VentasService } from '../../../core/services/ventas.service';
import { ProductsService } from '../../../core/services/products.service';

@Component({
  selector: 'app-edit-sale',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './edit-sale.component.html',
  styleUrls: ['./edit-sale.component.css']
})
export class EditSaleComponent implements OnInit {
  ventaId: number | null = null;
  cargando = true;
  guardando = false;
  venta: any = {};
  identificadorCrm: string = '';
  formData: any = {
    fecha: '', 
    fecha_pago: '',
    fecha_envio: '',
    fecha_entrega: '', // ✨ NUEVO
    estado_venta: '',
    estado_pago: '',
    metodo_pago: '',
    nombre_cliente: '',
    email_cliente: '',
    estado_envio: '',
    empresa_transporte: '',
    numero_seguimiento: '',
    notas_internas: '',
    total: 0,
    monto_reembolsado: 0,
    etiqueta_url: '',
    etiqueta_imprimida: false
  };

  // ✨ Variables de validación de etiqueta
  estadoEtiqueta: 'vacio' | 'cargando' | 'valida' | 'invalida' = 'vacio';

  // ✨ Variables para Modal de Devolución Parcial
  mostrarModalDevolucion = false;
  estadoEnvioPrevio = '';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private ventasService: VentasService,
    private productsService: ProductsService,
    private http: HttpClient
  ) {}

  ngOnInit() {
    this.ventaId = Number(this.route.snapshot.paramMap.get('id'));
    if (this.ventaId) {
      this.cargarVenta();
    }
  }

  // ✨ Manejador del Dropdown de Logística
  onEstadoEnvioChange(nuevoEstado: string) {
    if (nuevoEstado === 'devolucion_parcial') {
      // Revertimos el select visualmente al estado real
      setTimeout(() => this.formData.estado_envio = this.estadoEnvioPrevio, 0);
      // Abrimos el modal
      this.mostrarModalDevolucion = true;
    } else {
      this.estadoEnvioPrevio = nuevoEstado;
    }
  }

  // ✨ NUEVA FUNCIÓN: Verifica la URL cuando el usuario la pega
  validarUrlEtiqueta() {
    let url = this.formData.etiqueta_url?.trim();
    if (!url) {
      this.estadoEtiqueta = 'vacio';
      return;
    }

    if (!url.startsWith('http') && !url.startsWith('https')) {
      url = 'https://' + url;
      this.formData.etiqueta_url = url;
    }

    this.estadoEtiqueta = 'cargando';
    const proxyUrl = this.ventasService.obtenerUrlProxyEtiqueta(url);

    this.http.get(proxyUrl, { responseType: 'blob' }).subscribe({
      next: () => {
        this.estadoEtiqueta = 'valida';
      },
      error: () => {
        this.estadoEtiqueta = 'invalida';
      }
    });
  }

  fixUrl(url: string | null): string {
    if (!url) return '';
    let fixed = url.trim();
    if (!fixed.startsWith('http://') && !fixed.startsWith('https://')) {
      fixed = 'https://' + fixed;
    }
    if (fixed.toLowerCase().includes('pdf') || !fixed.includes('#')) {
       if (!fixed.includes('toolbar=')) {
         fixed += '#toolbar=0&navpanes=0&view=FitH';
       }
    }
    return fixed;
  }

  // Adapta la fecha de la base de datos al formato del input HTML
  formatDateForInput(dateString: string | null | undefined): string {
    if (!dateString) return '';
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return '';
      const tzOffset = date.getTimezoneOffset() * 60000; 
      return new Date(date.getTime() - tzOffset).toISOString().slice(0, 16);
    } catch (e) {
      return '';
    }
  }

  tieneItemsBloqueados = false;

  cargarVenta() {
    this.ventasService.obtenerVenta(this.ventaId!).subscribe({
      next: (res) => {
        this.venta = res;
        
        // Verificar si algún ítem está bloqueado (pagado)
        this.tieneItemsBloqueados = this.venta.detalles?.some((d: any) => d.pago_consignacion_id !== null) || false;

        if (res.cliente) {
          if (res.canal === 'vinted') {
            this.identificadorCrm = res.cliente.usuario_vinted ? `@${res.cliente.usuario_vinted}` : 'Sin usuario Vinted';
          } else if (res.canal === 'wallapop') {
            this.identificadorCrm = res.cliente.usuario_wallapop ? `@${res.cliente.usuario_wallapop}` : 'Sin usuario Wallapop';
          } else if (res.canal === 'tienda_fisica') {
            this.identificadorCrm = res.cliente.telefono || res.cliente.dni_nie || 'Cliente de Tienda';
          } else {
            this.identificadorCrm = res.cliente.email || 'Sin email';
          }
        }
        
        this.formData = {
          fecha: this.formatDateForInput(res.fecha), 
          fecha_pago: this.formatDateForInput(res.fecha_pago), 
          fecha_envio: this.formatDateForInput(res.fecha_envio),
          estado_venta: (res.estado_venta || '').toLowerCase(),
          estado_pago: (res.estado_pago || '').toLowerCase(),
          monto_reembolsado: res.monto_reembolsado || 0,
          nombre_cliente: res.nombre_cliente || '', 
          email_cliente: res.email_cliente || '',
          estado_envio: (res.estado_envio || '').toLowerCase(),
          empresa_transporte: res.empresa_transporte || '', 
          numero_seguimiento: res.numero_seguimiento || '',
          notas_internas: res.notas_internas || '',
          total: res.total || 0,
          etiqueta_url: res.etiqueta_url || '',
          etiqueta_imprimida: res.etiqueta_imprimida || false
        };
        this.cargando = false;
        
        // ✨ Validamos la URL que vino de la base de datos (si existe)
        if (this.formData.etiqueta_url) {
          this.validarUrlEtiqueta();
        }
      },
      error: () => {
        alert('Venta no encontrada');
        this.volver();
      }
    });
  }

  prepararDatosParaGuardar(): any {
    const dataToSend = { ...this.formData };
    if (!dataToSend.fecha) dataToSend.fecha = null;
    if (!dataToSend.fecha_pago) dataToSend.fecha_pago = null;
    if (!dataToSend.fecha_envio) dataToSend.fecha_envio = null;
    return dataToSend;
  }

  onEstadoPagoChange(nuevoEstado: string) {
    if (nuevoEstado === 'reembolsado') {
      this.formData.monto_reembolsado = this.formData.total;
    } else if (nuevoEstado !== 'reembolso_parcial') {
      this.formData.monto_reembolsado = 0;
    }
  }


  // ✨ FUNCIÓN PARA DEVOLUCIÓN FÍSICA PARCIAL
  devolverItem(detalleId: number, stockUnitId: number) {
    const confirma = confirm(`¿Estás seguro de que quieres devolver la prenda #${stockUnitId} al stock? \n\n- Se marcará como devuelta en el ticket.\n- El total de la venta disminuirá.\n- El dueño de la prenda NO cobrará su parte por este artículo.`);
    
    if (!confirma) return;

    const enTienda = confirm('¿La prenda ya está físicamente en la tienda?\n\n- [Aceptar]: Se marcará como ✅ En Almacén\n- [Cancelar]: Se marcará como 📦 En Tránsito (Devolución)');
    const estadoStock = enTienda ? 'en_stock' : 'en_camino_devolucion';

    this.ventasService.devolverItemFisicamente(this.ventaId!, detalleId, estadoStock).subscribe({
      next: (res) => {
        alert(`✅ Prenda devuelta. Estado: ${enTienda ? 'En Almacén' : 'En Tránsito'}. Venta actualizada.`);
        this.cargarVenta(); // Recargamos para ver los nuevos totales e ítems
      },
      error: (err) => {
        alert('❌ Error al devolver: ' + (err.error?.detail || 'No se pudo procesar la devolución.'));
      }
    });
  }

  // ✨ GESTIÓN DE PRENDAS DEVUELTAS EN TRÁNSITO
  actualizarEstadoDevolucion(item: any, nuevoEstado: string) {
    if (!item.stock_unit_id) return;
    
    const mensajes: any = {
      'en_stock': '¿Confirmas que la prenda YA LLEGÓ a la tienda y está lista para venderse de nuevo?',
      'extraviado': '¿Confirmas que la empresa de transporte HA EXTRAVIADO la prenda?\n\n- El sistema anulará la devolución.\n- La prenda constará como VENDIDA para que el dueño original cobre su comisión (ya que la plataforma/transporte te indemnizará a ti).'
    };
    
    if (!confirm(mensajes[nuevoEstado])) {
       // Restauramos select visualmente
       item.estado_gestion = 'en_camino_devolucion';
       return;
    }

    this.ventasService.resolverRetornoTransito(this.ventaId!, item.id, nuevoEstado).subscribe({
      next: () => {
        alert('✅ Estado de la prenda resuelto correctamente.');
        this.cargarVenta(); // Recargamos para que se actualice la vista (especialmente si es extravío, para que se quite lo de "devuelto")
      },
      error: (err: any) => {
        console.error(err);
        alert('❌ Error al actualizar el estado de la prenda.');
        item.estado_gestion = 'en_camino_devolucion';
      }
    });
  }

  // ✨ FUNCIÓN PARA COMPENSACIÓN ALLSYS (Sin devolución física)
  darCompensacion() {
    const input = prompt(`Introduce el monto (€) que Allsys reembolsará al cliente como compensación (Ej: por una mancha).\n\n- La prenda seguirá marcada como vendida.\n- El dueño de la prenda COBRARÁ lo pactado originalmente.\n- Allsys registrará un Gasto por este importe.`);
    
    if (!input) return;
    const monto = parseFloat(input);
    if (isNaN(monto) || monto <= 0) {
      alert('⚠️ El monto introducido no es válido.');
      return;
    }

    if (monto > this.formData.total) {
      alert('⚠️ No puedes compensar más del total de la venta.');
      return;
    }

    const motivo = prompt('Introduce brevemente el motivo de la compensación (Ej: Prenda con mancha leve):');
    if (!motivo) return;

    this.ventasService.registrarCompensacionAllsys(this.ventaId!, monto, motivo).subscribe({
      next: () => {
        alert('✅ Compensación registrada con éxito como gasto de Allsys.');
        this.cargarVenta();
      },
      error: (err) => {
        alert('❌ Error al registrar compensación: ' + (err.error?.detail || 'Desconocido'));
      }
    });
  }

  // ✨ FUNCIÓN PARA CORREGIR EL PRECIO DE UNA PRENDA
  corregirPrecioPrenda(item: any) {
    const input = prompt(`Introduce el NUEVO PRECIO REAL de venta para la prenda: ${item.nombre_producto} (SKU: ${item.stock_unit_id})\n\nPrecio actual: ${item.precio_unitario}€\n\n⚠️ ATENCIÓN:\n- Esto modificará el total del ticket.\n- Esto AFECTARÁ lo que cobra el dueño de la prenda (Se calculará su comisión sobre este nuevo valor).`);
    if (input === null) return;
    
    const nuevoPrecio = parseFloat(input);
    if (isNaN(nuevoPrecio) || nuevoPrecio < 0) {
      alert('⚠️ El precio introducido no es válido.');
      return;
    }

    this.ventasService.corregirPrecioItem(this.ventaId!, item.id, nuevoPrecio).subscribe({
      next: () => {
        alert('✅ Precio corregido correctamente.');
        this.cargarVenta();
      },
      error: (err) => {
        alert('❌ Error al corregir precio: ' + (err.error?.detail || 'Desconocido'));
      }
    });
  }

  imprimirEtiqueta() {
    if (!this.formData.etiqueta_url) {
      alert('⚠️ No hay ninguna URL de etiqueta registrada.');
      return;
    }
    this.formData.etiqueta_imprimida = true;
    
    let url = this.formData.etiqueta_url.trim();
    if (!url.startsWith('http') && !url.startsWith('https')) {
      url = 'https://' + url;
    }
    
    this.imprimirDocumento(url);
  }

  imprimirDocumento(url: string) {
    if (url.match(/\.(jpeg|jpg|gif|png|webp)(\?.*)?$/i)) {
      const printWindow = window.open('', '_blank');
      if (printWindow) {
        printWindow.document.write(`
          <html>
            <head><title>Imprimir Etiqueta</title></head>
            <body style="margin:0;display:flex;justify-content:center;align-items:center;height:100vh;">
              <img src="${url}" style="max-width:100%;max-height:100%;" onload="window.print();window.close();" />
            </body>
          </html>
        `);
        printWindow.document.close();
        return;
      }
    }

    // ✨ TÉCNICA ANTI-CORS: Descargar el PDF como Blob e inyectarlo en el iframe oculto
    const proxyUrl = this.ventasService.obtenerUrlProxyEtiqueta(url);
    
    this.http.get(proxyUrl, { responseType: 'blob' }).subscribe({
      next: (blob) => {
        const blobUrl = window.URL.createObjectURL(blob);
        const iframe = document.createElement('iframe');
        iframe.style.display = 'none';
        iframe.src = blobUrl;
        document.body.appendChild(iframe);

        iframe.onload = () => {
          setTimeout(() => {
            try {
              iframe.contentWindow?.focus();
              iframe.contentWindow?.print();
            } catch (err) {
              console.warn('El navegador bloqueó la impresión del Blob (raro).', err);
            }
            
            // Limpieza
            setTimeout(() => {
              window.URL.revokeObjectURL(blobUrl);
              if (document.body.contains(iframe)) {
                document.body.removeChild(iframe);
              }
            }, 5000);
          }, 500); // Pequeño delay para que el PDF se pinte dentro del iframe
        };
      },
      error: (err) => {
        console.warn('Fallo al descargar el PDF usando proxy.', err);
        if (err.status === 400 || err.status === 404 || err.status === 403) {
          alert('❌ Error: El enlace de la etiqueta está roto, no existe, o no es un documento válido.\n\nPor favor, verifica la URL ingresada.');
        } else {
          alert('⚠️ Hubo un problema de conexión al intentar generar la impresión interna.\n\nSe abrirá la etiqueta en una pestaña normal.');
          window.open(url, '_blank');
        }
      }
    });
  }

  guardarCambios() {
    this.guardando = true;
    
    const payload = this.prepararDatosParaGuardar();

    this.ventasService.editarVenta(this.ventaId!, payload).subscribe({
      next: () => {
        alert('✅ Venta actualizada con éxito.');
        this.volver();
      },
      error: (err) => {
        alert('Error al guardar: ' + (err.error?.detail || 'Desconocido'));
        this.guardando = false;
      }
    });
  }

  volver() {
    this.router.navigate(['/sales-list']);
  }

  get ventaGlobalCerradaLogistica(): boolean {
    const e = this.formData.estado_envio;
    return e === 'extraviado_envio' || e === 'extraviado_devolucion' || e === 'cancelado' || e === 'devuelto' || e === 'en_devolucion';
  }
}