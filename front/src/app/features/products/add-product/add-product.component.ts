import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { DragDropModule, CdkDragDrop, moveItemInArray } from '@angular/cdk/drag-drop';

// SERVICIOS
import { ProductsService } from '../../../core/services/products.service';
import { ClientesService } from '../../../core/services/clientes.service';
import { LocalizacionesService, Localizacion } from '../../../core/services/localizaciones.service';


// COMPONENTES
import { BrandSelectorComponent } from "./components/brand-selector/brand-selector.component";
import { SupplierSelectorComponent, Proveedor } from "./components/supplier-selector/supplier-selector.component";
import { ImageManagerComponent } from "./components/image-manager/image-manager.component";
import { CategorySelectorComponent, CategorySelectionEvent } from "../../../shared/components/selectors/category-selector/category-selector.component";
import { ColorSelectorComponent } from "../../../shared/components/selectors/color-selector/color-selector.component";
import { ClientSelectorComponent } from './components/client-selector/client-selector.component';
import { LocationSelectorComponent } from '../../../shared/components/selectors/location-selector/location-selector.component';

// CONFIGURACIÓN Y TIPADOS
import { 
  COLORES_PALETA, 
  Variante, StockVariante, ProductoBackend, AtributoBackend, Marca, EstadoPrenda, 
  Color
} from './product-form.config';

// UTILIDADES
import { 
  generarTempId, formatLabel, getPlaceholder, determinarTipoBase, 
  MAPEO_IDENTIDAD_POR_TIPO, MAPEO_MATERIAL_A_COLOR, determinarGenero 
} from './product-utils';

@Component({
  selector: 'app-add-product',
  standalone: true,
  imports: [
    CommonModule, FormsModule, DragDropModule,
    ClientSelectorComponent, BrandSelectorComponent, SupplierSelectorComponent, 
    ColorSelectorComponent, CategorySelectorComponent, ImageManagerComponent, LocationSelectorComponent
  ],
  templateUrl: './add-product.component.html',
  styleUrls: ['./add-product.component.css']
})
export class AddProductComponent implements OnInit {

  productoId: number | null = null;
  isEditMode = false;
  cargandoDatos = false;
  isSubmitting = false;
  
  nombre = '';
  descripcion = '';
  listaPublicos = ['Mujer', 'Hombre', 'Unisex', 'Niña', 'Niño', 'Bebé'];
  publicoSeleccionado = '';
  estadoSeleccionado: EstadoPrenda = 'segunda_mano';
  categoriaSeleccionadaFinal: number | null = null;
  marcaSeleccionada: Marca | null = null;
  tipoProductoBase: string = 'ropa_superior';
  
  esVintage: boolean = false;
  epoca: string | null = null;
  
  variantes: Variante[] = [];
  colores = COLORES_PALETA;
  clientesLista: any[] = [];
  plantillaAtributosDinamica: any[] = [];
  fragmentAEnfocar: string | null = null;
  listaLocalizaciones: Localizacion[] = [];

  private configEjes: Record<string, any> = {
    ropa_superior: { tipo: 'color', titulo: 'Estilo / Color', label: 'Color principal' },
    calzado: { tipo: 'color', titulo: 'Estilo / Color', label: 'Color principal' },
    joyeria_anillos: { 
      tipo: 'dropdown', 
      titulo: 'Variante de Metal', 
      label: 'Metal / Material', 
      opciones: ['Oro Amarillo 18K', 'Oro Blanco 18K', 'Oro Rosa 18K', 'Plata de Ley (925)', 'Acero Inoxidable', 'Latón Bañado', 'Cuero'] 
    },
    perfumeria: { tipo: 'texto', titulo: 'Formato', label: 'Capacidad', placeholder: 'Ej: 100ml' }
  };
  private defaultEje = { tipo: 'color', titulo: 'Estilo / Color', label: 'Color principal' };

  constructor(
    private productsService: ProductsService, 
    private router: Router, 
    private route: ActivatedRoute, 
    private clientesService: ClientesService,
    private localizacionesService: LocalizacionesService
  ) {}

  ngOnInit(): void {
    this.cargarLocalizaciones();
    this.route.fragment.subscribe(fragment => {
      if (fragment) {
        this.fragmentAEnfocar = fragment;
      }
    });

    this.route.paramMap.subscribe(params => {
      const id = params.get('id');
      if (id) {
        this.isEditMode = true;
        this.productoId = Number(id);
        this.cargarProductoParaEditar(this.productoId);
      } else {
        this.resetVariantes();
      }
    });
  }

  get ejeVariacion() {
    return this.configEjes[this.tipoProductoBase] || this.defaultEje;
  }

  get mapeoIdentidadPorCategoria(): string {
    return MAPEO_IDENTIDAD_POR_TIPO[this.tipoProductoBase] || 'color';
  }

  cargarLocalizaciones(): void {
    this.localizacionesService.obtenerLocalizaciones().subscribe({
      next: (data) => {
        const flat: Localizacion[] = [];
        const flatten = (nodes: Localizacion[]) => {
          nodes.forEach(n => {
            flat.push(n);
            if (n.hijos && n.hijos.length > 0) {
              flatten(n.hijos);
            }
          });
        };
        flatten(data);
        this.listaLocalizaciones = flat;

        // ✨ PRE-SELECCIONAR "CASA" POR DEFECTO PARA NUEVOS LOTES
        const casa = flat.find(l => l.nombre.toUpperCase() === 'CASA');
        if (casa) {
          this.variantes.forEach(v => {
            v.stocks.forEach(s => {
              if (!s.id && !s.localizacion_id) {
                s.localizacion_id = casa.id;
              }
            });
          });
        }
      }
    });
  }

  cargarProductoParaEditar(id: number) {
    this.cargandoDatos = true;
    this.productsService.obtenerProducto(id).subscribe({
      next: (productoDB: ProductoBackend) => {
        console.log("🚨 DATOS DEL PRODUCTO RECIBIDOS PARA EDICIÓN:", productoDB); // 🕵️‍♂️ ESPÍA: Ver qué llega del backend
        this.nombre = productoDB.nombre;
        this.descripcion = productoDB.descripcion;
        this.estadoSeleccionado = productoDB.estado;
        this.publicoSeleccionado = productoDB.publico_objetivo;
        this.tipoProductoBase = productoDB.tipo;
        this.marcaSeleccionada = productoDB.marca || null;
        this.categoriaSeleccionadaFinal = productoDB.categoria_id;
        this.esVintage = productoDB.es_vintage || false;
        this.epoca = productoDB.epoca || null;

        if (this.categoriaSeleccionadaFinal) {
          this.productsService.obtenerAtributosPorCategoria(this.categoriaSeleccionadaFinal).subscribe({
            next: (atributosDB) => {
              this.plantillaAtributosDinamica = atributosDB; 
              this.procesarVariantesParaEdicion(productoDB.variantes); 
            },
            error: () => {
              this.plantillaAtributosDinamica = [];
              this.procesarVariantesParaEdicion(productoDB.variantes);
            }
          });
        } else {
          this.procesarVariantesParaEdicion(productoDB.variantes);
        }
      }
    });
  }











  



