import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Component, inject, OnDestroy, OnInit, signal } from '@angular/core';
import { UwtScenario, UwtScenarioTelemetryService } from '@absaoss-cps/ngx-ui-watchtower';
import '../telemetry/telemetry.schema';

interface Customer {
  id: string;
  name: string;
}

@Component({
  selector: 'app-customers',
  template: `
    <input placeholder="Search customers" (input)="search($any($event.target).value)" />
    @if (error()) {
      <p>Could not load customers.</p>
    }
    @for (c of customers(); track c.id) {
      <p>{{ c.name }}</p>
    }
    <button (click)="exportCsv()">Export CSV</button>
  `
})
export class Customers implements OnInit, OnDestroy {
  private readonly http = inject(HttpClient);
  private readonly scenarios = inject(UwtScenarioTelemetryService);
  protected readonly customers = signal<Customer[]>([]);
  protected readonly error = signal(false);
  private loadScenario?: UwtScenario;

  ngOnInit(): void {
    const scenario = this.scenarios.start({ name: 'customers-load', feature: 'customers' });
    this.loadScenario = scenario;
    scenario.step('fetch');
    this.http.get<Customer[]>('/api/customers').subscribe({
      next: (rows) => {
        this.customers.set(rows);
        if (rows.length === 0) {
          scenario.incomplete({ reason: 'no-results' });
          return;
        }
        scenario.complete({ metadata: { count: rows.length } });
      },
      error: (error: HttpErrorResponse) => {
        this.error.set(true);
        scenario.fail({ error, statusCode: error.status });
      }
    });
  }

  ngOnDestroy(): void {
    this.loadScenario?.cancel({ reason: 'component-destroyed' });
  }

  search(query: string): void {
    this.http.get<Customer[]>('/api/customers', { params: { q: query } }).subscribe({
      next: (rows) => this.customers.set(rows),
      error: () => this.error.set(true)
    });
  }

  exportCsv(): void {
    window.location.href = '/api/customers/export?format=csv';
  }
}
