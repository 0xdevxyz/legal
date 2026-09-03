# WordPress-Plugin (Complyo Compliance)

**Stand:** 2026-07-17 · **Status:** 🟢 live

## Ziel
Liefert das, was das reine JS-Widget ([[cookie-consent-widget]]) **strukturell nicht kann**: Eingriffe
in die **Server-Ausgabe**, bevor der Browser das Markup parst. Vier Bausteine:
- **Widget-Einbindung** — Blocker synchron als erstes Script im `<head>`, Banner/A11y vor `</body>`.
- **Inline-Script-Blocking** — Tracking-Snippets werden schon im HTML neutralisiert (Consent VOR Ausführung).
- **A11y-Remediation** — zieht das Fix-Manifest und persistiert Fixes an der Quelle → [[accessibility-remediation]].
- **Local Fonts** — Google Fonts lokal ausliefern (Drittlandtransfer) → [[drittlandtransfer-erkennung]].

**Abgrenzung:** Der Content-Blocker im JS-Widget greift erst **ab seiner eigenen Ausführung**. Ein
`<script>gtag(…)</script>`, das im Markup **vor** dem Blocker steht, läuft beim Parsen sofort — kein
client-seitiger Code kann das nachträglich verhindern. Genau diese Lücke schließt der Inline-Blocker
server-seitig. Das ist der Kernwert des Plugins.

## Architektur (end-to-end)
- **Bootstrap:** `wordpress-plugin/complyo-compliance/complyo-compliance.php` (699 Z., Singleton `Complyo_Compliance`)
  - **Version 2.6.0** (Header + `COMPLYO_VERSION`), Requires WP 5.6 / PHP 7.4.
  - **URL-Konstanten (zentral, ein Ort):** `COMPLYO_API_BASE = 'https://api.complyo.de'` (Z. 22),
    `COMPLYO_APP_URL = 'https://app.complyo.de'` (Z. 23). Beide **hardcoded per `define()`** —
    kein Settings-Feld, kein Filter-Override.
  - **`site_id`:** Option `complyo_site_id`; Default via `generate_site_id()` — `home_url()`-Host,
    `www.`-Strip, `.`→`-`, `sanitize_key()`. Entspricht dem Backend-`derive_site_id` ("complyo.de"→"complyo-de").
  - **Script-Output:**
    - `output_cookie_blocker()` an `wp_head` **Priorität 1** → `<script src="{API}/public/cookie-blocker.js">`,
      **ohne** `async`/`defer` (synchron ist Pflicht), mit `data-cfasync="false"`, `data-no-optimize`, `data-no-defer`.
    - `output_banner_script()` an `wp_footer` → `{API}/api/widgets/cookie-compliance.js` (opt. `data-tcf="true"`)
      und `{API}/api/widgets/accessibility.js` (`data-auto-fix`, `data-show-toolbar`, opt.
      `data-a11y-statement-url`, `data-a11y-feedback`), beide `async`.
  - **Shortcodes:** `[complyo_cookie_settings]`, `[complyo_cookie_revoke]` (Attribute `text`/`class`/`style`);
    rendern `<a data-complyo-settings|data-complyo-revoke>` — kein Inline-JS (CSP-sicher), das Banner bindet
    die Klicks. `wp_nav_menu_items`-Filter rüstet Shortcode-Rendering in Menüs nach.
  - **Caching-Kompatibilität:** `get_script_patterns()` (Blocker/Banner/A11y/`api.complyo.de`) wird in
    WP Rocket (`rocket_exclude_js`, `rocket_delay_js_exclusions`), W3TC, Autoptimize, LiteSpeed und
    SiteGround ausgeschlossen — verhindert Minify/Defer des Blockers.