  // ✨ FUNCIÓN PARA INYECTAR UNIDADES DIRECTAS A UN LOTE EXISTENTE
  generarUnidadesEnLote(s: StockVariante | any) {
    const qty = Number(s.cantidad_agregar);
    if (!qty || qty <= 0) return;

    if (s.id) {
      // ✅ EL LOTE EXISTE EN BD: Llamamos al backend para que genere las unidades al instante
      s.cargandoLote = true;
      this.productsService.agregarUnidades(s.id, qty, s.fecha_compra_lote_nuevo).subscribe({
        next: (res: any) => {
          if (res.unidades) {
            // Añadimos las nuevas unidades a la tabla y aseguramos que guarden su id_original
            const nuevasUnidades = res.unidades.map((u: any) => ({ ...u, id_original: u.id, is_dirty: false, editandoId: false }));
            if (!s.unidades) s.unidades = [];
            s.unidades.push(...nuevasUnidades);
          }
          s.cantidad_agregar = 0; // Limpiamos el input
          s.mostrarUnidades = true; // Desplegamos la tabla para que el usuario vea el éxito
          s.cargandoLote = false;
        },
        error: () => { 
          s.cargandoLote = false; 
          alert("❌ Error al generar unidades en el backend."); 
        }
      });
    }
  }







  // enviarUnidadPapelera(grupoStock: StockVariante, idxUnidad: number, stockId: number) {
  //   if(!confirm('¿Seguro que quieres enviar ESTA UNIDAD específica a la papelera?')) return;
  //   this.productsService.moverStockPapelera(stockId).subscribe({
  //     next: () => {
  //       grupoStock.unidades?.splice(idxUnidad, 1);
  //       grupoStock.stock = grupoStock.unidades?.filter((u: any) => u.estado_gestion === 'en_stock').length || 0; 
  //       alert('🗑️ Unidad enviada a la papelera.');
  //     },
  //     error: (err) => alert('❌ No se pudo borrar: ' + (err.error?.detail || ''))
  //   });
  // }

  eliminarStockLocal(idxVariante: number, idxStock: number) {
    const s = this.variantes[idxVariante].stocks[idxStock];
    const msj = s.id 
      ? `¿Estás seguro de que quieres quitar este lote? Ya existe en la base de datos y se marcará como inactivo al guardar.`
      : `¿Seguro que quieres quitar este lote nuevo?`;
    
    if (confirm(msj)) {
      this.variantes[idxVariante].stocks.splice(idxStock, 1);
    }
  }

  private ejecutarScrollInteligente(fragment: string, intentos = 0) {
    setTimeout(() => {
      const elemento = document.getElementById(fragment);
      if (elemento) {
        const yOffset = -100;
        const y = elemento.getBoundingClientRect().top + window.pageYOffset + yOffset;
        window.scrollTo({ top: y, behavior: 'smooth' });
        elemento.scrollIntoView({ behavior: 'smooth', block: 'start' });
        elemento.classList.add('highlight-pulse');
        setTimeout(() => elemento.classList.remove('highlight-pulse'), 2500);
        this.fragmentAEnfocar = null;
      } else if (intentos < 10) {
        this.ejecutarScrollInteligente(fragment, intentos + 1);
      }
    }, 150); 
  }

  private hidratarAtributos(atributosDB: AtributoBackend[]): any[] {
    const molde = this.getAtributosVacios();
    const sinonimosTalla = ['talla', 'numero', 'talla_anillo', 'capacidad_ml'];

    return molde.map(attrForm => {
      const nombreBuscado = attrForm.nombre.toLowerCase();
      const match = atributosDB.find(a => {
        const nombreDB = a.nombre.toLowerCase();
        if (nombreDB === nombreBuscado) return true;
        if (sinonimosTalla.includes(nombreBuscado) && sinonimosTalla.includes(nombreDB)) return true;
        return false;
      });

      if (match) {
        attrForm.valor = match.valor ? String(match.valor).trim() : null;
      }

      if (attrForm.tipo === 'select' && attrForm.valor) {
        const valorGuardado = String(attrForm.valor).toLowerCase().trim();
        const opcionExacta = attrForm.opciones?.find((opt: string) => opt.toLowerCase().trim() === valorGuardado);
        if (opcionExacta) {
          attrForm.valor = opcionExacta;
        }
      }

      return attrForm;
    });
  }

  onBrandChanged(marca: Marca) { 
    if (this.marcaSeleccionada && marca && this.marcaSeleccionada.id === marca.id && this.marcaSeleccionada.nombre === marca.nombre) {
      return;
    }
    this.marcaSeleccionada = marca; 
  }

  onPropietarioChanged(clienteId: number | null | undefined, stock: StockVariante) {
    stock.propietario_id = clienteId;
    if (clienteId) {
      stock.proveedor = ''; // Limpiamos proveedor si ahora tiene dueño
      stock.proveedor_id = null;
    }
  }

  onCategorySelected(event: CategorySelectionEvent): void {
    const esMisma = this.categoriaSeleccionadaFinal === event.categoriaId;
    this.categoriaSeleccionadaFinal = event.categoriaId;

    if (event.categoriaId === null) {
      this.tipoProductoBase = '';
      this.publicoSeleccionado = '';
      this.plantillaAtributosDinamica = []; 
      return;
    }

    const rutaSegura = event.rutaCategorias || [];
    this.tipoProductoBase = determinarTipoBase(rutaSegura); 
    const generoDetectado = determinarGenero(rutaSegura);

    if (generoDetectado && generoDetectado !== 'unisex') {
      this.publicoSeleccionado = this.capitalizar(generoDetectado);
    }

    this.cargandoDatos = true;
    this.productsService.obtenerAtributosPorCategoria(event.categoriaId).subscribe({
      next: (atributosDB) => {
        this.plantillaAtributosDinamica = atributosDB;
        if (!esMisma) {
          this.refrescarAtributosEnVariantes();
        }
        this.cargandoDatos = false;
      },
      error: () => {
        console.error("Error al cargar atributos dinámicos");
        this.cargandoDatos = false;
      }
    });
  }

  private capitalizar(s: string): string {
    if (!s) return '';
    return s.charAt(0).toUpperCase() + s.slice(1);
  }

  onVintageChange(): void {
    if (!this.esVintage) {
      this.epoca = null;
    }
  }

  resetVariantes(): void { this.variantes = [this.nuevaVariante()]; }

  nuevaVariante(): Variante {
    return { 
        temp_id: generarTempId(), hex_identidad: '#FFFFFF', identidad_variante: '', 
        stocks: [this.nuevoStock()], imagenes: [], imagenesFiles: [], descripcion: '',
        isDirty: false, cargandoVariante: false
    };
  }

