import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DashboardService } from '../../core/services/dashboard.service';
import { Chart, registerables } from 'chart.js';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit {
  @ViewChild('canvasGrafica') canvasRef!: ElementRef<HTMLCanvasElement>;
  
  filtros = {
    fecha_inicio: this.getPrimerDiaMes(),
    fecha_fin: this.getFechaHoy()
  };

  // ✨ AÑADIDAS LAS NUEVAS VARIABLES DE CONSIGNACIÓN
  // ✨ AÑADIDAS LAS NUEVAS VARIABLES DE DESGLOSE
  resumen: any = {
    ingresos_totales: 0,
    ingresos_propios: 0,
    ingresos_consignacion: 0,
    gastos_operativos: 0,
    ganancia_real: 0,
    
    // ✨ VARIABLES NUEVAS
    margen_propio: 0,
    margen_consignacion: 0,
    pagos_clientes_periodo: 0,
    
    deuda_generada_periodo: 0,
    deuda_absoluta: 0,
    
    // ✨ DINERO EN TRÁNSITO
    ingresos_retenidos: 0,
    beneficio_retenido: 0,
    deuda_retenida_total: 0,
    
    inversion_en_stock: 0,
    unidades_propias: 0,
    unidades_consignacion: 0,
    saldo_teorico_banco: 0
  };
  
  cargando = true;
  chart: any;

  constructor(private dashboardService: DashboardService) {
    Chart.register(...registerables);
  }

  ngOnInit(): void {
    this.cargarTodo();
  }

  // ==========================================
  // HELPERS DE FECHAS
  // ==========================================
  getFechaHoy(): string {
    return new Date().toISOString().split('T')[0];
  }

  getPrimerDiaMes(): string {
    const d = new Date();
    return new Date(d.getFullYear(), d.getMonth(), 1).toISOString().split('T')[0];
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
      next: (data) => {
        this.resumen = data;
        this.cargando = false;
      },
      error: (err) => {
        console.error("❌ Error al obtener el resumen:", err);
        this.cargando = false;
      }
    });

    this.dashboardService.getDatosGrafica().subscribe({
      next: (datos) => {
        this.inicializarGrafica(datos);
      },
      error: (err) => console.error("❌ Error en datos de gráfica:", err)
    });
  }

  // ==========================================
  // LÓGICA DE LA GRÁFICA
  // ==========================================
  // ==========================================
  // LÓGICA DE LA GRÁFICA
  // ==========================================
  inicializarGrafica(datos: any[]) {
    if (!datos || datos.length === 0) {
      console.warn("⚠️ No hay datos para mostrar en la gráfica");
      return;
    }

    // Un pequeño log para asegurarnos de que el backend está enviando los datos
    console.log("📊 Datos recibidos para la gráfica:", datos);

    setTimeout(() => {
      if (!this.canvasRef) return;

      const canvas = this.canvasRef.nativeElement;
      const ctx = canvas.getContext('2d');

      if (!ctx) return;

      if (this.chart) {
        this.chart.destroy();
      }

      this.chart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: datos.map(d => d.mes),
          datasets: [
            {
              label: 'Ventas Brutas (€)',
              data: datos.map(d => d.ventas),
              backgroundColor: '#007782', // ✨ CORREGIDO: Hexadecimal directo (Tu Teal Vinted)
              borderRadius: 5
            },
            {
              label: 'Gastos Operativos (€)',
              data: datos.map(d => d.gastos),
              backgroundColor: '#e74c3c', // ✨ CORREGIDO: Hexadecimal directo (Rojo)
              borderRadius: 5
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: { duration: 500 },
          plugins: {
            legend: {
              position: 'top',
              labels: {
                usePointStyle: true,
                pointStyle: 'circle'
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              grid: { color: '#f0f2f5' }
            },
            x: {
              grid: { display: false }
            }
          }
        }
      });
      
      this.chart.resize();
    }, 200); 
  }
}