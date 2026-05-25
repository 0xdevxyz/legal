# Migrations-Inventur — Token-Direkt-Zugriffe
**Datum:** 2026-05-23

## Ausgangslage (38 Stellen)

Alle `localStorage.getItem('access_token')` / `localStorage.getItem('token')` Direkt-Zugriffe wurden identifiziert und migriert.

## Status nach Migration

| Datei | Alt | Neu | Status |
|---|---|---|---|
| `lib/auth-refresh.ts` | — | `localStorage.getItem('access_token')` | ✅ Zentrale Lese-Funktion (legitim) |
| `lib/api-client.ts` | `localStorage.getItem("access_token")` | `getAccessToken()` aus `auth-refresh.ts` | ✅ |
| `lib/api.ts` | Eigener Axios-Client mit `localStorage` | `getApiClient()` aus `api-client.ts` | ✅ |
| `lib/auth-helper.ts` | Direkt | Re-Export aus `auth-refresh.ts` + `@deprecated` | ✅ |
| `lib/ai-compliance-api.ts` | Eigener Axios-Client mit `localStorage` | `getApiClient()` aus `api-client.ts` | ✅ |
| `contexts/AuthContext.tsx` | `localStorage.setItem/removeItem` direkt | `setAccessToken()` / `clearAccessToken()` | ✅ |
| `components/dashboard/ComplianceIssueGroup.tsx` | `fetch` + `localStorage.getItem` | `apiClient.get/post` | ✅ |
| `components/fixes/ApplyFixModal.tsx` | `fetch` + `localStorage.getItem` | `apiClient.post` | ✅ |
| `components/dashboard/ExpertServiceModal.tsx` | `fetch` + `localStorage.getItem` | `apiClient.post` | ✅ |
| `components/dashboard/LegalTextWizard.tsx` | `fetch` + `localStorage.getItem` | `apiClient.post` | ✅ |
| `components/legal-changes/LegalActionWidget.tsx` | `fetch` + `localStorage.getItem` (3×) | `apiClient.get/post` | ✅ |
| `app/cookie-compliance/page.tsx` | `fetch` + `localStorage.getItem` | `apiClient.get/post` | ✅ |
| `components/cookie-compliance/RevocationChart.tsx` | `fetch` + `localStorage.getItem` | `apiClient.get` | ✅ |
| `components/cookie-compliance/ConsentModeSettings.tsx` | `fetch` + `localStorage.getItem` | `apiClient.post` | ✅ |
| `components/cookie-compliance/ServiceManager.tsx` | `fetch` + `localStorage.getItem` | `apiClient.get/post` | ✅ |
| `components/cookie-compliance/TCFManager.tsx` | `fetch` + `localStorage.getItem` | `apiClient.get/post` | ✅ |
| `components/legal/LegalDocumentGenerator.tsx` | `fetch` + `localStorage.getItem` | `apiClient.post` | ✅ |
| `app/profile/page.tsx` | `fetch` + `localStorage.getItem` | `apiClient.put` | ✅ |
| `app/register/page.tsx` | `fetch` + `localStorage.getItem` | `apiClient.post` | ✅ |
| `components/dashboard/ComplianceIssueCard.tsx` | `fetch` + `localStorage.getItem` (2×) | `apiClient.get/post` | ✅ |
| `components/dashboard/DomainLockStatus.tsx` | `localStorage.getItem` + axios direkt | `apiClient.get` | ✅ |
| `components/dashboard/CookieComplianceWidget.tsx` | `fetch` + `localStorage.getItem` | `apiClient.get` | ✅ |
| `components/dashboard/TCFComplianceWidget.tsx` | `fetch` + `localStorage.getItem` | `apiClient.get` | ✅ |
| `components/dashboard/LegalArchiveModal.tsx` | `fetch` + `localStorage.getItem` | `apiClient.get` | ✅ |
| `components/dashboard/LegalNews.tsx` | `fetch` + `localStorage.getItem` | `apiClient.post` | ✅ |
| `components/setup/ERecht24Setup.tsx` | `fetch` + `localStorage.getItem` | `apiClient.post` | ✅ |

## Verbleibende legitime Stellen

| Datei | Zeile | Begründung |
|---|---|---|
| `lib/auth-refresh.ts` | 9 | Zentrale Token-Lese-Funktion — einzige erlaubte Stelle |

## Finale Verifikation

```bash
# Nur noch auth-refresh.ts zeigt Treffer:
grep -r "localStorage.getItem('access_token')" src/
# > src/lib/auth-refresh.ts:9: ...
```