  nuevoStock(): StockVariante {
    const casa = this.listaLocalizaciones.find(l => l.nombre.toUpperCase() === 'CASA');
    return { 
        id_manual: null, sku: '', atributos: this.getAtributosVacios(), stock: 1, precio_compra: 0, ubicacion: '',
        localizacion_id: casa ? casa.id : null,
        precio_venta: 0, descuento: 0, proveedor: '', proveedor_id: null, 
        fecha_compra: '', publicar_vinted: false, publicar_wallapop: false, publicar_web: false, temp_id: generarTempId(),
        talla: null, propietario_id: null, donar_ganancias: false, estado_gestion: 'en_stock', unidades: [], mostrarUnidades: false,
        isDirty: false, cargandoLote: false, cantidad_agregar: 0,
        fecha_compra_lote_nuevo: new Date().toISOString().split('T')[0] // ✨ DEFAULT TODAY
    };
  }

// Actualiza tu onVariantColorChanged y onVariantDropdownChanged para llamar a marcarVarianteModificada(v)
// Y en el (imagesChanged) de tu HTML de app-image-manager añade: marcarVarianteModificada(v);

  onVariantDrop(event: CdkDragDrop<Variante[]>) { 
    moveItemInArray(this.variantes, event.previousIndex, event.currentIndex); 
    this.variantes.forEach(v => v.isDirty = true); 
  }
  
  onStockDrop(event: CdkDragDrop<StockVariante[]>, variantIndex: number) { 
    moveItemInArray(this.variantes[variantIndex].stocks, event.previousIndex, event.currentIndex); 
    this.variantes[variantIndex].stocks.forEach(s => s.isDirty = true); 
    this.variantes[variantIndex].isDirty = true; // ✨ Marcamos la variante también
  }

// 3. LA FUNCIÓN DE GUARDADO INDIVIDUAL
guardarVarianteIndividual(v: any) {
  if (!this.productoId || !v.id) {
    alert("⚠️ Este estilo es nuevo. Guarda el producto principal primero.");
    return;
  }

  v.cargandoVariante = true;
  const fd = new FormData();
  
  // Datos básicos
  fd.append('identidad_variante', v.identidad_variante || '');
  fd.append('hex_identidad', v.hex_identidad || '#E2E8F0');
  fd.append('descripcion', v.descripcion || '');

  // Mapeamos las imágenes que sobrevivieron (las que ya estaban en el servidor y no borraste)
  const urlsSobrevivientes = v.imagenes.filter((img: string) => img.startsWith('http'));
  fd.append('imagenes_sobrevivientes', JSON.stringify(urlsSobrevivientes));

  // Empaquetamos SOLO los archivos nuevos de esta variante
  v.imagenesFiles.forEach((file: any, idx: number) => {
    if (file !== null) {
      fd.append(`file_NUEVA_${idx}`, file);
    }
  });

  this.productsService.actualizarVarianteIndividual(v.id, fd).subscribe({
    next: (res: any) => {
      // El backend nos devuelve las URLs finales (antiguas + recién subidas a S3)
      v.imagenes = res.imagenes_actualizadas;
      v.imagenesFiles = v.imagenes.map(() => null); // Reseteamos los files pendientes
      v.isDirty = false;
      v.cargandoVariante = false;
    },
    error: () => {
      v.cargandoVariante = false;
      alert("❌ Error al guardar las imágenes y detalles del estilo.");
    }
  });
}


  // 2. Añade este método para que cualquier cambio en un input marque el lote como "Modificado"
  marcarModificado(stock: any) {
    if (stock.id) {
      stock.isDirty = true;
    }
  }

  // 3. Controles del generador de unidades (Spinbox)
  aumentarStock(s: any) {
    s.stock = (s.stock || 0) + 1;
    this.marcarModificado(s);
  }

  disminuirStock(s: any) {
    if (s.stock > 0) {
      s.stock -= 1;
      this.marcarModificado(s);
    }
  }


  // 4. LÓGICA MAESTRA: Guardar Lote Individual
guardarLoteIndividual(variante: Variante, s: any) {
    if (!this.productoId || !variante.id) {
      alert("⚠️ Este estilo o producto es nuevo. Para guardar lotes individuales, primero guarda el producto base usando el botón principal.");
      return;
    }

    // ✨ VALIDACIÓN: El campo de Medida/Talla/Número es obligatorio
    const sinonimosTalla = ['talla', 'numero', 'número', 'talla_anillo', 'capacidad_ml', 'medida'];
    const attrTalla = s.atributos.find((a: any) => sinonimosTalla.includes(a.nombre.toLowerCase()));
    if (!attrTalla || attrTalla.valor === null || attrTalla.valor === undefined || String(attrTalla.valor).trim() === '') {
      const labelTalla = attrTalla ? this.formatLabel(attrTalla.nombre) : 'Talla/Medida';
      alert(`⚠️ El campo "${labelTalla}" es obligatorio.`);
      return;
    }

    const atributosBlindados = s.atributos.filter((a: any) => a.valor !== null && a.valor !== '');
    const payload = {
      cantidad: s.stock || 1,
      precio_compra: s.precio_compra,
      precio_venta: s.precio_venta,
      ubicacion: s.ubicacion,
      proveedor_id: s.proveedor_id,
      proveedor_nombre_nuevo: s.proveedor_nombre_nuevo || s.proveedor,
      fecha_compra: s.fecha_compra_lote_nuevo,
      estado_gestion: s.estado_gestion,
      propietario_id: s.propietario_id,
      donar_ganancias: s.donar_ganancias,
      publicar_web: s.publicar_web,
      publicar_vinted: s.publicar_vinted,
      publicar_wallapop: s.publicar_wallapop,
      atributos: atributosBlindados
    };

    s.cargandoLote = true;

    if (s.id) {
      // 🔁 ACTUALIZAR LOTE EXISTENTE
      this.productsService.actualizarStockIndividual(s.id, payload).subscribe({
        next: () => {
          s.isDirty = false;
          s.cargandoLote = false;
        },
        error: () => { s.cargandoLote = false; alert("❌ Error al actualizar el lote."); }
      });
    } else {
      // ✨ CREAR LOTE NUEVO
      this.productsService.crearStockIndividual(variante.id, payload).subscribe({
        next: (res: any) => {
          s.id = res.stock_id; 
          s.unidades = res.unidades;     // ✨ Asignamos las unidades físicas con sus SKUs reales
          s.mostrarUnidades = true;      // ✨ Abrimos el desplegable automáticamente
          s.isDirty = false;
          s.cargandoLote = false;
        },
        error: () => { s.cargandoLote = false; alert("❌ Error al crear el lote."); }
      });
    }
  }

  agregarVariante(): void { this.variantes.push(this.nuevaVariante()); }
  
