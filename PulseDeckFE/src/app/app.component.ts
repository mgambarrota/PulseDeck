import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MetricsService, Metrics } from './metrics.service';
import { Observable, tap } from 'rxjs';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent {
  activeTab = 'overview';
  private cpuHistory: number[] = [];
  private ramHistory: number[] = [];
  cpuSparkline = '';
  ramSparkline = '';
  sampleCount = 0;

  private recordMetrics(metrics: Metrics) {
    this.cpuHistory = [...this.cpuHistory, metrics.cpu.total_percent].slice(-32);
    this.ramHistory = [...this.ramHistory, metrics.memory.ram_percent].slice(-32);
    this.sampleCount = this.cpuHistory.length;
    this.cpuSparkline = this.sparkline(this.cpuHistory);
    this.ramSparkline = this.sparkline(this.ramHistory);
  }

  private sparkline(values: number[]): string {
    return values.map((value, index) =>
      `${index * 240 / 31},${34 - Math.min(100, Math.max(0, value)) * .3}`
    ).join(' ');
  }

  trackCore(_index: number, core: number) { return core; }
  trackProcess(_index: number, process: { pid: number }) { return process.pid; }

  readonly tabs = [
    { id: 'overview', label: 'Panoramica', description: 'Il tuo sistema, a colpo d’occhio.', icon: 'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z' },
    { id: 'cpu', label: 'Processore', description: 'Potenza di calcolo e attività dei core.', icon: 'M7 7h10v10H7z M9 1v4 M15 1v4 M9 19v4 M15 19v4 M1 9h4 M1 15h4 M19 9h4 M19 15h4' },
    { id: 'memory', label: 'Memoria', description: 'Memoria fisica e spazio di swap.', icon: 'M3 6h18v12H3z M7 10v4 M11 10v4 M15 10v4 M6 18v3 M10 18v3 M14 18v3 M18 18v3' },
    { id: 'storage', label: 'Archiviazione', description: 'Spazio disponibile e attività dei dischi.', icon: 'M5 3h14l3 12v6H2v-6z M2 15h20 M6 18h.01 M10 18h.01' },
    { id: 'network', label: 'Rete', description: 'Connessioni e traffico delle interfacce.', icon: 'M4 5h16v6H4z M12 11v5 M4 20v-4h16v4 M2 20h4 M10 20h4 M18 20h4' },
    { id: 'processes', label: 'Processi', description: 'Le applicazioni e le risorse che utilizzano.', icon: 'M8 5h13 M8 12h13 M8 19h13 M3 5h.01 M3 12h.01 M3 19h.01' },
  ];

  get currentTab() { return this.tabs.find(tab => tab.id === this.activeTab)!; }
  metrics$: Observable<Metrics>;
  connectionError$;

  constructor(private svc: MetricsService) {
    this.metrics$ = svc.metrics$.pipe(tap(metrics => this.recordMetrics(metrics)));
    this.connectionError$ = svc.connectionError$;
  }

  setTab(tab: string) { this.activeTab = tab; }

  barColor(pct: number): string {
    if (pct > 80) return 'var(--danger)';
    if (pct > 60) return 'var(--warning)';
    return 'var(--mint)';
  }

  cores(n: number): number[] {
    return Array.from({ length: n }, (_, i) => i);
  }
}
