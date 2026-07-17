# Channel: HTML-CLI (statische Projekte)

**Stand:** 2026-07-17 · **Status:** 🟢 live

> Dies ist die Detailseite zu **Channel #2** aus [[accessibility-remediation]]. Kern-Contract,
> Fix-Speicher, Approval-Workflow und Guard-Regeln stehen dort und werden hier **nicht**
> wiederholt. Diese Datei enthält nur CLI-Spezifika. Schwester-Channels:
> [[wordpress-plugin]] (Channel #3), SPA-Runtime (`backend/widgets/a11y_remediation.js`).

## Ziel
Freigegebene Barrierefreiheits-Fixes **quellseitig** in statische HTML-Projekte schreiben
(Build-Output oder Repo), als Node-Skript ohne Abhängigkeiten — CI-tauglich, idempotent,
mit `--dry-run`. Runtime-Overlay = sofort, CLI = dauerhaft im Quellcode.

## Architektur (end-to-end)
- **Skript:** `channels/html-cli/complyo-a11y.mjs` (323 Z., pure ESM, nur `node:fs`/`node:path`).
  - Aufruf: `node complyo-a11y.mjs --site-id <id> --dir <pfad> [--api <url>] [--dry-run] [--ext html,htm]`
  - Offline-/CI-Modus: `--manifest ./manifest.json` statt `--site-id` (kein Netzwerk).
  - `fetchManifest(api, siteId)` → **`GET {api}/api/accessibility/fix-manifest/{site_id}`**,
    Default-API `https://api.complyo.de` (`DEFAULT_API`). Das ist der **einzige** Endpunkt,
    den die CLI kennt.
  - `buildManifest(body)` normalisiert auf `{ altMap, lang, skipLink, linkFixes, cssRules }`;
    rückwärtskompatibel mit nacktem Alt-Text-Array bzw. `{fixes:[…]}`.
  - `patchHtml(html, manifest)` = reine Funktion, ruft in fester Reihenfolge:
    `patchAltTexts` (Match über `normalizeFilename`, WP-Größensuffix `-300x200` wird entfernt)
    → `patchHtmlLang` → `patchSkipLink` → `patchLinkLabels` (WCAG 2.4.4) → `patchStyle`.
  - `walk()` läuft rekursiv, überspringt `node_modules` und `.git`.
  - Regex-basiert, **kein DOM-Parser** — bewusst, um die Datei abhängigkeitsfrei zu halten.
- **CLI-eigene Guards** (ergänzend zu den allgemeinen aus [[accessibility-remediation]]):
  - `patchSkipLink` setzt **keinen Dangling-Link**: Ziel wird nur gesetzt, wenn die `#id`
    existiert oder ein `<main>` vorhanden ist (dann ggf. `id="complyo-main"` ergänzt);
    ohne auflösbares Ziel passiert nichts. Wiedereinfügen verhindert `data-complyo-skip-link`.
  - `patchStyle` schreibt genau einen `<style id="complyo-a11y-style">`-Block (idempotent).
  - `patchAltTexts` füllt auch ein vorhandenes **leeres** `alt=""`, überschreibt aber nie
    ein nicht-leeres. `patchLinkLabels` respektiert vorhandenes `aria-label` **und** `title`.

## Test
- `channels/html-cli/test/rescan.test.mjs` (146 Z., `node --test`, offline, browserlos):
  Fixture mit Verstößen → `patchHtml` → heuristischer Re-Scan im Test selbst prüft
  1.1.1/2.4.1/2.4.4/3.1.1 → 0 adressierte Verstöße. Plus Guard-Test und
  Back-Compat-Test für `buildManifest`.

## Bekannte Lücken / Offen
- **Es gibt keinen zweiten Contract.** Die im Audit vermuteten `/v1/*`-Endpunkte
  (`/v1/sites/{site_id}/accessibility-fixes`, `/v1/sites/{site_id}/code-package/{framework}`,
  `/v1/widget/version`, `POST /v1/sites/{site_id}/widget-feedback`) existieren **nicht**:
  im Repo kein Treffer, im Live-OpenAPI (302 Pfade) **kein einziger `/v1/`-Pfad**, live alle
  `404`. Die CLI ruft ausschließlich das Fix-Manifest. Der Punkt ist damit erledigt.
- `--site-id` erwartet die **stabile, domain-abgeleitete** ID (`derive_site_id`, „complyo.de"
  → „complyo-de"). Es gibt kein `--url`-Convenience-Flag, das die Ableitung übernimmt →
  häufigste Fehlbedienung (leeres Manifest statt Fehler).
- Der Manifest-Abruf ist **unauthentifiziert** (`fetchManifest` sendet nur `accept`).
  Damit ist jedes approved-Manifest für jede bekannte site_id öffentlich lesbar — beabsichtigt
  für die Runtime-Channels, für die CLI aber nicht nötig. Ownership-Prüfung: keine.
- Kein Packaging (kein npm-Paket, kein `bin`-Eintrag) → Nutzung nur per Repo-Checkout.
- Regex-Patching bricht bei HTML mit `<img>`/`<a>` innerhalb von Kommentaren oder
  `<script>`-Strings; in der Praxis unauffällig, formal **nicht garantiert korrekt**.
