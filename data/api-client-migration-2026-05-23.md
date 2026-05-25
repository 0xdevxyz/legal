# apiClient Migration — localStorage → apiClient from @/lib/api-client

Date: 2026-05-23
Branch: rebuild-2026-05-22

## Summary

Migrated 15 files from manual `fetch()` with `localStorage.getItem('access_token')` Authorization headers to `apiClient` from `@/lib/api-client`.

The `apiClient` object methods (`get`, `post`, `put`, `delete`) return data directly (no `.data` needed), handle auth tokens via interceptors, and throw AxiosError on non-2xx responses.

---

## Files Changed

### Group B — Cookie Compliance

**1. `/dashboard-react/src/app/cookie-compliance/page.tsx`**
- Added `import { apiClient as httpApiClient } from '@/lib/api-client'`
- Removed `API_URL` constant and `getAuthHeaders()` helper
- Replaced 3 `fetch()` calls in `loadConfig()` (my-config, websites, config) with `httpApiClient.get()`
- Replaced `fetch()` in `saveConfig()` with `httpApiClient.post()`
- Used try/catch instead of `.ok` checks

**2. `/dashboard-react/src/components/cookie-compliance/RevocationChart.tsx`**
- Added `import { apiClient } from '@/lib/api-client'`
- Replaced `localStorage.getItem('access_token')` + `fetch()` in `loadStats()` with `apiClient.get('/api/cookie-compliance/revocation-stats/${siteId}', { days: period })`

**3. `/dashboard-react/src/components/cookie-compliance/ConsentModeSettings.tsx`**
- Added `import { apiClient } from '@/lib/api-client'`
- Removed `API_URL`, `getAuthHeaders()` 
- Replaced `fetch()` in `handleSave()` with `apiClient.post('/api/cookie-compliance/consent-mode-config', ...)`
- Removed `.ok` check — success now inferred if no throw

**4. `/dashboard-react/src/components/cookie-compliance/ServiceManager.tsx`**
- Added `import { apiClient } from '@/lib/api-client'`
- Removed `getAuthHeaders()`
- Replaced `fetch()` in `loadServicesAndWebsite()` with `apiClient.get('/api/cookie-compliance/services')`
- Replaced `fetch()` in `scanWebsiteAutomatically()` with `apiClient.post('/api/cookie-compliance/scan', ...)`

**5. `/dashboard-react/src/components/cookie-compliance/TCFManager.tsx`**
- Added `import { apiClient } from '@/lib/api-client'`
- Removed `API_URL`, `getAuthHeaders()`
- Replaced `fetch()` in `loadVendors()` with `apiClient.get('/api/cookie-compliance/tcf/vendors')`
- Replaced `fetch()` in `handleSave()` with `apiClient.post('/api/cookie-compliance/tcf/config', ...)`

---

### Group C — Rest

**6. `/dashboard-react/src/components/legal/LegalDocumentGenerator.tsx`**
- Added `import { apiClient } from '@/lib/api-client'`
- Replaced `localStorage.getItem('access_token')` + `fetch()` in `handleGenerate()` with `apiClient.post('/api/v2/legal/generate-complete', ...)`
- Local fallback (`generateLocalContent()`) still called in catch block

**7. `/dashboard-react/src/app/profile/page.tsx`**
- Added `import { apiClient } from '@/lib/api-client'`
- Removed `API_BASE` constant and `getAuthHeaders()`
- Replaced `fetch()` in `handleSaveProfile()` with `apiClient.put('/api/user/profile', ...)`
- Replaced `fetch()` in `handleSaveBilling()` with `apiClient.put('/api/user/billing', ...)`
- Replaced `fetch()` in `handleChangePassword()` with `apiClient.put('/api/user/password', ...)`

**8. `/dashboard-react/src/app/register/page.tsx`**
- Added `import { apiClient } from '@/lib/api-client'`
- Removed unused `API_BASE` constant
- Replaced `fetch()` + `localStorage.getItem('access_token')` for Stripe checkout with `apiClient.post('/api/stripe/create-checkout', ...)`
- Accesses `checkoutData.checkout_url` directly (no `.data`)

**9. `/dashboard-react/src/components/dashboard/ComplianceIssueCard.tsx`**
- Added `import { apiClient } from '@/lib/api-client'`
- Replaced `fetch()` + `localStorage.getItem('access_token')` for eRecht24 endpoint in `handleConfirmFix()` with `apiClient.get('/api/erecht24/imprint|privacy-policy', { language: 'de' })`
- Replaced inline `fetch()` in alt-text save button onClick with `apiClient.post('/api/accessibility/alt-text', ...)`

**10. `/dashboard-react/src/components/dashboard/DomainLockStatus.tsx`**
- Added `import { apiClient } from '@/lib/api-client'`
- Removed `import axios from 'axios'`
- Removed `localStorage.getItem('access_token')` token check + axios call
- Replaced with `apiClient.get('/api/user/domain-locks')`

**11. `/dashboard-react/src/components/dashboard/CookieComplianceWidget.tsx`**
- Added `import { apiClient } from '@/lib/api-client'`
- Removed `getAuthHeaders()` helper
- Replaced `fetch()` in `loadSiteIdAndStats()` for websites endpoint with `apiClient.get('/api/v2/websites')`
- Replaced `fetch()` for stats endpoint with `apiClient.get('/api/cookie-compliance/stats/${siteId}', { days: '7' })`

**12. `/dashboard-react/src/components/dashboard/TCFComplianceWidget.tsx`**
- Added `import { apiClient } from '@/lib/api-client'`
- Replaced `localStorage.getItem('access_token')` + `fetch()` in `loadTCFData()` with `apiClient.get('/api/tcf/status/${scanId}')`

**13. `/dashboard-react/src/components/dashboard/LegalArchiveModal.tsx`**
- Added `import { apiClient } from '@/lib/api-client'`
- Replaced `fetch()` + `localStorage.getItem('access_token')` in `loadArchive()` with `apiClient.get('/api/legal-ai/archive', { page, page_size: 20, severity? })`

**14. `/dashboard-react/src/components/dashboard/LegalNews.tsx`**
- Added `import { apiClient as httpApiClient } from '@/lib/api-client'` (alias to avoid conflict with existing `apiClient from '@/lib/api'`)
- Replaced `fetch()` + `localStorage.getItem('access_token')` in `trackFeedback()` with `httpApiClient.post('/api/legal-ai/feedback', ...)`
- `fetchLegalUpdates()` and `fetchRSSNews()` already used `apiClient from '@/lib/api'` — not changed

**15. `/dashboard-react/src/components/setup/ERecht24Setup.tsx`**
- Added `import { apiClient } from '@/lib/api-client'`
- Replaced `fetch()` + `localStorage.getItem('access_token')` in `handleSetup()` with `apiClient.post('/api/v2/erecht24/setup', ...)`
- Removed `.ok` check — error handled in catch block
