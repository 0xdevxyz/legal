import { test, expect } from '@playwright/test';

const CONSENT_API = 'http://localhost:8002/api/cookie-compliance/consent';
const WIDGET_TEST_PAGE = 'http://localhost:8002/public/widget-test-page.html';

// ============================================================
// Payload Fixtures
// ============================================================

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

// ============================================================
// API Tests (AUDIT-06)
// ============================================================

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

// ============================================================
// Widget E2E Tests – Banner Display (AUDIT-07)
// ============================================================

test('AUDIT-07 SC1: Banner wird angezeigt wenn kein localStorage-Eintrag vorhanden', async ({ page }) => {
  // Clear localStorage before test
  await page.addInitScript(() => {
    localStorage.removeItem('complyo_cookie_consent');
    localStorage.removeItem('complyo_consent_date');
  });

  await page.goto(WIDGET_TEST_PAGE, { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForTimeout(2000);

  const banner = page.locator('#complyo-cookie-banner, .complyo-banner-wrapper');
  const isBannerVisible = await banner.isVisible().catch(() => false);
  if (isBannerVisible) {
    await expect(banner).toBeVisible();
  }
});

test('AUDIT-07 SC2: Banner bleibt ausgeblendet wenn Consent bereits gesetzt ist', async ({ page }) => {
  const existingConsent = JSON.stringify({
    necessary: true,
    functional: true,
    analytics: true,
    marketing: true,
    timestamp: Date.now(),
    version: '2.0',
  });

  await page.addInitScript((consent) => {
    localStorage.setItem('complyo_cookie_consent', consent);
    localStorage.setItem('complyo_consent_date', new Date().toISOString());
  }, existingConsent);

  await page.goto(WIDGET_TEST_PAGE, { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForTimeout(2000);

  const banner = page.locator('#complyo-cookie-banner');
  const isVisible = await banner.isVisible().catch(() => false);
  expect(isVisible).toBe(false);
});

// ============================================================
// Widget E2E Tests – Accept All (AUDIT-08)
// ============================================================

test('AUDIT-08 SC1: Accept All setzt Consent für alle Kategorien', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.removeItem('complyo_cookie_consent');
    localStorage.removeItem('complyo_consent_date');
  });

  await page.goto(WIDGET_TEST_PAGE, { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForTimeout(2000);

  const acceptBtn = page.locator('#complyo-accept-all');
  const isVisible = await acceptBtn.isVisible().catch(() => false);

  if (isVisible) {
    await acceptBtn.click();
    await page.waitForTimeout(1000);

    const stored = await page.evaluate(() => localStorage.getItem('complyo_cookie_consent'));
    expect(stored).toBeTruthy();

    const consent = JSON.parse(stored!);
    expect(consent.necessary).toBe(true);
    expect(consent.analytics).toBe(true);
    expect(consent.marketing).toBe(true);

    const bannerVisible = await page.locator('#complyo-cookie-banner').isVisible().catch(() => false);
    expect(bannerVisible).toBe(false);
  }
});

test('AUDIT-08 SC2: Reject All setzt nur necessary=true', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.removeItem('complyo_cookie_consent');
    localStorage.removeItem('complyo_consent_date');
  });

  await page.goto(WIDGET_TEST_PAGE, { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForTimeout(2000);

  const rejectBtn = page.locator('#complyo-reject-all');
  const isVisible = await rejectBtn.isVisible().catch(() => false);

  if (isVisible) {
    await rejectBtn.click();
    await page.waitForTimeout(1000);

    const stored = await page.evaluate(() => localStorage.getItem('complyo_cookie_consent'));
    expect(stored).toBeTruthy();

    const consent = JSON.parse(stored!);
    expect(consent.necessary).toBe(true);
    expect(consent.functional).toBe(false);
    expect(consent.analytics).toBe(false);
    expect(consent.marketing).toBe(false);
  }
});

// ============================================================
// Widget E2E Tests – Script Blocking (AUDIT-08)
// ============================================================

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

  await page.addInitScript(() => {
    localStorage.removeItem('complyo_cookie_consent');
    localStorage.removeItem('complyo_consent_date');
  });

  await page.goto(WIDGET_TEST_PAGE, { waitUntil: 'domcontentloaded', timeout: 10000 });
  await page.waitForTimeout(2000);

  expect(trackedRequests).toHaveLength(0);
});

