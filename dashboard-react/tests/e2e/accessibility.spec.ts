import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('landing page – no critical accessibility violations', async ({ page }) => {
  await page.goto('http://localhost:3003');
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa'])
    .analyze();
  const critical = results.violations.filter(v => v.impact === 'critical');
  expect(critical).toHaveLength(0);
});

test('dashboard login – no critical accessibility violations', async ({ page }) => {
  await page.goto('http://localhost:3001/login');
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa'])
    .analyze();
  const critical = results.violations.filter(v => v.impact === 'critical');
  expect(critical).toHaveLength(0);
});
