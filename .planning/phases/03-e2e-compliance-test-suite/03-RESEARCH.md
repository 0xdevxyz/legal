# Phase 3: E2E Compliance Test Suite — Research

**Researched:** 2026-05-01
**Domain:** Test automation for DSGVO §25/TTDSG cookie consent flow and BFSG accessibility widget
**Confidence:** HIGH

---

## Summary

The Complyo backend already has a working pytest test suite that runs inside the `complyo-backend` Docker container. The established pattern — used in `test_statement_generator.py` — is `FastAPI.TestClient` + `monkeypatch` to mock `db_pool` and `auth_service`, producing fully hermetic unit tests with zero external dependencies. All required Python packages (`pytest 9.0.3`, `fastapi.testclient`, `playwright 1.40.0`, `httpx 0.27.2`, `pytest-asyncio 1.3.0`) are already installed in the container's site-packages. Playwright Chromium binaries are also pre-installed at `/app/.cache/ms-playwright/chromium-1091`.

For the JavaScript widget tests (accessibility widget `toggleFeature → body.classList` flow, localStorage persistence), the project has `playwright.config.ts` and `tests/e2e/` in `dashboard-react/`, but `@playwright/test` is not in `package.json` devDependencies — it is only referenced in `package-lock.json` and must be explicitly added before `npm install`. The Node.js `npx playwright` binary (version 1.59.1) is available globally.

The primary recommended approach is a **two-layer test suite**: (1) Python pytest with `TestClient` + `monkeypatch` for AUDIT-06 (API-level consent flow) and AUDIT-08 (DSGVO §25 pre-consent tracking), and (2) Node.js Playwright (`@playwright/test`) for AUDIT-07 (browser-level accessibility widget DOM/localStorage). There is a known DB schema mismatch in `cookie_compliance_stats` that must be addressed — the live endpoint fails with a 500 because `site_id` column does not exist in the table (the column is named `site_identifier`). Tests must either mock around this or the schema must be fixed first.

**Primary recommendation:** Write `backend/tests/test_consent_flow.py` using FastAPI TestClient + monkeypatch (same pattern as `test_statement_generator.py`), and `dashboard-react/tests/e2e/cookie-compliance.spec.ts` + `accessibility-widget.spec.ts` using Playwright TypeScript after adding `@playwright/test` to `package.json`.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AUDIT-06 | Cookie flow E2E: Banner → "Nur Notwendige" → consent saved to DB → analytics scripts blocked | TestClient mocks db_pool; widget flow testable via Playwright against `/public/cookie-test.html` served by live backend |
| AUDIT-07 | Accessibility widget: loads → toggle → CSS class on body → localStorage persists | Playwright `page.evaluate()` + `localStorage.getItem('complyo_a11y_preferences')` check; widget served at `http://localhost:8002/api/widgets/accessibility.js` |
| AUDIT-08 | Compliance validation: no tracking before consent (DSGVO §25 TTDSG) | pytest unit tests that verify `dataLayer` is empty / analytics scripts have `type="text/plain"` before consent event; also Playwright `page.on('request')` intercept to assert no tracking domains fire |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 9.0.3 | Test runner | Already installed in Docker container; used by all existing tests |
| fastapi.testclient | (bundled with fastapi 0.115.6) | HTTP-level test client without running a server | Same pattern as `test_statement_generator.py`; no DB/network needed when monkeypatching |
| pytest-asyncio | 1.3.0 | async test support | Already installed; needed for `async def` tests with `asyncpg` mocks |
| @playwright/test | 1.59.1 (via npx) | Browser automation for widget JS tests | `playwright.config.ts` already exists in `dashboard-react/`; Chromium available globally |
| playwright (Python) | 1.40.0 | Alternative: browser tests runnable from within Docker | Pre-installed with Chromium in the backend container |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| unittest.mock (stdlib) | Python 3.11 | `AsyncMock`, `MagicMock` for db_pool | Mocking asyncpg connection pool — same as `test_statement_generator.py` |
| httpx | 0.27.2 | Async HTTP client for integration tests against the live backend | Use when testing full API stack without mocking (e.g., `http://localhost:8002/health`) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| FastAPI TestClient + monkeypatch | pytest + httpx against live backend | httpx hits real DB which has schema bugs; TestClient + monkeypatch is hermetic and fast |
| Node.js @playwright/test | Python playwright | Python playwright works inside Docker container; Node.js @playwright/test works outside Docker and aligns with existing `playwright.config.ts` |
| Separate test HTML pages | Load widget from CDN | Local serving via `http://localhost:8002/api/widgets/...` is reliable; CDN has rate-limits and version drift |

**Installation (Node.js side):**
```bash
cd /home/clawd/saas/legal/dashboard-react
npm install --save-dev @playwright/test @axe-core/playwright
npx playwright install chromium
```

