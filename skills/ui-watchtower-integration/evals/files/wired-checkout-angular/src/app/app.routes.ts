import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'cart' },
  { path: 'cart', loadComponent: () => import('./checkout/cart').then((m) => m.Cart) },
  {
    path: 'summary',
    loadComponent: () => import('./checkout/order-summary').then((m) => m.OrderSummary)
  },
  {
    path: 'confirmation',
    loadComponent: () => import('./checkout/order-confirmation').then((m) => m.OrderConfirmation)
  }
];
