# Deep Cookie Scanner (Premium)

**Stand:** 2026-06-27 · **Status:** 🟢 live

## Ziel
Premium-Scan, der eine Website mit echtem Headless-Chromium (Playwright) lädt, alle
Requests/Cookies/Storage erfasst und die eingesetzten **Dienste über den
`cookie_services`-Katalog** klassifiziert (echter Name, Anbieter, Kategorie, `service_key`).
Erkannte Dienste lassen sich per 1-Klick in den Cookie-Banner übernehmen → fließen
automatisch in die öffentlich gehostete Cookie-Richtlinie ([[cookie-richtlinie-seite]]).

## Architektur (end-to-end)
- **Scanner:** `backend/compliance_engine/deep_cookie_scanner.py`
  - `DeepCookieScanner(scan_id, url, catalog=...)` — Playwright async; erfasst Requests
    (`page.on('request')`), Context-Cookies, localStorage/sessionStorage; simuliert Scroll
    für lazy Tracker.
  - **`CatalogMatcher`**: `match_url()` gegen `template.domains` (215/217 Dienste,
    nur echte Domains mit Punkt → kein „custom"-Rauschen), `match_cookie()` gegen
    `cookie_names`/`template.cookies` mit Präfix/Suffix-Wildcard (`_ga_*`).
  - Nicht zuordenbare Cookies → Label „Sonstige / First-Party" (KEIN
    `domain.capitalize()`-Junk mehr). `ScanResult.error` ist ein echtes Dataclass-Feld.
  - `categorized` ist nach Dienstname gruppiert und trägt `service_key`/`category`/
    `provider` (für 1-Klick-Übernahme). `ScanResult.service_keys` = erkannte Katalog-Keys.
- **Routes:** `backend/deep_cookie_scanner_routes.py` (Prefix `/api/v2`)
  - `POST /deep-cookie-scan/start` — Premium-Gate (`subscriptions.plan_type`) + Monats-
    kontingent (`deep_scan_usage`, Limit = `user_limits.websites_max`); legt Scan an,
    startet `asyncio.create_task(background_scan_job)`.
  - `background_scan_job` lädt den Katalog via `_load_service_catalog(conn)`, übergibt ihn
    dem Scanner, persistiert Ergebnis (nutzt **Modul-DB-Pool**, in main_production gesetzt).
  - `GET /deep-cookie-scan/{id}` Poll, `.../export` (service_keys/category/provider),
    `.../my-scans`, `.../stats`, `DELETE`, `GET /usage`.
  - **`POST /deep-cookie-scan/{id}/apply`** — übernimmt erkannte `service_key`s in
    `cookie_banner_configs.services` der primären Website (merge/dedup) → Banner + Teil-C-
    Richtlinie. Ziel-Site via `get_user_website_site_id` (oder `body.site_id`).
- **Frontend:** `dashboard-react/src/app/deep-cookie-scanner/page.tsx` (+ Sidebar „Deep Scan")
  - URL-Input, Quota, 5s-Polling, Ergebnis-/Privacy-Findings-Anzeige, JSON-Export,
    Button **„Erkannte Dienste in meinen Cookie-Banner übernehmen"** (→ `/apply`).
- **DB:** `backend/migrations/create_deep_cookie_scanner.sql` (in `ensure_migrations`
  registriert). Tabellen `deep_cookie_scans`, `deep_scan_usage`, `deep_scan_history`.

## Gefixte Bugs (2026-06-27)
- `deep_scan_usage` hatte `UNIQUE(user_id)` → Monatswechsel-INSERT brach ab. Geändert zu
  `UNIQUE(user_id, current_month)` (Live-DB + Migration).
- Migration war nicht in `ensure_migrations` → jetzt enthalten.
- Toter Code entfernt (`_intercept_*`, `_inject_storage_logger`, `_parse_set_cookie`,
  `_get_request_type`, `SERVICE_PATTERNS`-Heuristik).

## Verifiziert
- Katalog (217 Dienste) geladen; `googletagmanager.com`→GTM, `connect.facebook.net`→
  Meta Pixel (marketing), `example.com`→None; `_ga_*`→GA4 (analytics), `_fbp`→Meta,
  `PHPSESSID`→Session (necessary).
- Realer Scan w3schools.com → Firebase Auth, GA4, Google Maps, GTM (mit `service_key`s).
- B→C: Banner-Config mit service_keys → `/cookie-richtlinie/{site_id}` rendert Dienste
  inkl. Speicherdauer/Rechtsgrundlage/Drittland.
- Playwright+Chromium im Backend-Container vorhanden; alle 7 Routen live (apply 403/
  export 401 ohne Auth = vorhanden + geschützt).

## Voraussetzungen
- Premium-Plan (pro/premium/agency/enterprise/complete). Kontingent = freigeschaltete
  Websites (`websites_max`); Master-Account (-1) = unbegrenzt.

## Offen / optional
- Consent-bewusstes Scannen (vor/nach Einwilligung, CMP-Erkennung) — bewusst nicht in
  diesem Schritt (Scope A+B+C).
- `_ga` (ohne Suffix) matcht GTM statt GA4, da beide das Pattern listen (Reihenfolge);
  inhaltlich Google, Kategorie-Nuance. Bei Bedarf: spezifischste Übereinstimmung priorisieren.
