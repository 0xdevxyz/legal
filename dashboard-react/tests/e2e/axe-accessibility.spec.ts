/**
 * AUDIT-23: Axe-Core Accessibility Tests gegen Dashboard-Hauptseiten
 * Schlägt fehl bei WCAG-Violations (critical + serious)
 */
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const DASHBOARD_BASE = process.env.DASHBOARD_URL || 'http://localhost:3001';

const PAGES_TO_TEST = [
  { name: 'Home / Dashboard', path: '/' },
  { name: 'Cookie Compliance', path: '/cookie-compliance' },
  { name: 'Accessibility Statement', path: '/accessibility/statement' },
  { name: 'Alt-Text Review', path: '/accessibility/review' },
  { name: 'CMS Guides', path: '/docs/cms' },
  { name: 'Troubleshooting', path: '/docs/troubleshooting' },
];

for (const { name, path } of PAGES_TO_TEST) {
  test(`AUDIT-23: Keine kritischen WCAG-Verstöße auf "${name}" (${path})`, async ({ page }) => {
    const response = await page.goto(`${DASHBOARD_BASE}${path}`, {
      waitUntil: 'domcontentloaded',
      timeout: 15000,
    });

    if (response && (response.status() === 404 || response.status() === 401)) {
      test.skip(true, `Seite ${path} nicht erreichbar (${response.status()}) — Test übersprungen`);
      return;
    }

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .exclude('[aria-hidden="true"]')
      .analyze();

    const critical = results.violations.filter(
      (v) => v.impact === 'critical' || v.impact === 'serious'
    );

    if (critical.length > 0) {
      const summary = critical.map((v) =>
        `[${v.impact?.toUpperCase()}] ${v.id}: ${v.description} (${v.nodes.length} node(s))`
      ).join('\n');
      expect.soft(critical, `WCAG-Verstöße gefunden auf ${path}:\n${summary}`).toHaveLength(0);
    }

    expect(results.violations.filter((v) => v.impact === 'critical')).toHaveLength(0);
  });
}

test('AUDIT-23: Axe-Core läuft — kein Setup-Fehler', async ({ page }) => {
  await page.goto(`${DASHBOARD_BASE}/`, { waitUntil: 'domcontentloaded', timeout: 10000 });
  const results = await new AxeBuilder({ page }).withTags(['wcag2a']).analyze();
  expect(results).toBeDefined();
  expect(typeof results.violations).toBe('object');
});
