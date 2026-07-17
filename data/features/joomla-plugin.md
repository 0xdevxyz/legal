# Joomla-Plugin (plg_system_complyo)

**Stand:** 2026-07-17 · **Status:** 🟡 in Arbeit (Teilstand — nur Widget-Einbindung)

## Ziel
Joomla-System-Plugin, das den Complyo-Cookie-Blocker, das Cookie-Banner und optional das
Accessibility-Widget einbindet — inklusive DE/EN-Sprachdateien. Funktional die **Teilmenge** von
[[wordpress-plugin]]: die Server-Eingriffe (Inline-Blocker, Local Fonts, A11y-Remediation) fehlen.

## Architektur (end-to-end)
- **Plugin:** `joomla-plugin/plg_system_complyo/complyo.php` (145 Z., `PlgSystemComplyo extends CMSPlugin`)
  - **URL-Konstante:** `const API_BASE = 'https://api.complyo.de'` (Z. 21) — hardcoded, kein
    Settings-Feld, kein Override. **[BEHOBEN 2026-07-17]** Die deklarierte, aber nirgends genutzte
    Konstante `APP_URL` (toter Code) wurde entfernt.
  - **`onAfterInitialise()`** — frühestmöglicher Hook; `$app->getDocument()->addCustomTag($this->buildBlockerTag())`,
    damit der Blocker möglichst früh im `<head>` steht. Nur `isClient('site')`.
  - **[BEHOBEN 2026-07-17] `onBeforeCompileHead()` No-Op entfernt.** Der Hook war ein leerer
    No-Op (nur Client-Check), der eine nie existierende Fallback-Absicherung suggerierte → raus.
  - **`onAfterRender()`** — **[BEHOBEN 2026-07-17]** ersetzt jetzt nur noch das **letzte**
    `</body>` via `strripos()` + `substr_replace()` (zuvor `str_replace`, das **jedes** Vorkommen
    traf — auch `</body>` in Text-/JS-Strings → Mehrfach-/Fehlinjektion).
  - **`getSiteId()`** — Param `site_id`, sonst abgeleitet: `Uri::getInstance()`-Host, `www.`-Strip, `.`→`-`,
    lowercase. Entspricht dem Backend-`derive_site_id`. Escaping via `htmlspecialchars(ENT_QUOTES)`.
  - **`buildBlockerTag()`** — `<script src="{API}/public/cookie-blocker.js" data-site-id data-cfasync="false">`,
    **ohne** `async`/`defer` (synchron ist Pflicht).
  - **`buildBannerScripts()`** — `{API}/api/widgets/cookie-compliance.js` (opt. `data-tcf="true"`) und
    `{API}/api/widgets/accessibility.js` (`data-auto-fix`, `data-show-toolbar`), beide `async`, `data-cfasync="false"`.
- **Manifest:** `joomla-plugin/plg_system_complyo/complyo.xml` — `type="plugin" group="system"`,
  **Version 2.1.0**, Felder `site_id` (text), `enable_cookie_banner` (Default 1), `enable_tcf` (0),
  `enable_accessibility` (0).
- **Sprachen:** `joomla-plugin/plg_system_complyo/language/de-DE/` und `en-GB/`
  (je `plg_system_complyo.ini` + `.sys.ini`, je 11 Zeilen), `$autoloadLanguage = true`.

## Backend-Endpunkte (vom Plugin gerufen)
- `GET {API}/public/cookie-blocker.js`
- `GET {API}/api/widgets/cookie-compliance.js` → [[cookie-consent-widget]]
- `GET {API}/api/widgets/accessibility.js`

Kein Aufruf von `GET /api/accessibility/fix-manifest/{site_id}` — vgl. [[accessibility-remediation]].

## Installation & Konfiguration
- ZIP `joomla-plugin/plg_system_complyo.zip` (gebaut, geprüft: **v2.1.0**, ausschließlich `.de`-URLs) →
  Joomla-Admin → System → Erweiterungen installieren → Paketdatei hochladen; Plugin danach **aktivieren**
  (Joomla aktiviert System-Plugins nicht automatisch).
- Konfiguration: System → Plugins → „System – Complyo". `site_id` leer lassen → Auto-Ableitung aus der Domain.
- Dashboard-Konfiguration unter `app.complyo.de` (Link im Plugin selbst nicht hinterlegt, s. o.).

## Bekannte Lücken / Offen
- **`complyo.tech`: kein Fundort.** `grep -rn "complyo\.tech" joomla-plugin/` liefert **null Treffer**,
  auch nicht im entpackten `plg_system_complyo.zip`. Die Audit-/Plan-Aussage, das Joomla-Plugin zeige
  „ebenfalls auf `.tech`", ist **überholt**: `planning/STRUKTUR_FIXES_LAUNCH_PLAN.md` Phase 4.2/4.3
  (Domain-Sweep, URL-Konstanten) sind dort `[x]` und im Code verifiziert.
- **Fehlende Parität zu [[wordpress-plugin]]** (Plan Z. 122, Phase 6, nach Launch) — konkret fehlt:
  - **Inline-Script-Blocking** — kein Output-Buffer-Rewriting von `<script>`-Tags. Damit laufen im Markup
    stehende Tracking-Snippets **vor** dem Consent; der Client-Blocker kann das nicht nachholen.
    Das ist die schwerwiegendste Lücke.
  - **Local Fonts** — keine Lokalisierung von `fonts.googleapis.com`/`fonts.gstatic.com`
    → Drittlandtransfer bleibt bestehen, vgl. [[drittlandtransfer-erkennung]].
  - **A11y-Remediation** — kein Fix-Manifest-Abruf, keine Quell-Persistenz, kein Cron; nur das
    Client-Widget → [[accessibility-remediation]].
  - **Consent-Shortcodes** — kein Äquivalent zu `[complyo_cookie_settings]`/`[complyo_cookie_revoke]`
    (Joomla-Pendant wären Content-Plugin oder Modul).
  - **Caching-Kompatibilität** — nur `data-cfasync="false"`; keine Ausschlüsse für Joomla-Cache/JCH Optimizer
    o. ä. (WP schließt fünf Caching-Plugins aus). Blocker kann minifiziert/deferred werden.
  - **Scanner-/Statement-Optionen** — kein `data-a11y-statement-url`/`data-a11y-feedback`.
- **[BEHOBEN 2026-07-17] `onAfterRender`-Rewrite war naiv.** `str_replace('</body>', …)` ersetzte
  jedes Vorkommen (auch in Inline-JS/Kommentaren) → mehrfache Script-Einbindung. Fix:
  `strripos()` + `substr_replace()` trifft ausschließlich den schließenden Body-Tag.
- **Nur `enable_cookie_banner` gatet den Blocker.** Ist der Banner aus und nur A11y an, wird der Blocker
  nicht geladen — konsistent, aber unbelegt, ob gewollt (zu prüfen).
- Joomla-Versionskompatibilität (J4/J5) nicht dokumentiert; `complyo.xml` deklariert keine
  `<targetplatform>`-Einschränkung (zu prüfen).
