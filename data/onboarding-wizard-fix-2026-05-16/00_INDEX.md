# Onboarding Wizard Fix – Index

**Datum:** 2026-05-16

## Problem

1. Browser-Neustart bei eingeloggtem User → Onboarding-Wizard erscheint erneut
2. X-Button schließt Wizard → leeres Dashboard; beim nächsten Browser-Start Wizard wieder da

## Root Cause

| # | Datei | Zeilen | Problem |
|---|-------|--------|---------|
| 1 | `dashboard-react/src/app/page.tsx` | 32–42 | `useEffect` läuft sofort beim Mount; `user === null` (Auth-Context lädt noch via `isLoading`). Fallthrough zu `localStorage`-Check → leer → `showOnboarding=true`. |
| 2 | `dashboard-react/src/components/onboarding/OnboardingWizard.tsx` | 372–378 | X-Button ruft nur `onComplete()` auf — kein `markOnboardingCompleted()`, kein `localStorage.setItem()`. |
| 3 | `dashboard-react/src/app/page.tsx` | 44 | `isLoading` wird nicht als Render-Gate genutzt → Race Condition |

## Geänderte Dateien

- `dashboard-react/src/app/page.tsx`
- `dashboard-react/src/components/onboarding/OnboardingWizard.tsx`
- `dashboard-react/src/components/dashboard/DomainHeroSection.tsx` (ggf.)

## Verlinkung

- [01_TEST_RESULTS.md](./01_TEST_RESULTS.md)
- [02_FINAL_REPORT.md](./02_FINAL_REPORT.md)
