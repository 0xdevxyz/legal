# Complyo – Entwicklungsstand & Offene Tasks

> **Stand:** 2026-04-21  
> **Zweck:** Einstiegspunkt für jede neue Entwicklungssession – was ist offen, was läuft, wo ansetzen.

---

## Aktueller Systemstatus

| Service | Status | URL |
|---------|--------|-----|
| Backend API | Live | api.complyo.de |
| Dashboard | Live | app.complyo.de |
| Landing | Live | complyo.de |
| PostgreSQL | Running | intern |
| Redis | Running | intern |
| NGINX | Running | Proxy |

---

## Was vollständig implementiert ist

- User Auth (Firebase + JWT, Refresh-Tokens)
- Website-Scanner (Quick / Base / Deep, alle 4 Säulen)
- KI-Fix-Engine (Unified Fix Engine, 5 Handler, 3 AI-Modelle + Template-Fallback)
- Cookie-Banner v2 (DSGVO/TTDSG, 17 Sprachen, TCF 2.2, Consent-Logs)
- Cookie-Settings-Modal (4 Kategorien, Toggle-Switches, Consent-Persistierung) — **NEU 2026-04-21**
- Accessibility-Widget v6 (30+ Features, WCAG 2.1 AA)
- Deployment-Engine (FTP, SFTP, GitHub PR, Netlify, Vercel, WordPress, ZIP)
- Backup & Rollback (30 Tage, One-Click-Restore)
- Audit Trail (`fix_application_audit`)
- Widget-Analytics Persistierung in `widget_events` Tabelle — **NEU 2026-04-21**
- Upsell-Check mit echter DB-Abfrage auf `widget_usage_stats` — **NEU 2026-04-21**
- Widget-Config aus `cookie_banner_configs` DB laden — **NEU 2026-04-21**
- Expert-Service Email-Notifications (Kunden + Team) — **NEU 2026-04-21**
- eRecht24-Integration (API + Webhook, Rechtstexte-SDK)
- Stripe-Payment (Subscriptions + Webhooks + Freemium-Modell)
- Legal-News-Feed (RSS + KI-Klassifizierung)
- Legal-Change-Monitoring
- EU AI Act Modul (Risiko-Klassifizierung + Dokumenten-Generator)
- A/B-Testing (Cookie-Banner-Varianten)
- IAB TCF 2.2 Support
- GDPR-Datenrechte (Art. 17 & 20)
- i18n (DE/EN)
- Dashboard (Score, Issues, Fix-Modal, History, Quick Nav)
- Landing (6 A/B-Varianten)

---

## Offene Tasks (Technical Debt)

Vollständige Liste: `docs/TECHNICAL_DEBT.md`

### Kritisch (vor nächstem Major-Release)

| Problem | Datei | Zeile | Status |
|---------|-------|-------|--------|
| ~~Auth fehlt in `ai_legal_routes.py`~~ | `ai_legal_routes.py` | 20 | ✅ Erledigt v1 |
| ~~Auth fehlt in `cookie_compliance_routes.py`~~ | `cookie_compliance_routes.py` | 351 | ✅ Erledigt v1 |
| ~~Auth fehlt in `widget_routes.py`~~ | `widget_routes.py` | 462 | ✅ Erledigt 2026-04-21 |
| Stripe Price-IDs Fallback `price_XXXXX` | `stripe_routes.py` | 32 | Offen |

### Hoch (zeitnah)

| Problem | Datei | Zeile | Status |
|---------|-------|-------|--------|
| ~~Widget-Analytics nicht in DB~~ | `widget_routes.py` | 178 | ✅ Erledigt 2026-04-21 |
| ~~Widget-Usage-Count nicht aus DB~~ | `widget_routes.py` | 261 | ✅ Erledigt 2026-04-21 |
| ~~Widget-Config nicht aus DB~~ | `widget_routes.py` | 326 | ✅ Erledigt 2026-04-21 |
| ~~ML-Feedback nicht gespeichert~~ | `ai_legal_routes.py` | 173 | ✅ Via ai_feedback_learning |
| ~~Widget-Analytics (public)~~ | `public_routes.py` | 1388 | ✅ Erledigt 2026-04-21 |
| Admin-Check fehlt | `ai_legal_routes.py` | 632, 673 | Offen |
| Admin-Check fehlt | `legal_change_routes.py` | 364 | Offen |

### Mittel (geplante Features)

