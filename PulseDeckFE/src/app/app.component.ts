import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MetricsService, Metrics } from './metrics.service';
import { Observable } from 'rxjs';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent {
  activeTab = 'overview';
  metrics$: Observable<Metrics>;

  constructor(private svc: MetricsService) {
    this.metrics$ = svc.metrics$;
  }

  setTab(tab: string) { this.activeTab = tab; }

  barColor(pct: number): string {
    if (pct > 80) return '#e74c3c';
    if (pct > 60) return '#f39c12';
    return '#2ecc71';
  }

  cores(n: number): number[] {
    return Array.from({ length: n }, (_, i) => i);
  }
}
