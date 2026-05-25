# Domain Lock & Onboarding Flow Analysis

## 1. Domain Lock Logic — Backend

### Two separate lock mechanisms exist:

---

### 1a. `domain_locks` table (per-domain fix quota)
**File:** `/home/clawd/saas/legal/backend/fix_domain_lock_logic.sql`

PostgreSQL function `check_fix_limit(p_user_id, p_domain_name)`:
- Every domain starts with **1 free fix** (fixes_limit = 1, is_unlocked = FALSE)
- After 1 fix, the paywall is triggered
- After payment, `is_unlocked = TRUE` → unlimited fixes
- Lock record is created on first fix attempt if it doesn't exist yet

```sql
-- fix_domain_lock_logic.sql lines 7–39
CREATE OR REPLACE FUNCTION check_fix_limit(p_user_id INTEGER, p_domain_name VARCHAR)
RETURNS BOOLEAN AS $$
DECLARE
    v_domain_lock RECORD;
BEGIN
    SELECT * INTO v_domain_lock FROM domain_locks
    WHERE user_id = p_user_id AND domain_name = p_domain_name;

    IF NOT FOUND THEN
        INSERT INTO domain_locks (user_id, domain_name, fixes_used, fixes_limit, is_unlocked)
        VALUES (p_user_id, p_domain_name, 0, 1, FALSE);
        RETURN TRUE;
    END IF;

    IF v_domain_lock.is_unlocked THEN RETURN TRUE; END IF;
    IF v_domain_lock.fixes_used < v_domain_lock.fixes_limit THEN RETURN TRUE; END IF;

    RETURN FALSE;  -- Paywall
END;
$$ LANGUAGE plpgsql;
```

Backend API: `GET /api/user/domain-locks`
**File:** `/home/clawd/saas/legal/backend/user_routes.py` lines 28–88

---

### 1b. `tracked_websites` table — permanent primary website lock
**File:** `/home/clawd/saas/legal/backend/website_routes.py`

When saving a website for the first time (POST `/api/v2/websites`):
- The first website added is automatically set as `is_primary = TRUE` (line 181–182)
- `DELETE /{website_id}` **explicitly blocks deletion of the primary website** (lines 390–394):

```python
# website_routes.py lines 390–394
if website["is_primary"]:
    raise HTTPException(
        status_code=403,
        detail="Die primäre Website kann nicht gelöscht werden. Diese Verknüpfung ist dauerhaft. Bitte kontaktieren Sie den Support unter support@complyo.tech für Änderungen."
    )
```

This is the **actual permanent link** — once a website is saved as primary, it cannot be deleted by the user. No update/reassign endpoint exists.

---

## 2. Onboarding Step with the Warning

**File:** `/home/clawd/saas/legal/dashboard-react/src/components/onboarding/OnboardingWizard.tsx`

### First warning (Step 1, before scan — lines 495–510):
```tsx
<div className="bg-amber-50 border-2 border-amber-200 rounded-xl p-4 mb-4">
  <p className="font-semibold text-amber-800 mb-1">Wichtiger Hinweis</p>
  <p className="text-sm text-amber-700">
    Die hier eingetragene Website wird <strong>dauerhaft</strong> mit Ihrem Complyo-Konto verknüpft.
    Diese Verknüpfung kann <strong>nicht selbstständig rückgängig</strong> gemacht werden.
    Änderungen sind nur über ein <strong>Support-Ticket</strong> möglich.
  </p>
</div>
```

### Second warning (Step 3, final confirmation dialog — lines 712–762):
State variable `showConfirmLock` / `lockConfirmed`. A confirmation modal appears before finalizing:
```tsx
// lines 724–728
<ul className="text-sm text-red-700 space-y-1 mb-3">
  <li>• Diese Verknüpfung kann <strong>NICHT</strong> selbstständig rückgängig gemacht werden</li>
  <li>• Änderungen erfordern ein <strong>Support-Ticket</strong></li>
  <li>• Ihr Konto ist auf <strong>eine Website</strong> beschränkt</li>
</ul>
```
User must check a checkbox (`lockConfirmed`) before "Bestätigen & Fortfahren" is enabled.

### Onboarding trigger (page.tsx):
**File:** `/home/clawd/saas/legal/dashboard-react/src/app/page.tsx` lines 27–47

```tsx
// page.tsx lines 34–47
if (user?.onboarding_completed) {
  setShowOnboarding(false);
  return;
}
const hasCompleted = localStorage.getItem('complyo_onboarding_completed');
// if not completed → show OnboardingWizard
if (showOnboarding) {
  return <OnboardingWizard onComplete={() => setShowOnboarding(false)} />;
}
```

---

