# Barrierefreiheits-Remediation

**Stand:** 2026-06-26 · **Status:** 🟡 in Arbeit
**Verwandt:** [planning/accessibility-remediation-plan.md](../../planning/accessibility-remediation-plan.md) (Strategie/Roadmap)

## Ziel
Vom kosmetischen Client-Overlay zur echten Quell-/Runtime-Remediation. EIN Scan-/Fix-Kern,
EIN Fix-Speicher, EIN Review-Workflow, mehrere Auslieferungs-Adapter (Channels).

## Kernarchitektur: das Fix-Manifest
`GET /api/accessibility/fix-manifest/{site_id}` → vereinheitlichter Contract für alle Channels.
Nur Status `approved` wird ausgeliefert. ETag-revalidiert. Rückgabe:
```
{ success, version, site_id,
  alt_texts:[…], document_fixes:[…], link_fixes:[…], css_rules:[…], counts:{…} }
```
**site_id ist immer die stabile, domain-abgeleitete ID** (`derive_site_id`, "complyo.de"→"complyo-de").
Früher wurden Fixes unter `scan_id` gespeichert → Channel-Lookup lief ins Leere (behobener No-Op).
Alle Channel-Fixes sind **guarded**: vorhandenes alt/lang/aria/Skip-Link wird nie überschrieben.

## Datenspeicher (Tabellen)
| Tabelle | Inhalt | Approval | Migration |
|---|---|---|---|
| `accessibility_alt_text_fixes` | KI-Alt-Texte je Bild | HITL (pending→approved) | create_accessibility_alt_text_fixes.sql |
| `accessibility_document_fixes` | dokumentweit: html-lang, skip-link, landmark-main, css-rule | auto (Stufe 1) | create_accessibility_document_fixes.sql |
| `accessibility_link_fixes` | WCAG 2.4.4 aria-label-Vorschläge je Link | HITL (pending) | create_accessibility_link_fixes.sql |
| `accessibility_fix_packages` | Scan-Zusammenfassung für die Barrierefreiheitserklärung | – | create_accessibility_fix_packages.sql |

Alle Pflicht-Migrationen sind im self-healing Runner registriert: `backend/main_production.py` (`ensure_migrations`).

## Backend-Bausteine
- **Saver** `backend/accessibility_fix_saver.py`: `save_alt_text_fixes`/`get_fixes_for_site`,
  `save_document_fixes`/`get_document_fixes_for_site`, `save_link_fixes`/`get_link_fixes_for_site`/`set_link_status`,
  `set_status` (alt), `get_review_queue`, `link_key(href,text)`.
- **Post-Scan-Processor** `backend/accessibility_post_scan_processor.py` (aufgerufen aus `public_routes.py`):
  generiert Alt-Texte (heuristisch, TODO KI), leitet document_fixes deterministisch aus Scan-Issues ab,
  holt bei 2.4.4-Befund die Seite und generiert link_fixes (pending). Schreibt unter stabiler site_id.
- **Manifest-Endpoint** `backend/widget_routes.py` → `get_fix_manifest`. `/alt-text-fixes` bleibt back-compat.
- **Review-Endpoints** `backend/alt_text_routes.py` (Router `/api/accessibility`, Auth required):
  `GET /alt-text-review-queue`, `POST /approve-alt-text`, `POST /generate-alt-texts`, `POST /scan-images`,
  `GET /link-review-queue`, `POST /approve-link`, `GET /worklist` (vereinheitlicht: ein Call für die UI).

## Frontend (dashboard-react, App Router)
- **Worklist-Seite** `src/app/accessibility/worklist/page.tsx` + Komponente
  `src/components/accessibility/AccessibilityWorklist.tsx`: listet Alt-Text- und Link-Vorschläge
  (Approve/Reject, Label editierbar) und zeigt dokumentweite Fixes read-only; Zähler „zu prüfen / live“.
  site_id via `generateSiteId(activeSite.url)` (= Backend `derive_site_id`). Sidebar: „A11y-Worklist“.

## Channels (Adapter)
| Channel | Datei | Konsumiert Manifest | Setzt |
|---|---|---|---|
| SPA-Runtime (JS) | `backend/widgets/a11y_remediation.js` (Serve: `/api/widgets/a11y-fixes.js`) | ✅ | alt, html-lang, skip-link, css, (aria-label*) via MutationObserver |
| HTML-CLI | `channels/html-cli/complyo-a11y.mjs` | ✅ | quellseitig alt, lang, skip-link, style, (aria-label*) |
| WordPress | `wordpress-plugin/.../includes/class-complyo-a11y-remediation.php` | ✅ | Attachment-Alt-Quell-Persistenz + the_content-DOMDocument + Output-Buffer (lang/skip-link/css), (aria-label*) |

Alle Channels setzen jetzt auch **aria-label auf nichtssagende Links** (WCAG 2.4.4, guarded).
WP wendet Link-aria im Output-Buffer an (ganze Seite inkl. Navigation).

## Verifikation
- E2E-Re-Scan offline ohne Browser: `channels/html-cli/test/rescan.test.mjs` (`node --test`).
  Fixture mit Verstößen → `patchHtml` → heuristischer Re-Scan = 0 adressierte Verstöße. Guard- + Back-Compat-Tests.
- **Echter Re-Scan (axe/Playwright)** `backend/compliance_engine/live_validator.py::rescan_accessibility`:
  scannt die Live-URL, extrahiert WCAG-Kriterien kriteriengenau (Regex `[1-4]\.\d+\.\d+`, datumssicher)
  und meldet `resolved`/`unresolved`/`all_resolved` ggü. den adressierten Kriterien. Endpoint:
  `POST /api/accessibility/rescan {site_url, criteria?}`. Im Container gegen example.com verifiziert
  (Chromium/axe laufen). Älterer grober Endpoint `/api/v2/fixes/validate` bleibt unberührt.

## Status der Bausteine
- 🟢 **Fix-Manifest + alt_texts + document_fixes + alle 3 Channels** (Commit 85f832f, deployed)
- 🟢 **Block 1 — WCAG 2.4.4 Link-Zweck**: Tabelle `accessibility_link_fixes` + Saver
  (`save_link_fixes`/`get_link_fixes_for_site`/`set_link_status`/`link_key`) + Processor-Ableitung
  (holt Seite, findet vage Links, generiert Label-Vorschlag, persistiert `pending`/HITL) +
  Manifest `link_fixes` (v1.1.0) + alle 3 Channels setzen aria-label (guarded) + E2E-Test grün.
  Vorschläge sind heuristisch aus Kontext; Auslieferung erst nach Review (Block 2).
- 🟢 **Block 2 — Dashboard-Worklist/Review-UI**: Review-Endpoints (`/worklist`, `/link-review-queue`,
  `/approve-link`) + `dashboard-react`-Seite mit Approve/Reject + Zählern. tsc grün.
- 🟢 **Block 3 — Echter Playwright-Re-Scan**: `LiveValidator.rescan_accessibility` an `ComplianceScanner`
  (axe) angedockt, WCAG-kriteriengenau + datumssicher; Endpoint `POST /api/accessibility/rescan`;
  im Container gegen example.com verifiziert.

## Bewusste Grenzen
- Alt-Text-Generierung im Processor ist noch heuristisch (KI-Vision-Pfad existiert separat in `alt_text_routes.py`).
- Link-Label-Vorschläge sind heuristisch aus Kontext (KI-Upgrade möglich, gleiche Architektur).
- Runtime-Channels (SPA/HTML-runtime) sind nicht quellseitig — ehrliche Kommunikation: Runtime = sofort, Quelle = dauerhaft.
