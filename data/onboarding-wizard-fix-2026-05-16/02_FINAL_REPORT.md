# Abschluss-Log – Onboarding Wizard Fix

**Datum:** 2026-05-16

## Geänderte Dateien

### 1. `dashboard-react/src/app/page.tsx`

**Vorher:**
- `useEffect` lief sofort beim Mount, `user` war noch `null`
- Kein Wait auf `isLoading` → Race Condition → Wizard-Flash trotz eingeloggtem User
- `if (!isClient) return null` — kein Schutz während Auth lädt

**Nachher:**
- `isLoading` aus `useAuth()` destrukturiert
- `useEffect` hat separaten Guard: `if (isLoading) return`
- `user?.onboarding_completed === true` → synchronisiert auch localStorage-Flag
- `if (!isClient || isLoading) return null` — kein Render vor abgeschlossener Auth

### 2. `dashboard-react/src/components/onboarding/OnboardingWizard.tsx`

**Vorher:**
- X-Button und „Überspringen"-Button riefen nur `onComplete()` auf
- Kein `markOnboardingCompleted()`, kein `localStorage.setItem()` beim Schließen via X
- Beim nächsten Mount: localStorage leer → Wizard wieder da

**Nachher:**
- Neue Funktion `handleSkip()` ruft `markOnboardingCompleted()` + `localStorage.setItem('complyo_onboarding_completed','true')` + `onComplete()` auf
- X-Button (Z. 379) und „Überspringen"-Button (Z. 439) nutzen `handleSkip`
- Erfolgs-Flow (Zeilen 227, 233) unverändert — ruft direkt `onComplete()` nach eigenem `markOnboardingCompleted()` + `localStorage.setItem()`

### 3. `dashboard-react/src/components/dashboard/DomainHeroSection.tsx`

**Kein Fix nötig:** Else-Zweig (Z. 487–506) enthält bereits einen vollständigen Empty-State mit Globe-Icon, Headline und CTA.

## Vorher/Nachher-Verhalten

| Szenario | Vorher | Nachher |
|----------|--------|---------|
| Browser-Neustart bei eingeloggtem User | Wizard erscheint (Race Condition) | Direkt Dashboard |
| X-Button klicken | Wizard verschwindet, beim nächsten Start wieder da | Wizard persistiert Skip, kommt nicht mehr |
| Skip + Browser-Neustart | Wizard wieder da, leeres Dashboard | Dashboard mit Empty-State |
| Normal-Flow | Funktioniert | Unverändert |

## Optionale Folge-Iterationen

- **Backend-Persistierung des Skip-Status:** Falls `/api/auth/complete-onboarding` auch beim Skip aufgerufen werden soll (damit nach Re-Login aus neuem Browser kein Wizard erscheint), kann `handleSkip` diesen Endpoint aufrufen. Aktuell verhindert das localStorage-Flag nur den Browser-Neustart — nicht einen Login aus einem anderen Browser/Gerät.
- **Confirm-Dialog beim Skip:** `window.confirm('Onboarding wirklich überspringen?')` vor `handleSkip` kann Accidental-Skips reduzieren.
