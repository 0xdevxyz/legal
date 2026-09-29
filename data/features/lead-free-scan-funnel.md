# Lead- / Free-Scan-Funnel

**Stand:** 2026-09-28 · **Status:** 🟢 live (Warteliste, Double-Opt-in, Scan ohne Login, Kurzlinks)

## Ziel
Akquisekanal: kostenloser Compliance-Scan ohne Login auf der Landing (`/bfsg-check/`,
`/dsgvo-website-check/`), dazu die Early-Access-**Warteliste** (100 Plätze, Angebot
`ea100-49eur-12m`) mit Double-Opt-in (§ 7 UWG, Art. 6 Abs. 1 lit. a DSGVO). Der ältere
Lead-Pfad mit Report per Mail besteht im Backend weiter.

## Architektur (end-to-end)
- **Kanal-Kurzlinks** (Host-nginx `/etc/nginx/sites-enabled/complyo.de`, Kopie
  `nginx/complyo.de`, Commit `f77e6e2`): `/li /ig /tt /yt /fb` → 302 auf
  `/early-access/?utm_source=<kanal>&utm_medium=social&utm_campaign=ea100`, `/scan` →
  `/bfsg-check/?utm_source=social...`. `?c=<kennung>` wird als `utm_content` durchgereicht
  (`[A-Za-z0-9_-]{1,40}`). Live mit curl geprüft am 2026-09-28, alle sechs antworten 302 wie
  beschrieben, `/li?c=P01` → `utm_content=P01`.
- **Scan-Einstieg:** `backend/public_routes.py` (Router-Prefix `/api`)
  - `POST /api/analyze` (Z. 185): `Depends(get_current_user)`, eingeloggter Pfad, speichert.
  - `POST /api/analyze-auftrag` (Z. 2294) + `GET /api/analyze-auftrag/{kennung}` (Z. 2340):
    entkoppelter Weg, den die Landing zuerst nimmt (`landing-react/src/lib/api.ts:153`).
    Rate-Limit `analyze_preview` 3/60 s; Auftrag und Ergebnis liegen nur in Redis
    (`scan_auftraege.TTL_SEKUNDEN = 3600`).
  - `POST /api/analyze-preview` (Z. 2245): synchroner Rückfall (`api.ts:170`), ohne Auth,
    `rate_limit("analyze_preview", 3, 60)` plus `scan_platz`. Scan in
    `fuehre_preview_scan_aus()` (Z. 2102). In diesem Pfad steht kein INSERT/UPDATE; es bleiben
    Redis-Zähler (Rate-Limit, KI-Budget über `ai_budget.kosten_buchen`) und Log-Zeilen mit der
    URL. Ob `ComplianceScanner` selbst etwas in die DB schreibt, nicht vollständig geprüft
    (in `scanner.py`, `ki_zugang.py`, `ai_budget.py` kein `INSERT INTO`).
    Probescans des Betriebswächters laufen über denselben Endpunkt (`_ist_probescan`).
  Details in [[scan-analyze-kern]].
- **Warteliste:** `backend/lead_routes.py` (Router `/api/leads`, `main_production.py:711`)
  - `GET /waitlist/token` (Z. 387): signiertes Formular-Token (HMAC), einmal verwendbar
    (`_token_entwerten` über Redis), ersetzt die alte Zeitfalle (`1f29706`).
  - `POST /waitlist` (Z. 403): Honeypot `website` → 204; Formular-Token; Cloudflare Turnstile
    (**in Prod aus**, `TURNSTILE_SECRET` nicht gesetzt); In-Memory-Rate-Limit 3/10 min je
    IP-Hash (`_check_rate_limit`, Z. 371), Client-IP über `get_client_ip` (`28715eb`, `0926bcd`);
    MX-Prüfung der Domain (`domain_nimmt_mail_an`, Z. 257). INSERT in `waitlist_leads` mit
    `campaign`, `utm_*`, `landing_path`, `angebot` (serverseitig, nicht aus dem Request).
    Bestätigungsmail an den Interessenten und Admin-Meldung bei jedem Eintrag (`416063a`) als
    BackgroundTasks. `source` wird gesäubert statt gegen eine Allowlist geprüft.
  - `GET /waitlist/plaetze` (Z. 559): Zähler aus echten Zeilen; live
    `{"gesamt":100,"vergeben":0,"frei":100}`.
  - `GET /waitlist/confirm?token=` (Z. 593): prüft Ablauf (7 Tage), setzt `confirmed_at`,
    löscht den Token, zieht `platz_nr` aus `waitlist_platz_seq` nur bei gesetztem `angebot` und
    nur bis `EARLY_ACCESS_PLAETZE` (100), zweite Admin-Meldung mit Platz („Platz N“ vorn im
    Betreff, `edcb00e`), Redirect auf `landing_path?confirmed=1&platz=N`. `landing_path` nur als
    eigener Pfad zulässig (kein offener Redirect).
  - Frontend: `landing-react/src/components/kampagne/WartelistenFormular.tsx` liest
    `utm_*` aus der URL und sendet `campaign` und `landing_path`; `PlatzZaehler.tsx` zeigt die
    freien Plätze.
