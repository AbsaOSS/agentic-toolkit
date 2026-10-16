import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  standalone: false,
  template: `<app-search /><router-outlet />`
})
export class AppComponent {}
