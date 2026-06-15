export type EstadoPrenda = 'nuevo' | 'segunda_mano';

export interface Categoria {
  id: number;
  nombre: string;
  parent_id: number | null;
}

export interface AtributoBackend { id?: number; nombre: string; valor: any; }

export interface StockBackend {
  propietario_id: any; donar_ganancias?: boolean;
  id: number; sku: string; cantidad: number; precio_compra: number;
  precio_venta: number; fecha_compra: string; proveedor_id?: number | null;
  proveedor?: { id: number; nombre_proveedor: string };
  etiqueta?: string | null; descuento?: number; publicar_web: boolean;
  publicar_vinted: boolean; publicar_wallapop: boolean; atributos: AtributoBackend[];
  orden?: number; ubicacion: string; localizacion_id?: number | null;
}

// export interface VarianteBackend {
//   id: number; sku: string; identidad_variante: string; hex_identidad: string;
//   descripcion: string; imagenes: string[]; stocks: StockBackend[];
//   orden?: number;
// }

export interface ProductoBackend {
  id: number; nombre: string; descripcion: string; tipo: string;
  estado: EstadoPrenda; publico_objetivo: string; categoria_id: number;
  marca_id: number; variantes: VarianteBackend[]; marca?: Marca; es_vintage?: boolean; epoca?: string | null;
}

export interface StockVariante {
  id?: number; sku: string; atributos: any[]; stock: number; talla?: string | null | any;
  precio_compra: number; precio_venta: number; descuento: number;
  proveedor: string; proveedor_id?: number | null; fecha_compra: string;
  publicar_vinted: boolean; publicar_wallapop: boolean; publicar_web: boolean;
  etiqueta?: string; ubicacion: string; localizacion_id?: number | null; temp_id?: string; id_manual?: number | null; propietario_id?: number | null;
  donar_ganancias?: boolean; estado_gestion?: string;
  unidades?: any[]; mostrarUnidades?: boolean; isDirty?: boolean; cargandoLote?: boolean; 
  cantidad_agregar?: number; 
  fecha_compra_lote_nuevo?: string; // ✨ NUEVO
}

export interface Marca { id?: number; nombre: string; isNew?: boolean; }

export interface Variante {
  id?: number; temp_id: string; identidad_variante: string; hex_identidad: string;
  stocks: StockVariante[]; imagenes: string[]; imagenesFiles: (File | null)[];
  descripcion: string; isDirty?: boolean; cargandoVariante?: boolean; 
}



export interface StockUnitBackend {
  id: number;
  sku: string;
  estado_gestion: string;
  publicar_web: boolean;
  publicar_vinted: boolean;
  publicar_wallapop: boolean;
  activo?: boolean;
  is_dirty?: boolean;
  editandoId?: boolean;
}

export interface StockConfigBackend {
  id: number;
  etiqueta?: string | null;
  ubicacion: string;
  localizacion_id?: number | null;
  precio_compra: number;
  precio_venta: number;
  descuento?: number;
  fecha_compra: string;
  proveedor_id?: number | null;
  propietario_id?: number | null;
  donar_ganancias?: boolean;
  orden?: number;
  atributos: AtributoBackend[];
  // ✨ AQUÍ ESTÁ EL CAMBIO CLAVE: Las unidades físicas
  stock_units: StockUnitBackend[]; 
}

export interface VarianteBackend {
  id: number; 
  sku: string; 
  identidad_variante: string; 
  hex_identidad: string;
  descripcion: string; 
  imagenes: any[]; 
  // ✨ Y AQUÍ EL OTRO CAMBIO CLAVE
  stock_configs: StockConfigBackend[];
  orden?: number;
}








export interface Color {
  hex: string;
  nombre: string;
  claro?: boolean;
}