## 3. API Endpoints Called During Onboarding

### `/api/analyze` (POST)
**Frontend call:** `/home/clawd/saas/legal/dashboard-react/src/lib/api.ts` line 153
```ts
const response = await apiClient.post('/api/analyze', { url: normalizedUrl });
```
**Routing:** Next.js rewrites `/api/:path*` → `${NEXT_PUBLIC_API_URL}/:path*` (`next.config.js` line 20–23). So `/api/analyze` proxies to the backend at port 8002.

**Backend handler:** No `@app.post("/api/analyze")` found directly. The backend exposes:
- `POST /api/v2/analyze` (`main_production.py` line 1090)
- `POST /api/v2/analyze/quick` (line 1034)
- `POST /api/v2/analyze/complete` (line 771)

The `/api/analyze` route (without `/v2`) appears to be handled by the same backend but the exact route is not present in `main_production.py` — it may be an older/legacy route still proxied. It is listed in the CSRF exemption list in `csrf_middleware.py` line 40.

### `/api/v2/dashboard/metrics` (GET)
**File:** `/home/clawd/saas/legal/backend/dashboard_routes.py` lines 52–185

Reads from `tracked_websites`, `scan_history`, `user_limits`. Returns: `totalScore`, `websites`, `criticalIssues`, `scansAvailable`, `scansUsed`, `avgScore`, `totalRiskEuro`, `aiFixesUsed`, `aiFixesMax`, `websitesMax`, `scoreTrend`, `criticalTrend`.

### `/api/auth/refresh-cookie` (POST)
**File:** `/home/clawd/saas/legal/backend/auth_routes.py` lines 247–305

Reads the `refresh_token` HttpOnly cookie, validates it via `auth_service.refresh_access_token()`, rotates the token, and returns a new `access_token` + updated `onboarding_completed` flag from the `users` table (line 276–280).

### `/api/v2/websites` (POST) — called by `saveTrackedWebsite`
**Frontend:** `/home/clawd/saas/legal/dashboard-react/src/lib/api.ts` line 468
**Backend:** `/home/clawd/saas/legal/backend/website_routes.py` lines 134–363

This is the call that **permanently links the website**. It:
1. Inserts into `tracked_websites` with `is_primary = TRUE` if first website
2. Creates a default `cookie_banner_configs` entry
3. Creates an eRecht24 project
4. Increments `user_limits.websites_count`

### `/api/auth/complete-onboarding` (POST)
**Frontend:** `OnboardingWizard.tsx` line 211
**Backend:** `/home/clawd/saas/legal/backend/auth_routes.py` lines 377–395

Sets `users.onboarding_completed = TRUE` in the database for the authenticated user.

---

## 4. Permanent Website Link — Is It Truly Undoable?

**Yes, the primary website link is enforced at multiple layers:**

| Layer | File | What prevents undoing |
|---|---|---|
| DB constraint | `website_routes.py:390–394` | `DELETE` endpoint returns HTTP 403 for `is_primary=TRUE` rows |
| No update endpoint | `website_routes.py` | No `PUT /api/v2/websites/{id}/primary` route exists |
| Frontend lock | `stores/dashboard.ts:93–101` | `lockForOptimization(url)` stores URL in localStorage + Zustand state permanently |
| DB persistence | `contexts/ActiveSiteContext.tsx:39–41` | `restoreLockFromPrimary` restores lock from DB primary URL even if localStorage is cleared |
| Onboarding flag | `auth_routes.py:377–395` | `onboarding_completed = TRUE` in DB, prevents re-showing onboarding |

**To change the primary website, a user must contact support** (`support@complyo.tech`), as stated in both the frontend warning and the backend 403 error message.

---

## Flow Summary

```
Register/Login
  → auth_routes.py /api/auth/login or /register
  → returns onboarding_completed flag

First visit (onboarding_completed = FALSE)
  → page.tsx shows OnboardingWizard
  → Step 1: URL input + amber warning about permanent link
  → Step 2: Calls POST /api/analyze (proxied to backend port 8002)
  → Step 3: Results + red confirmation modal (showConfirmLock checkbox)
  → On confirm: calls saveTrackedWebsite → POST /api/v2/websites
      → sets is_primary=TRUE, creates cookie config, eRecht24 project
  → Calls POST /api/auth/complete-onboarding → sets onboarding_completed=TRUE in DB
  → localStorage.setItem('complyo_onboarding_completed', 'true')
  → lockForOptimization(url) → localStorage + Zustand state

Subsequent logins
  → /api/auth/refresh-cookie returns onboarding_completed=TRUE
  → ActiveSiteContext.tsx restoreLockFromPrimary() restores the locked URL
```
