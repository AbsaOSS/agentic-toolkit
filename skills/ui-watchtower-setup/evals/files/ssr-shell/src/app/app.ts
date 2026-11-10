import { Component, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { RouterOutlet } from '@angular/router';

/**
 * The shell composes independently deployed fragments. Each fragment is its
 * own Angular app, served through this shell's origin by a fragment gateway.
 */
@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
  template: `
    <header>Workspace</header>
    <web-fragment fragment-id="cart"></web-fragment>
    <web-fragment fragment-id="catalogue"></web-fragment>
    <router-outlet />
  `
})
export class App {}