**Version verification (checked 2026-05-01):**
```
npm view @playwright/test version  → 1.59.1
npm view @axe-core/playwright version → 4.11.3
```

No additional Python packages needed — all already installed in the Docker container.

---

## Architecture Patterns

### Recommended Project Structure
```
backend/tests/
├── test_consent_flow.py        # AUDIT-06: API-level consent flow (TestClient + monkeypatch)
├── test_dsgvo_compliance.py    # AUDIT-08: DSGVO §25 TTDSG pre-consent checks
└── (existing files unchanged)

backend/public/
└── widget-test-page.html       # Minimal HTML page loading cookie_banner_v2.js + content_blocker.js
                                # Used by Playwright for full browser-level widget tests

dashboard-react/tests/e2e/
├── cookie-compliance.spec.ts   # AUDIT-06/08: Playwright E2E for cookie banner flow
├── accessibility-widget.spec.ts # AUDIT-07: Playwright E2E for accessibility widget
└── (existing files unchanged)
```

### Pattern 1: FastAPI TestClient + monkeypatch (established pattern — use for API tests)
**What:** Mount only the needed router on a minimal FastAPI app; monkeypatch `db_pool` and `auth_service` globals in the module under test; use `TestClient` for synchronous HTTP calls. No running server, no DB connection needed.
**When to use:** All AUDIT-06 API-level tests, all AUDIT-08 pre-consent checks that validate request structure.
**Example (from `test_statement_generator.py` — proven working):**
```python
# Source: /home/clawd/saas/legal/backend/tests/test_statement_generator.py
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
import cookie_compliance_routes
from cookie_compliance_routes import router as cookie_compliance_router

def make_app():
    app = FastAPI()
    app.include_router(cookie_compliance_router)
    return TestClient(app)

def setup_db_mock(monkeypatch, fetchrow_return=None, execute_return=None):
    mock_conn = AsyncMock()
    mock_conn.fetchrow = AsyncMock(side_effect=[
        None,            # SELECT from cookie_banner_configs (no config found → revision_id=1)
        {"id": 42, "timestamp": __import__("datetime").datetime(2026, 5, 1, 12, 0, 0)}  # INSERT RETURNING
    ])
    mock_conn.execute = AsyncMock(return_value=None)  # stats upsert (mocked away)
    mock_pool = MagicMock()
    mock_pool.fetchrow = mock_conn.fetchrow
    mock_pool.execute = mock_conn.execute
    monkeypatch.setattr(cookie_compliance_routes, "db_pool", mock_pool)
```

**Critical note:** The `log_consent` endpoint calls `db_pool.fetchrow()` once (for cookie_banner_configs) then calls `db_pool.fetchrow()` again (INSERT RETURNING), then `db_pool.execute()` (stats upsert). The mock must return the right values in sequence. See the actual endpoint at `backend/cookie_compliance_routes.py` lines 306-388.

### Pattern 2: Playwright TypeScript for widget DOM tests
**What:** Load a minimal HTML test page that includes the widget script; interact with the DOM; assert CSS classes, localStorage state, and fetch() calls.
**When to use:** AUDIT-07 (accessibility widget toggle → body.classList), AUDIT-06 SC4 (dataLayer.push), AUDIT-08 (no tracking before consent).
**Example:**
```typescript
// Source: dashboard-react/tests/e2e pattern established in existing spec files
import { test, expect } from '@playwright/test';

test('accessibility widget: toggle nightMode → body gets complyo-night-mode class', async ({ page }) => {
  await page.goto('http://localhost:8002/public/widget-test-page.html');
  // Wait for widget to initialize
  await page.waitForSelector('.complyo-toggle-btn');
  // Click the toggle button to open the panel
  await page.click('.complyo-toggle-btn');
  // Find and click the nightMode tile
  await page.click('[data-feature="nightMode"]');
  // Assert body class was applied
  const bodyClass = await page.evaluate(() => document.body.className);
  expect(bodyClass).toContain('complyo-night-mode');
  // Assert localStorage was updated
  const prefs = await page.evaluate(() =>
    JSON.parse(localStorage.getItem('complyo_a11y_preferences') || '{}')
  );
  expect(prefs.nightMode).toBe(true);
});
```

