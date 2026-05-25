# Smoke-Test Szenarien

**Datum:** 2026-05-16  
**Status:** Manuell zu verifizieren

## Szenarien

| # | Szenario | Erwartetes Verhalten | Status |
|---|----------|----------------------|--------|
| A | Eingeloggt, `onboarding_completed=true`, Browser neu starten | Direkt Dashboard, kein Wizard | Manuell prüfen |
| B | Neuer User, eingeloggt, `onboarding_completed=false`, kein localStorage-Flag | Wizard erscheint | Manuell prüfen |
| C | Wizard mit X schließen, Browser neu starten | Dashboard mit Empty-State, kein Wizard | Manuell prüfen |
| D | Normal-Flow (Domain eingeben → scannen → fertigstellen) | Funktioniert unverändert | Manuell prüfen |
| E | „Überspringen"-Button in Step 0 klicken, Browser neu starten | Dashboard, kein Wizard | Manuell prüfen |

## Hinweise

- `localStorage`-Key: `complyo_onboarding_completed` (Wert: `'true'`)
- Backend-Feld: `user.onboarding_completed` (Boolean)
- Bei Szenario A: Falls Backend-Flag nicht gesetzt ist, greift localStorage als Fallback
