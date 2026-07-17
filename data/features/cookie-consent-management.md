# Cookie-Consent-Management (Server-Seite)

**Stand:** 2026-07-17 · **Status:** 🟡 in Arbeit

## Ziel
Server-/Verwaltungsseite des Consent-Managements: Banner-Konfiguration pro Site,
Dienst-Katalog, Consent-Protokollierung als Nachweis (Art. 7 Abs. 1 DSGVO) inkl. CSV-Export
und 3-Jahres-Ablauf, plus Zusatzmodule (Consent Mode, Altersprüfung, Geo, Widerruf).
**Abgrenzung:** das ausgelieferte JS-Widget → [[cookie-consent-widget]]; die öffentliche
Richtlinien-Seite `GET /cookie-richtlinie/{site_id}` → [[cookie-richtlinie-seite]] (nicht
hier doppeln); Playwright-Scan → [[deep-cookie-scanner]]; Agentur-Block → [[agentur-white-label]].

## Architektur (end-to-end)
- **Router (God-File):** `backend/cookie_compliance_routes.py`, 3660 Z., ~50 Routen, Prefix
  `/api/cookie-compliance` (plus die eine prefixlose Public-Route). Funktionsblöcke:
  - **Auth/Helper** (Z. 57–420): `security = HTTPBearer(auto_error=False)`,
    `get_current_user_optional` (JWT + Redis-`jti`-Blacklist) / `get_current_user_required`
    (401), `require_module(user, 'cookie')`, `_url_to_site_id` (Hostname → `complyo-de`),
    `get_user_site_ids` (Multi-Site für Agentur/Expert), `hash_ip_address` (SHA-256),
    `truncate_user_agent` (nur `Chrome/120`, prioritätsbasiert).
  - **Consent-Logging** (Z. 423–531): `POST /consent` — s. u.
  - **Banner-Config** (Z. 537–1157): `GET /my-config`, `GET /config/{site_id}` (öffentlich,
    Widget-Quelle), `POST /config` (voll), `PATCH /config/{site_id}` (partiell),
    `POST /extract-colors` (Farbübernahme von der Kundenseite).
  - **Service-Katalog** (Z. 1162–1309) + **Custom-Services** (Z. 1314–1458).
  - **Statistiken/Logs** (Z. 1463–1673), **Utility/Scan** (Z. 1678–2176), **Consent Mode/
    Alter/TCF** (Z. 2181–2501), **Geo/Forwarding** (Z. 2506–2730), **Policy/Revisionen/
    Import-Export** (Z. 2731–3177), **Reconsent/Bannerless** (Z. 3182–3242), **Widerruf/
    Service-Stats/Rate-Limit** (Z. 3247–3380), **Agentur** (Z. 3386–3660, → [[agentur-white-label]]).
- **Scanner-Anbindung:** `POST /scan` (Z. 1700, Rate-Limit 5/min) → `backend/cookie_scanner_service.py`,
  `backend/compliance_engine/cookie_analyzer.py`, `.../automated_cookie_scanner.py` (HTML/
  BeautifulSoup-Heuristik: `_has_google_analytics`, `_has_meta_pixel`, …). Der HTML-Scanner
  rendert kein JS → JS-injizierte CMP-Banner sind für ihn unsichtbar; Erkennung läuft über
  funktionale/CMP-Signatur-Checks statt Seitentext-Keywords. Echter Scan → [[deep-cookie-scanner]].
- **UI:** `dashboard-react/src/app/cookie-compliance/page.tsx` (706 Z.) mit
  `dashboard-react/src/components/cookie-compliance/*`: `CookieSetupWizard.tsx`,
  `CookieBannerDesigner.tsx`, `ServiceManager.tsx`, `ConsentStatistics.tsx`,
  `ConsentModeSettings.tsx`, `AgeVerification.tsx`, `GeoRestriction.tsx`, `TCFManager.tsx`,
  `RevocationChart.tsx`, `IntegrationGuide.tsx`, `CookiePolicyGenerator.tsx`.
