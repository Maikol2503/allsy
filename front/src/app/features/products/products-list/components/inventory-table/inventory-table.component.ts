import { Component, Input, OnChanges, SimpleChanges, OnInit } from '@angular/core';
import { CommonModule, TitleCasePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ProductsService } from '../../../../../core/services/products.service';
import { LocationsService, Localizacion } from '../../../../../core/services/locations.service';
import { FormsModule } from '@angular/forms';

export interface UnidadStock {
  id: number;          // ✨ Actualizado
  sku: string;         // ✨ Actualizado
  estado_gestion: string;
  nuevo_estado?: string; 
  canales?: any;
  fecha_compra?: string; // ✨ AÑADIDO PARA LA TABLA INTERNA
  venta_id?: number; // ✨ AÑADIDO PARA ENLACE A VENTA
}

export interface LoteAgrupado {
  expandido: boolean;
  pagina_interna: number;
  stock_units: UnidadStock[];  // ✨ Actualizado
  stock_config_id: number;     // ✨ Actualizado
  producto_nombre: string;
  imagen_cover: string | null;
  marca?: { nombre: string; [key: string]: any };
  hex_identidad: string;
  identidad_variante: string;
  talla: string | null;
  localizacion_id?: number; // ✨ AÑADIDO PARA BUSCAR RUTA
  localizacion?: { id: number, nombre: string }; // ✨ AÑADIDO
  ruta_localizacion?: string; // ✨ AÑADIDO PARA LA RUTA COMPLETA
  propietario?: { id: number, nombre: string, email?: string }; // ✨ AÑADIDO
  precio_compra: number; // ✨ AÑADIDO
  precio_venta: number;
  fecha_registro?: string; // ✨ AÑADIDO
  stock_disponible: number;    // ✨ El backend ya nos manda esto sumado
  [key: string]: any; 
}

@Component({
  selector: 'app-inventory-table',
  standalone: true,
  imports: [CommonModule, RouterLink, TitleCasePipe, FormsModule],
  templateUrl: './inventory-table.component.html',
  styleUrl: './inventory-table.component.css'
})
export class InventoryTableComponent implements OnChanges, OnInit {

  @Input() stocks: any[] = []; 
  Math = Math;
  stocksAgrupados: LoteAgrupado[] = [];
  mapaLocalizaciones = new Map<number, string>();

  constructor(
    private productsService: ProductsService,
    private locService: LocationsService
  ) {}

  ngOnInit(): void {
    this.locService.listarArbol().subscribe(arbol => {
      this.construirMapaNombres(arbol, '');
      this.actualizarRutas();
    });
  }

  private construirMapaNombres(nodos: Localizacion[], prefijo: string) {
    for (const n of nodos) {
      const path = prefijo ? `${prefijo} > ${n.nombre}` : n.nombre;
      this.mapaLocalizaciones.set(n.id!, path);
      if (n.hijos) this.construirMapaNombres(n.hijos, path);
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['stocks'] && changes['stocks'].currentValue) {
      this.stocksAgrupados = this.stocks.map(s => ({
        ...s,
        expandido: this.stocks.length === 1,
        pagina_interna: 1,
        ruta_localizacion: this.mapaLocalizaciones.get(s.localizacion_id) || s.localizacion?.nombre || 'Sin asignar',
        stock_units: (s.stock_units || []).map((u: any) => ({
          ...u,
          nuevo_estado: u.estado_gestion
        }))
      }));
      this.actualizarRutas();
    }
  }

  private actualizarRutas() {
    this.stocksAgrupados.forEach(s => {
      if (s.localizacion_id) {
         s.ruta_localizacion = this.mapaLocalizaciones.get(s.localizacion_id) || s.localizacion?.nombre || 'Sin asignar';
      }
    });
  }

  getBackground(hexString: string): string {
    if (!hexString) return '#f2f2f2';
    if (hexString.includes('gradient')) return hexString; // Ya es un patrón
    const colors = hexString.split(',');
    if (colors.length === 1) return colors[0];
    if (colors.length === 2) return `linear-gradient(90deg, ${colors[0]} 50%, ${colors[1]} 50%)`;
    if (colors.length === 3) return `linear-gradient(90deg, ${colors[0]} 33.3%, ${colors[1]} 33.3%, ${colors[1]} 66.6%, ${colors[2]} 66.6%)`;
    return '#f2f2f2';
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

  // ✨ FUNCIÓN DE EDICIÓN EN LÍNEA APUNTANDO AL NUEVO ENDPOINT
  guardarEstadoInline(u: UnidadStock, lote: LoteAgrupado) {
    const estadoAnterior = u.estado_gestion;

    if (estadoAnterior === 'vendido') {
      alert('⛔ No se puede modificar el estado de una prenda que ya ha sido vendida.');
      u.nuevo_estado = estadoAnterior; // Revierte el select visualmente
      return;
    }

    this.productsService.actualizarEstadoUnidadFisica(u.id, u.nuevo_estado!).subscribe({
      next: () => {
        u.estado_gestion = u.nuevo_estado!; 
        
        // Recalculamos la etiqueta de "Disponibles" en tiempo real
        if (estadoAnterior === 'en_stock' && u.nuevo_estado !== 'en_stock') {
          lote.stock_disponible--;
        } else if (estadoAnterior !== 'en_stock' && u.nuevo_estado === 'en_stock') {
          lote.stock_disponible++;
        }

        // ✨ Si es extraviado y tiene precio, actualizamos el stock config en paralelo
        if (u.nuevo_estado === 'extraviado' && lote.propietario && lote.precio_venta !== undefined) {
          this.productsService.actualizarStockIndividual(lote.stock_config_id, { precio_venta: lote.precio_venta }).subscribe();
        }
      },
      error: (err) => {
        console.error("Error al actualizar:", err);
        u.nuevo_estado = u.estado_gestion; // Revierte el select visualmente
      }
    });
  }
}