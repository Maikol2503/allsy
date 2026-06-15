import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { VentasService } from '../../../core/services/ventas.service';
import { SafeUrlPipe } from '../../../shared/pipes/safe-url.pipe';
import { LocationSelectorComponent } from '../../../shared/components/selectors/location-selector/location-selector.component';

@Component({
  selector: 'app-order-fulfillment',
  standalone: true,
  imports: [CommonModule, FormsModule, SafeUrlPipe, LocationSelectorComponent],
  templateUrl: './order-fulfillment.component.html',
  styleUrls: ['./order-fulfillment.component.css']
})
export class OrderFulfillmentComponent implements OnInit {
  ordenesAgrupadas: any[] = [];
  cargando = false;

  // ✨ VARIABLES DE PAGINACIÓN
  page = 1;
  limit = 10;
  totalItems = 0;

  // ✨ FILTROS (Backend)
  filtroSearch = '';
  tipoBusqueda = 'stock_unit_id';
  filtroEstado = 'preparacion'; 
  localizacion_id: number | null | undefined = null; // ✨ NUEVO

  constructor(
    private ventasService: VentasService,
    private http: HttpClient
  ) {}

  ngOnInit(): void {
    this.cargarListaPicking();
  }

  // ✨ Al cambiar filtros desde la UI, volvemos a la página 1 y recargamos
  onFiltrosChange() {
    this.page = 1;
    this.cargarListaPicking();
  }

  cargarListaPicking() {
    this.cargando = true;
    this.ventasService.obtenerPendientesLogistica(
      this.page, 
      this.limit, 
      this.filtroSearch, 
      this.tipoBusqueda,
      this.filtroEstado,
      this.localizacion_id
    ).subscribe({
      next: (res: any) => {
        // ✨ La respuesta ahora viene con { total, items }
        this.totalItems = res.total || 0;
        const data = Array.isArray(res.items) ? res.items : [];
        
        this.ordenesAgrupadas = data.map((o: any) => ({
          ...o,
          guardando: false,
          seleccionada: false
        }));
        this.cargando = false;
      },
      error: (err) => {
        console.error('Error al cargar lista logística:', err);
        alert('No se pudo cargar la lista de empaque. Revisa la conexión.');
        this.cargando = false;
      }
    });
  }

  cambiarPagina(nuevaPagina: number) {
    if (nuevaPagina >= 1 && nuevaPagina <= this.totalPages) {
      this.page = nuevaPagina;
      this.cargarListaPicking();
      window.scrollTo(0, 0);
    }
  }

  get totalPages(): number {
    return Math.ceil(this.totalItems / this.limit);
  }

  // ✨ RESALTAR ORDEN AL CLICAR
  marcarSeleccionada(orden: any) {
    this.ordenesAgrupadas.forEach(o => o.seleccionada = false);
    orden.seleccionada = true;
  }

  // ✨ Eliminamos el getter ordenesFiltradas antiguo ya que ahora el backend hace el trabajo
  get ordenesParaMostrar() {
    return this.ordenesAgrupadas;
  }

  imprimirEtiqueta(orden: any) {
    this.abrirEtiqueta(orden);
  }

  // ✨ NUEVA FUNCIÓN: Ejecuta la impresión de la etiqueta sin marcarla automáticamente
  imprimirYMarcar(orden: any) {
    const url = this.fixUrl(orden.etiqueta_url);
    if (!url) return;

    // Ya no marcamos como impresa automáticamente aquí.
    // Solo lanzamos la orden de impresión.
    this.imprimirDocumento(url);
  }