- **asyncpg-JSONB-Regel:** Der Pool hat **keinen** json-Codec — JSONB-Spalten müssen mit
  `json.dumps()` geschrieben werden, rohes `dict`/`list` → `DataError`/500. `POST /config`
  und `PATCH /config` halten sich daran (`texts`, `services`, `show_on_pages`,
  `geo_restriction`); `BannerConfig.texts` ist bewusst `Dict[str, Dict[str, Any]]` statt
  Model, weil Pydantic sonst nicht-serialisierbare Objekte erzeugt (Kommentar Z. 267–271).
  Verstöße s. „Bekannte Lücken".

## Consent-Logging (Nachweis Art. 7)
- `POST /api/cookie-compliance/consent` — ohne Auth (Besucher-Endpunkt), Redis-Sliding-Window
  100/min pro `site_id` (`check_rate_limit`, Z. 3363).
- Gespeichert in **`cookie_consent_logs`**: `site_id`, `visitor_id` (pseudonym),
  `consent_categories` (JSONB inkl. `third_country_consent`, Art. 49 Abs. 1 lit. a),
  `services_accepted` (JSONB), `ip_address_hash` (SHA-256) **oder** `device_fingerprint`,
  `user_agent` (gekürzt), `revision_id` (= `cookie_banner_configs.id` der Site — **nicht** die
  Revisionsnummer), `language`, `banner_shown`, `action` (`accept|revoke|update`), `timestamp`,
  `expires_at` (DB-Default `now() + 3 years`).
- Parallel Tagesaggregat-Upsert in `cookie_compliance_stats` (Impressions, all/partial/reject,
  je Kategorie).
- **Lesen:** `GET /consents/{site_id}` (paginiert, max 1000). **Export:**
  `GET /consents/{site_id}/export` — CSV, `;`-getrennt, UTF-8-BOM (Excel), 13 Spalten;
  authentifiziert + Modul `cookie`.
- **Ablauf:** `DELETE /consents/expired` ruft die PG-Funktion `delete_expired_consents()`
  (`DELETE … WHERE expires_at < NOW()`). Der Docstring behauptet „läuft per Cronjob" — **es
  existiert kein Cron/Timer dafür** (nur manueller Aufruf), s. „Bekannte Lücken".
- **Widerruf:** `POST /revoke` schreibt einen Log-Satz mit `action='revoke'` (alles außer
  `necessary` = false). `GET /revocation-stats/{site_id}` (auth) = Accept/Revoke-Rate,
  `GET /service-stats/{site_id}` (auth) = Zustimmung je Dienst aus `services_accepted`.

## Zusatzmodule (je Endpunkt)
- **Google Consent Mode v2:** `GET|POST /consent-mode-config[/{site_id}]` — `consent_mode_enabled`,
  `consent_mode_default` (ad_storage/analytics_storage/ad_user_data/ad_personalization, Default
  alle `denied`), `gtm_enabled`, `gtm_container_id`. Live funktionsfähig.
- **Altersverifikation:** `GET|POST /age-verification[/{site_id}]` (Art. 8 DSGVO) — Schalter +
  Mindestalter, liefert EU-Ländertabelle (DE 16, AT 14, …). Spalten fehlen in der Live-DB → 500.
- **Geo-Restriction:** `GET|POST /geo-restriction[/{site_id}]` + `GET /geo-check`
  (Land via `CF-IPCountry`, Cache-Tabelle `geo_ip_cache`). Beide in der Live-DB defekt.
- **Consent-Forwarding:** `GET|POST /forwarding[/{site_id}]` — Consent auf Partner-Sites
  spiegeln. Spalten fehlen → 500.
- **Bannerlose Modi:** `GET /bannerless/{site_id}` — nur Content-Blocker, kein Banner. Spalte
  fehlt → 500.
- **Re-Consent-Check:** `GET /reconsent-check/{site_id}?config_hash=` — vergleicht Client-Hash
  mit `config_hash`/`requires_reconsent`; erzwingt neue Einwilligung nach Config-Änderung.
  `requires_reconsent` fehlt → 500.
- **Config-Revisionen:** `GET /revisions/{site_id}` — liest `cookie_consent_revisions`; diese
  Tabelle existiert **nicht**, real vorhanden ist `cookie_banner_revisions` → 500.
- **Import/Export:** `GET /export/{site_id}` (JSON, `version: 1.0`, interne Felder entfernt),
  `POST /import` (nur Update bestehender Config).