  agregarStock(i: number): void { 
    const nuevoStock = this.nuevoStock();
    const variante = this.variantes[i];

    if (variante.stocks.length > 0) {
      const ultimoStock = variante.stocks[variante.stocks.length - 1]; 

      // Rompemos la referencia compartida en memoria usando clonación profunda
      const atributosClonados = JSON.parse(JSON.stringify(ultimoStock.atributos));

      nuevoStock.atributos = atributosClonados.map((nuevoAttr: any) => {
        const ignorar = ['talla', 'numero', 'capacidad_ml', 'talla_anillo', 'cantidad_ml_g', 'talla_guantes'];
        if (ignorar.includes(nuevoAttr.nombre.toLowerCase())) {
          nuevoAttr.valor = null; // Las tallas deben nacer vacías en el nuevo lote
        }
        return nuevoAttr;
      });

      nuevoStock.proveedor = ultimoStock.proveedor || '';
      nuevoStock.proveedor_id = ultimoStock.proveedor_id || null;
      nuevoStock.precio_compra = ultimoStock.precio_compra || 0;
      nuevoStock.precio_venta = ultimoStock.precio_venta || 0;
      nuevoStock.fecha_compra = ultimoStock.fecha_compra || '';
      nuevoStock.propietario_id = ultimoStock.propietario_id || null;
      nuevoStock.donar_ganancias = ultimoStock.donar_ganancias || false;
      nuevoStock.ubicacion = ultimoStock.ubicacion || ''; 
      nuevoStock.estado_gestion = ultimoStock.estado_gestion || 'en_stock';
    }

    variante.stocks.push(nuevoStock); 
  }

  eliminarVariante(index: number): void { 
    const v = this.variantes[index];
    const msj = v.id 
      ? `¿Estás seguro de que quieres eliminar este estilo completo? Ya existe en la base de datos y se marcará como inactivo al guardar.`
      : `¿Seguro que quieres eliminar este estilo nuevo?`;

    if (confirm(msj)) {
      this.variantes.splice(index, 1); 
    }
  }

getAtributosVacios(): any[] {
    let atributosBase: any[] = [];

    // 1. Cargamos lo que el backend nos dio (si hay algo)
    if (this.plantillaAtributosDinamica.length > 0) {
      atributosBase = this.plantillaAtributosDinamica.map(attr => ({ 
        nombre: attr.nombre,
        tipo: attr.tipo,
        opciones: attr.opciones || [],
        valor: null 
      }));
    }

    // 2. ✨ BLINDAJE: Garantizamos que SIEMPRE exista un campo para la Talla o Medida
    // Revisamos si el backend ya nos envió algún sinónimo de talla
    const sinonimosTalla = ['talla', 'numero', 'número', 'talla_anillo', 'capacidad_ml', 'medida'];
    const tieneTalla = atributosBase.some(a => sinonimosTalla.includes(a.nombre.toLowerCase()));
    
    if (!tieneTalla) {
      // Si no viene del backend, lo inyectamos a la fuerza al principio de la lista
      atributosBase.unshift({ 
        nombre: 'talla', 
        tipo: 'text', 
        opciones: [], 
        valor: null 
      });
    }

    // 3. ✨ BLINDAJE: Garantizamos que SIEMPRE exista un campo para el Peso (Necesario para envíos)
    const tienePeso = atributosBase.some(a => a.nombre.toLowerCase() === 'peso_kg');
    if (!tienePeso) {
      atributosBase.push({ 
        nombre: 'peso_kg', 
        tipo: 'number', 
        opciones: [], 
        valor: null 
      });
    }

    return atributosBase;
  }

  private refrescarAtributosEnVariantes(): void {
    const nuevosTemplate = this.getAtributosVacios();
    
    this.variantes.forEach(v => {
      v.stocks.forEach(s => {
        const viejosAtributos = s.atributos || [];
        
        // Mapeamos el nuevo template pero rescatando valores viejos si coinciden en nombre o función (talla)
        s.atributos = nuevosTemplate.map(nt => {
          const ntNombreLower = nt.nombre.toLowerCase();
          const sinonimosTalla = ['talla', 'numero', 'número', 'talla_anillo', 'capacidad_ml', 'medida'];
          const esTallaNT = sinonimosTalla.includes(ntNombreLower);

          const coincidencia = viejosAtributos.find((va: any) => {
            const vaNombreLower = va.nombre.toLowerCase();
            // Coincidencia exacta
            if (vaNombreLower === ntNombreLower) return true;
            // Coincidencia por ser sinónimos de "Talla"
            if (esTallaNT && sinonimosTalla.includes(vaNombreLower)) return true;
            return false;
          });

          return {
            ...nt,
            valor: coincidencia ? coincidencia.valor : null 
          };
        });
        
        // Marcamos como modificado para que el guardado global lo tome en cuenta si cambió algo
        if (s.id) s.isDirty = true;
      });
    });
  }

  onVariantColorChanged(v: Variante, color: Color) {
    v.identidad_variante = color.nombre;
    v.hex_identidad = color.hex;
  }

  onVariantDropdownChanged(v: Variante) {
    if (this.tipoProductoBase.startsWith('joyeria')) {
      const nombreColorAuto = MAPEO_MATERIAL_A_COLOR[v.identidad_variante];
      if (nombreColorAuto) {
        const found = this.colores.find(c => c.nombre === nombreColorAuto);
        v.hex_identidad = found ? found.hex : '#E2E8F0';
      } else {
        v.hex_identidad = '#E2E8F0';
      }
    } else {
      v.hex_identidad = '#E2E8F0';
    }
  }

  // onVariantDrop(event: CdkDragDrop<Variante[]>) { moveItemInArray(this.variantes, event.previousIndex, event.currentIndex); }
  
  // onImageDrop(event: CdkDragDrop<string[]>, variantIndex: number) {
  //   const v = this.variantes[variantIndex];
  //   moveItemInArray(v.imagenes, event.previousIndex, event.currentIndex);
  //   moveItemInArray(v.imagenesFiles, event.previousIndex, event.currentIndex);
  // }
  
  // onStockDrop(event: CdkDragDrop<StockVariante[]>, variantIndex: number) { 
  //   moveItemInArray(this.variantes[variantIndex].stocks, event.previousIndex, event.currentIndex); 
  // }

  // 1. Al seleccionar archivos nuevos
  async onFilesSelected(event: Event, i: number): Promise<void> {
    const files = (event.target as HTMLInputElement).files;
    if (!files) return;

    const filesArray = Array.from(files);
    
    for (const file of filesArray) {
      const base64 = await this.fileToBase64(file);
      this.variantes[i].imagenesFiles = [...this.variantes[i].imagenesFiles, file];
      this.variantes[i].imagenes = [...this.variantes[i].imagenes, base64];
    }
    
    // ✨ DISPARADOR DE CAMBIO AÑADIDO AQUÍ
    this.marcarVarianteModificada(this.variantes[i]); 
    
    (event.target as HTMLInputElement).value = '';
  }

