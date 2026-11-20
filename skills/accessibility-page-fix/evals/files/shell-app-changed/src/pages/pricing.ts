export function renderPricing(content: HTMLElement): void {
  const plans = [
    ['Starter', 'Free', 'For one person trying things out.'],
    ['Team', '$12 per user', 'Shared projects and reports.'],
    ['Enterprise', 'Contact us', 'Single sign-on and audit logs.'],
  ];
  content.innerHTML = `
    <div class="page">
      <div class="hero">
        <div class="hero__title">Plans for every team</div>
        <p class="hero__text">Start free and upgrade when your team grows. Every plan includes unlimited projects and reports.</p>
      </div>
      <div class="plans">
        ${plans.map(([name, price, text]) => `<div class="plan"><div class="page__title">${name}</div><div class="plan__price">${price}</div><div>${text}</div><button class="uk-btn uk-btn--outline" type="button">Choose ${name}</button></div>`).join('')}
      </div>
    </div>`;
}