- **TCF 2.2:** `GET /tcf/vendors`, `GET|POST /tcf/config` — UI vorbereitet, Tabelle
  `tcf_vendors` vorhanden.

## Service-Katalog
- **`cookie_services`** (Live: **217** aktive Dienste): `service_key` (UNIQUE, Ankerschlüssel für
  Banner-Config, Deep-Scan-Übernahme und Richtlinie), `name`, `category`
  (`necessary|functional|analytics|marketing`), `provider`, `description`, `cookies` (JSONB),
  `template` (JSONB: `domains`, `cookies`, `cookie_lifetime`, `legal_basis`,
  `data_processing_countries`, `description_de/en`), `privacy_url`, `provider_*`-Felder,
  `plan_required`, `is_active`.
- `GET /services?category=&plan=&site_id=` gruppiert nach Kategorie und hängt
  `_enrich_third_country()` an (Art.-49-Flag). `GET /services/{service_key}` = Detail.
- **Custom-Services pro Kunde:** `GET|POST|PUT|DELETE /custom-services/{site_id}[/{service_key}]`
  (`_slugify(name)` → `service_key`), Tabelle `cookie_custom_services` (`backend/cookie_custom_services.sql`).
  Im Katalog-Endpunkt defensiv in try/except (`is_custom: true`), fehlende Tabelle bricht den
  Katalog also nicht — die CRUD-Routen aber schon.
- `cookie_banner_configs.services` hält nur die `service_key`-Liste; die Metadaten kommen beim
  Rendern aus dem Katalog ([[cookie-richtlinie-seite]]).

## DB
- `cookie_banner_configs` — 38 Spalten. Basis (`backend/migrations/create_cookie_compliance_tables.sql`):
  `site_id` UNIQUE, `user_id`, Design (`layout`, 4 Farben, `button_style`, `position`,
  `width_mode`), JSONB `texts`/`services`/`show_on_pages`/`geo_restriction`,
  `auto_block_scripts`, `respect_dnt`, `cookie_lifetime_days`, `show_branding`,
  `custom_logo_url`, `revision`, `is_active`. Live zusätzlich: `consent_mode_enabled`,
  `consent_mode_default`, `gtm_enabled`, `gtm_container_id`, `privacy_policy_url`,
  `cookie_policy_url`, `imprint_url`, `config_hash`, `revision_id`, `scan_completed_at`,
  `last_scan_url`, `client_name`, `client_email`. Diese Zeile ist die Single Source für das
  ausgelieferte Widget (`GET /config/{site_id}`).
- `cookie_consent_logs` — s. o. (Live-Schema weicht von der Migrationsdatei ab).
- `cookie_compliance_stats` — Tagesaggregat, `UNIQUE(site_id, date)`.
- `cookie_services` — Katalog (217).
- `cookie_banner_revisions` — `site_id`, `revision`, `config_snapshot`, `services_snapshot`,
  `changed_by`, `change_reason` (vorhanden, vom Revisions-Endpunkt nicht genutzt).
- `tcf_vendors`, `deep_cookie_scans`, `deep_scan_usage` ([[deep-cookie-scanner]]).
- **Fehlt in der Live-DB, aber im Code referenziert:** `cookie_consent_revisions`,
  `cookie_custom_services`, `geo_ip_cache`.
- PG-Funktion `delete_expired_consents()`.

## Auth-Modell (seit 2026-07-17)
Zuvor hatten **28 von 46 Routen** keine Auth-Prüfung — u. a. lieferte `GET /consents/{site_id}`
personenbezogene Consent-Protokolle ohne Token aus (live 200 verifiziert) und `POST /import`
überschrieb fremde Banner-Configs. Behoben:

- **`require_site_access(site_id, credentials)`** (Z. ~206) — Auth + Modul + **Ownership** gegen
  `get_user_site_ids()` (agenturfähig, mehrere Sites pro Account). Wirft 403 bei fremder
  `site_id`; **kein** stiller Fallback auf die eigene Site wie in `save_banner_config`, und eine
  leere Site-Menge gilt als „darf nichts" statt „darf alles".
