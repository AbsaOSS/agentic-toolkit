/** The app's shared error page, shown for requests that fail with 401 or 403. */
export function renderError(content: HTMLElement): void {
  content.innerHTML = `
    <div class="page">
      <h1>Something went wrong</h1>
      <p>You may not have access to this page. <a href="/home">Go to the home page</a>.</p>
    </div>`;
}