- **Inline-Blocker:** `includes/class-complyo-inline-blocker.php` (136 Z., Option `complyo_enable_inline_blocker`, Default `0`)
  - Hook `template_redirect` Prio 1 → `ob_start(rewrite)`; übersprungen für Admin, Feeds, REST, AJAX.
  - `rewrite($html)`: `preg_replace_callback` über `#<script\b([^>]*)>(.*?)</script>#is`.
    - **Externe `<script src>` bleiben unangetastet** — die behandelt der Client-Blocker.
    - Nicht-JS-Typen (JSON-LD, `importmap`, `module`, bereits neutralisierte) werden übersprungen; leere Bodies auch.
    - Kategorisierung über kuratierte Regex-Signaturen (`patterns()`, via Filter `complyo_inline_patterns` erweiterbar):
      `analytics` (gtag, `ga('create'`, GoogleAnalyticsObject, `dataLayer.push`, GTM, `_gaq`, `_paq`/Matomo,
      Hotjar, Clarity) und `marketing` (fbq/Meta, LinkedIn, TikTok, Pinterest, Bing UET, Snap).
      **`marketing` hat Vorrang** (strenger).
    - Treffer → `<script type="text/plain" data-complyo-consent="<kategorie>" data-complyo-inline="1">`;
      ein vorhandenes `type` wird entfernt. Nach Consent führt der Client-Blocker sie aus (`unblockInlineScript`).
  - Bewusst kuratiert statt breit gematcht, um legitimes Inline-JS nicht zu beschädigen.
- **A11y-Remediation:** `includes/class-complyo-a11y-remediation.php` (553 Z.) — Details in [[accessibility-remediation]], hier nur der WP-Adapter:
  - `sync_fixes()` ruft **`GET {COMPLYO_API_BASE}/api/accessibility/fix-manifest/{site_id}`** (`wp_remote_get`, Timeout 15 s).
    Nur HTTP 200 wird verarbeitet. Manifest-Feld `alt_texts`, Fallback auf `fixes` (Alt-Endpoint, rückwärtskompatibel).
  - Persistenz in Optionen: `complyo_a11y_alt_map` (normalisierter Dateiname → Alt), `complyo_a11y_doc_fixes`,
    `complyo_a11y_link_fixes`, `complyo_a11y_last_sync`.
  - Ausgelöst per WP-Cron (`complyo_a11y_sync_event`, `maybe_schedule()` an `init`) und manuell über
    `admin_post_complyo_a11y_sync`. Deaktivierung → `wp_unschedule_event`.
  - **Quell-Persistenz:** `persist_to_attachment()` setzt `_wp_attachment_image_alt` am Attachment (nur wenn leer).
  - **Render-Fallbacks:** `wp_get_attachment_image_attributes` (Prio 20), `the_content` (Prio 20, DOMDocument)
    sowie Output-Buffer ab `template_redirect` Prio 1 für `<html lang>`, Skip-Link, `<main>`-Landmark,
    CSS-Regeln und `aria-label` auf nichtssagende Links (WCAG 2.4.4, ganze Seite inkl. Navigation).
- **Local Fonts:** `includes/class-complyo-local-fonts.php` (421 Z., Option `complyo_enable_local_fonts`, Default `0`)
  - Erkennt `fonts.googleapis.com`-Stylesheets in drei Pfaden: `wp_enqueue_scripts` (Prio 100,
    `rewrite_enqueued_fonts`), `style_loader_tag`-Filter und Output-Buffer ab `template_redirect` (`rewrite_html`)
    — letzterer erwischt auch von Themes/Buildern direkt ins Markup geschriebene `<link>`s.
  - `process_url()` holt das Google-CSS (Desktop-UA), lädt die referenzierten `fonts.gstatic.com`-Dateien
    herunter, schreibt sie in `wp_upload_dir()` und rewritet die `url()`-Referenzen auf die lokale Kopie.
  - Unbekannte URLs werden gequeued und per Cron (`process_pending`) bzw. `process_site()`
    (holt `home_url('/')`) nachgezogen; manueller Anstoß über `admin_post_complyo_localize_fonts`,
    Ergebnis-Notice via `?complyo_fonts&cf_found&cf_localized&cf_errors`. `localized_count()`/`purge()` im Admin.
  - Rechtlicher Bezug: externes Google-Fonts-Laden überträgt die Besucher-IP in ein Drittland —
    Leitfall LG München I, 3 O 17493/20 → [[drittlandtransfer-erkennung]].
- **Admin:** `add_options_page` → Settings → „Complyo Compliance"; `assets/admin.css`.
  Options-Gruppe `complyo_settings_group`, alle Felder `sanitize_text_field` (Statement-URL `esc_url_raw`).