- Geschützt: `consents/{site_id}` (+`/export`, das zuvor zwar Auth, aber **keine** Ownership
  prüfte → IDOR), `stats/`, `export/`, `revisions/`, `bannerless/`, `age-verification/`,
  `geo-restriction/`, `forwarding/`, `tcf/config`, `monitor/check/`, `import`, `consent-mode-config`.
- `DELETE /consents/expired` löscht site-übergreifend → **`require_admin`** (`dependencies.py:292`).
- **Bewusst öffentlich** (Widget/Besucher, belegt durch `backend/widgets/*.js`):
  `GET /config/{site_id}`, `POST /consent`, `POST /revoke` (Widerrufsrecht des Besuchers),
  `GET /reconsent-check/{site_id}`, `GET /geo-check`, `GET /services[/{key}]`,
  `GET /policy/{site_id}`, `GET /tcf/vendors`, `GET /health`, `GET /scan/capabilities`.
- Abgesichert durch `backend/tests/test_cookie_consent_auth.py` — der statische Wächter schlägt an,
  sobald eine neue Route ohne Auth hinzukommt, die nicht in der Allowlist steht.

## Bekannte Lücken / Offen
- **Fünf Endpunktgruppen live defekt (500)** wegen fehlender Spalten/Tabellen — verifiziert gegen
  `api.complyo.de`: `revisions/`, `reconsent-check/`, `bannerless/`, `age-verification/`,
  `geo-restriction/`, `forwarding/`; `geo-check` fällt still auf `country_code: "EU"` zurück
  (`relation "geo_ip_cache" does not exist`). Es fehlt eine Migration, die die Live-DB an den
  Code angleicht (bzw. `cookie_consent_revisions` → `cookie_banner_revisions` im Code).
- **asyncpg-JSONB-Verstöße:** `POST /import` (Z. 3161) schreibt `config.get('services', [])` als
  rohe Liste in die JSONB-Spalte `services` → `DataError`/500. `POST /geo-restriction` (Z. 2646,
  `countries`) und `POST /forwarding` (Z. 2723, `target_sites`) hätten dasselbe Problem, sobald die
  Spalten angelegt werden. Fix: `json.dumps(...)`. Die Haupt-Config-Routen sind korrekt.
- **Kein Cleanup-Automatismus:** `delete_expired_consents()` läuft nirgends automatisch (kein
  Cronjob/Timer im Repo, kein Aufruf in `backend/main_production.py`) → Logs bleiben über die
  3 Jahre hinaus liegen (Art. 5 Abs. 1 lit. e). Endpunkt existiert, muss manuell getriggert werden.
- **Fehler-Detail-Leaks:** die Zusatzmodul-Routen nutzen durchgehend `detail=str(e)` (entgegen
  Punkt 1.3 des Launch-Plans, der nur die Kernrouten erfasst hat).
- **`POST /consent`:** das `except Exception` (Z. 529) fängt auch die eigene `HTTPException(429)`
  → Rate-Limit-Überschreitung meldet dem Widget 500 statt 429. Dasselbe Muster war in den
  Zusatzmodul-Routen; dort ist seit dem Auth-Fix ein `except HTTPException: raise` vorgeschaltet
  (sonst wäre aus jedem 403 ein 500 geworden — und die bestehenden `400 site_id required`
  wurden zuvor ebenfalls verschluckt). `POST /consent` selbst ist **noch offen**.
- **Stilles Auth-Schlucken** (`planning/STRUKTUR_FIXES_LAUNCH_PLAN.md` 1.2, dort als erledigt
  markiert): `get_current_user_optional` (Z. 61) gibt bei ungültigem/blacklisted Token weiterhin
  `None` zurück. Für die optionale Variante ist das gewollt; geschützte Routen nutzen
  `get_current_user_required` (401).
- **God-File:** 3660 LOC, in `planning/STRUKTUR_FIXES_LAUNCH_PLAN.md` Phase 6 (nach Launch) zum
  Aufteilen in Router/Service/Repository markiert.
- **Migration nicht in `ensure_migrations`:** `create_cookie_compliance_tables.sql` und
  `cookie_custom_services.sql` stehen nicht in der Liste in `backend/main_production.py:397` →
  neue Umgebungen bekommen die Tabellen nicht automatisch.
