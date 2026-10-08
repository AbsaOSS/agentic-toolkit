import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'customers' },
  {
    path: 'customers',
    loadComponent: () => import('./customers/customers').then((m) => m.Customers)
  },
  {
    path: 'customers/:customerId',
    loadComponent: () => import('./customers/customer-detail').then((m) => m.CustomerDetail)
  }
];
