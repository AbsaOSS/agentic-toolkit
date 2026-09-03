import {
  test,
  expectNoViolations,
  waitForAnimationsToFinish
} from '../fixtures/axe-helpers';

// Dummy example scan proving the infrastructure works end to end.
// Replace the route and add real scans in dedicated *.accessibility.spec.ts files.
// The "accessibility" in the filename routes this spec to the accessibility project.
test.describe('Accessibility - example scan', () => {
  test('home route has no WCAG 2.2 AA violations', async ({
    page,
    makeAxeBuilder
  }, testInfo) => {
    await page.goto('/');
    await waitForAnimationsToFinish(page);

    const results = await makeAxeBuilder().analyze();

    await testInfo.attach('home-accessibility-scan', {
      body: JSON.stringify(results, null, 2),
      contentType: 'application/json'
    });

    expectNoViolations(results.violations);
  });
});
