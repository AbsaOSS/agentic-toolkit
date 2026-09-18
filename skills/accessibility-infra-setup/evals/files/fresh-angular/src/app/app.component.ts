import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  standalone: true,
  template: `
    <main>
      <h1>Welcome to the sample Angular app</h1>
      <p>Accessibility infrastructure smoke test.</p>
    </main>
  `,
})
export class AppComponent {
  title = 'sample-angular-app';
}