  // 2. Al reordenar las imágenes (drag & drop)
  onImageDrop(event: CdkDragDrop<string[]>, variantIndex: number) {
    const v = this.variantes[variantIndex];
    moveItemInArray(v.imagenes, event.previousIndex, event.currentIndex);
    moveItemInArray(v.imagenesFiles, event.previousIndex, event.currentIndex);
    
    // ✨ DISPARADOR DE CAMBIO AÑADIDO AQUÍ
    this.marcarVarianteModificada(v);
  }

  // 3. (Si usas esta función nativa para eliminar)
  eliminarImagen(i: number, j: number): void {
    this.variantes[i].imagenes.splice(j, 1);
    this.variantes[i].imagenesFiles.splice(j, 1);
    
    // ✨ DISPARADOR DE CAMBIO AÑADIDO AQUÍ
    this.marcarVarianteModificada(this.variantes[i]);
  }
  
  // 4. ✨ Asegúrate de que esta función marque el cambio sin importar si la variante tiene ID o no
  marcarVarianteModificada(v: any) {
    v.isDirty = true;
  }

  private fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target?.result as string);
      reader.onerror = (e) => reject(e);
      reader.readAsDataURL(file);
    });
  }

  // eliminarImagen(i: number, j: number): void {
  //   this.variantes[i].imagenes.splice(j, 1);
  //   this.variantes[i].imagenesFiles.splice(j, 1);
  // }

  productoVaAPublicarse(): boolean {
    return this.variantes.some(v => 
      v.stocks.some(s => s.publicar_web || s.publicar_vinted || s.publicar_wallapop)
    );
  }
  
  varianteVaAPublicarse(v: Variante): boolean {
    return v.stocks.some(s => s.publicar_web || s.publicar_vinted || s.publicar_wallapop);
  }

  private lanzarError(msj: string): boolean {
    alert(msj);
    return false;
  }

  private validarFormulario(): boolean {
    const vaAPublicarGlobal = this.productoVaAPublicarse();

    if (vaAPublicarGlobal && (!this.nombre || !this.nombre.trim())) {
      return this.lanzarError('El nombre del producto es obligatorio para poder publicarlo en la web.');
    }

    if (!this.categoriaSeleccionadaFinal) {
      return this.lanzarError('Selecciona una categoría para continuar.');
    }

    if (!this.marcaSeleccionada) {
      return this.lanzarError('Debes seleccionar una marca (o crear una nueva).');
    }

    if (this.esVintage && !this.epoca) {
      return this.lanzarError('Has indicado que la prenda es Vintage. Por favor, selecciona la Época/Década.');
    }

    for (let i = 0; i < this.variantes.length; i++) {
      const v = this.variantes[i];
      const nV = i + 1;

      if (!v.identidad_variante) {
        return this.lanzarError(`Variante ${nV}: El campo "${this.formatLabel(this.mapeoIdentidadPorCategoria)}" es obligatorio.`);
      }

      if (!v.descripcion || !v.descripcion.trim()) {
        return this.lanzarError(`Variante ${nV}: Debes añadir una descripción específica.`);
      }

      for (let j = 0; j < v.stocks.length; j++) {
        const s = v.stocks[j];
        const nS = j + 1;

        // ✨ NUEVA VALIDACIÓN: Exige que haya ítems en BD o un número mayor a 0 en el input
        const qtyExtra = Number(s.cantidad_agregar) || 0;
        const qtyExistente = s.unidades ? s.unidades.length : 0;
        
        if (qtyExistente === 0 && qtyExtra <= 0) {
          return this.lanzarError(`Var ${nV}, Lote ${nS}: Debes indicar al menos 1 unidad en "Cantidad de unidades físicas".`);
        }

        if (!s.localizacion_id) {
          return this.lanzarError(`Var ${nV}, Lote ${nS}: Indica la localización/lugar de almacenamiento.`);
        }

        if (!s.propietario_id) {
          if (s.precio_compra <= 0) {
            return this.lanzarError(`Var ${nV}, Lote ${nS}: Al ser Inventario Propio (Allsys), el precio de compra debe ser mayor a 0.`);
          }
          if (!s.proveedor_id && !s.proveedor) {
            return this.lanzarError(`Var ${nV}, Lote ${nS}: Al ser Inventario Propio, debes seleccionar o escribir un proveedor.`);
          }
        } else {
          if (s.precio_compra < 0) {
            return this.lanzarError(`Var ${nV}, Lote ${nS}: El precio de compra/depósito no puede ser negativo.`);
          }
          s.proveedor = '';
          s.proveedor_id = null;
        }

        // ✨ NUEVA VALIDACIÓN: El campo de Medida/Talla/Número es obligatorio para el inventario
        const sinonimosTalla = ['talla', 'numero', 'número', 'talla_anillo', 'capacidad_ml', 'medida'];
        const attrTalla = s.atributos.find((a: any) => sinonimosTalla.includes(a.nombre.toLowerCase()));
        if (!attrTalla || attrTalla.valor === null || attrTalla.valor === undefined || String(attrTalla.valor).trim() === '') {
          const labelTalla = attrTalla ? this.formatLabel(attrTalla.nombre) : 'Talla/Medida';
          return this.lanzarError(`Var ${nV}, Lote ${nS}: El campo "${labelTalla}" es obligatorio.`);
        }

        const vaAPublicarEsteStock = s.publicar_web || s.publicar_vinted || s.publicar_wallapop;
        if (vaAPublicarEsteStock) {
          if (!v.imagenes || v.imagenes.length === 0) {
            return this.lanzarError(`Variante ${nV}: Debes subir al menos una foto para poder publicar este artículo.`);
          }
          if (s.precio_venta <= 0) {
            return this.lanzarError(`Var ${nV}, Lote ${nS}: Para publicar, el precio de venta debe ser mayor a 0.`);
          }
          const pesoAttr = s.atributos.find((a: any) => a.nombre === 'peso_kg');
          const pesoValor = pesoAttr ? pesoAttr.valor : null;
          if (pesoValor === null || pesoValor === undefined || Number(pesoValor) <= 0) {
            return this.lanzarError(`Var ${nV}, Lote ${nS}: El peso (kg) es obligatorio para calcular los costos de envío automáticos.`);
          }
        }
      }
    }
    return true;
  }


  

  private crearObjetoFila(grupoBase: any, unidadReal: any, etiqueta: string, atributos: any[]) {
    return { 
        ...grupoBase, 
        id: unidadReal ? unidadReal.id : null,
        id_manual: (unidadReal && unidadReal.id_manual) ? unidadReal.id_manual : null, 
        cantidad: 1, 
        ubicacion: grupoBase.ubicacion,
        etiqueta: etiqueta, 
        atributos: atributos,
        sku: unidadReal ? unidadReal.sku : 'TEMP',
        estado_gestion: unidadReal ? unidadReal.estado_gestion : 'en_stock'
    };
  }

