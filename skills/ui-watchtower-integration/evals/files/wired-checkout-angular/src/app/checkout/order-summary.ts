import { HttpClient } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-order-summary',
  template: `
    <h2>Order summary</h2>
    @if (error()) {
      <p>Could not place the order.</p>
    }
    <button [disabled]="placing()" (click)="placeOrder()">Place order</button>
  `
})
export class OrderSummary {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  protected readonly placing = signal(false);
  protected readonly error = signal(false);

  placeOrder(): void {
    this.placing.set(true);
    this.error.set(false);
    this.http.post<{ id: string }>('/api/orders', {}).subscribe({
      next: () => void this.router.navigate(['/confirmation']),
      error: () => {
        this.placing.set(false);
        this.error.set(true);
      }
    });
  }
}
