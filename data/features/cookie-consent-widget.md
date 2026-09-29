# Cookie-Consent-Widget (Auslieferung / Client)

**Stand:** 2026-09-28 · **Status:** 🟢 live (Banner in Besuchersprache, XSS- und Kontrastfixes live; offen: kein Cache/Minify, TCF-Stub, zwei Blocker)

## Ziel
Das JS, das auf **Kundenseiten** eingebunden wird: Cookie-Banner v2 plus Content-Blocker als ein
Bundle von `api.complyo.de`, Config pro `site_id` vom Server, Consent-Speicherung/-Übermittlung,
Google Consent Mode v2. Diese Doku ist die **Client-/Auslieferungs-Seite**; die Server-Seite
(Consent-Logging, Banner-Config-CRUD, Service-Katalog, Farb-Extraktion) ist
[[cookie-consent-management]] (`backend/cookie_compliance_routes.py`).

## Architektur (end-to-end)
- **Snippet → Kundenseite**
  - `GET /api/widgets/snippet/{widget_type}?site_id=…` (`backend/widget_routes.py:443`) liefert
    `<script src="https://api.complyo.de/api/widgets/cookie-compliance.js" data-site-id="…">`.
    Basis-URL `base_url = "https://api.complyo.de"` (Z. 491). Seit 03372ec (2026-08-04) nur mit
    Anmeldung (live ohne Token 401) und nicht im Free-Tarif (402 `plan_upgrade_required`).
  - `tests/test_einbettungscode.py` (f48eea9, 2026-09-22) bewacht `base_url` und die
    ausgeschriebenen Schnipsel in `backend/ai_fix_engine/prompts_v2.py`; dort stand vorher der
    nicht existierende Host `widgets.complyo.de` (kein DNS-Eintrag).
  - Dashboard-Anzeige: `dashboard-react/src/components/cookie-compliance/IntegrationGuide.tsx`
    und `CookieSetupWizard.tsx` (zeigen zusätzlich `/public/cookie-blocker.js`, s. u.).
- **Bundle-Auslieferung:** `serve_cookie_compliance_widget` (`widget_routes.py:64-66`), erreichbar
  als `/api/widgets/privacy-manager.js` **und** `/api/widgets/cookie-compliance.js` (Alias gegen
  Adblocker). Liest bei **jedem Request** drei Dateien von Platte und konkateniert in dieser
  Reihenfolge: `widgets/locales/translations.js` (setzt `window.COMPLYO_TRANSLATIONS`),
  `widgets/content_blocker.js`, `widgets/cookie_banner_v2.js`. Kein Build-Step, kein Minify.
  - Live gemessen 2026-09-28: 250.946 Byte unkomprimiert, 53.939 Byte gzip;
    `Cache-Control: no-cache, no-store, must-revalidate`, `ETag` (MD5), gzip bei
    `Accept-Encoding`. `Access-Control-Allow-Origin` kommt live als gespiegelte Origin (nginx).
  - Die tote Route `/api/widgets/cookie-consent.js` ist entfernt (live 404).
- **Zweiter, eigenständiger Blocker:** `backend/public/cookie-blocker.js` (33 KB, Static-Mount
  `/public`, `main_production.py:246`, live 200). Eingebunden von `IntegrationGuide.tsx`,
  `CookieSetupWizard.tsx` und dem WordPress-Plugin (`complyo-compliance.php:175`), ermittelt
  `site_id` aus `data-site-id` (c5876a4). Daneben `public/privacy-shield.js`, `public/complyo-cmp-adapter.js`.
- **Config-Ladung:** der Banner nutzt `/api/cookie-compliance/config/{site_id}`, nicht
  `/api/widgets/config/{site_id}` (den liest nur `accessibility-v6.js:425`). `cookie_banner_v2.js` (3912 Z.):
  - `site_id` aus `data-site-id` des eigenen `<script>` (`document.currentScript`, Z. 163).
  - `loadServerConfig()` (Z. 622) → `GET /api/cookie-compliance/config/{site_id}` →
    `applyServerConfig()` (Z. 757) mappt u. a. `cookie_policy_url` auf die gehostete Richtlinie
    ([[cookie-richtlinie-seite]]). `loadServiceDetails()` (Z. 711) →
    `/api/cookie-compliance/services?site_id=…`. Dazu `geo-check` (Z. 360), `reconsent-check`
    (Z. 467, Config-Hash → Re-Consent), `/api/ab-tests/assign|track` (Z. 660/696, [[ab-testing-cookie-banner]]).
  - Lizenz: die Config liefert `license_active`/`license` aus `evaluate_license()`
    (`cookie_compliance_routes.py:1058`); bei `false` statt Banner ein Hinweis
    (`renderLicenseNotice`, Z. 278), bei `unlicensed_domain` als Vollbildsperre.
    Durchsetzung live `COMPLYO_LICENSE_ENFORCEMENT=warn`; Subdomains einer gebuchten Domain
    gelten als lizenziert (4f14890).
