# Cookie-Consent-Management (Server-Seite)

**Stand:** 2026-09-28 · **Status:** 🟢 live (Zusatzmodule repariert, Nachweis mit Banner-Fassung und gepfeffertem IP-Hash; offen: widersprüchliche Aufbewahrungsfrist, God-File)

## Ziel
Server-/Verwaltungsseite des Consent-Managements: Banner-Konfiguration pro Site,
Dienst-Katalog, Consent-Protokollierung als Nachweis (Art. 7 Abs. 1 DSGVO) inkl. CSV-Export
und Ablauf, plus Zusatzmodule (Consent Mode, Altersprüfung, Geo, Forwarding, Widerruf, TCF).
**Abgrenzung:** das ausgelieferte JS-Widget → [[cookie-consent-widget]]; die öffentliche
Richtlinien-Seite `GET /cookie-richtlinie/{site_id}` → [[cookie-richtlinie-seite]]; Playwright-Scan →
[[deep-cookie-scanner]]; Agentur-Block → [[agentur-white-label]]; Aufbewahrungsfristen im
Ganzen → [[dsgvo-betroffenenrechte]].

## Architektur (end-to-end)
- **Router (God-File):** `backend/cookie_compliance_routes.py`, 4049 Z., 51 Routen, Pfade
  `/api/cookie-compliance/...` plus die prefixlose Public-Route `/cookie-richtlinie/{site_id}`
  (Z. 3334). Funktionsblöcke:
  - **Auth/Helper** (Z. 58 bis 575): `get_current_user_optional` (Z. 71, JWT + Redis-`jti`-Blacklist),
    `_url_to_site_id` (Z. 182), `get_user_site_ids` (Z. 194, agenturfähig), `require_site_access`
    (Z. 217) / `require_site_access_user` (Z. 247), `ConsentLog` (Z. 275), `hash_ip_address`
    (Z. 426), `truncate_user_agent` (Z. 464), `get_client_ip` (Z. 497).
  - **Consent-Logging:** `POST /consent` (Z. 581).
  - **Banner-Config:** `GET /my-config` (Z. 743), `GET /config/{site_id}` (Z. 915, öffentlich,
    Widget-Quelle, liefert auch `license_active`/`license`), `POST /extract-colors` (Z. 1076,
    über `ssrf_protection.validate_url`), `POST /config` (Z. 1157), `PATCH /config/{site_id}` (Z. 1347).
  - **Service-Katalog** (Z. 1425, 1539) und **Custom-Services** (Z. 1581 bis 1737).
  - **Statistik/Logs/Export** (Z. 1738 bis 1993), **Scan/Monitor/Blocking** (Z. 1994 bis 2432),
    **Consent Mode/Alter/TCF** (Z. 2433 bis 2788), **Geo/Forwarding** (Z. 2789 bis 3050),
    **Policy/Richtlinie/Revisionen/Import-Export** (Z. 3192 bis 3525), **Reconsent/Bannerless**
    (Z. 3526, 3588), **Widerruf/Service-Stats** (Z. 3629 bis 3748), **Rate-Limit** (Z. 3749),
    **Agentur** (Z. 3772 bis 4049, → [[agentur-white-label]]).
- **Scanner-Anbindung:** `POST /scan` (Z. 1994, 5/min) → `backend/cookie_scanner_service.py`,
  `.../automated_cookie_scanner.py` (HTML-Heuristik, rendert kein JS). `compliance_engine/cookie_analyzer.py`
  ist entfernt (fc9f5e1). `POST /scan/deep` (Z. 2228) antwortet sofort mit Hinweis, weil
  Playwright im Image fehlt; der tote Rest ist entfernt (db395d8). Echter Scan → [[deep-cookie-scanner]].
- **UI:** `dashboard-react/src/app/cookie-compliance/page.tsx` (720 Z.) mit
  `dashboard-react/src/components/cookie-compliance/*`: `CookieSetupWizard`, `CookieBannerDesigner`,
  `ServiceManager`, `ConsentStatistics`, `ConsentModeSettings`, `AgeVerification`,
  `GeoRestriction`, `TCFManager`, `RevocationChart`, `IntegrationGuide`, `CookiePolicyGenerator`,
  `AdvancedSettings`, `ABTestManager`, `ScanMonitor`, `AccessibilityScore`.
- **asyncpg-JSONB-Regel:** der Pool hat **keinen** json-Codec. JSONB-Spalten schreiben mit
  `json.dumps()`, beim Lesen kommt eine Zeichenkette zurück und muss geparst werden.
  `GET /blocking-config/{site_id}` (Z. 2319) las `services` roh und antwortete für jede Site mit
  500; behoben in b860f7f (2026-09-10), Wächter `tests/test_jsonb_spalten.py`.
  `geo_countries` und `forwarding_target_sites` sind `ARRAY`-Spalten, keine JSONB; dort ist
  eine Python-Liste korrekt.

