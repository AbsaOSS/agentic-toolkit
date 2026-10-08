import { HttpClient } from '@angular/common/http';
import { Component, inject, OnInit, signal } from '@angular/core';

interface Customer {
  id: string;
  name: string;
}

@Component({
  selector: 'app-customers',
  template: `
    @if (error()) {
      <p>Could not load customers.</p>
    }
    @for (c of customers(); track c.id) {
      <p>{{ c.name }}</p>
    }
    <button (click)="exportCsv()">Export CSV</button>
  `
})
export class Customers implements OnInit {
  private readonly http = inject(HttpClient);
  protected readonly customers = signal<Customer[]>([]);
  protected readonly error = signal(false);

  ngOnInit(): void {
    this.http.get<Customer[]>('/api/customers').subscribe({
      next: (rows) => this.customers.set(rows),
      error: () => this.error.set(true)
    });
  }

  exportCsv(): void {
    window.location.href = '/api/customers/export?format=csv';
  }
}
