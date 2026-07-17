# Cookie-Consent-Widget (Auslieferung / Client)

**Stand:** 2026-07-17 · **Status:** 🟢 live (mit toten Pfaden, s. u.)

## Ziel
Das JS, das auf **Kundenseiten** eingebunden wird: Cookie-Banner v2 + Content-Blocker als ein
Bundle von `api.complyo.de`, Config pro `site_id` vom Server, Consent-Speicherung/-Übermittlung,
Google Consent Mode v2. Diese Doku ist die **Client-/Auslieferungs-Seite**; die Server-Seite
(Consent-Logging, Banner-Config-CRUD, Service-Katalog, Farb-Extraktion) ist
[[cookie-consent-management]] (`backend/cookie_compliance_routes.py`).

## Architektur (end-to-end)
- **Snippet → Kundenseite**
  - `GET /api/widgets/snippet/{widget_type}?site_id=…` (`backend/widget_routes.py:426`) liefert
    `<script src="https://api.complyo.de/api/widgets/cookie-compliance.js" data-site-id="…">`.
    Basis-URL dort **hart auf `api.complyo.de`** — sauber.
  - Dashboard-Anzeige: `dashboard-react/src/components/cookie-compliance/IntegrationGuide.tsx`.
- **Bundle-Auslieferung** — `serve_cookie_compliance_widget` (`backend/widget_routes.py:89`),
  erreichbar als `/api/widgets/privacy-manager.js` **und** `/api/widgets/cookie-compliance.js`
  (Alias gegen Adblocker). Liest die beiden Dateien bei **jedem Request** von Platte und
  konkateniert: Blocker zuerst, dann Banner. Kein Build-Step, kein Minify.
  - Header: `Cache-Control: no-cache, no-store, must-revalidate` (bewusst? — Config-Änderungen
    schlagen sofort durch, aber ~210 KB unkomprimiert pro Pageview), `ETag`, gzip bei
    `Accept-Encoding`, `Access-Control-Allow-Origin: *`.
- **Config-Ladung** — der Banner nutzt **nicht** `/api/widgets/config/{site_id}`, sondern
  `backend/widgets/cookie_banner_v2.js`:
  - `site_id` aus `data-site-id` des eigenen `<script>` (`document.currentScript`, Z. 153).
  - `loadServerConfig()` (Z. 407) → `GET /api/cookie-compliance/config/{site_id}` →
    `applyServerConfig()` (Z. 542) mappt u. a. `cookie_policy_url` → Link auf die gehostete
    Richtlinie ([[cookie-richtlinie-seite]]). `loadServiceDetails()` (Z. 496) →
    `/api/cookie-compliance/services?site_id=…`. Dazu `geo-check`, `reconsent-check`
    (Config-Hash → Re-Consent), `/api/ab-tests/assign|track`.
  - `license_active === false` → statt Banner ein Betreiber-Hinweis (`renderLicenseNotice`, Z. 259).
- **Consent-Erteilung/-Ablehnung**
  - `saveConsent()` (Z. 761): `localStorage` `complyo_cookie_consent` + `complyo_consent_date`
    (+ `complyo_consent_history`), dann `POST /api/cookie-compliance/consent` (Server-Log).
  - `applyConsent()` (Z. 830): Event `complyoConsent` (der Blocker hört darauf), `dataLayer`-Push
    `complyo_consent_update`, `updateGoogleConsentMode()`.
  - Widerruf/Nachträglich: `renderFloatingButton()` (Z. 3198) + Settings-Modal mit Tabs
    (Dienstgruppen / Dienste / Anbieter / Historie).
- **`backend/widgets/content_blocker.js`** (1323 Z.) — läuft im selben Bundle vor dem Banner:
  - `installEarlyHooks()` (Z. 238) patcht `document.createElement` für `script`/`link` und
    setzt vor dem Request `type="text/plain"` / `media="not all"` + `data-complyo-src`.
  - `blockAllContent()` + `MutationObserver` (Z. 397) für statisch im DOM stehende Tags;
    Iframes (YouTube/Maps/…) → Click-to-Load-Placeholder; `unblockContent()` (Z. 677) reinjiziert.
  - Blockliste: hartkodierte `BLOCKED_DOMAINS` (analytics/marketing/…) + zur Laufzeit
    `loadServiceDomains()` aus dem Service-Katalog.
  - **Grenze:** Der `createElement`-Hook greift erst, wenn das Bundle geladen ist — synchrone
    `<script src=…>`-Tags, die **vor** dem Complyo-Snippet im `<head>` stehen, laufen durch.
    Für lückenloses Pre-Consent-Blocking braucht es den serverseitigen Inline-Blocker des
    WordPress-Plugins (`wordpress-plugin/complyo-compliance/includes/class-complyo-inline-blocker.php`,
    [[wordpress-plugin]]) bzw. Platzierung als allererstes Script.
  - Blocking ist auf `app|dashboard.complyo.(de|tech)` deaktiviert (Selbstschutz) und wird bei
    fehlender Lizenz per `enforceLicense()` abgeschaltet.
- **Google Consent Mode v2** — `initGoogleConsentMode()` (`cookie_banner_v2.js:867`), läuft als
  **erstes** in `init()`: `gtag('consent','default', …)` alles `denied` außer `security_storage`;
  `updateGoogleConsentMode()` (Z. 893) mappt `marketing`→`ad_storage`/`ad_user_data`/
  `ad_personalization`, `analytics`→`analytics_storage`, `functional`→`functionality_storage`/
  `personalization_storage`. Defaults auch per Server-Config (`consent_mode_default`).
- **IAB TCF 2.2** — `initTCF()` (Z. 926) ist ein **Stub**, opt-in via `data-tcf="true"`, meldet
  `cmpId: 0` (nicht registriert). Laut Code-Kommentar (AUDIT-02) **nicht produktionsreif**.
