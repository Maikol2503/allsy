import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { StatisticsService } from '../../core/services/statistics.service';
import { Chart, registerables } from 'chart.js';

@Component({
  selector: 'app-statistics',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './statistics.component.html',
  styleUrls: ['./statistics.component.css']
})
export class StatisticsComponent implements OnInit {
  @ViewChild('vendedoresCanvas') vCanvas!: ElementRef;
  @ViewChild('canalesCanvas') cCanvas!: ElementRef;

  fechaInicio: string = new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0];
  fechaFin: string = new Date().toISOString().split('T')[0];
  
  // ✨ NUEVAS PESTAÑAS SEPARADAS
  activeTab: 'propias' | 'consignacion' | 'inversion' | 'proveedores' = 'propias';

  stats: any = null;             
  statsInversion: any = null;    
  statsProveedores: any = null;  
  
  cargando = true;
  private charts: any[] = [];

  constructor(private statsService: StatisticsService) {
    Chart.register(...registerables);
  }

  ngOnInit() { 
    this.cargarDatos(); 
  }

  cambiarPestana(tab: 'propias' | 'consignacion' | 'inversion' | 'proveedores') {
    this.activeTab = tab;
    
    // Si saltamos entre Propias y Consignación, no recargamos el backend, solo redibujamos las gráficas
    if ((tab === 'propias' || tab === 'consignacion') && this.stats) {
      this.inicializarGraficas();
      return;
    }
    
    this.cargarDatos();
  }

  cargarDatos() {
    this.cargando = true;
    
    // --- PESTAÑAS 1 y 2: Inteligencia de Ventas ---
    if (this.activeTab === 'propias' || this.activeTab === 'consignacion') {
      this.statsInversion = null; 
      this.statsProveedores = null; 
      
      this.statsService.obtenerEstadisticas(this.fechaInicio, this.fechaFin).subscribe({
        next: (data) => {
          this.stats = data;
          this.cargando = false;
          this.inicializarGraficas();
        },
        error: (err) => {
          console.error("Error cargando finanzas:", err);
          this.cargando = false;
        }
      });
    } 
    
    // --- PESTAÑA 3: Rendimiento de Compras ---
    else if (this.activeTab === 'inversion') {
      this.stats = null; 
      this.statsProveedores = null; 
      
      this.statsService.obtenerRendimientoCompras(this.fechaInicio, this.fechaFin).subscribe({
        next: (data) => {
          this.statsInversion = data.analisis_inversion;
          this.cargando = false;
        },
        error: (err) => {
          console.error("Error cargando inversiones:", err);
          this.cargando = false;
        }
      });
    }

    // --- PESTAÑA 4: Análisis de Proveedores ---
    else if (this.activeTab === 'proveedores') {
      this.stats = null; 
      this.statsInversion = null; 
      
      this.statsService.obtenerRendimientoProveedores(this.fechaInicio, this.fechaFin).subscribe({
        next: (data) => {
          this.statsProveedores = data.ranking_proveedores;
          this.cargando = false;
        },
        error: (err) => {
          console.error("Error cargando proveedores:", err);
          this.cargando = false;
        }
      });
    }
  }

  inicializarGraficas() {
    if ((this.activeTab !== 'propias' && this.activeTab !== 'consignacion') || !this.stats) return;

    const dataTab = this.stats[this.activeTab];

    setTimeout(() => {
      this.charts.forEach(c => c.destroy());
      this.charts = [];

      if (!this.vCanvas || !this.cCanvas) return;

      const vChart = new Chart(this.vCanvas.nativeElement, {
        type: 'bar',
        data: {
          labels: dataTab.vendedores.map((v: any) => v.nombre),
          datasets: [{
            label: 'Ventas €',
            data: dataTab.vendedores.map((v: any) => v.total),
            backgroundColor: '#007782'
          }]
        },
        options: { responsive: true, maintainAspectRatio: false }
      });

      const cChart = new Chart(this.cCanvas.nativeElement, {
        type: 'doughnut',
        data: {
          labels: dataTab.canales.map((c: any) => c.nombre),
          datasets: [{
            data: dataTab.canales.map((c: any) => c.total),
            backgroundColor: ['#007782', '#27ae60', '#e74c3c', '#f1c40f']
          }]
        },
        options: { responsive: true, maintainAspectRatio: false }
      });

      this.charts.push(vChart, cChart);
    }, 300);
  }
}