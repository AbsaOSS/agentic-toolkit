import {
  test,
  expectNoViolations,
  annotateIncomplete,
  waitForAnimationsToFinish
} from '../fixtures/axe-helpers';

// Dummy example scan proving the infrastructure works end to end. Uses static,
// known-compliant HTML rather than a real app route, so it stays green regardless
// of whether the app itself is WCAG-compliant yet - fixing app violations is out
// of scope here. Add real per-page scans in dedicated *.accessibility.spec.ts files.
const COMPLIANT_HTML = `<!DOCTYPE html>
<html lang="en">
  <head><title>Accessibility smoke test</title></head>
  <body>
    <header><h1>Accessibility smoke test</h1></header>
    <main>
      <p>This page exists only to prove the axe-core + Playwright plumbing works.</p>
    </main>
  </body>
</html>`;

test.describe('Accessibility - example scan', () => {
  test('dummy page has no WCAG 2.2 AA violations', async ({ page, makeAxeBuilder }, testInfo) => {
    await page.setContent(COMPLIANT_HTML);
    await waitForAnimationsToFinish(page);

    const results = await makeAxeBuilder().analyze();

    await testInfo.attach('dummy-accessibility-scan', {
      body: JSON.stringify(results, null, 2),
      contentType: 'application/json'
    });

    // "incomplete" results need human judgement - report, don't fail the build.
    annotateIncomplete(results.incomplete, testInfo);
    expectNoViolations(results.violations);
  });
});
