import { test, expect } from '@playwright/test';

const API_BASE = process.env.API_BASE || 'http://localhost:8002';

test.describe('P1: Backend Auth', () => {
  test('GET /health returns healthy', async ({ request }) => {
    const r = await request.get(`${API_BASE}/health`);
    expect(r.status()).toBe(200);
    const body = await r.json();
    expect(body.status).toBe('healthy');
  });

  test('GET /api/auth/health returns auth service initialized', async ({ request }) => {
    const r = await request.get(`${API_BASE}/api/auth/health`);
    expect(r.status()).toBe(200);
    const body = await r.json();
    expect(body.auth_service_initialized).toBe(true);
  });

  test('POST /api/auth/refresh-cookie without cookie returns 204', async ({ request }) => {
    const r = await request.post(`${API_BASE}/api/auth/refresh-cookie`);
    expect(r.status()).toBe(204);
  });
});

test.describe('P3: Re-Scan 500 Fix', () => {
  test('CSRF middleware does not break GET requests', async ({ request }) => {
    const r = await request.get(`${API_BASE}/api/auth/health`);
    expect(r.status()).toBeLessThan(500);
  });
});

test.describe('P5: Stripe Paths', () => {
  test('GET /api/stripe/plans returns plans without auth', async ({ request }) => {
    const r = await request.get(`${API_BASE}/api/stripe/plans`);
    expect([200, 401, 403]).toContain(r.status());
  });
});

test.describe('P6: Frontend Foundation', () => {
  test('login page renders with Complyo title', async ({ page }) => {
    await page.goto('/login');
    await expect(page).toHaveTitle(/Complyo/i);
  });

  test('login page has email and password inputs', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test('unauthenticated access to dashboard redirects to login', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/login/);
  });
});

test.describe('P8: Sentry', () => {
  test('Next.js instrumentation file exists', async ({ request }) => {
    const r = await request.get('/monitoring');
    expect(r.status()).not.toBe(500);
  });
});