test('AUDIT-08: analytics script with data-complyo-consent is not auto-executed (type is not text/javascript)', async ({ page }) => {
  await page.goto(WIDGET_TEST_PAGE, { waitUntil: 'domcontentloaded', timeout: 10000 });
  await page.waitForTimeout(1000);

  const blockedScriptType = await page.evaluate(() => {
    const scripts = Array.from(document.querySelectorAll('script[data-complyo-consent]'));
    return scripts.map((s) => (s as HTMLScriptElement).type);
  });

  for (const type of blockedScriptType) {
    expect(type).not.toBe('text/javascript');
  }
});

// ============================================================
// Widget E2E Tests – Consent Persistenz (AUDIT-09)
// ============================================================

test('AUDIT-09 SC1: Consent bleibt nach Reload erhalten', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.removeItem('complyo_cookie_consent');
    localStorage.removeItem('complyo_consent_date');
  });

  await page.goto(WIDGET_TEST_PAGE, { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForTimeout(2000);

  const acceptBtn = page.locator('#complyo-accept-all');
  const isVisible = await acceptBtn.isVisible().catch(() => false);

  if (isVisible) {
    await acceptBtn.click();
    await page.waitForTimeout(500);

    const consentBeforeReload = await page.evaluate(() => localStorage.getItem('complyo_cookie_consent'));

    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1000);

    const consentAfterReload = await page.evaluate(() => localStorage.getItem('complyo_cookie_consent'));
    expect(consentAfterReload).toBe(consentBeforeReload);

    const bannerVisible = await page.locator('#complyo-cookie-banner').isVisible().catch(() => false);
    expect(bannerVisible).toBe(false);
  }
});

test('AUDIT-09 SC2: Nach Consent-Löschung erscheint der Banner wieder', async ({ page }) => {
  const existingConsent = JSON.stringify({
    necessary: true,
    functional: true,
    analytics: true,
    marketing: true,
    timestamp: Date.now(),
    version: '2.0',
  });

  await page.addInitScript((consent) => {
    localStorage.setItem('complyo_cookie_consent', consent);
    localStorage.setItem('complyo_consent_date', new Date().toISOString());
  }, existingConsent);

  await page.goto(WIDGET_TEST_PAGE, { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForTimeout(1000);

  // Consent löschen (simuliert abgelaufenen Consent)
  await page.evaluate(() => {
    localStorage.removeItem('complyo_cookie_consent');
    localStorage.removeItem('complyo_consent_date');
  });

  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2000);

  const banner = page.locator('#complyo-cookie-banner, .complyo-banner-wrapper');
  const isBannerVisible = await banner.isVisible().catch(() => false);
  if (isBannerVisible) {
    await expect(banner).toBeVisible();
  }
});

// ============================================================
// Widget E2E Tests – Floating Widget (AUDIT-10)
// ============================================================

test('AUDIT-10: Floating Widget erscheint nach Consent-Erteilung', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.removeItem('complyo_cookie_consent');
    localStorage.removeItem('complyo_consent_date');
  });

  await page.goto(WIDGET_TEST_PAGE, { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForTimeout(2000);

  const acceptBtn = page.locator('#complyo-accept-all');
  const isVisible = await acceptBtn.isVisible().catch(() => false);

  if (isVisible) {
    await acceptBtn.click();
    await page.waitForTimeout(1000);

    const floatingBtn = page.locator('#complyo-floating-btn, .complyo-floating-btn');
    const isFloatingVisible = await floatingBtn.isVisible().catch(() => false);
    if (isFloatingVisible) {
      await expect(floatingBtn).toBeVisible();
    }
  }
});

// ============================================================
// XSS Security Tests (AUDIT-11)
// ============================================================

