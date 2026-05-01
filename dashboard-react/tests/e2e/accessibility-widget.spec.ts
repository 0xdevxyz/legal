import { test, expect } from '@playwright/test';

const WIDGET_PAGE = 'http://localhost:8002/public/widget-test-page.html';
const WIDGET_TIMEOUT = 8000;

test.describe('AUDIT-07: Accessibility Widget', () => {
  test('widget toggle button is visible after page load', async ({ page }) => {
    await page.goto(WIDGET_PAGE, { waitUntil: 'domcontentloaded', timeout: WIDGET_TIMEOUT });
    await page.waitForTimeout(2000);
    const toggleBtn = page.locator('.complyo-toggle-btn').first();
    await expect(toggleBtn).toBeVisible({ timeout: 5000 });
  });

  test('clicking toggle button opens the accessibility panel', async ({ page }) => {
    await page.goto(WIDGET_PAGE, { waitUntil: 'domcontentloaded', timeout: WIDGET_TIMEOUT });
    await page.waitForSelector('.complyo-toggle-btn', { timeout: 5000 });
    await page.click('.complyo-toggle-btn');
    const panel = page.locator('.complyo-panel').first();
    await expect(panel).toBeVisible({ timeout: 3000 });
  });

  test('AUDIT-07 SC3: nightMode tile adds complyo-night-mode class to body', async ({ page }) => {
    await page.goto(WIDGET_PAGE, { waitUntil: 'domcontentloaded', timeout: WIDGET_TIMEOUT });
    await page.waitForSelector('.complyo-toggle-btn', { timeout: 5000 });
    await page.click('.complyo-toggle-btn');
    await page.waitForSelector('[data-feature="nightMode"]', { timeout: 3000 });
    await page.click('[data-feature="nightMode"]');
    await page.waitForTimeout(300);

    const hasClass = await page.evaluate(
      () => document.body.classList.contains('complyo-night-mode')
    );
    expect(hasClass).toBe(true);
  });

  test('AUDIT-07 SC3: nightMode preference is persisted to localStorage', async ({ page }) => {
    await page.goto(WIDGET_PAGE, { waitUntil: 'domcontentloaded', timeout: WIDGET_TIMEOUT });
    await page.waitForSelector('.complyo-toggle-btn', { timeout: 5000 });
    await page.click('.complyo-toggle-btn');
    await page.waitForSelector('[data-feature="nightMode"]', { timeout: 3000 });
    await page.click('[data-feature="nightMode"]');
    await page.waitForTimeout(300);

    const prefs = await page.evaluate(() => {
      const raw = localStorage.getItem('complyo_a11y_preferences');
      return raw ? JSON.parse(raw) : null;
    });
    expect(prefs).not.toBeNull();
    expect(prefs.nightMode).toBe(true);
  });

  test('AUDIT-07 SC3: turning off nightMode removes the body class', async ({ page }) => {
    await page.goto(WIDGET_PAGE, { waitUntil: 'domcontentloaded', timeout: WIDGET_TIMEOUT });
    await page.waitForSelector('.complyo-toggle-btn', { timeout: 5000 });
    await page.click('.complyo-toggle-btn');
    await page.waitForSelector('[data-feature="nightMode"]', { timeout: 3000 });
    await page.click('[data-feature="nightMode"]');
    await page.waitForTimeout(200);
    await page.click('[data-feature="nightMode"]');
    await page.waitForTimeout(300);

    const hasClass = await page.evaluate(
      () => document.body.classList.contains('complyo-night-mode')
    );
    expect(hasClass).toBe(false);
  });

  test('AUDIT-07 SC3: highlightLinks tile adds complyo-highlight-links class to body', async ({ page }) => {
    await page.goto(WIDGET_PAGE, { waitUntil: 'domcontentloaded', timeout: WIDGET_TIMEOUT });
    await page.waitForSelector('.complyo-toggle-btn', { timeout: 5000 });
    await page.click('.complyo-toggle-btn');
    await page.waitForSelector('[data-feature="highlightLinks"]', { timeout: 3000 });
    await page.click('[data-feature="highlightLinks"]');
    await page.waitForTimeout(300);

    const hasClass = await page.evaluate(
      () => document.body.classList.contains('complyo-highlight-links')
    );
    expect(hasClass).toBe(true);
  });

  test('AUDIT-07 SC3: localStorage persists multiple preferences independently', async ({ page }) => {
    await page.goto(WIDGET_PAGE, { waitUntil: 'domcontentloaded', timeout: WIDGET_TIMEOUT });
    await page.waitForSelector('.complyo-toggle-btn', { timeout: 5000 });
    await page.click('.complyo-toggle-btn');
    await page.waitForSelector('[data-feature="nightMode"]', { timeout: 3000 });
    await page.click('[data-feature="nightMode"]');
    await page.waitForTimeout(200);
    await page.click('[data-feature="highlightLinks"]');
    await page.waitForTimeout(300);

    const prefs = await page.evaluate(() => {
      const raw = localStorage.getItem('complyo_a11y_preferences');
      return raw ? JSON.parse(raw) : null;
    });
    expect(prefs).not.toBeNull();
    expect(prefs.nightMode).toBe(true);
    expect(prefs.highlightLinks).toBe(true);
  });

  test('AUDIT-07 SC3: preferences are restored after page reload', async ({ page }) => {
    await page.goto(WIDGET_PAGE, { waitUntil: 'domcontentloaded', timeout: WIDGET_TIMEOUT });
    await page.waitForSelector('.complyo-toggle-btn', { timeout: 5000 });
    await page.click('.complyo-toggle-btn');
    await page.waitForSelector('[data-feature="nightMode"]', { timeout: 3000 });
    await page.click('[data-feature="nightMode"]');
    await page.waitForTimeout(300);

    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1500);

    const hasClass = await page.evaluate(
      () => document.body.classList.contains('complyo-night-mode')
    );
    expect(hasClass).toBe(true);
  });
});