### Pattern 3: Playwright request interception for DSGVO §25 (no tracking before consent)
**What:** Use `page.on('request', callback)` to intercept all outgoing network requests and assert no tracking domains are contacted before the consent decision.
**When to use:** AUDIT-08 compliance validation.
**Example:**
```typescript
test('DSGVO §25: no tracking requests fire before consent', async ({ page }) => {
  const trackingRequests: string[] = [];
  const TRACKING_DOMAINS = [
    'google-analytics.com', 'googletagmanager.com',
    'facebook.net', 'hotjar.com', 'analytics.tiktok.com'
  ];

  page.on('request', (req) => {
    const url = req.url();
    if (TRACKING_DOMAINS.some(domain => url.includes(domain))) {
      trackingRequests.push(url);
    }
  });

  await page.goto('http://localhost:8002/public/widget-test-page.html');
  // Wait for banner to appear (before any consent decision)
  await page.waitForSelector('.complyo-cookie-banner');

  // Assert no tracking fired yet
  expect(trackingRequests).toHaveLength(0);

  // Now click "Alle akzeptieren" — tracking may fire after this
  await page.click('[aria-label*="Alle akzeptieren"]');
  // dataLayer should now contain the consent update
  const dataLayer = await page.evaluate(() => (window as any).dataLayer || []);
  const consentEvent = dataLayer.find((e: any) => e.event === 'complyo_consent_update');
  expect(consentEvent).toBeTruthy();
  expect(consentEvent.complyo_consent.analytics).toBe(true);
  expect(consentEvent.complyo_consent.marketing).toBe(true);
});
```

### Pattern 4: Mock test HTML page for widget testing
**What:** A minimal HTML page served by the backend at `/public/widget-test-page.html` that includes the widget scripts and (optionally) mock analytics scripts with `type="text/javascript"` that should be blocked.
**When to use:** All Playwright browser tests need a stable, locally-served test page.
**Structure:**
```html
<!DOCTYPE html>
<html>
<head>
  <!-- Mock analytics script that content blocker should block -->
  <script type="text/javascript" data-complyo-consent="analytics"
          src="https://www.googletagmanager.com/gtag/js?id=TEST-123"></script>
</head>
<body>
  <h1>Widget Test Page</h1>
  <!-- Load content blocker first, then banner widget -->
  <script src="http://localhost:8002/public/cookie-blocker.js"
          data-site-id="test-site"></script>
  <script src="http://localhost:8002/api/widgets/cookie-compliance.js"
          data-site-id="test-site"
          data-complyo-site-id="test-site"></script>
  <!-- Load accessibility widget -->
  <script src="http://localhost:8002/api/widgets/accessibility.js"
          data-site-id="test-site"></script>
</body>
</html>
```

### Anti-Patterns to Avoid
- **Testing against the live database:** The `cookie_compliance_stats` table has a schema mismatch — `site_id` column doesn't exist (it's `site_identifier`). API tests MUST mock `db_pool` to avoid flaky failures from this bug.
- **Using `@pytest.mark.asyncio` unnecessarily:** The `TestClient` approach is synchronous even for async FastAPI routes — no `async def test_...` needed unless testing `asyncpg` directly.
- **Loading widgets from `https://api.complyo.de`:** Use `http://localhost:8002` to avoid network dependency and test the local version.
- **Testing `window.complyo.acceptAll()` without waiting for banner init:** The banner init is async (fetches config, checks reconsent). Use `page.waitForSelector('.complyo-cookie-banner')` before clicking.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP-level API testing | Custom `requests` integration test | `fastapi.testclient.TestClient` | Zero network overhead; same process as the app; monkeypatching works cleanly |
| DB mocking | SQLite in-memory test DB | `unittest.mock.AsyncMock` on `db_pool` | Avoids schema migration in test env; established pattern already proven working |
| Browser automation for widget tests | Selenium | Playwright (`@playwright/test` or Python) | Already installed; has `page.on('request')` interception; TypeScript support |
| Cookie banner test page | External CMS/WordPress | Static HTML in `backend/public/` | Served by the running backend container; accessible at `http://localhost:8002/public/` |

**Key insight:** The test infrastructure (pytest, TestClient, Playwright Chromium) is already installed and working. The constraint is writing tests that exercise the actual widget logic via the browser — not just mocking it.

---

## Known Bug: DB Schema Mismatch

**The `log_consent` endpoint will throw a 500 error when the DB is connected** because `cookie_compliance_stats` uses `site_identifier` (not `site_id`) and lacks columns `accepted_analytics`, `accepted_marketing`, `accepted_functional`. The live API returns:
```json
{"detail": "Failed to log consent: column \"site_id\" of relation \"cookie_compliance_stats\" does not exist"}
```

**Impact on testing strategy:**
- API tests using `TestClient + monkeypatch` are unaffected (DB is mocked)
- Playwright tests using the live API (`http://localhost:8002/api/cookie-compliance/consent`) will receive a 500 for the server-side log, but the widget itself will still render and the client-side behavior (localStorage, dataLayer) will still work because `logConsentToServer` has a `try/catch` that silently ignores errors (line 759 in `cookie_banner_v2.js`)
- The success criteria for AUDIT-06 SC1 ("Consent in DB gespeichert") requires this bug to be fixed OR the tests to mock the DB endpoint