- **Klassischer Lead-Pfad** (gleiche Datei, „Legacy lead endpoints“):
  - `POST /collect` (Z. 714), `GET /verify/{token}` (Z. 842, danach Report-Mail mit PDF),
    `GET /stats` (Z. 921, `Depends(require_admin)`, live 401 ohne Login),
    `POST /unsubscribe` (Z. 959, signierter HMAC-Token).
  - Kein Frontend ruft `/collect` auf (grep in `landing-react/src`, `dashboard-react/src`);
    nur `landing-react/src/app/verify-email/page.tsx` ruft `/verify/{token}`.
- **E-Mail:** `backend/email_service.py`, einziger Versandweg `_send_email()` (Z. 132).
  `demo_mode` (Z. 44) ist in Prod aus: `SMTP_HOST=mail.complyo.de`, `SMTP_USERNAME` und
  `SMTP_PASSWORD` gesetzt, `ENVIRONMENT=production`. Fiele er an, liefert `_send_email` in Prod
  jetzt `False` statt Erfolg. Tatsächliche Zustellung einer Wartelisten-Mail nicht geprüft
  (seit Containerstart 2026-09-25 keine Anmeldung im Log).

## DB
Alembic-Baseline (`backend/alembic/versions/20260717_baseline_2026_07.py`, Dump
`backend/alembic/baseline_schema.sql`) plus Revisionen:
- `waitlist_leads` (`baseline_schema.sql:3283`); Revision `20260902_0018_waitlist_kampagne`
  ergänzt Kampagnenfelder, `platz_nr` (eindeutiger Index) und Sequenz `waitlist_platz_seq`.
  Live: 1 Zeile (2026-09-07, `source=landing`, Kampagne gesetzt), **unbestätigt**, kein Platz
  vergeben, Sequenz noch nicht gezogen.
- `leads`, `lead_consents`, `communication_log`, `email_verifications`: Revision
  `20260717_0003_missing_lead_and_audit_tables`; `20260729_0008_leads_verification_columns`
  zieht `email_verified`, `verified_at`, `updated_at` nach (`98d1204`). Live: `leads` und
  `lead_consents` leer.
- `analysis_data` wird mit `json.dumps(...)` geschrieben (`database_service.py:87`).

## Bekannte Lücken / Offen
- **[BEHOBEN 2026-09-28] Bestätigungslink der Warteliste führte ins Leere.** `lead_routes.py`
  baute den Link aus `FRONTEND_URL` (`https://complyo.de`); dort geht `/api/` an die Landing,
  live 308 auf 404. Kein Eintrag konnte bestätigt werden, die einzige Anmeldung vom 07.09. blieb
  ohne Platz. Jetzt kommt der Link aus `PUBLIC_API_BASE` (Vorgabe `https://api.complyo.de`),
  wie bei der Cookie-Richtlinie. Wächter in `tests/test_waitlist.py`
  (`test_bestaetigungslink_zeigt_auf_api_host`). Die Anmeldung vom 07.09. hat den toten Link
  erhalten und braucht einen neuen.
- **Turnstile ist aus** (`TURNSTILE_SECRET` leer). Es greifen Honeypot, Formular-Token,
  MX-Prüfung und Rate-Limit.
- **Wartelisten-Rate-Limit ist prozesslokal** (`defaultdict`), nicht Redis wie
  `dependencies.rate_limit`; überlebt keinen Neustart, zählt je Worker.
- **Klassischer Lead-Pfad ohne Einstieg:** `/collect` hat keinen Aufrufer in den Frontends,
  `leads` ist leer. Behalten oder entfernen entscheiden.
- `GET /api/leads/waitlist` (Admin-CSV-Export) weiter nur TODO (`lead_routes.py:691`).
- **Behoben:** fehlende Tabelle `leads` (Revision 0003); Lead-Bestätigung scheiterte an
  fehlenden Spalten und naivem Datum (`98d1204`, Revision 0008); SMTP-`demo_mode` meldete
  Erfolg (jetzt SMTP gesetzt, in Prod `False`); `/stats` ohne Auth; `/unsubscribe` ohne Token;
  `/analyze-preview` ohne Rate-Limit; Gateway-IP statt Besucher-IP im Einwilligungsnachweis
  (`28715eb`); Warteliste in der Datenschutzerklärung ergänzt (`db512a5`).
