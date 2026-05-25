# Early-Access Landing – Fortschritt

**Projekt:** complyo.de / complyo.tech Early-Access Landing  
**Start:** 2026-05-15  
**Status:** Implementierung abgeschlossen, Deployment ausstehend

---

## Status-Übersicht

| Task | Beschreibung | Status |
|---|---|---|
| T1 | /data Dokumentation anlegen | ✅ Done |
| T2 | DB-Migration create_waitlist_leads.sql | ✅ Done |
| T3 | Backend: API-Endpoints | ✅ Done |
| T4 | Backend: E-Mail-Template | ✅ Done |
| T5 | Frontend: page.tsx Routing | ✅ Done |
| T6 | Frontend: EarlyAccessLanding.tsx | ✅ Done |
| T7 | Frontend: NavBar vereinfacht | ✅ Done |
| T8 | Frontend: HeroSection angepasst | ✅ Done |
| T9 | Frontend: WebsiteScanner CTA | ✅ Done |
| T10 | Frontend: JoinEarlySection | ✅ Done |
| T11 | Frontend: API-Wrapper | ✅ Done |
| T12 | Frontend: FooterSection | ✅ Done |
| T13 | Frontend: Smooth-Scroll CSS | ✅ Done |
| T14 | A/B-Test deaktivieren | ✅ Done |
| T15 | Tests test_waitlist.py | ✅ Done |
| T16 | Deployment-Vorbereitung | ✅ Done (Anleitung unten) |
| T17 | Rollback-Doku | ✅ Done |

---

## Geänderte / Neue Dateien

### Neu erstellt
- `backend/migrations/create_waitlist_leads.sql`
- `backend/tests/test_waitlist.py`
- `landing-react/src/components/saas-landing/EarlyAccessLanding.tsx`
- `landing-react/src/components/saas-landing/JoinEarlySection.tsx`
- `data/early-access-landing-plan.md`
- `data/early-access-landing-progress.md`

### Geändert
- `backend/lead_routes.py` — POST /api/leads/waitlist + GET /api/leads/waitlist/confirm
- `backend/email_service.py` — send_waitlist_confirmation()
- `backend/MIGRATIONS.md` — Migration registriert
- `landing-react/src/app/page.tsx` — EarlyAccessLanding statt ABTestRouter
- `landing-react/src/components/saas-landing/NavBar.tsx` — Nur Logo + Waitlist-CTA
- `landing-react/src/components/saas-landing/HeroSection.tsx` — CTAs zu #waitlist / #scanner
- `landing-react/src/components/saas-landing/FooterSection.tsx` — Produkt-Spalte entfernt
- `landing-react/src/components/landing/WebsiteScanner.tsx` — id="scanner", CTA → #waitlist
- `landing-react/src/lib/api.ts` — leadsApi.joinWaitlist()
- `landing-react/src/types/api.ts` — WaitlistJoinRequest / WaitlistJoinResponse Typen
- `landing-react/src/app/globals.css` — scroll-behavior + scroll-margin-top

### Unverändert (für Rollback)
- `landing-react/src/app/ABTestRouter.tsx`
- Alle alten Landing-Varianten (alfima, modern, landing, saas-landing/SaasLanding.tsx)

---

## Deployment-Anleitung

### 1. DB-Migration ausführen (Production)
```bash
cd /home/clawd/saas/legal/backend
psql $DATABASE_URL -f migrations/create_waitlist_leads.sql
```

### 2. Backend-Container neu starten
```bash
docker compose restart backend
# oder wenn kein Docker:
# systemctl restart complyo-backend
```

### 3. Landing-Frontend bauen und deployen
```bash
cd /home/clawd/saas/legal/landing-react
npm run build
# Danach Container-Deploy oder PM2-Restart:
docker compose build landing && docker compose up -d landing
# Port: 3003 (complyo.de → 3003 laut nginx/complyo.de)
```

### 4. Smoke-Test
- [ ] `https://complyo.de` → zeigt neue Early-Access-Seite
- [ ] `https://complyo.tech` → zeigt neue Early-Access-Seite
- [ ] Scanner: URL eingeben, scannen, Ergebnis erscheint, CTA → scrollt zu #waitlist
- [ ] Waitlist: Formular ausfüllen (Name + E-Mail + Consent), absenden → Erfolgsbox
- [ ] Bestätigungsmail empfangen, Link klicken → Redirect `/?confirmed=1`
- [ ] NavBar: Nur Logo + "Auf Warteliste" Button sichtbar
- [ ] Footer: Nur Brand + Rechtliches + Kontakt

### 5. Env-Variablen prüfen
```
FRONTEND_URL=https://complyo.de
SMTP_HOST=...
SMTP_PORT=587
SMTP_USERNAME=...
SMTP_PASSWORD=...
SENDER_EMAIL=noreply@complyo.de
SECRET_SALT=<zufälliger-starker-salt>
```

---

## Rollback-Anleitung (< 5 Minuten)

1. `landing-react/src/app/page.tsx` editieren:
   ```tsx
   'use client';
   import ABTestRouter from './ABTestRouter';
   export const dynamic = 'force-dynamic';
   export default function Page() { return <ABTestRouter />; }
   ```
2. `npm run build` + Container-Deploy
3. Tabelle `waitlist_leads` bleibt erhalten (für späteren Re-Launch nutzbar)

---

## Log

### 2026-05-15
- T1: Dokumentationsdateien angelegt
- T2: DB-Migration create_waitlist_leads.sql mit UPSERT-Indexes
- T3: POST /api/leads/waitlist + GET /api/leads/waitlist/confirm in lead_routes.py
- T4: send_waitlist_confirmation() mit HTML + Plaintext-Template in email_service.py
- T5: page.tsx → EarlyAccessLanding (ABTestRouter entkoppelt)
- T6: EarlyAccessLanding.tsx als neue Kompositions-Seite
- T7: NavBar.tsx vereinfacht (nur Logo + Waitlist-CTA)
- T8: HeroSection.tsx – CTAs zu #waitlist / #scanner, Social-Proof angepasst
- T9: WebsiteScanner.tsx – id="scanner", Ergebnis-CTA → #waitlist
- T10: JoinEarlySection.tsx – Formular mit E-Mail/Name/Telefon/Consent, alle States
- T11: leadsApi.joinWaitlist() in api.ts, Typen in types/api.ts
- T12: FooterSection.tsx – Produkt-Spalte entfernt, nur Rechtliches + Kontakt
- T13: globals.css – scroll-behavior + scroll-margin-top für #scanner + #waitlist
- T14: ABTestRouter aus page.tsx entkoppelt (Datei selbst bleibt)
- T15: test_waitlist.py mit 9 Test-Cases (Happy-Path, Honeypot, Consent, Duplicate, Rate-Limit, Token-Confirm)
- T16+T17: Deployment-Anleitung + Rollback dokumentiert
