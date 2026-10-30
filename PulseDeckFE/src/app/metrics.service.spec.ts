import { TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Metrics, MetricsService } from './metrics.service';

describe('MetricsService', () => {
  let service: MetricsService;
  let http: HttpTestingController;
  const snapshot = { timestamp: '2026-01-01T12:00:00' } as Metrics;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(MetricsService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('recovers from an API error on the next polling interval', fakeAsync(() => {
    const received: Metrics[] = [];
    const subscription = service.metrics$.subscribe(value => received.push(value));
    tick(0);
    http.expectOne('/api/metrics').flush('Unavailable', { status: 503, statusText: 'Unavailable' });
    expect(service.connectionError$.value).toContain('503');
    tick(1500);
    http.expectOne('/api/metrics').flush(snapshot);
    expect(received).toEqual([snapshot]);
    expect(service.connectionError$.value).toBeNull();
    subscription.unsubscribe();
  }));

  it('keeps a slow request alive without overlapping requests', fakeAsync(() => {
    const subscription = service.metrics$.subscribe();
    tick(0);
    const request = http.expectOne('/api/metrics');
    tick(3000);
    expect(request.cancelled).toBeFalse();
    http.expectNone('/api/metrics');
    request.flush(snapshot);
    subscription.unsubscribe();
  }));

  it('times out a stalled request and retries', fakeAsync(() => {
    const subscription = service.metrics$.subscribe();
    tick(0);
    const request = http.expectOne('/api/metrics');
    tick(8000);
    expect(request.cancelled).toBeTrue();
    expect(service.connectionError$.value).toContain('scaduta');
    tick(1000);
    http.expectOne('/api/metrics').flush(snapshot);
    expect(service.connectionError$.value).toBeNull();
    subscription.unsubscribe();
  }));
});
