#!/usr/bin/env node
// Reads the JSON reporter output (playwright-report/summary.json) and prints every
// test that carries a 'warning' annotation (pushed by annotateIncomplete() in
// axe-helpers.ts for axe "incomplete" results) - lets you find those without
// opening the HTML report. Run after `npm run test:a11y`.
const fs = require('fs');
const path = require('path');

const reportPath = path.join('playwright-report', 'summary.json');

function* walkSpecs(suites) {
  for (const suite of suites ?? []) {
    yield* suite.specs ?? [];
    yield* walkSpecs(suite.suites);
  }
}

let report;
try {
  report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
} catch {
  console.warn(`Could not read ${reportPath}; run "npm run test:a11y" first.`);
  process.exit(0);
}

let found = 0;
for (const spec of walkSpecs(report.suites)) {
  for (const test of spec.tests ?? []) {
    for (const result of test.results ?? []) {
      const warnings = (result.annotations ?? []).filter((a) => a.type === 'warning');
      if (warnings.length === 0) continue;
      found++;
      console.log(`\n${spec.file} > ${spec.title}`);
      for (const w of warnings) console.log(`  ${w.description}`);
    }
  }
}

if (found === 0) console.log('No incomplete (warning) results found.');
