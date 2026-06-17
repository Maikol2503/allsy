import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { VentasService, VentaData } from '../../../core/services/ventas.service';
import { SafeUrlPipe } from '../../../shared/pipes/safe-url.pipe';

@Component({
  selector: 'app-pos',
  standalone: true,
  imports: [CommonModule, FormsModule, SafeUrlPipe],
  templateUrl: './pos.component.html',
  styleUrls: ['./pos.component.css']
})
export class PosComponent {
  codigoBusqueda: string = '';
  procesando: boolean = false;
  cargando: boolean = false; // ✨ NUEVO: Para búsquedas
  
  comprasPreviasCliente: number | null = null;
  carrito: any[] = [];
  subtotal: number = 0;
  total: number = 0;

  // ✨ Variables de validación de etiqueta
  estadoEtiqueta: 'vacio' | 'cargando' | 'valida' | 'invalida' = 'vacio';

  prefijosPaises = [
    { codigo: '+34', pais: 'España (+34)' },
    { codigo: '+58', pais: 'Venezuela (+58)' },
    { codigo: '+57', pais: 'Colombia (+57)' },
    { codigo: '+52', pais: 'México (+52)' },
    { codigo: '+1', pais: 'EE.UU/Canadá (+1)' },
    { codigo: '+33', pais: 'Francia (+33)' },
    { codigo: '+39', pais: 'Italia (+39)' }
  ];

  listaPaises = [
    { nombre: 'España', bandera: '🇪🇸' },
    { nombre: 'Francia', bandera: '🇫🇷' },
    { nombre: 'Italia', bandera: '🇮🇹' },
    { nombre: 'Portugal', bandera: '🇵🇹' },
    { nombre: 'Bélgica', bandera: '🇧🇪' },
    { nombre: 'Alemania', bandera: '🇩🇪' },
    { nombre: 'Países Bajos', bandera: '🇳🇱' },
    { nombre: 'Reino Unido', bandera: '🇬🇧' },
    { nombre: 'EE.UU.', bandera: '🇺🇸' },
    { nombre: 'Otros', bandera: '🌍' }
  ];

  datosVenta: VentaData = {
    fecha: new Date().toISOString().split('T')[0],
    canal: 'vinted',
    vendedor: '', 
    metodo_pago: 'vinted',
    estado_pago: 'pendiente',  
    estado_envio: 'pendiente_envio',
    pais: '',
    tipo_identificador: 'telefono',
    prefijo_telefono: '+34',
    tipo_documento: 'DNI',
    identificador_cliente: '',
    nombre_cliente: '',
    descuento_total: 0,
    costo_envio: 0,
    empresa_transporte: '',
    numero_seguimiento: '',
    etiqueta_url: '',
    etiqueta_imprimida: false,
    detalles: []
  };

  constructor(private ventasService: VentasService, private http: HttpClient) {
    this.onCanalChange();
  }

