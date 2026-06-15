export interface CrearVentaPayload {
  variante_id: number;
  talla_id: number;

  precio_venta: number;
  cantidad: number;

  // nombres EXACTOS que espera FastAPI
  fecha: string; // yyyy-mm-dd
  canal: 'wallapop' | 'vinted' | 'web';
  vendedor: 'maikol' | 'paola' | 'yenny';

  comprador?: string;
}
