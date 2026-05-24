# Bug: Score 0 bei neuer Seite

## Problem
Wenn eine neue Seite analysiert wird, zeigt das Dashboard Score 0.

## Root Causes

### Bug 1 (Fix applied): DomainHeroSection - falsches Feldname
`DomainHeroSection.tsx` Zeile 105-106 (Fallback Load via `getTrackedWebsites`):

```ts
// VORHER (falsch)
lastScan: latestWebsite.last_scan || new Date().toISOString(),
complianceScore: latestWebsite.compliance_score || 0,

// NACHHER (korrekt)
lastScan: latestWebsite.last_scan_date || latestWebsite.last_scan || new Date().toISOString(),
complianceScore: latestWebsite.last_score ?? latestWebsite.compliance_score ?? 0,
```

Backend gibt `last_scan_date` und `last_score` zurück (TrackedWebsite interface), nicht `last_scan` oder `compliance_score`. Dadurch war `complianceScore` immer `0` wenn die Website aus der DB geladen wurde.

### Bug 2 (Analyse): Priority-Chain in WebsiteAnalysis
`WebsiteAnalysis.tsx` Zeile 62:
```ts
const analysisData = latestScanData || fetchedAnalysisData || storedAnalysisData;
```
`latestScanData` hat höchste Priorität. Bei Race-Conditions kann ein alter Scan aus der DB den frischen Scan überschreiben. Kein Fix nötig solange Backend korrekt antwortet.

## Betroffene Dateien
- `dashboard-react/src/components/dashboard/DomainHeroSection.tsx` → Fix applied