  imprimirDocumento(url: string) {
    // Si es imagen, podemos imprimir el contenido abriendo una ventana limpia
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
    // Usamos el proxy de nuestro propio backend para evadir las políticas del servidor final (S3)
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
              // Fallback extremo
              window.open(url, '_blank');
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

  // ✨ MEJORA: Asegura que la URL sea absoluta y abre en nueva pestaña
  abrirEtiqueta(orden: any) {
    const url = this.fixUrl(orden.etiqueta_url);
    if (!url) {
      alert('⚠️ No hay URL de etiqueta para este pedido.');
      return;
    }
    // Abrimos el PDF normalmente para que el móvil muestre su barra de herramientas
    window.open(url, '_blank');
  }

  // ✨ NORMALIZADOR DE URL: Evita que el navegador crea que es una ruta interna y mande al LOGIN
  // Además fuerza a que aparezca la BARRA DE HERRAMIENTAS del PDF (Zoom, Imprimir, etc)
  fixUrl(url: string | null): string {
    if (!url) return '';
    let fixed = url.trim();
    if (!fixed.startsWith('http://') && !fixed.startsWith('https://')) {
      fixed = 'https://' + fixed;
    }

    // ✨ TRUCO: Forzamos la barra de herramientas del visor de PDF del navegador
    if (fixed.toLowerCase().includes('pdf') || !fixed.includes('#')) {
       if (!fixed.includes('toolbar=')) {
         fixed += '#toolbar=1&navpanes=0&view=FitH';
       }
    }
    return fixed;
  }

  // ✨ CAMBIO MANUAL DE ID (Trueque Inteligente)
  cambiarIdFisico(orden: any, item: any) {
    const input = prompt(`Vas a cambiar la prenda #${item.stock_unit_id} por otra idéntica del mismo lote.\n\nIntroduce el ID de la nueva prenda física a empaquetar:`);
    
    if (!input) return; // Canceló

    const nuevoId = parseInt(input, 10);
    if (isNaN(nuevoId) || nuevoId <= 0) {
      alert("⚠️ El ID introducido no es válido. Debe ser un número.");
      return;
    }

    if (nuevoId === item.stock_unit_id) {
      alert("⚠️ Has introducido el mismo ID que ya está en la caja.");
      return;
    }

    item.cambiandoId = true; // Activa el loader local de ese ítem

    this.ventasService.intercambiarItemVenta(orden.id, item.detalle_id, nuevoId).subscribe({
      next: (res: any) => {
        alert(res.mensaje || '✅ Trueque realizado con éxito.');
        item.stock_unit_id = nuevoId;
        item.cambiandoId = false;
        
        // Verificamos de nuevo si todo está listo
        this.comprobarEmpaquetadoCompleto(orden);
      },
      error: (err) => {
        item.cambiandoId = false;
        alert(`❌ Error al intercambiar:\n\n${err.error?.detail || 'No se pudo procesar la solicitud.'}`);
      }
    });
  }

  // Comprueba si todas las prendas están verificadas y marca el pedido como empaquetado
  comprobarEmpaquetadoCompleto(orden: any) {
    // Si la lógica de empaquetado automático depende de verificación manual,
    // podríamos mantener un flag visual. Por ahora, al cambiar de ID manualmente se puede asumir
    // que el paquete está siendo preparado.
  }

  cambiarFase(orden: any) {
    this.actualizarLogisticaServidor(orden);
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

  actualizarLogisticaServidor(orden: any, silencioso: boolean = false) {
    orden.guardando = true; // ✨ Mostrar loader
    
    const payload: any = {
      estado_envio: orden.estado_envio,
      etiqueta_url: orden.etiqueta_url,
      etiqueta_imprimida: orden.etiqueta_imprimida
    };

    // ✨ Si el usuario filtró por una prenda específica y le dio a guardar,
    // mandamos ese ID al backend para que intente el "Intercambio Inteligente"
    if (this.tipoBusqueda === 'stock_unit_id' && this.filtroSearch) {
       const idNum = parseInt(this.filtroSearch);
       if (!isNaN(idNum)) {
         payload.scanned_unit_id = idNum;
       }
    }

    this.ventasService.editarVenta(orden.id, payload).subscribe({
      next: (res: any) => {
        orden.guardando = false; 
        
        // ✨ MOSTRAR ALERTA DE TRUEQUE SI OCURRIÓ
        if (res.alerta_logistica) {
          alert(res.alerta_logistica);
          this.cargarListaPicking(); // Recargamos para ver los nuevos IDs en la tabla
        }

        // ✨ Se ha eliminado la lógica de auto-remoción local. 
        // Si el usuario cambia el estado (incluso a 'enviado'), la orden permanecerá 
        // en la pantalla hasta que refresque o cambie de filtro.
      },
      error: (err) => {
        orden.guardando = false;
        alert('Error al guardar: ' + (err.error?.detail || 'Desconocido'));
      }
    });
  }
}
