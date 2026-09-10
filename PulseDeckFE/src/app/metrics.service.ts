import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, timer, EMPTY } from 'rxjs';
import { switchMap, shareReplay, catchError } from 'rxjs/operators';

export interface Metrics {
  timestamp: string;
  system: System;
  cpu: Cpu;
  memory: Memory;
  storage: Storage;
  network: Network;
  processes: Process[];
}

export interface System {
  hostname: string; os: string; arch: string;
  boot_time: string; uptime: string; user: string;
}

export interface Cpu {
  model: string; physical_cores: number; logical_cores: number; arch: string;
  freq_current: string; freq_min: string; freq_max: string;
  total_percent: number; per_core: number[];
  ctx_switches: number; interrupts: number; soft_interrupts: number;
  times_user: number; times_system: number; times_idle: number;
  times_interrupt: number; times_dpc: number;
  load_1: number | null; load_5: number | null; load_15: number | null;
  process_count: number; thread_count: number;
}

export interface Memory {
  ram_total: string; ram_used: string; ram_free: string; ram_available: string; ram_percent: number;
  swap_total: string; swap_used: string; swap_free: string; swap_percent: number;
  swap_in: string; swap_out: string;
}

export interface Storage {
  read_speed: string; write_speed: string; read_total: string; write_total: string;
  partitions: Partition[];
}

export interface Partition {
  device: string; mountpoint: string; fstype: string; opts: string;
  total: string; used: string; free: string; percent: number;
}

export interface Network {
  upload_speed: string; download_speed: string;
  sent_total: string; recv_total: string;
  packets_sent: number; packets_recv: number;
  err_in: number; err_out: number; drop_in: number; drop_out: number;
  interfaces: NetInterface[];
}

export interface NetInterface {
  name: string; ipv4: string; ipv6: string; mac: string;
  status: string; speed: string; mtu: string;
}

export interface Process {
  pid: number; name: string; status: string;
  cpu_percent: number; ram: string; threads: number; user: string;
}

@Injectable({ providedIn: 'root' })
export class MetricsService {
  private readonly url = 'http://localhost:8001/api/metrics';

  metrics$: Observable<Metrics> = timer(0, 1500).pipe(
    switchMap(() => this.http.get<Metrics>(this.url).pipe(
      catchError(() => EMPTY)
    )),
    shareReplay(1)
  );

  constructor(private http: HttpClient) { }
}
