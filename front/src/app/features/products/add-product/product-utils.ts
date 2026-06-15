export function generarTempId(): string {
  return crypto.randomUUID();
}

export function formatLabel(nombre: string): string {
  const diccionario: Record<string, string> = {
    'sisa_a_sisa_cm': 'Sisa a Sisa (cm)',
    'hombros_cm': 'Hombros (cm)',
    'largo_manga_cm': 'Largo de manga (cm)',
    'largo_total_cm': 'Largo Total (cm)',
    'cintura_cm': 'Cintura (cm)',
    'cadera_cm': 'Cadera (cm)',
    'largo_pierna_cm': 'Largo Pierna (cm)',
    'largo_entrepierna_cm': 'Largo Entrepierna (cm)',
    'ancho_bajo_cm': 'Ancho Bajo (cm)',
    'longitud_plantilla_cm': 'Plantilla (cm)',
    'tacon_cm': 'Tacón (cm)',
    'capacidad_ml': 'Capacidad (ml)',
    'talla_anillo': 'Talla de Anillo',
    'cantidad_ml_g': 'Contenido (ml/g)',
    'peso_kg': 'Peso (Kg)'
  };
  return diccionario[nombre] || nombre.replace(/_/g, ' ').toUpperCase();
}

export function getPlaceholder(nombre: string): string {
  if (nombre.includes('_cm')) return '0';
  if (nombre.includes('_ml')) return '100';
  if (nombre.includes('_kg')) return '0.5';
  if (nombre === 'material') return 'Ej: Oro 18k, Algodón...';
  return '...';
}

export function determinarTipoBase(ruta: any[]): string {
  if (!ruta || ruta.length === 0) return 'accesorios';

  const nombresRuta = ruta.map(cat => cat.nombre.toLowerCase());
  const nombreRaiz = nombresRuta[0];

  if (nombreRaiz.includes('calzado')) return 'calzado';
  if (nombreRaiz.includes('bolsos')) return 'bolsos';
  
  if (nombresRuta.some(n => n.includes('anillos') || n.includes('sortijas'))) {
    return 'joyeria_anillos';
  }

  if (nombresRuta.some(n => n.includes('guantes'))) return 'guantes';

  if (nombreRaiz.includes('ropa')) {
    const palabrasInferior = [
      'falda', 'pantalón', 'pantalon', 'vaquero', 'short', 'bermuda', 
      'leggin', 'chino', 'jogger', 'braguita', 'polaina', 'culetine', 
      'calzoncillo', 'slip', 'boxer', 'vestido'
    ];

    const esInferior = nombresRuta.some(nombre => 
      palabrasInferior.some(palabra => nombre.includes(palabra))
    );

    if (esInferior) return 'ropa_inferior';
    return 'ropa_superior';
  }

  return 'accesorios';
}

export function determinarGenero(ruta: any[]): string {
  if (!ruta || ruta.length === 0) return 'unisex';
  
  for (let i = ruta.length - 1; i >= 0; i--) {
    if (ruta[i].genero && ruta[i].genero !== 'null') {
      return ruta[i].genero; 
    }
  }

  return 'unisex';
}

export const MAPEO_IDENTIDAD_POR_TIPO: Record<string, string> = {
    ropa_superior: 'color',
    ropa_inferior: 'color',
    calzado: 'color',
    joyeria_anillos: 'material',
    joyeria_general: 'material',
    perfumeria: 'capacidad_ml',
    accesorios: 'color'
};

export const MAPEO_MATERIAL_A_COLOR: Record<string, string> = {
  'Oro Amarillo 18K': 'Dorado',
  'Oro Blanco 18K': 'Plateado',
  'Oro Rosa 18K': 'Rosa', 
  'Plata de Ley (925)': 'Plateado',
  'Acero Inoxidable': 'Plateado',
  'Latón Bañado': 'Dorado',
  'Cuero': 'Negro', 
  'Aluminio': 'Plateado',
  'Cobre': 'Burdeos' 
};