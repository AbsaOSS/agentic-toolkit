import { loadCatalogue, renderCatalogue } from './catalogue';

const app = document.getElementById('app')!;
app.innerHTML = '<section><h2>Catalogue</h2><ul id="products"></ul></section>';

loadCatalogue().then(
  (products) => renderCatalogue(app.querySelector('#products')!, products),
  () => renderCatalogue(app.querySelector('#products')!, [])
);