- **Sprache (53cea2f, 2026-09-25):** `detectLanguage()` (Z. 853) wählt in dieser Reihenfolge
  URL-Parameter `lang`/`language`, `<html lang>` der Kundenseite, `navigator.language`; 17
  Sprachen (`SUPPORTED_LANGUAGES`, Z. 34). `applyServerConfig()` mischt die Übersetzung aus
  `translations.js` ein (Z. 794) und überschreibt sie nur mit Kundentext **in genau dieser
  Sprache** (Z. 801). Der frühere Rückfall auf `texts['de']` ist entfernt; vorher sah jeder
  nichtdeutsche Besucher deutschen Text. Live im Bundle geprüft. Test `tests/test_banner_sprache.py`.
- **Consent-Erteilung/-Ablehnung**
  - `saveConsent()` (Z. 997): `localStorage` `complyo_cookie_consent` + `complyo_consent_date`
    (+ `complyo_consent_history`), dann `POST /api/cookie-compliance/consent`. Ein
    `ip_address`-Feld schickt der Banner nicht; die IP bestimmt der Server (c5c98a0).
  - `applyConsent()` (Z. 1066): `window.complyoConsent`, Event `complyoConsent` (Z. 1357, der
    Blocker hört darauf), `dataLayer`-Push `complyo_consent_update` (Z. 1325), `updateGoogleConsentMode()`.
  - Widerruf/Nachträglich: `renderFloatingButton()` (Z. 3459) plus Settings-Modal mit Tabs.
- **Sicherheit und Barrierefreiheit des Widgets selbst**
  - XSS (98b7f71, 2026-09-09): Fremddaten (Adressen, Dienstnamen aus dem Katalog) laufen durch
    `sanitizeText`/`complyoEsc`, jedes `href` durch eine Schema-Allowlist; im Content-Blocker
    ebenso. Wächter `tests/test_widget_xss.py`.
  - Kontrast (1e5a2d7, 4a611ee): Banner und Einstellungsdialog rechnen Schrift- und
    Markenfarben mit `lesbareSchrift`/`lesbareMarkenschrift`/`gedaempfteSchrift` auf 4,5:1.
    Wächter `tests/test_eigene_widgets_barrierefrei.py` misst auch den geöffneten Dialog.
  - 096a391 (2026-08-11) behob einen `ReferenceError` in `getStyles`, durch den ab 10.08. kein
    Banner renderte und keine Einwilligung ankam.
- **`backend/widgets/content_blocker.js`** (1333 Z.), im Bundle vor dem Banner:
  - `installEarlyHooks()` (Z. 254) patcht `document.createElement` für `script`/`link` und setzt
    vor dem Request `type="text/plain"` / `media="not all"` + `data-complyo-src`.
  - `blockAllContent()` (Z. 429) + `MutationObserver` (Z. 407) für statische Tags; Iframes →
    Click-to-Load-Platzhalter; `unblockContent()` (Z. 687) reinjiziert.
  - Blockliste: `BLOCKED_DOMAINS` (Z. 45) plus `loadServiceDomains()` (Z. 315) aus dem Katalog.
  - Blocking auf `app|dashboard.complyo.(de|tech)` deaktiviert (Z. 196); `enforceLicense()`
    (Z. 367) schaltet es bei fehlender Lizenz ab.
  - **Grenze:** der `createElement`-Hook greift erst nach dem Laden des Bundles; synchrone
    `<script src>` **vor** dem Snippet laufen durch. Lückenlos nur mit serverseitigem
    Inline-Blocker des WordPress-Plugins ([[wordpress-plugin]]) bzw. Snippet als erstes Script.
- **Google Consent Mode v2:** `initGoogleConsentMode()` (Z. 1103) läuft als erstes in `init()`
  (Z. 196): alles `denied` ausser `security_storage`; `updateGoogleConsentMode()` (Z. 1128) mappt
  `marketing`→`ad_storage`/`ad_user_data`/`ad_personalization`, `analytics`→`analytics_storage`,
  `functional`→`functionality_storage`/`personalization_storage`. Defaults auch per Server-Config.
