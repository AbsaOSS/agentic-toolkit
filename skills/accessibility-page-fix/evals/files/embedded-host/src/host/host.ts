import { mountCuration } from '../app/mount';

/**
 * Stand-in for the real host's loader: the partner portal embeds each fragment in its own open shadow root and
 * serves it under /host.
 */
class CurationApp extends HTMLElement {
  connectedCallback() {
    const root = this.attachShadow({ mode: 'open' });
    mountCuration(root, { basePath: '/host' });
  }
}
customElements.define('curation-app', CurationApp);
