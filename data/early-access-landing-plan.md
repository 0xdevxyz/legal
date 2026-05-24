# Early-Access Landing Page – Plan

**Datum:** 2026-05-15  
**Domains:** complyo.de, complyo.tech  
**Status:** In Umsetzung

## Ziel

Vorübergehende, schlanke Startseite, die ausschließlich den Website-Scanner und eine "Join Early"-Waitlist zeigt. Keine Pricing-, Features- oder sonstige Marketingabschnitte.

## Struktur

```
NavBar (vereinfacht: nur Logo + Waitlist-CTA)
  ↓
HeroSection (CTA → #waitlist, Demo → #scanner)
  ↓
WebsiteScanner (id="scanner", Ergebnis-CTA → #waitlist)
  ↓
JoinEarlySection (id="waitlist", Formular mit Double-Opt-In)
  ↓
FooterSection (nur Rechtliches bleibt)
```

## Neue Dateien

| Datei | Zweck |
|---|---|
| `backend/migrations/create_waitlist_leads.sql` | DB-Tabelle für Warteliste |
| `backend/tests/test_waitlist.py` | Pytest-Tests für Waitlist-Endpoints |
| `landing-react/src/components/saas-landing/EarlyAccessLanding.tsx` | Neue Kompositions-Seite |
| `landing-react/src/components/saas-landing/JoinEarlySection.tsx` | Waitlist-Formular |

## Geänderte Dateien

| Datei | Änderung |
|---|---|
| `backend/lead_routes.py` | POST /api/leads/waitlist + GET /api/leads/waitlist/confirm |
| `backend/email_service.py` | send_waitlist_confirmation() |
| `backend/MIGRATIONS.md` | Migration registrieren |
| `landing-react/src/app/page.tsx` | ABTestRouter → EarlyAccessLanding |
| `landing-react/src/components/saas-landing/NavBar.tsx` | Vereinfacht |
| `landing-react/src/components/saas-landing/HeroSection.tsx` | CTA-Ziele |
| `landing-react/src/components/saas-landing/FooterSection.tsx` | Produkt-Spalte entfernt |
| `landing-react/src/components/landing/WebsiteScanner.tsx` | Ergebnis-CTA → #waitlist |
| `landing-react/src/lib/api.ts` | joinWaitlist() Funktion |
| `landing-react/src/types/api.ts` | WaitlistJoinRequest Typen |
| `landing-react/src/app/globals.css` | scroll-behavior + scroll-margin-top |

## Rollback

1. `landing-react/src/app/page.tsx` → `<ABTestRouter />` zurück
2. Build deployen (< 5 min)
3. Tabelle `waitlist_leads` bleibt für späteren Re-Launch erhalten

## Sicherheit

- DSGVO-Consent required (client + server)
- Double-Opt-In via Token-Mail
- Honeypot-Feld gegen Bots
- Rate-Limit: max 3 Submits/IP/10min
- IP als SHA-256-Hash gespeichert (kein Klartext)
- Confirm-Token: secrets.token_urlsafe(32), 7 Tage, single-use