// private construirFormData(): FormData {
//     const fd = new FormData();

//     fd.append('nombre', this.nombre);
//     fd.append('descripcion', this.descripcion);
//     fd.append('tipo', this.tipoProductoBase);
//     fd.append('estado', this.estadoSeleccionado);
//     fd.append('categoria_id', String(this.categoriaSeleccionadaFinal));
//     fd.append('publico_objetivo', this.publicoSeleccionado);
//     fd.append('es_vintage', String(this.esVintage));
    
//     if (this.esVintage && this.epoca) {
//       fd.append('epoca', this.epoca);
//     }

//     if (this.marcaSeleccionada) {
//       if (this.marcaSeleccionada.isNew) {
//         fd.append('marca_nombre', this.marcaSeleccionada.nombre);
//       } else {
//         fd.append('marca_id', String(this.marcaSeleccionada.id));
//       }
//     }

//     const cleanV = this.variantes.map((v, idxV) => {
//       const identidadPadre = v.identidad_variante || 'ÚNICA';
//       let explodedStocks: any[] = []; 

//       v.stocks.forEach((s) => {
//         const attrTallaEditado = s.atributos.find((a: any) => ['talla', 'numero', 'talla_anillo', 'capacidad_ml'].includes(a.nombre.toLowerCase()));
//         const valorFinalTalla = attrTallaEditado?.valor || s.talla || 'UNICA';
//         const etiquetaCompuesta = `${identidadPadre} / ${valorFinalTalla}`.trim().toUpperCase();

//         let atributosBlindados = s.atributos.filter((a: any) => 
//           !['talla', 'numero', 'talla_anillo', 'capacidad_ml'].includes(a.nombre.toLowerCase()) && a.valor !== null && a.valor !== ''
//         );
//         atributosBlindados.push({ nombre: 'talla', valor: valorFinalTalla });

//         // Evaluamos cuántas unidades se van a procesar de forma segura
//         const qtyExtraInput = Number(s.cantidad_agregar) || 0;
//         const unidadesExistentes = s.unidades || [];
        
//         // Si el lote es nuevo (sin ID) y no se han usado botones rápidos, usamos el input numérico directo
//         const totalIteraciones = Math.max(qtyExtraInput, unidadesExistentes.length);
//         let creadasEnMemoria = 0;

//         for (let i = 0; i < totalIteraciones; i++) {
//           const uni = unidadesExistentes[i];

//           // Reconstrucción del objeto de transporte plano (EAV)
//           const filaObjeto = this.crearObjetoFila(s, uni, etiquetaCompuesta, atributosBlindados);
          
//           if (uni) {
//             // Si la unidad ya existía en la BD, preservamos su identidad e indicamos si cambió
//             explodedStocks.push({
//               ...filaObjeto,
//               is_dirty: s.isDirty || uni.is_dirty
//             });
//           } else if (creadasEnMemoria < qtyExtraInput) {
//             // Si son unidades nuevas escritas directamente en el input
//             explodedStocks.push({
//               ...filaObjeto,
//               id: null,
//               sku: 'TEMP',
//               is_dirty: true
//             });
//             creadasEnMemoria++;
//           }
//         }
//       });

//       return {
//         id: v.id || null, 
//         temp_id: v.temp_id, 
//         is_dirty: v.isDirty || !v.id,
//         identidad_variante: identidadPadre, 
//         hex_identidad: v.hex_identidad,
//         descripcion: v.descripcion, 
//         orden: idxV, 
//         stocks: explodedStocks,
//         imagenes: v.imagenes.map((img: any, idxI: number) => v.imagenesFiles[idxI] !== null ? `NUEVA_${idxI}` : img)
//       };
//     });

//     fd.append('variantes', JSON.stringify(cleanV));

//     this.variantes.forEach(v => {
//       v.imagenesFiles.forEach((file: any, idx: number) => {
//         if (file !== null) {
//           fd.append(`file_${v.temp_id}_NUEVA_${idx}`, file);
//         }
//       });
//     });
    