- **IAB TCF 2.2:** `initTCF()` (Z. 1162) ist ein **Stub**, opt-in via `data-tcf="true"`, meldet
  `cmpId: 0` (nicht registriert, live im Bundle), laut Kommentar „Coming Soon" (AUDIT-02).
- **Erkennbarkeit durch den eigenen Scanner:** `backend/compliance_engine/checks/cookie_check.py:261`
  erkennt das Widget am `<script src>` (`cookie-compliance.js`, `cookie-blocker.js`, `complyo`).

## Auslieferung / CORS
- Alles über **`https://api.complyo.de`** (nginx `location /` → `127.0.0.1:8002`).
- `/etc/nginx/sites-enabled/complyo.de` und Repo `nginx/complyo.de` sind in den CORS-Maps
  gleich (geprüft 2026-09-28): `$cors_allow_origin` spiegelt jede Origin,
  `$cors_allow_credentials` nur für Complyo-eigene Origins. Live: Widget-Bundle und
  `/api/cookie-compliance/config/…` antworten mit gespiegelter `Access-Control-Allow-Origin`.
- Backend-Ebene: `public_widget_cors` (`main_production.py:306`) für `_PUBLIC_WIDGET_PREFIXES`
  (Z. 295: `/api/cookie-compliance/config|services|consent|geo-check|reconsent-check`,
  `/api/ab-tests/track`, `/api/widgets/`).
- `gateway/nginx-production.conf` liegt noch im Repo, ist nicht live (nicht erneut geprüft, ob referenziert).

## DB
- `widget_events`: Ziel von `POST /api/widgets/analytics` (Z. 275, 120/min je IP, d4bf484).
  Die nicht existierende DB-Funktion `track_widget_feature` ist ersetzt (7b7cd13); die Route
  `POST /api/widgets/track` ist entfernt (Hinweis Z. 264). Live: 20 Zeilen, letzte 2026-09-24.
  Frist 90 Tage über `loeschfristen.py` ([[dsgvo-betroffenenrechte]]).
- `GET /api/widgets/analytics/{site_id}` (Z. 932) liest `widget_events`, nur mit Anmeldung und
  Ownership (d4bf484).
- `widget_analytics` und `widget_usage_stats` existieren live nicht; `_check_upsell_opportunity`
  (Z. 344) liest `widget_events`.
- `cookie_banner_configs`: Quelle für die Banner-Config ([[cookie-consent-management]]).

## Plan-Gating
Snippet-Route: Anmeldung plus kein Free-Tarif (402). Auf der Kundenseite ist das Gate die
**Laufzeit-Lizenz** pro Site: `evaluate_license()` / `site_has_active_license()`
(`backend/license_check.py:193/253`), Modus `off|warn|block` über `COMPLYO_LICENSE_ENFORCEMENT`
(live `warn`), fail-open bei fehlenden Headern oder DB-Fehler. Farb-Extraktion:
`POST /api/cookie-compliance/extract-colors`, siehe [[cookie-consent-management]].

## Bekannte Lücken / Offen
- **Kein Build/Minify/CDN:** rund 251 KB (54 KB gzip) werden pro Request von Platte gelesen,
  konkateniert und mit `no-store` ausgeliefert. Üblich wäre Hash-URL mit langem Cache (Config
  kommt ohnehin per Fetch).
- **Zwei Blocker-Implementierungen:** `widgets/content_blocker.js` im Bundle und
  `public/cookie-blocker.js` (Integrationsanleitung, WordPress-Plugin). Welche Blocklisten
  auseinanderlaufen, nicht geprüft.
- **TCF-Stub** `cmpId: 0`: nicht registriert, nicht produktiv nutzbar (AUDIT-02).
- **Zwei Config-Endpunkte** mit unterschiedlichem Schema: `/api/widgets/config/{site_id}`
  (A11y-Widget) und `/api/cookie-compliance/config/{site_id}` (Cookie-Banner).
- `backend/widgets/optout_center.js` (824 Z.) ist weiter toter Code mit Warnkopf, von keiner Route ausgeliefert.
- Lizenzdurchsetzung steht auf `warn`; `block` ist nicht eingeschaltet.
- Sprachwahl richtet sich zuerst nach `<html lang>` der Kundenseite, nicht nach dem Browser des
  Besuchers; auf einer deutsch ausgezeichneten Seite bleibt der Banner deutsch.
