import { HttpClient } from '@angular/common/http';
import { Component, inject, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

interface CartLine {
  sku: string;
  name: string;
  quantity: number;
}

@Component({
  selector: 'app-cart',
  imports: [RouterLink],
  template: `
    @if (error()) {
      <p>Could not load the cart.</p>
    }
    @for (line of lines(); track line.sku) {
      <p>{{ line.quantity }} x {{ line.name }}</p>
    }
    <input placeholder="Coupon code" #code />
    <button (click)="applyCoupon(code.value)">Apply coupon</button>
    @if (couponRejected()) {
      <p>That coupon is not valid.</p>
    }
    <a routerLink="/summary">Continue to order summary</a>
  `
})
export class Cart implements OnInit {
  private readonly http = inject(HttpClient);
  protected readonly lines = signal<CartLine[]>([]);
  protected readonly error = signal(false);
  protected readonly couponRejected = signal(false);

  ngOnInit(): void {
    this.http.get<CartLine[]>('/api/cart').subscribe({
      next: (rows) => this.lines.set(rows),
      error: () => this.error.set(true)
    });
  }

  applyCoupon(code: string): void {
    this.couponRejected.set(false);
    this.http.post<CartLine[]>('/api/cart/coupon', { code }).subscribe({
      next: (rows) => this.lines.set(rows),
      error: () => this.couponRejected.set(true)
    });
  }
}