## Consent-Logging (Nachweis Art. 7)
- `POST /api/cookie-compliance/consent` (Z. 581), ohne Auth (Besucher-Endpunkt),
  Redis-Sliding-Window 100/min pro `site_id` (`check_rate_limit`, Z. 3749); eigene 429 wird
  durchgereicht.
- **IP bestimmt der Server** (28715eb, c5c98a0, 2026-09-02): `get_client_ip` delegiert an
  `dependencies`, das `X-Forwarded-For` nur von `TRUSTED_PROXIES` glaubt. Das Body-Feld
  `ip_address` ist aus `ConsentLog` entfernt; User-Agent kommt aus dem Header, Body nur als Rückfall.
  Wächter `tests/test_besucher_ip_quelle.py`.
- **IP-Hash mit Pfeffer** (882c178, 2026-09-22): `hash_ip_address` = SHA-256 über
  `COMPLYO_IP_PFEFFER + ip`. Fail-open mit Warnung, wenn der Pfeffer fehlt (Nachweis geht vor).
  Live gesetzt (im Container vorhanden, 44 Zeichen). Wirkt nur nach vorn, ältere Hashes bleiben
  ungepfeffert. Test `tests/test_ip_pfeffer.py`.
- Gespeichert in **`cookie_consent_logs`**: `site_id`, `visitor_id` (pseudonym),
  `consent_categories` (JSONB inkl. `third_country_consent`), `services_accepted` (JSONB),
  `ip_address_hash` **oder** `device_fingerprint`, `user_agent` (gekürzt), `revision_id`
  (= `cookie_banner_configs.id`, nicht die Fassung), **`banner_revision`** (Fassung des Banners,
  Migration `0031`, 7b7cd13), `language`, `banner_shown`, `action`, `timestamp`, `expires_at`.
  Live: 1.349 Zeilen (2026-05-01 bis 2026-09-27), davon 198 mit `banner_revision`; Altdaten bleiben NULL.
- Nach dem Insert: Tagesaggregat-Upsert in `cookie_compliance_stats` und Rücksetzen von
  `requires_reconsent` der Site.
- **Lesen:** `GET /consents/{site_id}` (Z. 1823, paginiert). **Export:**
  `GET /consents/{site_id}/export` (Z. 1879): CSV, `;`, UTF-8-BOM, 14 Spalten inkl.
  „Banner-Fassung" (Altdaten „nicht erfasst"); Auth + Modul `cookie` + Ownership.
- **Ablauf:** automatisch über zwei Mechanismen (siehe Lücken): `_daily_gdpr_cleanup()`
  (`main_production.py:864`) löscht Zeilen älter 24 Monate, `loeschfristen.py` (Cron 03:30,
  `LOESCHFRISTEN_SCHARF=ja` live) Zeilen älter 1095 Tage mit abgelaufenem `expires_at`.
  DB-Default `expires_at = now() + 2 years` (Alembic 0015). Zusätzlich manuell
  `DELETE /consents/expired` (Z. 1964, nur Admin) → PG-Funktion `delete_expired_consents()`.
- **Widerruf:** `POST /revoke` (Z. 3629) schreibt `action='revoke'`. `GET /revocation-stats/{site_id}`
  und `GET /service-stats/{site_id}` mit Auth und Ownership (e8d846b).

## Zusatzmodule (je Endpunkt)
Die Spalten `requires_reconsent`, `bannerless_mode`, `tcf_enabled`, `tcf_vendors`,
`age_verification_*`, `geo_restriction_enabled`, `geo_countries`, `forwarding_*` hat Alembic
0015 angelegt (c5876a4, 2026-08-11); live vorhanden (49 Spalten in `cookie_banner_configs`).
- **Google Consent Mode v2:** `GET /consent-mode-config/{site_id}`, `POST /consent-mode-config`.
- **Altersverifikation:** `GET /age-verification/{site_id}`, `POST /age-verification` (Art. 8).
- **Geo-Restriction:** `GET /geo-restriction/{site_id}`, `POST /geo-restriction`, öffentlich
  `GET /geo-check` (Z. 2789, `CF-IPCountry`, Cache `geo_ip_cache` aus Alembic 0007, eae3b40).
  Live: `{"country_code":"DE","cached":true}`. Rückfall bei Fehler ist `DE` (Banner zeigen).
- **Consent-Forwarding:** `GET /forwarding/{site_id}`, `POST /forwarding`.
- **Bannerlos:** `GET /bannerless/{site_id}`.
- **Re-Consent-Check:** öffentlich `GET /reconsent-check/{site_id}?config_hash=`, live 200.
- **Revisionen:** `GET /revisions/{site_id}` (Z. 3355) liest jetzt `cookie_banner_revisions`
  (7b7cd13); Trigger `trigger_banner_revision` legt je Änderung einen Schnappschuss an (live 13).