//     return fd;
//   }


















  onSubmit(): void {
    if (!this.validarFormulario()) return;

    // ✨ RESTRICCIÓN GLOBAL: Verificar si hay IDs manuales modificados
    let idsModificados: { original: number, nuevo: number }[] = [];
    this.variantes.forEach(v => {
      v.stocks.forEach(s => {
        s.unidades?.forEach((u: any) => {
          if (u.id_original && u.id && u.id !== u.id_original) {
            idsModificados.push({ original: u.id_original, nuevo: u.id });
          }
        });
      });
    });

    if (idsModificados.length > 0) {
      const listaStr = idsModificados.map(m => `#${m.original} -> #${m.nuevo}`).join(', ');
      const confirmar = confirm(`Has modificado los siguientes IDs de prendas: ${listaStr}. \n\n¿Estás seguro de que quieres aplicar estos cambios de forma global? Esta acción es irreversible.`);
      if (!confirmar) return;
    }

    this.isSubmitting = true;
    const formData = this.construirFormData();

    // ✨ ======================================================== ✨
    // 🕵️‍♂️ LOG DETALLADO DEL FORMDATA (Súper útil para depurar)
    // ✨ ======================================================== ✨
    console.groupCollapsed('🚀 [SUBMIT] DATOS ENVIADOS AL BACKEND');
    
    formData.forEach((value, key) => {
      if (key === 'variantes') {
        // Volvemos a parsear el texto a JSON solo para que la consola lo muestre bonito y expandible
        console.log(`📦 %c${key}:`, 'color: #27ae60; font-weight: bold;', JSON.parse(value as string));
      } else if (value instanceof File) {
        // Si es una foto, mostramos su nombre y cuánto pesa
        console.log(`📎 %c${key}:`, 'color: #e74c3c; font-weight: bold;', `Archivo -> ${value.name} (${(value.size / 1024).toFixed(2)} KB)`);
      } else {
        // Variables normales (nombre, descripción, etc.)
        console.log(`📝 %c${key}:`, 'color: #2980b9; font-weight: bold;', value);
      }
    });
    
    console.groupEnd();
    // ✨ ======================================================== ✨

    const req = (this.isEditMode && this.productoId) 
      ? this.productsService.editarProducto(this.productoId, formData) 
      : this.productsService.crearProducto(formData);

    req.subscribe({
      next: (res: any) => {
        this.isSubmitting = false;
        const idFinal = res?.id || res?.producto_id || this.productoId;
        if (idFinal) {
          this.router.navigate(['/detail-product', idFinal]);
        } else {
          this.router.navigate(['/view-products']); 
        }
      },
      error: (err) => {
        this.isSubmitting = false;
        console.error('❌ Error en el servidor:', err);
        alert('Error al guardar: ' + (err.error?.detail || 'Error desconocido'));
      }
    });
  }

  formatLabel(n: string): string { return formatLabel(n); }
  getPlaceholder(n: string): string { return getPlaceholder(n); }
  
  getHexColor(n: string): string { 
    if (!n) return '#fff';
    const colorGuardado = String(n).toLowerCase().trim();
    return this.colores.find(c => c.nombre.toLowerCase().trim() === colorGuardado)?.hex || '#fff'; 
  }

  moverProductoPapelera(): void {
    if (!this.productoId) return;
    const confirmar = confirm('¿Quieres mover este producto a la papelera?');
    if (confirmar) {
      this.cargandoDatos = true;
      this.productsService.moverProductoPapelera(this.productoId).subscribe({
        next: (res: any) => {
          alert(res.mensaje || '🗑️ Movido a la papelera.');
          this.router.navigate(['/view-products']); 
        },
        error: (err) => {
          this.cargandoDatos = false;
          alert('❌ Error: ' + (err.error?.detail || 'Inténtalo de nuevo.'));
        }
      });
    }
  }











































  // 1. CARGA DESDE EL BACKEND: Adaptamos los nombres que llegan de la BD
  private procesarVariantesParaEdicion(variantesDB: any[]) {
    this.variantes = variantesDB.sort((a: any, b: any) => (a.orden || 0) - (b.orden || 0)).map((vDB: any) => ({
      id: vDB.id,
      temp_id: generarTempId(),
      identidad_variante: vDB.identidad_variante,
      hex_identidad: vDB.hex_identidad,
      descripcion: vDB.descripcion,
      imagenes: vDB.imagenes ? vDB.imagenes.map((img: any) => typeof img === 'string' ? img : img.url) : [],
      imagenesFiles: vDB.imagenes ? vDB.imagenes.map(() => null) : [],
      isDirty: false,
      cargandoVariante: false,
      
      // ✨ LEEMOS 'stock_configs' EN VEZ DE 'stocks' DESDE EL BACKEND
      stocks: (vDB.stock_configs || []).map((loteDB: any) => {
        // ✨ LEEMOS 'stock_units' EN VEZ DE 'unidades'
        const unidadesSeguras = loteDB.stock_units || [];
        const hayDisponibles = unidadesSeguras.some((u: any) => u.estado_gestion === 'en_stock');
        
        return {
          id: loteDB.id, 
          temp_id: generarTempId(),
          stock: unidadesSeguras.filter((u: any) => u.estado_gestion === 'en_stock').length, 
          precio_compra: loteDB.precio_compra,
          precio_venta: loteDB.precio_venta,
          descuento: loteDB.descuento || 0,
          fecha_compra: loteDB.fecha_compra,
          proveedor: loteDB.proveedor?.nombre_proveedor || loteDB.proveedor_nombre || '',
          proveedor_id: loteDB.proveedor_id,
          etiqueta: loteDB.etiqueta || '',
          ubicacion: loteDB.ubicacion || '',
          localizacion_id: (loteDB.localizacion_id || loteDB.localizacion?.id) ? Number(loteDB.localizacion_id || loteDB.localizacion?.id) : null,
          propietario_id: loteDB.propietario_id,
          atributos: this.hidratarAtributos(loteDB.atributos),
          donar_ganancias: loteDB.donar_ganancias || false,
          estado_gestion: hayDisponibles ? 'en_stock' : 'agotado', 
          
          // Guardamos las unidades para pintarlas en la tabla HTML
          unidades: unidadesSeguras.map((u: any) => ({ 
             ...u, 
             id_original: u.id, // ✨ Guardamos el ID original para poder editarlo
             publicar_web: u.publicar_web || false, 
             publicar_vinted: u.publicar_vinted || false, 
             publicar_wallapop: u.publicar_wallapop || false, 
             is_dirty: false,
             editandoId: false
          })), 
          
          mostrarUnidades: false,
          isDirty: false,
          cargandoLote: false,
          cantidad_agregar: 0,
          fecha_compra_lote_nuevo: new Date().toISOString().split('T')[0] // ✨ DEFAULT TODAY
        };
      })
    }));
    
    this.cargandoDatos = false;
    if (this.fragmentAEnfocar) this.ejecutarScrollInteligente(this.fragmentAEnfocar);
  }


  // 2. ACTUALIZAR ESTADO FÍSICO INDIVIDUAL:
  guardarEstadoUnidad(grupoStock: StockVariante, idxUnidad: number, stockUnitId: number, nuevoEstado: string) {
    // ✨ APUNTAMOS AL NUEVO SERVICIO QUE MODIFICA EL STOCK-UNIT
    this.productsService.actualizarEstadoUnidadFisica(stockUnitId, nuevoEstado).subscribe({
      next: () => {
        grupoStock.unidades![idxUnidad].estado_gestion = nuevoEstado;
        const hayDisponibles = grupoStock.unidades!.some((u: any) => u.estado_gestion === 'en_stock');
        grupoStock.estado_gestion = hayDisponibles ? 'en_stock' : nuevoEstado;
        grupoStock.stock = grupoStock.unidades!.filter((u: any) => u.estado_gestion === 'en_stock').length;
        alert('✅ Estado de la unidad actualizado.');
      },
      error: () => alert('❌ Error al actualizar la unidad física.')
    });
  }

  intentarEditarId(u: any) {
    if (u.estado_gestion === 'vendido') {
      alert(`⛔ No puedes editar el ID de la prenda #${u.id_original || u.id} porque ya ha sido vendida. El ID debe permanecer intacto para mantener la integridad del historial de ventas y finanzas.`);
      return;
    }
    u.editandoId = true;
  }

  guardarCambiosUnidad(grupoStock: StockVariante, idxUnidad: number) {
    const unidad = grupoStock.unidades![idxUnidad];
    
    if (!unidad.id || unidad.id <= 0) {
      alert('⚠️ El ID debe ser un número positivo.');
      return;
    }

    // ✨ RESTRICCIÓN: Confirmación si el ID ha cambiado
    if (unidad.id !== unidad.id_original) {
      const confirmar = confirm(`¿Estás seguro de que quieres cambiar el ID de ${unidad.id_original} a ${unidad.id}? Esta es una operación sensible.`);
      if (!confirmar) {
        unidad.id = unidad.id_original; // Revertimos el cambio en el input
        unidad.editandoId = false;
        return;
      }
    }

    const payload = {
      id: unidad.id, // ✨ Nuevo ID (Primary Key)
      sku: unidad.sku,
      estado_gestion: unidad.estado_gestion,
      publicar_web: unidad.publicar_web || false,
      publicar_vinted: unidad.publicar_vinted || false,
      publicar_wallapop: unidad.publicar_wallapop || false,
      fecha_compra: (unidad as any).fecha_compra ? (unidad as any).fecha_compra.split('T')[0] : null
    };

    // Usamos unidad.id_original para localizar el registro en el backend
    this.productsService.actualizarStockUnit(unidad.id_original, payload).subscribe({
      next: (res: any) => {
        unidad.is_dirty = false;
        unidad.editandoId = false; // ✨ Salimos del modo edición
        unidad.id_original = res.id; // Actualizamos el ID original tras el éxito
        unidad.id = res.id;
        
        // Recalcular stock disponible
        const hayDisponibles = grupoStock.unidades!.some((u: any) => u.estado_gestion === 'en_stock');
        grupoStock.estado_gestion = hayDisponibles ? 'en_stock' : unidad.estado_gestion;
        grupoStock.stock = grupoStock.unidades!.filter((u: any) => u.estado_gestion === 'en_stock').length;

        // ✨ Si es extraviado y tiene precio, actualizamos el stock config en paralelo
        if (unidad.estado_gestion === 'extraviado' && grupoStock.propietario_id && grupoStock.precio_venta !== undefined) {
          this.productsService.actualizarStockIndividual(grupoStock.id!, { precio_venta: grupoStock.precio_venta }).subscribe();
        }

        alert('✅ ID y cambios guardados correctamente.');
      },
      error: (err) => {
        console.error('Error al guardar unidad:', err);
        alert('❌ Error: ' + (err.error?.detail || 'No se pudo guardar los cambios.'));
      }
    });
  }

  // 3. ENVIAR A LA PAPELERA LA UNIDAD FÍSICA
  enviarUnidadPapelera(grupoStock: StockVariante, idxUnidad: number, stockUnitId: number) {
    if(!confirm('¿Seguro que quieres enviar ESTA PRENDA específica a la papelera?')) return;
    
    // ✨ APUNTAMOS AL SERVICIO DE STOCK-UNIT
    this.productsService.moverStockUnitPapelera(stockUnitId).subscribe({
      next: () => {
        grupoStock.unidades?.splice(idxUnidad, 1);
        grupoStock.stock = grupoStock.unidades?.filter((u: any) => u.estado_gestion === 'en_stock').length || 0; 
        alert('🗑️ Prenda enviada a la papelera.');
      },
      error: (err) => alert('❌ No se pudo borrar: ' + (err.error?.detail || ''))
    });
  }


  // 4. EL CONSTRUCTOR DEL JSON DE GUARDADO MAESTRO (Vital)
  private construirFormData(): FormData {
    const fd = new FormData();

    fd.append('nombre', this.nombre);
    fd.append('descripcion', this.descripcion);
    fd.append('tipo', this.tipoProductoBase);
    fd.append('estado', this.estadoSeleccionado);
    fd.append('categoria_id', String(this.categoriaSeleccionadaFinal));
    fd.append('publico_objetivo', this.publicoSeleccionado);
    fd.append('es_vintage', String(this.esVintage));
    
    if (this.esVintage && this.epoca) {
      fd.append('epoca', this.epoca);
    }

    if (this.marcaSeleccionada) {
      if (this.marcaSeleccionada.isNew) {
        fd.append('marca_nombre', this.marcaSeleccionada.nombre);
      } else {
        fd.append('marca_id', String(this.marcaSeleccionada.id));
      }
    }

    // ✨ ESTRUCTURA EXACTA PARA FASTAPI
    const cleanV = this.variantes.map((v, idxV) => {
      const identidadPadre = v.identidad_variante || 'ÚNICA';
      let configStocksFormateados: any[] = []; 

      v.stocks.forEach((s, idxS) => {
        const sinonimosTalla = ['talla', 'numero', 'número', 'talla_anillo', 'capacidad_ml', 'medida'];
        const attrTallaEditado = s.atributos.find((a: any) => sinonimosTalla.includes(a.nombre.toLowerCase()));
        const valorFinalTalla = attrTallaEditado?.valor || s.talla || 'UNICA';
        const etiquetaCompuesta = `${identidadPadre} / ${valorFinalTalla}`.trim().toUpperCase();

        // ✨ DINÁMICO: Usamos el nombre que realmente tiene el atributo en esta categoría (talla, numero, etc.)
        const nombreAtributoTalla = attrTallaEditado ? attrTallaEditado.nombre : 'talla';

        let atributosBlindados = s.atributos.filter((a: any) => 
          !sinonimosTalla.includes(a.nombre.toLowerCase()) && a.valor !== null && a.valor !== ''
        );
        atributosBlindados.push({ nombre: nombreAtributoTalla, valor: valorFinalTalla });

        // Extraemos las unidades físicas
        const unidadesSeguras = (s.unidades || []).map((u: any) => ({
            id: u.id || null,
            id_original: u.id_original || u.id || null, // ✨ ENVIAMOS EL ID ORIGINAL PARA QUE EL BACKEND NO SE PIERDA
            estado_gestion: u.estado_gestion || 'en_stock',
            publicar_web: u.publicar_web || false,
            publicar_vinted: u.publicar_vinted || false,
            publicar_wallapop: u.publicar_wallapop || false,
            fecha_compra: (u as any).fecha_compra ? (u as any).fecha_compra.split('T')[0] : null
        }));

        // ✨ EMPAQUETAMOS COMO "StockConfig"
        configStocksFormateados.push({
            id: s.id || null,
            proveedor_id: s.proveedor_id || null,
            proveedor_nombre_nuevo: s.proveedor_id ? null : s.proveedor,
            propietario_id: s.propietario_id || null,
            precio_compra: s.precio_compra,
            precio_venta: s.precio_venta,
            localizacion_id: s.localizacion_id,
            etiqueta: etiquetaCompuesta,
            donar_ganancias: s.donar_ganancias,
            orden: idxS, // ✨ Orden dinámico basado en la posición actual del drag & drop
            atributos: atributosBlindados,
            cantidad_agregar: Number(s.cantidad_agregar) || 0, // Unidades físicas a generar
            fecha_compra_lote_nuevo: (s as any).fecha_compra_lote_nuevo, // Fecha general si generan nuevas
            stock_units: unidadesSeguras // Las que ya existen
        });
      });

      return {
        id: v.id || null, 
        temp_id: v.temp_id, 
        is_dirty: v.isDirty || !v.id,
        identidad_variante: identidadPadre, 
        hex_identidad: v.hex_identidad,
        descripcion: v.descripcion, 
        orden: idxV, 
        // ✨ LA LLAVE MÁGICA QUE ESPERA FASTAPI
        stock_configs: configStocksFormateados, 
        imagenes: v.imagenes.map((img: any, idxI: number) => v.imagenesFiles[idxI] !== null ? `NUEVA_${idxI}` : img)
      };
    });

    fd.append('variantes', JSON.stringify(cleanV));

    this.variantes.forEach(v => {
      v.imagenesFiles.forEach((file: any, idx: number) => {
        if (file !== null) {
          fd.append(`file_${v.temp_id}_NUEVA_${idx}`, file);
        }
      });
    });
    
    return fd;
  }
}