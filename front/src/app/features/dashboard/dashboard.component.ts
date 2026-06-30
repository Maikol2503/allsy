import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DashboardService } from '../../core/services/dashboard.service';
import { VentasService } from '../../core/services/ventas.service';
import { Chart, registerables } from 'chart.js';
import { Router, RouterModule } from '@angular/router';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit {
  @ViewChild('canvasGrafica') canvasRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('canvasIngresos') canvasIngresos!: ElementRef;
  @ViewChild('canvasEgresos') canvasEgresos!: ElementRef;
  @ViewChild('canvasBeneficio') canvasBeneficio!: ElementRef;
  @ViewChild('canvasDeuda') canvasDeuda!: ElementRef;
  @ViewChild('canvasSaldo') canvasSaldo!: ElementRef;
  @ViewChild('canvasInventario') canvasInventario!: ElementRef;
  
  filtros = {
    fecha_inicio: this.getPrimerDiaMes(),
    fecha_fin: this.getFechaHoy()
  };

  resumen: any = {
    ingresos_totales: 0,
    ingresos_propios: 0,
    ingresos_consignacion: 0,
    egresos_operativos: 0,
    ganancia_real: 0,
    
    margen_propio: 0,
    margen_consignacion: 0,
    pagos_clientes_periodo: 0,
    
    deuda_generada_periodo: 0,
    deuda_absoluta: 0,
    
    ingresos_retenidos: 0,
    beneficio_retenido: 0,
    deuda_retenida_total: 0,
    
    inversion_en_stock: 0,
    inversion_historica: 0,
    unidades_propias: 0,
    unidades_consignacion: 0,
    saldo_teorico_banco: 0
  };
  
  cargando = true;
  tieneDatosGrafica = true;
  chart: any;
  chartIngresos: any;
  chartEgresos: any;
  chartBeneficio: any;
  chartDeuda: any;
  chartSaldo: any;
  chartInventario: any;
  ultimasVentas: any[] = [];
  activeInfo: string | null = null;
  
  isDateModalOpen = false;

  constructor(
    private dashboardService: DashboardService,
    private ventasService: VentasService,
    private router: Router
  ) {
    Chart.register(...registerables);
  }

  ngOnInit(): void {
    this.cargarTodo();
  }

  toggleDateModal() {
    this.isDateModalOpen = !this.isDateModalOpen;
  }

  aplicarFiltroFechas() {
    this.isDateModalOpen = false;
    this.cargarTodo();
  }

  private formatDateStr(dateStr: string): string {
    if (!dateStr) return '';
    const parts = dateStr.split('-');
    if (parts.length !== 3) return dateStr;
    const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
    const d = parseInt(parts[2], 10);
    const m = months[parseInt(parts[1], 10) - 1];
    const y = parts[0];
    return `${d} ${m} ${y}`;
  }

  get formattedDateRange(): string {
    const inicio = this.formatDateStr(this.filtros.fecha_inicio);
    const fin = this.formatDateStr(this.filtros.fecha_fin);
    if (inicio === fin) return inicio;
    return `${inicio} - ${fin}`;
  }

  // ==========================================
  // HELPERS DE FECHAS
  // ==========================================
  getFechaHoy(): string {
    const d = new Date();
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  getPrimerDiaMes(): string {
    const d = new Date();
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    return `${year}-${month}-01`;
  }

  setFiltroRapido(periodo: string) {
    const hoy = new Date();
    this.filtros.fecha_fin = this.getFechaHoy();

    if (periodo === 'hoy') {
      this.filtros.fecha_inicio = this.getFechaHoy();
    } else if (periodo === 'mes') {
      this.filtros.fecha_inicio = this.getPrimerDiaMes();
    } else if (periodo === 'año') {
      this.filtros.fecha_inicio = `${hoy.getFullYear()}-01-01`;
    }
    
    this.cargarTodo();
  }

  // ==========================================
  // CARGA DE DATOS
  // ==========================================
  cargarTodo() {
    this.cargando = true;
    
    this.dashboardService.getResumen(this.filtros).subscribe({
      next: (data: any) => {
        this.resumen = data.data || data;
        
        // Cargar gráfica después del resumen para poder inyectar el valor actual
        this.dashboardService.getDatosGrafica(this.filtros).subscribe({
          next: (datos) => {
            this.inicializarGrafica(datos);
            this.cargando = false;
          },
          error: (err) => {
            console.error("❌ Error en datos de gráfica:", err);
            this.cargando = false;
          }
        });
      },
      error: (err) => {
        console.error("❌ Error al obtener el resumen:", err);
        this.cargando = false;
      }
    });

    this.cargarUltimasVentas();
  }

  verDeudores() {
    this.router.navigate(['/clientes'], { queryParams: { conDeuda: 'true' } });
  }

  cargarUltimasVentas() {
    this.ventasService.listarVentas(
      1, 4,
      undefined, undefined,
      undefined,
      undefined, undefined,
      undefined,
      undefined,
      undefined,
      undefined, undefined, undefined,
      undefined, undefined, undefined,
      'creacion',
      false,
      true // include_details
    ).subscribe({
      next: (res: any) => {
        this.ultimasVentas = res.items || res.data || [];
      },
      error: (err) => console.error("Error cargando ventas recientes:", err)
    });
  }

  getVentaTitulo(venta: any): string {
    if (!venta.detalles || venta.detalles.length === 0) return 'Venta sin detalles';
    if (venta.detalles.length === 1) {
      return venta.detalles[0].nombre_producto || venta.detalles[0].stock?.producto?.nombre || 'Prenda';
    } else {
      return `Lote de ${venta.detalles.length} prendas`;
    }
  }

  getVentaImagen(venta: any): string {
    if (!venta.detalles || venta.detalles.length === 0) return '';
    if (venta.detalles.length === 1) {
      return venta.imagen_cover || venta.detalles[0].stock?.producto?.foto_principal || 'https://via.placeholder.com/100?text=Sin+Foto';
    }
    return '';
  }

  toggleInfo(infoId: string) {
    this.activeInfo = this.activeInfo === infoId ? null : infoId;
  }

  getModalText(infoId: string): string {
    const texts: any = {
      'ingresos': 'Suma del dinero ingresado por ventas propias y consignación, incluyendo retenciones de apps.',
      'egresos': 'Gastos de funcionamiento: facturas, reembolsos y sueldos. Se restan de ingresos para calcular el beneficio real.',
      'beneficio': 'Tu ganancia libre total. Suma de márgenes propios y consignación, menos los Egresos Operativos.',
      'deuda-periodo': 'Balance de deuda generada <b>en estos días filtrados</b> frente a los pagos realizados a proveedores.',
      'saldo-banco': 'Efectivo teórico disponible calculando: Ingresos Históricos - Egresos Operativos - Pagos a Consignación - Acumulado Histórico Comprado.',
      'deuda-total': 'Deuda histórica total a quienes te dejaron ropa en consignación (incluye ventas pasadas no pagadas).',
      'inventario': 'Inversión actual solo en <b>Ropa Propia</b> (comprada a mayoristas), ignora prendas de consignación.'
    };
    return texts[infoId] || '';
  }

  // ==========================================
  // LÓGICA DE LA GRÁFICA
  // ==========================================
  inicializarGrafica(datos: any[]) {
    if (!datos || datos.length === 0) {
      this.tieneDatosGrafica = false;
      console.warn("⚠️ No hay datos para mostrar en la gráfica");
      return;
    }
    this.tieneDatosGrafica = true;

    // Un pequeño log para asegurarnos de que el backend está enviando los datos
    console.log("📊 Datos recibidos para la gráfica:", datos);

    setTimeout(() => {
      if (!this.canvasRef) return;

      const canvas = this.canvasRef.nativeElement;
      const ctx = canvas.getContext('2d');

      if (!ctx) return;

      if (this.chart) this.chart.destroy();
      if (this.chartIngresos) this.chartIngresos.destroy();
      if (this.chartEgresos) this.chartEgresos.destroy();
      if (this.chartBeneficio) this.chartBeneficio.destroy();
      if (this.chartDeuda) this.chartDeuda.destroy();
      if (this.chartSaldo) this.chartSaldo.destroy();
      if (this.chartInventario) this.chartInventario.destroy();

      const labels = datos.map(d => d.mes);
      const dataVentas = datos.map(d => d.ventas);
      const dataEgresos = datos.map(d => d.egresos);
      const dataBeneficio = datos.map(d => d.ventas - d.egresos);
      // Asumiremos deuda vacía o cero ya que no viene en la gráfica base
      const dataDeuda = datos.map(d => 0);

      // 1. Gráfica Principal (Tendencia Mensual)
      this.chart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: datos.map(d => d.mes),
          datasets: [
            {
              label: 'Ingresos (€)',
              data: datos.map(d => d.ventas),
              backgroundColor: '#0f172a', // Slate 900 (Dark/Elegant) for Sales
              borderRadius: 6,
              barPercentage: 0.6,
              categoryPercentage: 0.8
            },
            {
              label: 'Gastos (€)',
              data: datos.map(d => d.egresos),
              backgroundColor: '#e2e8f0', // Slate 200 (Soft Gray) for Expenses
              borderRadius: 6,
              barPercentage: 0.6,
              categoryPercentage: 0.8
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: 'index', intersect: false },
          plugins: {
            legend: { 
              position: 'top', 
              align: 'end',
              labels: { usePointStyle: true, boxWidth: 8, font: { family: 'inherit', weight: 'bold' } }
            },
            tooltip: {
              backgroundColor: '#1e293b',
              padding: 12,
              titleFont: { family: 'inherit', size: 13 },
              bodyFont: { family: 'inherit', size: 14, weight: 'bold' },
              cornerRadius: 8,
              displayColors: true,
              boxPadding: 4,
              usePointStyle: true
            }
          },
          scales: {
            y: { 
              beginAtZero: true, 
              border: { display: false },
              grid: { color: '#f1f5f9', drawTicks: false },
              ticks: { font: { family: 'inherit' }, color: '#94a3b8', padding: 10 }
            },
            x: { 
              border: { display: false },
              grid: { display: false },
              ticks: { font: { family: 'inherit', weight: 'bold' }, color: '#64748b', padding: 10 }
            }
          }
        }
      });

      const miniChartOptions: any = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { enabled: false } },
        scales: { x: { display: false }, y: { display: false, suggestedMin: 0, suggestedMax: 0 } },
        elements: { point: { radius: 0 }, line: { tension: 0.4, borderWidth: 2 } },
        layout: { padding: 0 }
      };

      // Para que las mini gráficas apunten al número actual, inyectamos el valor de 'resumen' al final
      const miniLabels = [...labels, 'Actual'];
      const miniVentas = [...dataVentas, this.resumen.ingresos_totales || 0];
      const miniEgresos = [...dataEgresos, this.resumen.egresos_operativos || 0];
      const miniBeneficio = [...dataBeneficio, this.resumen.ganancia_real || 0];
      const miniDeuda = [...dataDeuda, this.resumen.deuda_generada_periodo || 0];
      
      const dataSaldo = datos.map(d => 0);
      const miniSaldo = [...dataSaldo, this.resumen.saldo_teorico_banco || 0];
      const dataInventario = datos.map(d => this.resumen.inversion_en_stock || 0);
      const miniInventario = [...dataInventario, this.resumen.inversion_en_stock || 0];

      // 2. Mini Gráfica Ingresos
      if (this.canvasIngresos) {
        this.chartIngresos = new Chart(this.canvasIngresos.nativeElement.getContext('2d'), {
          type: 'line',
          data: { labels: miniLabels, datasets: [{ data: miniVentas, borderColor: '#0d9488', backgroundColor: 'rgba(13,148,136,0.1)', fill: true }] },
          options: miniChartOptions
        });
      }

      // 3. Mini Gráfica Egresos
      if (this.canvasEgresos) {
        this.chartEgresos = new Chart(this.canvasEgresos.nativeElement.getContext('2d'), {
          type: 'line',
          data: { labels: miniLabels, datasets: [{ data: miniEgresos, borderColor: '#dc2626', backgroundColor: 'rgba(220,38,38,0.1)', fill: true }] },
          options: miniChartOptions
        });
      }

      // 4. Mini Gráfica Beneficio
      if (this.canvasBeneficio) {
        this.chartBeneficio = new Chart(this.canvasBeneficio.nativeElement.getContext('2d'), {
          type: 'line',
          data: { labels: miniLabels, datasets: [{ data: miniBeneficio, borderColor: '#16a34a', backgroundColor: 'rgba(22,163,74,0.1)', fill: true }] },
          options: miniChartOptions
        });
      }

      // 5. Mini Gráfica Deuda
      if (this.canvasDeuda) {
        this.chartDeuda = new Chart(this.canvasDeuda.nativeElement.getContext('2d'), {
          type: 'line',
          data: { labels: miniLabels, datasets: [{ data: miniDeuda, borderColor: '#ea580c', backgroundColor: 'rgba(234,88,12,0.1)', fill: true }] },
          options: miniChartOptions
        });
      }

      // 6. Mini Gráfica Saldo Banco
      if (this.canvasSaldo) {
        this.chartSaldo = new Chart(this.canvasSaldo.nativeElement.getContext('2d'), {
          type: 'line',
          data: { labels: miniLabels, datasets: [{ data: miniSaldo, borderColor: '#2563eb', backgroundColor: 'rgba(37,99,235,0.1)', fill: true }] },
          options: miniChartOptions
        });
      }

      // 7. Mini Gráfica Inventario
      if (this.canvasInventario) {
        this.chartInventario = new Chart(this.canvasInventario.nativeElement.getContext('2d'), {
          type: 'line',
          data: { labels: miniLabels, datasets: [{ data: miniInventario, borderColor: '#4f46e5', backgroundColor: 'rgba(79,70,229,0.1)', fill: true }] },
          options: miniChartOptions
        });
      }
    }, 0);
  }
}