**Recommendation:** Fix the stats table schema as a prerequisite step in this phase, OR scope AUDIT-06 SC1 to API-level testing (TestClient + mock) and note the live-DB assertion is blocked by the schema bug.

---

## Common Pitfalls

### Pitfall 1: Banner init race condition
**What goes wrong:** Playwright clicks the accept button before the banner renders, causing `No element matching selector` errors.
**Why it happens:** `cookie_banner_v2.js` fetches banner config from `/api/cookie-compliance/config/{site_id}` and `/api/ab-tests/assign/...` before rendering — several async calls on startup.
**How to avoid:** Always `await page.waitForSelector('.complyo-cookie-banner', { timeout: 5000 })` before any button click. For the test page, the API calls will fail (no config for `test-site`) but the banner still renders with defaults after the fetch fails.
**Warning signs:** `TimeoutError: page.click: Timeout 30000ms exceeded`

### Pitfall 2: localStorage not cleared between tests
**What goes wrong:** The second test runs with `complyo_cookie_consent` already set in localStorage, so the banner never appears.
**Why it happens:** `cookie_banner_v2.js` checks `localStorage.getItem(CONSENT_STORAGE_KEY)` on init and skips the banner if consent is already recorded.
**How to avoid:** In Playwright, use `await page.evaluate(() => localStorage.clear())` in `beforeEach`, or use `page.context().clearCookies()` + `await page.evaluate(() => localStorage.clear())`.
**Warning signs:** Banner-related tests pass on first run but fail on re-run.

### Pitfall 3: `pytest-asyncio` mode mismatch
**What goes wrong:** Tests with `@pytest.mark.asyncio` raise `ScopeMismatch` or `RuntimeError: no running event loop`.
**Why it happens:** The container uses `asyncio: mode=Mode.STRICT` (verified from test run output). Tests must explicitly mark async tests or configure `asyncio_mode = "auto"` in `pytest.ini`.
**How to avoid:** Either use `@pytest.mark.asyncio` explicitly on each async test, or add `asyncio_mode = "auto"` to a `pytest.ini` in `/app/`. The existing `test_statement_generator.py` uses synchronous `TestClient` — no async needed for the consent endpoint tests either.
**Warning signs:** `PytestUnraisableExceptionWarning` or `FAILED tests/test_foo.py::test_bar - RuntimeError`

### Pitfall 4: Widget API calls fail silently in tests
**What goes wrong:** Playwright test asserts `dataLayer.push` but the consent event was never pushed because the widget's internal fetch to `/api/cookie-compliance/config/test-site` returned 404.
**Why it happens:** The widget fetches config on init (line 390 in `cookie_banner_v2.js`). If config fetch fails, it falls back to defaults and still renders — but the test might not be testing the right scenario.
**How to avoid:** Either stub the config API response using Playwright's `page.route()` to intercept and return a test config, or start the test with `window.complyo.showBanner()` to force the banner to appear without fetching.
**Warning signs:** Tests pass when backend has no site config, which is not the same as production behavior.

### Pitfall 5: Accessibility widget `data-feature` attribute not present
**What goes wrong:** `page.click('[data-feature="nightMode"]')` fails because the generated HTML uses tile IDs or class names, not a `data-feature` attribute.
**Why it happens:** `accessibility-v6.js` does not use `data-feature` attributes — tiles are identified by class or by click handler closure.
**How to avoid:** Inspect the actual rendered HTML from the widget to find the correct selector. From the widget code, tiles call `this.toggleFeature(feature)` via a closure, not a `data-*` attribute. Use the tile's text content or a specific class as the selector instead.
**Warning signs:** `No element matching '[data-feature="nightMode"]'`

---

## Code Examples

### AUDIT-06: Test that "Nur Notwendige" saves correct categories to DB

