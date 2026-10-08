import { Component, input } from '@angular/core';

@Component({
  selector: 'app-customer-detail',
  template: `<h2>Customer {{ customerId() }}</h2>`
})
export class CustomerDetail {
  readonly customerId = input.required<string>();
}
