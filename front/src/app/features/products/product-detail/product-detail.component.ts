import { Component, OnInit } from '@angular/core';
import { CommonModule, TitleCasePipe } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ProductsService } from '../../../core/services/products.service';

@Component({
  selector: 'app-product-detail',
  imports: [CommonModule, TitleCasePipe, RouterLink],
  templateUrl: './product-detail.component.html',
  styleUrls: ['./product-detail.component.css']
})
export class ProductDetailComponent implements OnInit {

  producto: any = null;
  cargando = true;

  afectadosIds: number[] = [];
  tipoAccion: string | null = null;
  contextoAfectados: any = null;

  constructor(
    private route: ActivatedRoute,
    private productsService: ProductsService,
    private router: Router,
  ) {}

  ngOnInit() {
    const state = history.state;
    if (state && state.ids) {
      this.afectadosIds = state.ids || [];
      this.tipoAccion = state.accion || null;
    }

    const id = Number(this.route.snapshot.paramMap.get('id'));
    if (id) {
      this.productsService.obtenerProducto(id).subscribe({
          next: (data: any) => {
            // ✨ PROCESAMIENTO: Mapeamos StockConfigs a lotes_agrupados para el HTML
            if (data && data.variantes) {
              data.variantes.forEach((v: any) => {
                v.lotes_agrupados = (v.stock_configs || []).map((sc: any) => {
                  const unidades = sc.stock_units || [];
                  const hayStock = unidades.some((u: any) => u.estado_gestion === 'en_stock');
                  
                  return {
                    ...sc,
                    cantidad_agrupada: unidades.length,
                    ids_incluidos: unidades.map((u: any) => u.id),
                    sku: unidades.length > 0 ? unidades[0].sku : 'N/A', // Usamos el primer SKU como referencia
                    estado_gestion: hayStock ? 'en_stock' : (unidades.length > 0 ? unidades[0].estado_gestion : 'agotado'),
                    // Canales: true si al menos una unidad lo tiene
                    publicar_web: unidades.some((u: any) => u.publicar_web),
                    publicar_vinted: unidades.some((u: any) => u.publicar_vinted),
                    publicar_wallapop: unidades.some((u: any) => u.publicar_wallapop)
                  };
                });
              });
            }

            this.producto = data; 
            this.extraerContextoAfectados();
            this.cargando = false;
          },
          error: (err) => {
            console.error('Error al cargar producto:', err);
            this.cargando = false;
          }
        });
    } else {
      this.cargando = false;
    }
  }

  extraerContextoAfectados() {
    if (!this.afectadosIds.length || !this.producto) return;

    const primerId = this.afectadosIds[0];

    for (const v of this.producto.variantes) {
      if (!v.lotes_agrupados) continue;
      for (const lote of v.lotes_agrupados) {
        if (lote.ids_incluidos.includes(primerId)) {
          this.contextoAfectados = {
            color: v.identidad_variante,
            talla: lote.etiqueta
          };
          return; 
        }
      }
    }
  }

  editarProducto(id: number) {
    this.router.navigate(['/edit', id]);
  }
  
  loteTieneAfectados(idsDelLote: number[]): boolean {
    if (!this.afectadosIds || this.afectadosIds.length === 0) return false;
    return idsDelLote.some(idFisico => this.afectadosIds.includes(Number(idFisico)));
  }

  verImagen(imagen: string) {
    window.open(imagen, '_blank');
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
}