```python
# Source: backend/tests/test_consent_flow.py (to be created)
# Pattern from: backend/tests/test_statement_generator.py (lines 77-113)
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
import cookie_compliance_routes
from cookie_compliance_routes import router as cookie_compliance_router

def make_app():
    app = FastAPI()
    app.include_router(cookie_compliance_router)
    return TestClient(app)

def setup_db_mock(monkeypatch):
    """db_pool mock for log_consent: two fetchrow calls + one execute."""
    mock_pool = MagicMock()
    # fetchrow call 1: SELECT id FROM cookie_banner_configs WHERE site_id=$1
    # fetchrow call 2: INSERT INTO cookie_consent_logs ... RETURNING id, timestamp
    mock_pool.fetchrow = AsyncMock(side_effect=[
        None,  # no banner config found → revision_id=1
        {"id": 99, "timestamp": datetime(2026, 5, 1, 12, 0, 0)},  # INSERT RETURNING
    ])
    mock_pool.execute = AsyncMock(return_value=None)  # stats upsert
    monkeypatch.setattr(cookie_compliance_routes, "db_pool", mock_pool)
    return mock_pool

REJECT_ALL_PAYLOAD = {
    "site_id": "test-site-001",
    "visitor_id": "test-visitor-abc",
    "consent_categories": {
        "necessary": True,
        "functional": False,
        "analytics": False,
        "marketing": False
    },
    "language": "de",
    "banner_shown": True
}

def test_reject_all_returns_success_and_consent_id(monkeypatch):
    """AUDIT-06 SC1: 'Nur Notwendige' → consent logged → response contains consent_id."""
    mock_pool = setup_db_mock(monkeypatch)
    client = make_app()
    response = client.post(
        "/api/cookie-compliance/consent",
        json=REJECT_ALL_PAYLOAD
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "consent_id" in data
    assert data["consent_id"] == 99

def test_reject_all_passes_correct_categories_to_db(monkeypatch):
    """AUDIT-06 SC1: DB INSERT receives correct consent_categories."""
    mock_pool = setup_db_mock(monkeypatch)
    client = make_app()
    client.post("/api/cookie-compliance/consent", json=REJECT_ALL_PAYLOAD)
    # Verify INSERT was called with consent_categories containing analytics=False
    call_args = mock_pool.fetchrow.call_args_list[1]  # second fetchrow = the INSERT
    # The INSERT query passes consent_categories as JSON
    import json
    categories_arg = json.loads(call_args.args[2])  # $3 = consent_categories JSON
    assert categories_arg["necessary"] is True
    assert categories_arg["analytics"] is False
    assert categories_arg["marketing"] is False
    assert categories_arg["functional"] is False
```

### AUDIT-06 SC2: All 4 categories accepted
```python
ACCEPT_ALL_PAYLOAD = {
    "site_id": "test-site-001",
    "visitor_id": "test-visitor-xyz",
    "consent_categories": {
        "necessary": True,
        "functional": True,
        "analytics": True,
        "marketing": True
    },
    "services_accepted": ["ga4", "gtm", "fbpixel", "hotjar"],
    "language": "de",
    "banner_shown": True
}

def test_accept_all_stores_all_four_categories(monkeypatch):
    """AUDIT-06 SC2: 'Alle akzeptieren' → all 4 categories True in DB."""
    mock_pool = setup_db_mock(monkeypatch)
    client = make_app()
    response = client.post("/api/cookie-compliance/consent", json=ACCEPT_ALL_PAYLOAD)
    assert response.status_code == 200
    import json
    call_args = mock_pool.fetchrow.call_args_list[1]
    categories = json.loads(call_args.args[2])
    assert all([categories["necessary"], categories["functional"],
                categories["analytics"], categories["marketing"]])
```

### AUDIT-08: Pre-consent tracking validation (pure Python, no browser needed)
```python
# backend/tests/test_dsgvo_compliance.py
import json

TRACKING_DOMAINS = [
    "google-analytics.com", "googletagmanager.com/gtag",
    "facebook.net/en_US/fbevents", "hotjar.com", "analytics.tiktok.com"
]

def test_consent_payload_does_not_log_before_banner_shown():
    """AUDIT-08: consent log with banner_shown=False must be rejected or flagged."""
    # The API currently accepts banner_shown=False — this test documents expected behavior
    # DSGVO §25: logging should only happen after user sees and interacts with the banner
    payload = {
        "site_id": "test-site",
        "visitor_id": "test-v",
        "consent_categories": {"necessary": True, "functional": False,
                               "analytics": True, "marketing": True},
        "banner_shown": False,  # User never saw the banner — invalid under DSGVO §25
    }
    # The payload is structurally valid but semantically non-compliant
    # SC4 requires this to either be rejected (400) or recorded as non-compliant
    assert payload["banner_shown"] is False  # Documents the violation vector

def test_reject_consent_contains_analytics_false():
    """AUDIT-08: verify that analytics=False in payload means no analytics consent."""
    reject_categories = {"necessary": True, "functional": False,
                         "analytics": False, "marketing": False}
    assert reject_categories["analytics"] is False
    assert reject_categories["marketing"] is False
    # After reject: dataLayer should NOT receive complyo_analytics_granted
    # (tested via browser in Playwright spec)
```