export const COLORES_PALETA = [
  // Neutros y Básicos
  { hex: '#FFFFFF', nombre: 'Blanco', claro: true },
  { hex: '#000000', nombre: 'Negro' },
  { hex: '#808080', nombre: 'Gris' },
  { hex: '#D3D3D3', nombre: 'Gris Claro', claro: true },
  { hex: '#A9A9A9', nombre: 'Gris Oscuro' },
  { hex: '#F5F5DC', nombre: 'Beige', claro: true },
  { hex: '#FFE4C4', nombre: 'Bisque (Crema)', claro: true },
  { hex: '#D2B48C', nombre: 'Arena / Tan' },

  // Marrones
  { hex: '#8B4513', nombre: 'Marrón' },
  { hex: '#A0522D', nombre: 'Marrón Arcilla' },
  { hex: '#D2691E', nombre: 'Chocolate Claro' },
  { hex: '#654321', nombre: 'Marrón Oscuro' },
  { hex: '#C19A6B', nombre: 'Camel' },
  { hex: '#964B00', nombre: 'Café' },

  // Rojos y Rosas
  { hex: '#FF0000', nombre: 'Rojo' },
  { hex: '#DC143C', nombre: 'Rojo Carmesí' },
  { hex: '#800000', nombre: 'Granate / Burdeos' },
  { hex: '#8B0000', nombre: 'Rojo Vino' },
  { hex: '#FFC0CB', nombre: 'Rosa Pastel', claro: true },
  { hex: '#FF69B4', nombre: 'Fucsia / Rosa Fuerte' },
  { hex: '#FF1493', nombre: 'Rosa Chicle' },
  { hex: '#C71585', nombre: 'Magenta Oscuro' },

  // Naranjas y Amarillos
  { hex: '#FFA500', nombre: 'Naranja' },
  { hex: '#FF8C00', nombre: 'Naranja Oscuro' },
  { hex: '#FF7F50', nombre: 'Coral' },
  { hex: '#E2725B', nombre: 'Terracota' },
  { hex: '#FFFF00', nombre: 'Amarillo', claro: true },
  { hex: '#FFD700', nombre: 'Amarillo Oro', claro: true },
  { hex: '#E1AD01', nombre: 'Mostaza' },
  { hex: '#FFFACD', nombre: 'Amarillo Pastel', claro: true },

  // Verdes
  { hex: '#008000', nombre: 'Verde' },
  { hex: '#006400', nombre: 'Verde Oscuro' },
  { hex: '#556B2F', nombre: 'Verde Oliva' },
  { hex: '#808000', nombre: 'Verde Militar' },
  { hex: '#32CD32', nombre: 'Verde Lima' },
  { hex: '#98FB98', nombre: 'Verde Menta', claro: true },
  { hex: '#2E8B57', nombre: 'Verde Mar' },
  { hex: '#00FF7F', nombre: 'Verde Primavera', claro: true },

  // Azules y Cianes
  { hex: '#0000FF', nombre: 'Azul' },
  { hex: '#000080', nombre: 'Azul Marino' },
  { hex: '#1560BD', nombre: 'Azul Denim' },
  { hex: '#007FFF', nombre: 'Azul Royal' },
  { hex: '#4169E1', nombre: 'Azul Acero' },
  { hex: '#87CEEB', nombre: 'Azul Celeste', claro: true },
  { hex: '#ADD8E6', nombre: 'Azul Claro', claro: true },
  { hex: '#00FFFF', nombre: 'Cian', claro: true },
  { hex: '#40E0D0', nombre: 'Turquesa', claro: true },
  { hex: '#008080', nombre: 'Cerceta (Teal)' },

  // Morados y Violetas
  { hex: '#800080', nombre: 'Morado' },
  { hex: '#4B0082', nombre: 'Indigo' },
  { hex: '#9370DB', nombre: 'Violeta Claro' },
  { hex: '#8A2BE2', nombre: 'Violeta Azulado' },
  { hex: '#DDA0DD', nombre: 'Lila', claro: true },
  { hex: '#E6E6FA', nombre: 'Lavanda', claro: true },

  // Metales Específicos (Joyería)
  { hex: '#FFD700', nombre: 'Dorado', claro: true },
  { hex: '#C0C0C0', nombre: 'Plateado', claro: true },
  { hex: '#B76E79', nombre: 'Oro Rosa' }, 
  { hex: '#B87333', nombre: 'Cobre' },    
  { hex: '#CD7F32', nombre: 'Bronce' },   
  { hex: '#E5E4E2', nombre: 'Platino / Acero', claro: true },

  // Especiales / Patrones
  { hex: 'linear-gradient(45deg, #000 25%, #fff 25%, #fff 50%, #000 50%, #000 75%, #fff 75%, #fff 100%)', nombre: 'Rayas / Patrón', es_patron: true },
  { hex: 'conic-gradient(#ff0000, #ffff00, #00ff00, #00ffff, #0000ff, #ff00ff, #ff0000)', nombre: 'Multicolor', es_patron: true },
  { hex: '#000000', nombre: 'Animal Print', es_patron: true, icon: '🐆' },
  { hex: '#000000', nombre: 'Transparente', es_patron: true, icon: '🫥' }
];