# Web Fragments skill — experiments

Verified mini-apps backing the references. Each is runnable; see the matching reference doc.

- css-vars-isolation/ + measure-css.cjs  -> references/css-and-styling.md
- astro-fragment/ + astro-host/ + measure-astro.cjs -> references/frameworks-astro.md (basic ClientRouter embed)
- astro-fragment/src/pages/[...path].astro + measure-head.cjs -> the #297 head-accumulation repro
- astro-fragment/src/{layouts/SmoothLayout.astro, pages/smooth/[site].astro} + measure-smooth.cjs
  -> smooth transitions WITHOUT ClientRouter (stable head + View Transition API), avoids #297

These are reference experiments, not part of the skill runtime. Node + a chromium from
`@playwright/test` are required to re-run them.