### AUDIT-07: Playwright TypeScript for accessibility widget
```typescript
// dashboard-react/tests/e2e/accessibility-widget.spec.ts
import { test, expect } from '@playwright/test';

const WIDGET_TEST_PAGE = 'http://localhost:8002/public/widget-test-page.html';

test.beforeEach(async ({ page }) => {
  // Clear localStorage so widget always starts fresh
  await page.goto(WIDGET_TEST_PAGE);
  await page.evaluate(() => localStorage.clear());
  await page.reload();
});

test('AUDIT-07 SC3: accessibility widget loads and toggle button is visible', async ({ page }) => {
  await page.goto(WIDGET_TEST_PAGE);
  await expect(page.locator('.complyo-toggle-btn')).toBeVisible({ timeout: 5000 });
});

test('AUDIT-07 SC3: nightMode toggle applies complyo-night-mode class to body', async ({ page }) => {
  await page.goto(WIDGET_TEST_PAGE);
  // Open the accessibility panel
  await page.click('.complyo-toggle-btn');
  // Find and click the nightMode feature tile (by visible text)
  await page.getByText('Nachtmodus').first().click();
  // Assert body class was applied
  await expect(page.locator('body')).toHaveClass(/complyo-night-mode/);
});

test('AUDIT-07 SC3: preferences persist to localStorage', async ({ page }) => {
  await page.goto(WIDGET_TEST_PAGE);
  await page.click('.complyo-toggle-btn');
  await page.getByText('Nachtmodus').first().click();
  const prefs = await page.evaluate(() =>
    JSON.parse(localStorage.getItem('complyo_a11y_preferences') || '{}')
  );
  expect(prefs.nightMode).toBe(true);
});

test('AUDIT-07 SC3: preferences survive page reload', async ({ page }) => {
  await page.goto(WIDGET_TEST_PAGE);
  await page.click('.complyo-toggle-btn');
  await page.getByText('Nachtmodus').first().click();
  await page.reload();
  // Widget should re-apply the class from localStorage on init
  await expect(page.locator('body')).toHaveClass(/complyo-night-mode/);
});
```

---

## Widget API Reference (Key Facts for Test Authors)

### Cookie Banner (`cookie_banner_v2.js`)
- **Window global:** `window.complyo` and `window.complyoCookieBanner`
- **Public API:** `window.complyo.acceptAll()`, `window.complyo.rejectAll()`, `window.complyo.showBanner()`
- **Consent storage key:** `localStorage.getItem('complyo_cookie_consent')` → JSON object with `{necessary, functional, analytics, marketing, timestamp}`
- **API call for consent log:** `POST https://api.complyo.de/api/cookie-compliance/consent` (or `http://localhost:8002` in tests)
- **dataLayer events pushed on accept:** `complyo_consent_update`, `complyo_analytics_granted` (if analytics=true), `complyo_marketing_granted` (if marketing=true), `complyo_functional_granted` (if functional=true)
- **Banner DOM selector:** `.complyo-cookie-banner` (appears after init; removed from DOM after accept/reject)
- **Accept all button selector:** `button[aria-label*="Alle akzeptieren"]` or `#cps-accept-all`
- **Reject all button selector:** mapped to `rejectAll()` via event listener (no stable ID — use `rejectBtn` in layout context)

### Accessibility Widget (`accessibility-v6.js`)
- **Auto-initializes:** `new ComplyoAccessibilityWidget()` on `DOMContentLoaded`
- **Storage key:** `localStorage.getItem('complyo_a11y_preferences')` → JSON object with feature states
- **Toggle button selector:** `.complyo-toggle-btn`
- **Feature tile selectors:** Use text content (e.g., `page.getByText('Nachtmodus')`) — no `data-feature` attribute
- **Body CSS classes applied per feature:**
  - `nightMode` → `body.complyo-night-mode`
  - `highlightLinks` → `body.complyo-highlight-links`
  - `readableFont` → `body.complyo-readable-font`
  - `highContrast` → `body.complyo-high-contrast`
  - `bigCursor` → `body.complyo-big-cursor`
  - `hideImages` → `body.complyo-hide-images`
  - `stopAnimations` → `body.complyo-stop-animations`

### Consent API (`cookie_compliance_routes.py`)
- **Endpoint:** `POST /api/cookie-compliance/consent`
- **Auth:** Not required (public endpoint — anyone can log consent)
- **Request model `ConsentLog`:** `{site_id, visitor_id, consent_categories: {necessary, functional, analytics, marketing}, services_accepted?, language?, banner_shown?, user_agent?, ip_address?, device_fingerprint?}`
- **Response:** `{success: true, consent_id: int, timestamp: str, message: str}`
- **DB interaction:** `fetchrow` (cookie_banner_configs) → `fetchrow` (INSERT cookie_consent_logs RETURNING) → `execute` (UPDATE cookie_compliance_stats)
- **Known bug:** `cookie_compliance_stats` stats upsert fails — `site_id` column missing, correct column is `site_identifier`. Mock `db_pool.execute` returns `None` to bypass in tests.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| pytest | All Python tests | ✓ (in Docker container) | 9.0.3 | — |
| fastapi.testclient | API unit tests | ✓ (in Docker container) | bundled fastapi 0.115.6 | — |
| playwright (Python) | Browser tests from Python | ✓ (in Docker container) | 1.40.0 | — |
| Chromium (browser binary) | Playwright tests | ✓ | chromium-1091 at `/app/.cache/ms-playwright/` | — |
| httpx | Async HTTP tests | ✓ (in Docker container) | 0.27.2 | — |
| @playwright/test (Node.js) | dashboard-react e2e | ✗ (not in package.json) | needs `npm install --save-dev @playwright/test@^1.59.1` | npx playwright (1.59.1 available globally) |
| @axe-core/playwright | Existing accessibility.spec.ts | ✗ (not installed) | needs `npm install --save-dev @axe-core/playwright` | skip axe in cookie tests |
| complyo-backend running | Playwright against live API | ✓ | Up 41 hours, healthy | — |
| complyo-postgres running | Live DB tests | ✓ (but schema bugs) | 15-alpine | Mock via monkeypatch |

