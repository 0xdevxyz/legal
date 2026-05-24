# Phase 10: Dashboard-Widgets + Multi-Domain
Datum: 2026-05-22
Status: completed

## Bestand (bereits vorhanden)
- Multi-Domain: `ActiveSiteContext.tsx` + `SiteSwitcher.tsx` + `GET/POST /api/v2/websites`
- SiteSwitcher: sichtbar nur für agency-Plan, enforced websites_max
- ActiveSiteContext: persistiert active site in localStorage

## Implementiert in P10

### useMetrics.ts
- Migriert von Legacy-`apiClient` (aus `@/lib/api`) auf neuen `apiClient` (aus `@/lib/api-client`)
- Neuer Client nutzt NextAuth session.accessToken → keine 401-Fehler mehr
- `apiClient.get<DashboardMetrics>()` mit korrektem Generic-Typing

### DashboardHeader.tsx
- `apiClient` aus `@/lib/api-client` (statt `.then(r => r.data)` Doppelaufruf bereinigt)
- Notification-Badge korrekt: `notifData.pending + notifData.critical_pending`

## TypeScript
- `tsc --noEmit`: 0 Fehler ✓
