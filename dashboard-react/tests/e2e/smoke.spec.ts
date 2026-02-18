import { test, expect } from '@playwright/test';

test('health check – backend API is reachable', async ({ request }) => {
  const response = await request.get('http://localhost:8002/health');
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body.status).toBe('healthy');
});

test('dashboard – login page renders', async ({ page }) => {
  await page.goto('http://localhost:3001/login');
  await expect(page).toHaveTitle(/Complyo/i);
});

test('landing – home page renders', async ({ page }) => {
  await page.goto('http://localhost:3003');
  await expect(page).toHaveTitle(/Complyo/i);
});