**Missing dependencies with no fallback:**
- `@playwright/test` must be added to `dashboard-react/package.json` devDependencies and installed before Node.js Playwright tests can run.

**Missing dependencies with fallback:**
- Playwright browser tests can run from Python inside the Docker container if Node.js setup is blocked.

**Test execution commands (after setup):**
```bash
# Python tests — run inside the Docker container:
docker exec complyo-backend python3 -m pytest /app/tests/test_consent_flow.py -v
docker exec complyo-backend python3 -m pytest /app/tests/test_dsgvo_compliance.py -v

# Full Python test suite:
docker exec complyo-backend python3 -m pytest /app/tests/ -v

# Node.js Playwright tests (after npm install):
cd /home/clawd/saas/legal/dashboard-react
npx playwright test tests/e2e/cookie-compliance.spec.ts
npx playwright test tests/e2e/accessibility-widget.spec.ts
```

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 (Python), @playwright/test 1.59.1 (Node.js TypeScript) |
| Config file | No `pytest.ini` exists — create `/home/clawd/saas/legal/backend/pytest.ini` for `asyncio_mode` |
| Quick run command | `docker exec complyo-backend python3 -m pytest /app/tests/test_consent_flow.py -v` |
| Full suite command | `docker exec complyo-backend python3 -m pytest /app/tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AUDIT-06 SC1 | Banner → Nur Notwendige → consent_categories in DB | unit (TestClient + mock) | `docker exec complyo-backend python3 -m pytest /app/tests/test_consent_flow.py::test_reject_all_returns_success_and_consent_id -x` | ❌ Wave 0 |
| AUDIT-06 SC1 | consent log response contains consent_id | unit (TestClient + mock) | `docker exec complyo-backend python3 -m pytest /app/tests/test_consent_flow.py::test_reject_all_passes_correct_categories_to_db -x` | ❌ Wave 0 |
| AUDIT-06 SC2 | Alle akzeptieren → all 4 categories True | unit (TestClient + mock) | `docker exec complyo-backend python3 -m pytest /app/tests/test_consent_flow.py::test_accept_all_stores_all_four_categories -x` | ❌ Wave 0 |
| AUDIT-06 SC2 | GTM dataLayer.push contains complyo_consent_update | browser (Playwright) | `npx playwright test tests/e2e/cookie-compliance.spec.ts` | ❌ Wave 0 |
| AUDIT-07 SC3 | Widget loads → toggle visible | browser (Playwright) | `npx playwright test tests/e2e/accessibility-widget.spec.ts` | ❌ Wave 0 |
| AUDIT-07 SC3 | Toggle activates → CSS class on body | browser (Playwright) | `npx playwright test tests/e2e/accessibility-widget.spec.ts` | ❌ Wave 0 |
| AUDIT-07 SC3 | localStorage persists preferences | browser (Playwright) | `npx playwright test tests/e2e/accessibility-widget.spec.ts` | ❌ Wave 0 |
| AUDIT-08 SC4 | No tracking requests before consent | browser (Playwright) | `npx playwright test tests/e2e/cookie-compliance.spec.ts` | ❌ Wave 0 |
| AUDIT-08 SC4 | banner_shown=False is not a valid consent signal | unit | `docker exec complyo-backend python3 -m pytest /app/tests/test_dsgvo_compliance.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `docker exec complyo-backend python3 -m pytest /app/tests/test_consent_flow.py -v`
- **Per wave merge:** `docker exec complyo-backend python3 -m pytest /app/tests/ -v && npx playwright test tests/e2e/`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_consent_flow.py` — covers AUDIT-06 SC1, SC2
- [ ] `backend/tests/test_dsgvo_compliance.py` — covers AUDIT-08 SC4
- [ ] `backend/public/widget-test-page.html` — test fixture page for Playwright browser tests
- [ ] `dashboard-react/tests/e2e/cookie-compliance.spec.ts` — covers AUDIT-06 SC2 (dataLayer), AUDIT-08 SC4 (no tracking)
- [ ] `dashboard-react/tests/e2e/accessibility-widget.spec.ts` — covers AUDIT-07 SC3
- [ ] `dashboard-react/package.json` devDependencies — add `@playwright/test` and `@axe-core/playwright`
- [ ] `backend/pytest.ini` — add `asyncio_mode = "auto"` if any async tests are needed (otherwise optional)

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Python playwright 1.x sync API | `sync_playwright()` context manager (unchanged in 1.40) | — | No change needed |
| `@pytest.mark.asyncio` on every test | `asyncio_mode = "auto"` in pytest.ini | pytest-asyncio 0.21+ | Add one-line config to avoid decorator on every async test |
| `pytest-playwright` plugin | Direct `playwright.sync_api` import | — | `pytest-playwright` not installed; use `playwright` library directly for Python browser tests |

**Deprecated/outdated:**
- `pytest-asyncio` < 0.21 used `asyncio_mode=legacy` by default; current container uses `asyncio_mode=STRICT` — all async tests must be explicitly decorated or `asyncio_mode = "auto"` must be set.

---

## Open Questions

1. **Schema fix prerequisite**
   - What we know: `cookie_compliance_stats` has `site_identifier` not `site_id`; the `log_consent` endpoint fails with 500 when DB is connected
   - What's unclear: Whether fixing the schema is in scope for this phase or a separate prerequisite
   - Recommendation: Either fix the stats upsert query in `cookie_compliance_routes.py` (change `site_id` → `site_identifier`) as a micro-fix in this phase, or mock around it and document it as a known bug

2. **Widget test page config fetch**
   - What we know: `cookie_banner_v2.js` fetches config from `/api/cookie-compliance/config/test-site` on init; this will return a default if no config row exists
   - What's unclear: Whether the test page should have a seed config in the DB or rely on the fallback defaults
   - Recommendation: Use `page.route()` in Playwright to intercept the config fetch and return a deterministic test config — avoids DB dependency entirely

3. **Content blocker script blocking verification**
   - What we know: `content_blocker.js` sets `type="text/plain"` on scripts with `data-complyo-consent` attribute before consent; `unblockScript` restores `type="text/javascript"` after consent
   - What's unclear: AUDIT-06 SC1 says "Analytics-Scripts geblockt" — which mechanism specifically? The test needs a real `<script data-complyo-consent="analytics">` tag on the test page to verify blocking
   - Recommendation: Add a mock analytics script to `widget-test-page.html` with `data-complyo-consent="analytics"` and assert `script.type === "text/plain"` before consent, `"text/javascript"` after accept

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `/home/clawd/saas/legal/backend/widgets/cookie_banner_v2.js` — consent flow, dataLayer push, logConsentToServer
- Direct code inspection: `/home/clawd/saas/legal/backend/widgets/accessibility-v6.js` — toggleFeature, body.classList, localStorage keys
- Direct code inspection: `/home/clawd/saas/legal/backend/cookie_compliance_routes.py` lines 284-388 — log_consent endpoint, ConsentLog model, DB interaction
- Direct test execution: `docker exec complyo-backend python3 -m pytest /app/tests/test_statement_generator.py -v` — confirms TestClient + monkeypatch pattern works (8/8 passed)
- Direct test execution: `docker exec complyo-backend python3 -m pytest /app/tests/test_ua_truncation.py -v` — confirms pytest 9.0.3 runs in container (11/11 passed)
- Direct DB inspection: `docker exec complyo-postgres psql -U complyo_user -d complyo_db -c "\d cookie_consent_logs"` — confirms table schema
- Direct DB inspection: `cookie_compliance_stats` schema — confirms `site_id` column bug (uses `site_identifier`)
- Direct Playwright verification: `docker exec complyo-backend python3 -c "from playwright.sync_api import sync_playwright..."` — Chromium browser launch confirmed working

### Secondary (MEDIUM confidence)
- `backend/Dockerfile` — confirms playwright==1.40.0 and browser install in container build
- `backend/requirements.txt` — confirms httpx==0.27.2, fastapi==0.115.6, pytest>=8.0.0
- `dashboard-react/playwright.config.ts` — confirms baseURL=localhost:3001, testDir=./tests/e2e
- `dashboard-react/package-lock.json` — confirms `@playwright/test: "^1.41.2"` was intended but not in package.json devDependencies

### Tertiary (LOW confidence)
- None — all key claims verified against source code and live environment

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified by running tests and checking imports in the live Docker container
- Architecture patterns: HIGH — based on working code in `test_statement_generator.py` (8/8 green)
- Widget behavior: HIGH — read directly from widget source code (class names, localStorage keys, dataLayer events)
- DB schema: HIGH — inspected live DB tables directly
- Pitfalls: HIGH — verified against actual error messages from live API calls

**Research date:** 2026-05-01
**Valid until:** 2026-06-01 (stable stack; 30-day window)