- **Erkennbarkeit durch den eigenen Scanner:** Der HTML-Scanner sieht JS-injizierte Banner nicht
  ([[deep-cookie-scanner]]), erkennt das Complyo-Widget aber am `<script src>` —
  `backend/compliance_engine/checks/cookie_check.py:459` matcht `cookie-compliance.js`/`complyo`.

## Auslieferung / CORS
- Alles über **`https://api.complyo.de`** (nginx `api.complyo.de location /` → `127.0.0.1:8002`).
- `/etc/nginx/sites-enabled/complyo.de` (Repo: `nginx/complyo.de`) — **live weicht vom Repo ab**:
  live `map $http_origin $cors_allow_origin { default $http_origin; }` (spiegelt **jede**
  Kunden-Origin) + `$cors_allow_credentials` nur für Complyo-eigene Origins. Die Repo-Fassung
  hat noch `default ""` → würde die Widget-Fetches killen. **Repo nachziehen.**
- Zweite Ebene im Backend: `public_widget_cors`-Middleware (`backend/main_production.py:258`)
  spiegelt die Origin für `_PUBLIC_WIDGET_PREFIXES` (`/api/cookie-compliance/config|services|
  consent|geo-check|reconsent-check`, `/api/ab-tests/track`, `/api/widgets/`).
- `gateway/nginx-production.conf` ist eine **alte, nicht-live** Fassung (listet `.tech`-Origins).

## DB
- `widget_events` — `POST /api/widgets/track` (`site_id`, `widget_type='tracking'`, `event_name`,
  `event_data` JSONB via `json.dumps`).
- `widget_analytics` + SQL-Funktion `track_widget_feature(...)` — `POST /api/widgets/analytics`;
  Schema `backend/migrations/create_widget_analytics.sql`.
- `widget_usage_stats` — gelesen von `_check_upsell_opportunity`; `GET /api/widgets/analytics/{site_id}`
  (Dashboard, `days`-Fenster) aggregiert Feature-Popularität.
- `cookie_banner_configs` — Quelle für Position/Farben/Sprache in `/api/widgets/config/{site_id}`
  und (über [[cookie-consent-management]]) für die eigentliche Banner-Config.

## Plan-Gating
Kein Plan-Gate auf den Widget-Routen. Gate ist die **Laufzeit-Lizenz** pro Site:
`site_has_active_license(db_pool, site_id)` (`backend/license_check.py`), ausgeliefert in
`/api/widgets/config/{site_id}` als `license_active` und im Banner/Blocker ausgewertet.
Farb-Extraktion aus der Kundenseite: `POST /api/cookie-compliance/extract-colors`
(`backend/cookie_compliance_routes.py:861`, genutzt von `CookieBannerDesigner.tsx:82`) —
serverseitig, dokumentiert unter [[cookie-consent-management]].

## Bekannte Lücken / Offen
- **[BEHOBEN 2026-07-17] `.tech` im Widget-Pfad:** `backend/widget_manager.py` Z. 39/40/391
  zeigten auf `widgets.complyo.tech`, `cdn.complyo.tech`, `docs.complyo.tech` (`.tech` ist tot,
  [[live-domains]]) → `WidgetManager` erzeugte Integrations-Snippets mit toten Domains. Fix: alle
  auf `.de` umgestellt (`widgets.complyo.de`, `cdn.complyo.de/widgets`, `docs.complyo.de`).
  (CSP in `nginx/complyo.de` und mailto in `IntegrationGuide.tsx` ggf. noch prüfen.)
- **[BEHOBEN 2026-07-17] `GET /api/widgets/cookie-consent.js` war tot** (las die nicht
  existierende `widgets/cookie_consent.js` → immer 404, kein Konsument). Fix: die tote
  Legacy-v1-Route ist entfernt; Auslieferung läuft über `/api/widgets/cookie-compliance.js`
  bzw. `/privacy-manager.js`.
- **[BEHOBEN 2026-07-17] `backend/widgets/locales/translations.js` (17 Sprachen) wurde nirgends
  geladen** → der Banner las `window.COMPLYO_TRANSLATIONS`, das nie gesetzt war, i18n war tot.
  Fix: `translations.js` wird jetzt vom Bundle **vor** dem Banner ausgeliefert (setzt
  `window.COMPLYO_TRANSLATIONS`, `widget_routes.py:serve_cookie_compliance_widget`) → i18n greift.
- **[BEHOBEN 2026-07-17] `backend/widgets/optout_center.js` als toter Code markiert:** wird von
  keiner Route ausgeliefert und von keinem Konsumenten geladen (redundant zum Banner-eigenen
  Preferences-Modal). Ein deutlicher `⚠️ TOTER CODE`-Header steht jetzt oben in der Datei; vor
  Wiederbelebung erst eine serve-Route ergänzen.
- **`IntegrationGuide.tsx:51` verweist auf `${API_BASE}/public/cookie-blocker.js`** — im Backend
  existiert keine solche Route → Snippet lädt 404.
- **TCF-Stub** `cmpId: 0` — nicht registriert, nicht produktiv nutzbar (AUDIT-02).
- **Kein Build/Minify/CDN:** 156 KB Banner + 56 KB Blocker werden pro Request von Platte gelesen,
  konkateniert und mit `no-store` ausgeliefert. Für Kundenseiten teuer; Immutable-Hash-URL +
  langem Cache wäre der übliche Weg (Config kommt ohnehin separat per Fetch).
- `/api/widgets/config/{site_id}` und `/api/cookie-compliance/config/{site_id}` sind zwei
  parallele Config-Endpunkte mit unterschiedlichem Schema; der Cookie-Banner nutzt nur letzteren.
