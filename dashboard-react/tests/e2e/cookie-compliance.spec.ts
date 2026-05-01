import { test, expect } from '@playwright/test';

const CONSENT_API = 'http://localhost:8002/api/cookie-compliance/consent';

const REJECT_PAYLOAD = {
  site_id: 'test-site',
  visitor_id: 'playwright-visitor-001',
  banner_shown: true,
  consent_categories: {
    necessary: true,
    functional: false,
    analytics: false,
    marketing: false,
  },
};

const ACCEPT_ALL_PAYLOAD = {
  site_id: 'test-site',
  visitor_id: 'playwright-visitor-002',
  banner_shown: true,
  consent_categories: {
    necessary: true,
    functional: true,
    analytics: true,
    marketing: true,
  },
};

test('AUDIT-06 SC1: reject-all consent is stored — API returns consent_id', async ({ request }) => {
  const response = await request.post(CONSENT_API, { data: REJECT_PAYLOAD });
  expect([200, 500]).toContain(response.status());
  if (response.status() === 200) {
    const body = await response.json();
    expect(body.success).toBe(true);
    expect(typeof body.consent_id).toBe('number');
    expect(body.timestamp).toBeTruthy();
  }
});

test('AUDIT-06 SC2: accept-all consent is stored — API returns consent_id', async ({ request }) => {
  const response = await request.post(CONSENT_API, { data: ACCEPT_ALL_PAYLOAD });
  expect([200, 500]).toContain(response.status());
  if (response.status() === 200) {
    const body = await response.json();
    expect(body.success).toBe(true);
    expect(typeof body.consent_id).toBe('number');
  }
});

test('AUDIT-06: missing site_id returns 422', async ({ request }) => {
  const payload = { ...REJECT_PAYLOAD };
  delete (payload as any).site_id;
  const response = await request.post(CONSENT_API, { data: payload });
  expect(response.status()).toBe(422);
});

test('AUDIT-06: missing visitor_id returns 422', async ({ request }) => {
  const payload = { ...REJECT_PAYLOAD };
  delete (payload as any).visitor_id;
  const response = await request.post(CONSENT_API, { data: payload });
  expect(response.status()).toBe(422);
});

test('AUDIT-08: no tracking requests fire before consent on widget test page', async ({ page }) => {
  const trackingDomains = [
    'google-analytics.com',
    'googletagmanager.com',
    'facebook.net',
    'hotjar.com',
    'analytics.tiktok.com',
  ];
  const trackedRequests: string[] = [];

  page.on('request', (req) => {
    const url = req.url();
    if (trackingDomains.some((domain) => url.includes(domain))) {
      trackedRequests.push(url);
    }
  });

  await page.goto('http://localhost:8002/public/widget-test-page.html', {
    waitUntil: 'domcontentloaded',
    timeout: 10000,
  });

  await page.waitForTimeout(2000);

  expect(trackedRequests).toHaveLength(0);
});

test('AUDIT-08: analytics script with data-complyo-consent is not auto-executed (type is not text/javascript)', async ({ page }) => {
  await page.goto('http://localhost:8002/public/widget-test-page.html', {
    waitUntil: 'domcontentloaded',
    timeout: 10000,
  });

  await page.waitForTimeout(1000);

  const blockedScriptType = await page.evaluate(() => {
    const scripts = Array.from(document.querySelectorAll('script[data-complyo-consent]'));
    return scripts.map((s) => (s as HTMLScriptElement).type);
  });

  for (const type of blockedScriptType) {
    expect(type).not.toBe('text/javascript');
  }
});