- **Import/Export:** `GET /export/{site_id}`, `POST /import` (nur Update, `services` per `json.dumps`).
- **TCF 2.2:** `GET /tcf/vendors` (öffentlich), `GET /tcf/config/{site_id}`, `POST /tcf/config`;
  lesen `tcf_data` aus `scan_history.scan_data` statt der nie existierenden `analysis_results` (7b7cd13).
- Die geschützten Zusatzmodul-Routen antworten live ohne Token mit 401; die Antwort mit gültigem
  Token (vormals 500) ist in dieser Prüfung **nicht geprüft**. Laut 7b7cd13/b860f7f lief ein
  Abschlussdurchlauf über 105 Rechtsendpunkte ohne 500er.

## Service-Katalog
- **`cookie_services`** (live **217**, alle aktiv): `service_key` (UNIQUE, Anker für
  Banner-Config, Deep-Scan und Richtlinie), `name`, `category`, `provider`, `description`,
  `cookies`/`template` (JSONB), `privacy_url`, `provider_*`, `plan_required`, `is_active`.
- `GET /services?category=&plan=&site_id=` gruppiert und hängt `_enrich_third_country()` an.
  `GET /services/{service_key}` = Detail.
- **Custom-Services:** `GET|POST|PUT|DELETE /custom-services/{site_id}[/{service_key}]`, Tabelle
  `cookie_custom_services` (live vorhanden). Seit e8d846b (2026-09-09) mit Ownership-Prüfung.
- `cookie_banner_configs.services` hält nur die `service_key`-Liste.

## DB
- `cookie_banner_configs`: 49 Spalten (live), Single Source für das Widget. Live 6 Sites.
- `cookie_consent_logs` (s. o.), `cookie_compliance_stats` (`UNIQUE(site_id, date)`),
  `cookie_services`, `cookie_custom_services`, `cookie_banner_revisions`, `tcf_vendors`,
  `geo_ip_cache` (Frist 30 Tage in `loeschfristen.py`), `cookie_ab_tests`/`cookie_ab_assignments`
  ([[ab-testing-cookie-banner]]).
- `cookie_consent_revisions` wird nicht mehr referenziert.
- PG-Funktion `delete_expired_consents()` (`DELETE … WHERE expires_at < NOW()`).

## Auth-Modell
- `require_site_access(site_id, credentials)` (Z. 217): Auth + Modul + **Ownership** gegen
  `get_user_site_ids()`, 403 bei fremder `site_id`, leere Menge = darf nichts.
  `PATCH /config/{site_id}` prüft gegen alle Sites des Kontos (e8d846b).
- `DELETE /consents/expired` → `require_admin` (`dependencies.py:292`).
- **Bewusst öffentlich** (live ohne Token 200 geprüft): `GET /config/{site_id}`,
  `GET /services`, `GET /blocking-config/{site_id}`, `GET /reconsent-check/{site_id}`,
  `GET /geo-check`, `GET /policy/{site_id}`, `GET /tcf/vendors`, `GET /health`,
  `GET /scan/capabilities`; dazu `POST /consent` und `POST /revoke` (nicht aufgerufen).
- Wächter: `tests/test_cookie_consent_auth.py`, `tests/test_mandantentrennung.py`,
  `tests/test_oeffentliche_routen.py`, `tests/test_cookie_schema_kontrakt.py`,
  `tests/test_nachweiskette.py`. Ob aktuell grün: nicht geprüft.

## Bekannte Lücken / Offen
- **Aufbewahrungsfrist der Einwilligungsprotokolle widersprüchlich:** 24 Monate hart im
  Daily-Cleanup, 1095 Tage (36 Monate) in `loeschfristen.py`, `expires_at`-Default 2 Jahre,
  Docstrings von `log_consent` (Z. 593) und `DELETE /consents/expired` (Z. 1970) sagen 3 Jahre,
  letzterer behauptet zudem, es gebe keinen Cron. Wirksam sind 24 Monate. Details und
  Textstellen (AVV, Datenschutzerklärung) in [[dsgvo-betroffenenrechte]].
- **Alt-Hashes ohne Pfeffer:** Zeilen vor dem Setzen von `COMPLYO_IP_PFEFFER` bleiben
  rückrechenbar, bis sie nach Frist gelöscht sind.
- **`revision_id` doppeldeutig:** enthält die Config-ID; massgeblich ist `banner_revision`, für
  1.151 Altzeilen NULL.
- **God-File:** 4049 Zeilen, Aufteilung in Router/Service/Repository weiter offen.
- **Migrationen ausserhalb Alembic:** `create_cookie_compliance_tables.sql` und
  `cookie_custom_services.sql` stehen nicht in `ensure_migrations` (`main_production.py:517`);
  Live-Tabellen existieren, frische Umgebungen hängen an Alembic (nicht geprüft, ob die Baseline sie vollständig anlegt).
- `get_current_user_optional` gibt bei ungültigem Token `None` zurück (gewollt für optionale
  Routen; geschützte Routen nutzen `require_site_access`).