  // ✨ NUEVA FUNCIÓN: Verifica la URL cuando el usuario la pega
  validarUrlEtiqueta() {
    let url = this.datosVenta.etiqueta_url?.trim();
    if (!url) {
      this.estadoEtiqueta = 'vacio';
      return;
    }

    if (!url.startsWith('http') && !url.startsWith('https')) {
      url = 'https://' + url;
      this.datosVenta.etiqueta_url = url;
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

  fixUrl(url: string | null | undefined): string {
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

  onCanalChange() {
    if (this.datosVenta.canal === 'tienda_fisica') {
      this.datosVenta.estado_pago = 'pagado';
      this.datosVenta.metodo_pago = 'efectivo';
      this.datosVenta.pais = 'España';
    } else {
      this.datosVenta.estado_pago = 'pendiente';
      this.datosVenta.metodo_pago = this.datosVenta.canal === 'web' ? 'plataforma' : this.datosVenta.canal;
    }
  }

  buscarHistorialCliente() {
    let idParaBuscar = this.datosVenta.identificador_cliente?.trim();

    if (this.datosVenta.canal === 'tienda_fisica' && this.datosVenta.tipo_identificador === 'telefono') {
      idParaBuscar = `${this.datosVenta.prefijo_telefono}${idParaBuscar}`;
    }

    if (!idParaBuscar || idParaBuscar.length < 3) {
      this.comprasPreviasCliente = null;
      return;
    }

    this.ventasService.obtenerConteoCompras(idParaBuscar).subscribe({
      next: (res) => {
        this.comprasPreviasCliente = res.compras_totales;
      },
      error: () => this.comprasPreviasCliente = 0
    });
  }

  buscarYAgregarProducto() {
    if (!this.codigoBusqueda.trim()) return;

    const query = this.codigoBusqueda.trim();
    this.cargando = true; // ✨ Activar loader

    this.ventasService.buscarProductoPorStock(query).subscribe({
      next: (res) => {
        this.cargando = false; // ✨ Desactivar loader
        if (res.alerta) {
          alert(res.alerta);
          return;
        }

        const existe = this.carrito.find(item => item.stock_unit_id === res.stock_unit_id);
        if (existe) {
          alert(`⚠️ Este ítem físico (ID #${res.stock_unit_id}) ya está en el carrito.`);
          this.codigoBusqueda = '';
          return;
        }

        this.carrito.push({
          ...res,
          cantidad_venta: 1,
          precio_unitario: res.precio_venta
        });
        
        this.codigoBusqueda = '';
        this.calcularTotales();
      },
      error: () => {
        this.cargando = false; // ✨ Desactivar loader
        alert('No se encontró la unidad física.');
      }
    });
  }

  eliminarDelCarrito(index: number) {
    this.carrito.splice(index, 1);
    this.calcularTotales();
  }

  calcularTotales() {
    this.subtotal = this.carrito.reduce((acc, item) => acc + (1 * Number(item.precio_unitario)), 0);
    let d = Number(this.datosVenta.descuento_total) || 0;
    let e = Number(this.datosVenta.costo_envio) || 0;
    this.total = (this.subtotal + e) - d;
    if (this.total < 0) this.total = 0;
  }

  completarVenta() {
    if (this.carrito.length === 0) return;

    if (!this.datosVenta.fecha) {
      alert('⚠️ La Fecha de Venta es obligatoria.'); return;
    }
    if (!this.datosVenta.vendedor) {
      alert('⚠️ Seleccionar el Vendedor es obligatorio.'); return;
    }

    const canalesQueExigenCliente = ['vinted', 'wallapop', 'web'];
    if (canalesQueExigenCliente.includes(this.datosVenta.canal)) {
      if (!this.datosVenta.identificador_cliente || this.datosVenta.identificador_cliente.trim() === '') {
        alert(`⚠️ Para ventas en ${this.datosVenta.canal.toUpperCase()}, el identificador del cliente es OBLIGATORIO.`);
        return;
      }
    }

    if (!this.datosVenta.pais) {
      alert('⚠️ El País de Compra es obligatorio.'); return;
    }
    if (this.total <= 0) {
      alert('⚠️ Error: El TOTAL de la venta debe ser mayor a 0 €.'); return;
    }

    this.procesando = true;

    this.datosVenta.detalles = this.carrito.map(item => ({
      stock_id: item.stock_unit_id,
      cantidad: 1,
      precio_unitario: Number(item.precio_unitario)
    }));

    if (this.datosVenta.canal === 'tienda_fisica') {
      this.datosVenta.estado_venta = 'completada';
    } else {
      this.datosVenta.estado_venta = 'abierta';
    }

    this.ventasService.registrarVenta(this.datosVenta).subscribe({
      next: (res) => {
        alert(`✅ VENTA REGISTRADA\nCódigo: ${res.codigo}`);
        this.limpiarCaja();
      },
      error: (err) => {
        this.procesando = false; 
        const mensaje = err.error?.detail || 'Ocurrió un error inesperado al procesar la venta.';
        if (err.status === 400) {
          alert(`⚠️ ERROR DE ESTADO DE STOCK:\n\n${mensaje}`);
        } else {
          alert(`❌ Error al registrar la venta: ${mensaje}`);
        }
      }
    });
  }

  limpiarCaja() {
    this.carrito = [];
    this.datosVenta.identificador_cliente = '';
    this.datosVenta.nombre_cliente = '';
    this.datosVenta.apellidos_cliente = '';
    this.datosVenta.pais = '';
    this.datosVenta.descuento_total = 0;
    this.datosVenta.costo_envio = 0;
    this.datosVenta.numero_seguimiento = '';
    this.datosVenta.empresa_transporte = '';
    this.datosVenta.etiqueta_url = '';
    this.estadoEtiqueta = 'vacio';
    this.comprasPreviasCliente = null;
    this.datosVenta.fecha = new Date().toISOString().split('T')[0];
    this.onCanalChange(); 
    this.calcularTotales();
    this.procesando = false;
  }
}