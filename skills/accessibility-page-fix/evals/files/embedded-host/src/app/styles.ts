// The fragment's styles, as text: in the host they go into the shadow root, standalone into the document.
export const FRAGMENT_CSS = `
.curation { font-family: Arial, sans-serif; color: #1f2933; }
.curation__title { font-size: 22px; font-weight: bold; margin: 0 0 16px; }
.filters { display: flex; gap: 8px; margin-bottom: 16px; }
.chip { padding: 4px 12px; border-radius: 12px; background: #fff; border: 1px solid #bcccdc; font-size: 13px; cursor: pointer; }
.chip--active { background: #2680c2; color: #fff; border-color: #2680c2; }
.orders { width: 100%; border-collapse: collapse; background: #fff; }
.orders td, .orders .head { padding: 10px 12px; border-bottom: 1px solid #e4e7eb; font-size: 14px; }
.orders .head { font-weight: bold; color: #829ab1; }
.status { font-size: 12px; padding: 2px 8px; border-radius: 8px; }
.status--new { background: #e3f8ff; color: #47a3f3; }
.status--review { background: #fffbea; color: #f0b429; }
.status--approved { background: #e3f9e5; color: #57ae5b; }
.status--rejected { background: #ffeeee; color: #e66a6a; }
.toggle-note { color: #2680c2; cursor: pointer; font-size: 13px; }
.note { font-size: 13px; color: #627d98; }
.order-link, .help-link { color: #2680c2; }
.help-link { font-size: 13px; font-weight: normal; margin-left: 12px; }
.curation :focus { outline: none; }
`;

// Focus ring for keyboard users. Written for the document, like the rest of the portal's global styles.
export const FOCUS_CSS = `.curation a:focus-visible, .curation [tabindex]:focus-visible { outline: 3px solid #1d4ed8; outline-offset: 2px; }`;
