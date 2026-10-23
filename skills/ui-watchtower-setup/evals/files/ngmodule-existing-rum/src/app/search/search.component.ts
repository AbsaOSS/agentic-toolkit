import { Component } from '@angular/core';
import { RumService } from '../services/rum.service';

@Component({
  selector: 'app-search',
  standalone: false,
  template: `<input (input)="onInput($any($event.target).value)" placeholder="Instrument" />`
})
export class SearchComponent {
  constructor(private readonly rum: RumService) {}

  onInput(value: string): void {
    this.rum.trackSearch(value);
  }
}