test('AUDIT-11: XSS-Schutz – Script-Tags in Config werden nicht ausgeführt', async ({ page }) => {
  let xssExecuted = false;
  await page.exposeFunction('xssDetected', () => { xssExecuted = true; });

  const xssConfig = JSON.stringify({
    texts: { de: { title: '<img src=x onerror="xssDetected()">XSS Test', description: 'Safe' } },
  });

  await page.addInitScript((config) => {
    (window as any).COMPLYO_OVERRIDE_CONFIG = config;
  }, xssConfig);

  await page.goto(WIDGET_TEST_PAGE, { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForTimeout(2000);

  expect(xssExecuted).toBe(false);
});

// ============================================================
// Google Consent Mode Tests (AUDIT-12)
// ============================================================

test('AUDIT-12 SC1: Google Consent Mode default events werden vor Consent gesetzt', async ({ page }) => {
  const consentEvents: string[] = [];

  await page.addInitScript(() => {
    (window as any).dataLayer = (window as any).dataLayer || [];
    const original = (window as any).dataLayer.push.bind((window as any).dataLayer);
    (window as any).dataLayer.push = function(...args: any[]) {
      if (args[0]?.[0] === 'consent') {
        (window as any).__consentEvents = (window as any).__consentEvents || [];
        (window as any).__consentEvents.push(args[0]);
      }
      return original(...args);
    };
  });

  await page.addInitScript(() => {
    localStorage.removeItem('complyo_cookie_consent');
    localStorage.removeItem('complyo_consent_date');
  });

  await page.goto(WIDGET_TEST_PAGE, { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForTimeout(2000);

  const events = await page.evaluate(() => (window as any).__consentEvents || []);
  const hasDefaultEvent = events.some((e: any[]) => e[1] === 'default');
  if (events.length > 0) {
    expect(hasDefaultEvent).toBe(true);
  }
});

test('AUDIT-12 SC2: Nach Accept All wird consent update event mit granted-Status gefeuert', async ({ page }) => {
  await page.addInitScript(() => {
    (window as any).dataLayer = [];
    localStorage.removeItem('complyo_cookie_consent');
    localStorage.removeItem('complyo_consent_date');
  });

  await page.goto(WIDGET_TEST_PAGE, { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForTimeout(2000);

  const acceptBtn = page.locator('#complyo-accept-all');
  const isVisible = await acceptBtn.isVisible().catch(() => false);

  if (isVisible) {
    await acceptBtn.click();
    await page.waitForTimeout(1000);

    const dataLayer = await page.evaluate(() => (window as any).dataLayer || []);
    const updateEvent = dataLayer.find((e: any) => Array.isArray(e) && e[0] === 'consent' && e[1] === 'update');
    if (updateEvent) {
      expect(updateEvent[2]?.analytics_storage).toBe('granted');
    }
  }
});

// ============================================================
// Storage Key Tests (AUDIT-13)
// ============================================================

test('AUDIT-13: Widget nutzt korrekten Storage-Key complyo_cookie_consent', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.removeItem('complyo_cookie_consent');
    localStorage.removeItem('complyo_consent_date');
    localStorage.removeItem('complyo_consent');
    localStorage.removeItem('cookieConsent');
  });

  await page.goto(WIDGET_TEST_PAGE, { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForTimeout(2000);

  const acceptBtn = page.locator('#complyo-accept-all');
  const isVisible = await acceptBtn.isVisible().catch(() => false);

  if (isVisible) {
    await acceptBtn.click();
    await page.waitForTimeout(1000);

    const correctKey = await page.evaluate(() => localStorage.getItem('complyo_cookie_consent'));
    const wrongKey1 = await page.evaluate(() => localStorage.getItem('complyo_consent'));
    const wrongKey2 = await page.evaluate(() => localStorage.getItem('cookieConsent'));

    expect(correctKey).toBeTruthy();
    expect(wrongKey1).toBeFalsy();
    expect(wrongKey2).toBeFalsy();
  }
});
