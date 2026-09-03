# Agentur / White-Label

**Stand:** 2026-07-17 · **Status:** 🟢 live

## Ziel
Agenturen verwalten mehrere Kundenwebsites unter einem Account: Sites werden einem
Kunden (`client_name`) zugeordnet, Consent-Statistiken je Kunde aggregiert und als
PDF-Report mit **eigenem Agentur-Logo** (White-Label) ausgeliefert. Kein eigenes
Mandantenmodell — alles hängt am `user_id` der Agentur.

## Architektur (end-to-end)
- **Routes:** Agency-Block in `backend/cookie_compliance_routes.py` (Zeilen ~3477–3750),
  alle mit `get_current_user_required` → Auth vorhanden, Ownership über `user_id`-Filter.
  - `GET /api/cookie-compliance/agency/stats` — 30-Tage-Consent-Stats je Site.
    `cookie_compliance_stats` INNER JOIN `cookie_banner_configs ON c.user_id = $1` →
    Ownership im JOIN erzwungen.
  - `PATCH /api/cookie-compliance/agency/sites/{site_id}/client` — setzt `client_name`/
    `client_email`. `WHERE site_id = $3 AND user_id = $4`; asyncpg-Rückgabe `"UPDATE 0"`
    → 404. Fremde site_id ist damit nicht beschreibbar.
  - `GET /api/cookie-compliance/agency/clients` — Gruppierung nach `client_name`
    (site_count, impressions, acceptance_rate), `LEFT JOIN cookie_compliance_stats`.
  - `POST /api/cookie-compliance/agency/logo` — PNG-only (`content_type == "image/png"`),
    max 2 MB, Ablage über `file_storage`, Pfad in `users.agency_logo_path`.
    `GET /agency/logo` liefert die URL, `GET /agency/logo/file` streamt die Bytes
    (beide auth-pflichtig, Pfad aus der eigenen `users`-Zeile → kein Pfad-Parameter).
  - `GET /api/cookie-compliance/agency/client-report/{client_name}` — je Site letzter
    Score via `LEFT JOIN LATERAL` auf `scan_history`, Top-3-Issues nach
    `severity_rank`, PDF via `AgencyReportGenerator.generate(...)`, Dateiname
    über `isalnum()`-Whitelist entschärft.
- **PDF:** `backend/agency_report_generator.py` — `generate(client_name, sites,
  agency_logo_bytes)`; Logo wird eingebettet, sonst Complyo-Default.
- **Frontend:** `dashboard-react/src/app/agency/page.tsx` (ruft `/agency/stats` +
  `/agency/clients`), `src/components/agency/AgencyLogoUpload.tsx`,
  `src/components/agency/ClientGroup.tsx`. Add-on-Kauf über `/api/stripe/create-checkout`.

## Plan-/Kontingent-Kopplung
- Agentur-Add-ons erhöhen `websites_max` **additiv**: `agency_extra` +1, `agency2` +25.
  Details in [[billing-plans-addons]].
- `get_user_site_ids()` (`backend/cookie_compliance_routes.py:184`) ist **bewusst**
  multi-site-fähig: die einzelne primäre Website (`get_user_website_site_id`) reicht für
  Agenturen nicht, sonst landen Saves auf der falschen Site. Siehe
  [[cookie-consent-management]].

## DB
Gegen die Alembic-Baseline (`backend/alembic/versions/20260717_baseline_2026_07.py`,
Schema-Dump `backend/alembic/baseline_schema.sql`) verifiziert:
- `users.agency_logo_path text` — Pfad unter `FILE_STORAGE_PATH` (Phase 10 AGENCY-03).
- `cookie_banner_configs.client_name varchar(255)`, `.client_email varchar(255)`
  (Phase 10 AGENCY-01) + Partial-Index `idx_banner_config_user_client`
  `(user_id, client_name) WHERE client_name IS NOT NULL`.
- Keine eigene Agentur-/Mandanten-Tabelle. Gelesen werden zusätzlich
  `cookie_compliance_stats`, `tracked_websites`, `scan_history`.
- Kein JSONB-Write im Agency-Block → asyncpg-JSONB-Regel hier nicht berührt.

## Bekannte Lücken / Offen
- **`backend/ai_fix_engine/white_label.py` ist toter Code** (verifiziert: `grep` über alle
  `*.py` findet **keinen** Importeur von `white_label`/`WhiteLabelProcessor`). Inhaltlich
  gehört die Datei ohnehin **nicht** zum Agentur-White-Label: `WhiteLabelProcessor` ist ein
  Branding-Cleaner, der eRecht24-Marken aus importierten Rechtstexten entfernt. Deckt sich
  mit dem Tote-Code-Verdacht aus [[ai-fix-engine]] → Kandidat zum Löschen.
- **Kein Plan-Gate:** Die Agency-Endpunkte prüfen nur Auth, nicht `plan_type`. Jeder
  eingeloggte User kann Clients zuweisen, Logo hochladen und Kundenreports ziehen. Ob das
  gewollt ist (Gate rein über `websites_max`), ist **zu klären**.
- **Logo-Upload validiert nur den Client-`Content-Type`**, nicht den PNG-Magic-Header —
  beliebige ≤2-MB-Bytes landen im Storage und werden von `/agency/logo/file` mit
  `image/png` zurückgeliefert. Niedriges Risiko (nur der Uploader liest die Datei), aber
  Magic-Byte-Prüfung fehlt.
- `client-report` joint `scan_history` über `url = c.last_scan_url`; ist `last_scan_url`
  NULL, fällt die Site auf `site_id` als Anzeige-URL zurück und hat keinen Score.
- Kundenzugriff selbst (Login/Read-only-Portal für den Endkunden) existiert nicht — der
  Report ist ein Agentur-seitiger PDF-Pull.
