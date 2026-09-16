import { test as base, expect, type Page, type TestInfo } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

type Violations = Awaited<ReturnType<AxeBuilder['analyze']>>['violations'];
type Incomplete = Awaited<ReturnType<AxeBuilder['analyze']>>['incomplete'];

type AxeFixture = {
  makeAxeBuilder: () => AxeBuilder;
};

/**
 * Shared axe-core fixture. Every accessibility scan builds its AxeBuilder from
 * here so the WCAG 2.2 AA tag set stays identical across the whole suite.
 */
export const test = base.extend<AxeFixture>({
  makeAxeBuilder: async ({ page }, use) => {
    const makeAxeBuilder = () =>
      new AxeBuilder({ page }).withTags([
        'wcag2a',
        'wcag2aa',
        'wcag21a',
        'wcag21aa',
        'wcag22a',
        'wcag22aa',
        'best-practice'
      ]);
    await use(makeAxeBuilder);
  }
});

export function formatViolations(violations: Violations): string {
  if (violations.length === 0) return '';
  return violations
    .map((v) => {
      const nodes = v.nodes
        .map((n) => `    - ${n.html}\n      ${n.failureSummary}`)
        .join('\n');
      return `\n[${v.impact}] ${v.id}: ${v.description}\n  Help: ${v.helpUrl}\n${nodes}`;
    })
    .join('\n');
}

export function expectNoViolations(violations: Violations) {
  expect(violations, formatViolations(violations)).toHaveLength(0);
}

/**
 * Surface axe "incomplete" results (checks axe couldn't confirm without human
 * judgement, e.g. combobox aria-controls patterns) as a non-blocking warning
 * annotation instead of failing the test. Visible in the HTML report and
 * printable via `print-a11y-warnings.js` without opening it.
 */
export function annotateIncomplete(incomplete: Incomplete, testInfo: TestInfo) {
  if (incomplete.length === 0) return;
  testInfo.annotations.push({
    type: 'warning',
    description: incomplete
      .map((r) => `[${r.impact ?? 'unknown'}] ${r.id} (${r.nodes.length} node(s))`)
      .join('; ')
  });
}

/**
 * Wait for all animations/transitions to complete before scanning. Without this,
 * axe may capture intermediate states (e.g. mid-transition background color) and
 * report false-positive color-contrast violations.
 */
export async function waitForAnimationsToFinish(page: Page) {
  await page.evaluate(() =>
    Promise.all(
      document
        .getAnimations()
        .filter((a) => a.effect?.getTiming().iterations !== Infinity)
        .map((a) => a.finished.catch(() => {}))
    )
  );
}