## Backend-Endpunkte (vom Plugin gerufen)
- `GET {API}/public/cookie-blocker.js` — synchroner Blocker, `data-site-id`.
- `GET {API}/api/widgets/cookie-compliance.js` — Banner v2 → [[cookie-consent-widget]].
- `GET {API}/api/widgets/accessibility.js` — A11y-Widget/Toolbar.
- `GET {API}/api/accessibility/fix-manifest/{site_id}` — Fix-Manifest, nur Status `approved` → [[accessibility-remediation]].

## Installation & Konfiguration
- ZIP `wordpress-plugin/complyo-compliance.zip` (gebaut, Stand geprüft: enthält **v2.6.0** und
  ausschließlich `.de`-URLs) → WP-Admin → Plugins → Installieren → Hochladen.
- Bei Aktivierung (`activate()`) werden Defaults gesetzt: `site_id` (auto-generiert),
  `complyo_enable_cookie_banner=1`, `complyo_enable_scanner=1`, alles übrige `0`
  (A11y, TCF, Local Fonts, Inline-Blocker) — die Server-Eingriffe sind **opt-in**.
- Deaktivierung löscht Optionen bewusst nicht (nur der A11y-Cron wird entfernt).
- Konfiguration im Dashboard unter `COMPLYO_APP_URL`; Site-ID muss zur dort gepflegten Domain passen.
- Installationshinweise: `wordpress-plugin/complyo-compliance/install.txt`, `README.md`.

## Bekannte Lücken / Offen
- **`complyo.tech`: kein Fundort.** `grep -rn "complyo\.tech" wordpress-plugin/` liefert **null Treffer** —
  weder in der Quelle noch im entpackten `complyo-compliance.zip`. Die Warnung in
  `planning/STRUKTUR_FIXES_LAUNCH_PLAN.md` Z. 75 („WordPress-Plugin (`app.complyo.tech` hardcoded!)")
  beschreibt einen **behobenen** Zustand: Phase 4.2 (Domain-Sweep) und 4.3 (URL-Konstanten,
  Versions-Bump WP → 2.6.0, neue ZIPs) sind dort als `[x]` abgehakt und im Code verifiziert
  (`COMPLYO_API_BASE`/`COMPLYO_APP_URL`, Version 2.6.0, ZIP gebaut). Der Plan-Text ist an
  dieser Stelle veraltet, nicht der Code.
- **URLs nicht überschreibbar.** Plan 4.3 forderte „Konstante mit Default" — erfüllt. Für Staging/Self-Hosting
  fehlt aber jeder Override-Weg (kein `wp-config.php`-Vorrang via `defined()`-Guard, kein Filter, kein Settings-Feld).
- **[BEHOBEN 2026-07-17] `complyo_enable_scanner` war ein toter Schalter** (registriert, Default `1`,
  im Admin gerendert, aber nirgends gelesen). Fix: die tote Option/Konstante `COMPLYO_OPTION_SCANNER`
  ist entfernt.
- **[BEHOBEN 2026-07-17] `languages/` fehlte.** Header deklariert `Domain Path: /languages` und
  `load_plugin_textdomain()` lädt von dort, das Verzeichnis existierte aber nicht. Fix:
  `languages/complyo-compliance.pot` ergänzt (Übersetzungs-Template; UI selbst bleibt deutsch).
- **Inline-Blocker per Regex.** `preg_replace_callback` auf ganzem HTML: `</script>` in einem JS-String
  kann den Block vorzeitig beenden. Kuratierte Signaturen begrenzen den Schaden, aber Output-Buffering über
  die komplette Seite kostet Speicher/Zeit — Wechselwirkung mit Page-Cache-Plugins nicht systematisch getestet (zu prüfen).
- **[BEHOBEN 2026-07-17] Kein ETag im WP-Adapter.** Das Manifest ist server-seitig ETag-revalidiert,
  `sync_fixes()` sendete aber kein `If-None-Match` und wertete nur 200 aus → jeder Cron-Lauf war
  ein Vollabruf. Fix: `sync_fixes()` merkt sich das letzte ETag (`OPTION_ETAG`), sendet
  `If-None-Match` und behandelt `304 Not Modified` als „unverändert, keine Verarbeitung".
- Vgl. [[joomla-plugin]] (deutlich kleinerer Funktionsumfang) und [[channel-html-cli]].
