export interface Product {
  sku: string;
  title: string;
}

export async function loadCatalogue(): Promise<Product[]> {
  const response = await fetch('/api/catalogue');
  return response.ok ? ((await response.json()) as Product[]) : [];
}

export function renderCatalogue(target: HTMLElement, products: Product[]): void {
  target.replaceChildren(
    ...products.map((product) => {
      const item = document.createElement('li');
      item.textContent = product.title;
      return item;
    })
  );
}