| Feature | Datei | Zeile | Status |
|---------|-------|-------|--------|
| LiveValidator für Fix-Validierung | `main_production.py` | 624 | Offen |
| Staging-Preview-Frontend | `fix_apply_routes.py` | 348 | Offen |
| Background-Task-Tracking | `fix_apply_routes.py` | 381 | Offen |
| ~~Email-Service in Expert-Routes~~ | `expert_service_routes.py` | 271 | ✅ Erledigt 2026-04-21 |
| Automatische Fix-Anwendung | `legal_change_routes.py` | 549 | Offen |
| ~~Cookie-Settings-Modal~~ | `widgets/cookie_consent.js` | 214 | ✅ Erledigt 2026-04-21 |

### Niedrig / Beabsichtigt (nicht anfassen)

- `[TODO: ...]` Platzhalter in `ai_act_doc_generator.py` – für Benutzer gedacht
- `<!-- TODO: An Ihre Bedürfnisse anpassen -->` in Code-Handles – Template-Kommentare
- Beispiel-Platzhalter in `compliance_engine/prompts/` – korrekt so

---

## Vorbereitet aber nicht aktiviert

| Feature | Status | Aktivierung |
|---------|--------|------------|
| Unified Fix Engine (vollständig) | Code fertig, in Produktion | Bereits aktiv via `erecht24_routes_v2.py` |
| Widget-Manager | Code fertig | Import aktivieren |
| White-Labeling (Enterprise) | Code fertig | Konfiguration nötig |
| Monitoring-System | Code fertig | Sentry-DSN setzen |
| Staging-Preview | Backend fertig, Frontend TODO | Frontend-Komponente bauen |

---

## Backlog (Roadmap)

Vollständige Liste: `md/ROADMAP.md`

| Feature | Priorität | Notiz |
|---------|-----------|-------|
| TCF 2.2 Full Support (Enterprise) | Niedrig | Nur für große Publisher |
| Mobile App | Geplant | – |
| Browser-Extension | Geplant | – |
| VS-Code-Plugin | Geplant | – |
| Figma-Plugin | Geplant | – |
| Advanced AI-Learning | In Entwicklung | `ai_feedback_learning.py` |

---

## Bekannte Konfigurationsprobleme

1. **Domains:** System war auf `complyo.tech` konfiguriert, läuft jetzt auf `complyo.de`  
   → `docker-compose.yml` VIRTUAL_HOST bereits auf `complyo.de` angepasst  
   → SSL-Zertifikate prüfen: `scripts/ssl-setup.sh`

2. **eRecht24-API-Key:** Optional, nur für Premium-Rechtstexte nötig  
   → Ohne Key: Template-Fallback aktiv

3. **UNLIMITED_FIXES / BYPASS_PAYMENT:** Beide auf `false` in Production  
   → Für Testzwecke: `.env` anpassen

---

## Wichtige Konventionen

- **DB-Zugriff:** Immer über `database_service.py` (`db_service`)
- **Auth:** Immer `Depends(get_current_user)` aus `dependencies.py`
- **AI-Calls:** Immer über `AIApiClient` in `ai_fix_engine/unified_fix_engine.py` (Retry + Fallback)
- **Fehlerbehandlung:** `HTTPException` mit klaren `detail`-Strings
- **Logging:** `logging.getLogger(__name__)` – kein `print()` in Production
- **Migrationen:** Neue SQL-Dateien nach `backend/migrations/`, Namensschema: `create_XYZ.sql`
- **Neue Routes:** In eigene `*_routes.py` Datei, Import + `include_router` in `main_production.py`

---

## Nächste Session – Checkliste

Vor dem Start einer neuen Session:

1. `docker-compose ps` – alle Container laufen?
2. `curl https://api.complyo.de/health` – API erreichbar?
3. `docs/SYSTEM_OVERVIEW.md` lesen (diese Übersicht)
4. Relevante Route-Datei und zugehörige Service-Datei lesen
5. Bestehende Tests in `backend/tests/` prüfen bevor Änderungen

---

## Referenz: Kritische Dateipfade

| Was | Pfad |
|-----|------|
| FastAPI Entry-Point | `backend/main_production.py` |
| DB-Service | `backend/database_service.py` |
| Auth-Dependency | `backend/dependencies.py` |
| Auth-Service | `backend/auth_service.py` |
| Fix-Engine | `backend/ai_fix_engine/unified_fix_engine.py` |
| Scanner | `backend/compliance_engine/scanner.py` |
| Alle Checks | `backend/compliance_engine/checks/` |
| Dashboard-Entry | `dashboard-react/src/app/page.tsx` |
| API-Client | `dashboard-react/src/lib/api.ts` |
| Auth-Context | `dashboard-react/src/contexts/AuthContext.tsx` |
| Dashboard-Types | `dashboard-react/src/types/api.ts` |
| Docker Compose | `docker-compose.yml` |
