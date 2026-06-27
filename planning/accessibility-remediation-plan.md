# Barrierefreiheits-Remediation: Vom Overlay zur echten Quell-Korrektur

**Stand:** 2026-06-25 · **Scope:** WordPress + HTML · **Ziel:** das Client-Overlay als „Compliance-Lösung" durch echte serverseitige/quellseitige Remediation ersetzen.

> Leitsatz: Niemand kann „100 % barrierefrei" garantieren (~30–40 % der WCAG-Kriterien sind automatisiert prüfbar, der Rest braucht menschliches Urteil). Erreichbares und rechtlich tragfähiges Ziel ist **nachweisbare Konformität + dokumentierte Maßnahmen + Barrierefreiheitserklärung + Monitoring**.

---

## 1. Ist-Zustand — was schon existiert (besser als gedacht)

Die Pipeline ist in drei Schichten bereits gebaut:

### Erkennung (stark)
- **axe-core 4.8.4 im gerenderten DOM** via Playwright/Chromium headless — `compliance_engine/axe_scanner.py:22,249-256`. Volle WCAG-2.1-A/AA-Engine, Mapping `wcag111…wcag413` (`axe_scanner.py:78-210`).
- **HTML-Heuristiken** zusätzlich für ~30+ Kriterien — `compliance_engine/barrierefreiheit_check.py` (lang 3.1.1 `:327`, Title 2.4.2 `:345`, Skip-Link 2.4.1 `:363`, Link-Zweck 2.4.4 `:389`, Touch 2.5.5 `:1302`, Tabellen/SVG/Canvas, Video-Captions, PDF-Hinweise).
- **Media-Check** 1.2.1–1.2.5 + Autoplay + iframe-title — `media_accessibility_check.py:166-363`.
- ⚠️ `website_crawler.py` ist **kein** WCAG-Scanner (nur statisches HTML, Kennzahlen + Kontext/CMS-Erkennung) — `website_crawler.py:345-367`.

### Kategorisierung (sauber)
- 10 Feature-IDs mit WCAG-Refs, `AutoFixLevel` (HIGH/MEDIUM/LOW/MANUAL) und `FixType` (WIDGET/CODE/MANUAL) — `compliance_engine/feature_engine.py:25-258`.
- Summary trennt `auto_fixable` / `widget_fixable` / `manual_only` — `feature_engine.py:486-496`.

### Fix-Generierung (existiert, aber endet im Download)
- **LLM-Patches als git-Unified-Diffs** — `compliance_engine/patch_service.py:441-521`; echter HTML/CSS-Patcher via BeautifulSoup in `accessibility_patch_generator.py:127-333`.
- **Downloadbares ZIP** mit `.patch`-Diffs, HTML-Snippets, CSS, **fertigem WordPress-Plugin**, Widget-Snippet, README, summary.json — `accessibility_patch_generator.py:777-828`.
- **KI-Alt-Texte (Vision)** mit Generate→Approve-Queue — `alt_text_routes.py:124-261` (Claude Vision, `status pending→applied`).
- **BFSG-Barrierefreiheitserklärung** (Jinja2, HTML+MD, 6 Pflichtfelder, datengetrieben) — `accessibility_fix_routes.py:495-609`.
- **Fix-Validierung** 4-stufig (pre-gen/syntax/legal/AI-review) — `fix_validator.py:424-521`; **Re-Scan** via `LiveValidator.validate_fix` — `live_validator.py:15`.

### Endpoints
13 unter `/api/v2/accessibility/*`; Kern-Flow `analyze → generate-fixes → download-bundle` — `accessibility_fix_routes.py`.

---

## 2. Die zentrale Lücke

**Nichts wird auf die Live-Website zurückgeschrieben.** Output = downloadbares ZIP; persistiert wird nur das Paket-JSON in `accessibility_fix_packages`. „Live"-Wirkung entsteht heute ausschließlich über das **clientseitige Overlay** (`accessibility.js` mit `data-auto-fix="true"`). Auch approved Alt-Texte bleiben in der DB und werden nur zur Laufzeit per Widget injiziert (`GET /alt-text-fixes`) — **keine Quell-Korrektur**.

Das ist der eine Schritt, der den Unterschied zwischen „Overlay" und „echter Remediation" ausmacht.

---

## 3. WordPress ist der kürzeste Weg — Infrastruktur ist da

Das Plugin hat **bereits zwei produktive `ob_start`-HTML-Rewrite-Pipelines** mit korrekten Ausschlüssen (admin/feed/REST/ajax):
- Inline-Blocker — `class-complyo-inline-blocker.php:41,76-135`
- Local-Fonts — `class-complyo-local-fonts.php:57,95-149`
- Plus erprobte Muster: **Hintergrund-Cron** (`wp_schedule_single_event`, `local-fonts.php:209-211`) und **`update_option`-Persistenz** (`local-fonts.php:208,338`).

**Noch ungenutzt, aber ideal für echte Quell-Remediation:**
- `update_post_meta(_wp_attachment_image_alt)` / `wp_update_post` → Alt-Texte **an der Quelle** persistieren (greifen dann in allen `wp_get_attachment_image`-Aufrufen).
- `the_content`- und `wp_get_attachment_image_attributes`-Filter → Content-Remediation WP-nativ.
- **DOMDocument statt Regex** im bestehenden Buffer → robuste ARIA-/Heading-/Label-Fixes.

⚠️ Aktuell ist beides **regex-basiert** — für A11y zu fragil; DOMDocument ist Pflicht.

---

## 4. Zielarchitektur (3 Stufen)

```
        Scan (axe + Heuristik, gerendertes DOM)
                     │
            Kategorisierung (feature_engine)
                     │
        ┌────────────┼─────────────────────────┐
        ▼            ▼                          ▼
  STUFE 1        STUFE 2                    STUFE 3
  Auto-sicher    Human-in-the-loop          Manuell + Anleitung
  (anwenden)     (Vorschlag → Review → an-  (Worklist, kein Auto-Fix)
                  wenden → Re-Scan)
        │            │                          │
        └────────────┴──────────────┬───────────┘
                                     ▼
              Persistenz an der QUELLE
        ┌──────────────────────────┬───────────────────┐
        ▼                          ▼                   ▼
   WordPress-Plugin          HTML/Nicht-WP        Monitoring +
   (DOMDocument-Rewrite       (Snippet/SDK         Barrierefreiheits-
    + Attachment-alt +         oder Proxy)          erklärung (auto)
    the_content-Filter,
    Fix-Map per Cron)
```

- **Stufe 1 (auto-sicher anwenden):** `lang`, `<title>`, Alt-Texte (nach Review), Form-Label-Zuordnung, ARIA-Landmarks, Skip-Links, Button-/Link-Namen, Fokus-/Kontrast-CSS. (Heute schon als HIGH/MEDIUM markiert.)
- **Stufe 2 (HITL):** Lesereihenfolge, Link-Zwecktexte, komplexe Widgets/Tastatur, Untertitel → Vorschlag + Approve + Re-Scan-Verifikation (`live_validator.py` andocken).
- **Stufe 3 (manuell):** Media-Transkripte, PDF, inhaltliche Semantik → priorisierte Worklist im Dashboard.

---

## 5. WordPress-Plan (MVP zuerst)

**Backend (neu):** Endpoint `GET /api/widgets/fixes/{site_id}` der die **approved, auto-sicheren** Fixes als kompakte JSON-Fix-Map liefert (Alt-Texte je `image_url_hash`, lang, Landmarks, CSS-Regeln).

**Plugin (neu, auf bestehender Infrastruktur):**
1. **Cron-Sync** (Muster `local-fonts.php:209`): holt die Fix-Map vom Backend, cached in `update_option`.
2. **Alt-Text-Quell-Persistenz:** `update_post_meta($id, '_wp_attachment_image_alt', $alt)` für gematchte Attachments → echte Quell-Korrektur, kein Output-Hack.
3. **DOMDocument-Rewriter** im bestehenden `template_redirect`+`ob_start`-Hebel (analog `inline-blocker.php:41`): setzt fehlende `alt`/`aria-label`/`lang`/Skip-Links/Landmarks im ausgelieferten HTML, wo Quell-Persistenz nicht greift.
4. **Admin-UI:** Status „X Fixes angewendet, Y in Review" + Link zur Dashboard-Worklist.

**Overlay bleibt** — aber reduziert auf **End-User-Komfort** (Schriftgröße/Kontrast), klar gelabelt (Disclaimer ist bereits drin), **nicht** mehr als „Auto-Fix-Compliance".

---

## 6. HTML / Nicht-WP

- **Variante A (Snippet/SDK):** kleines JS, das aber — anders als das Overlay — **echtes, semantisch korrektes** Markup beim Server-Render erzeugt bzw. ein Build-Step/CLI, der HTML-Dateien patcht (die `.patch`-Diffs existieren schon).
- **Variante B (Reverse-Proxy):** HTML serverseitig vor Auslieferung rewriten (DOMDocument-Äquivalent serverseitig). Mächtig, aber Betriebsaufwand (TLS, Caching, Latenz).
- **Empfehlung:** WP zuerst fertigstellen; für HTML mit dem **CLI/Build-Patcher** starten (nutzt vorhandene Diffs), Proxy nur bei konkreter Nachfrage.

---

## 7. WCAG-Abdeckung: Lücken schließen

Erkennung deckt ~30+ Kriterien, **Fix-Templates nur 8** (`bfsg_prompts.py:371-381`). Priorisierte Lücken:
- **2.4.4 Link-Zweck** — wird erkannt, hat aber **keinen** Fix (kein Mapping/Prompt). Hoher Impact, gut HITL-fähig.
- **1.4.4/1.4.10 Reflow/Text-Resize, 3.2.x, 3.3.1/3.3.3 Fehlerbehandlung, 4.1.3 Status-Messages** — nur via axe gemeldet, keine Fix-Logik.
- **Heuristik-Kontrast** rechnet ohne Playwright **kein** echtes Verhältnis (`barrierefreiheit_check.py:908-934`) — axe-Pfad sicherstellen.

---

## 8. Tech-Debt / Risiken ZUERST klären (Blocker)

1. **🔴 Schema-Konflikt `accessibility_alt_text_fixes`:** zwei inkompatible Definitionen — Saver/Processor (`SERIAL`, `suggested_alt`, `site_id` String, `status='approved'`) vs. Routes (`UUID`, `generated_alt`, `is_approved`, `site_id` UUID). `UUID(site_id)` in `alt_text_routes.py:84` bricht bei `scan-...`-IDs. **Welche Migration ist produktiv?** Einer der Pfade bricht zur Laufzeit. → vor allem anderen verifizieren & konsolidieren.
2. **🟠 Doppelter Alt-Text-Pfad:** `accessibility_post_scan_processor.py:293-334` erzeugt **heuristische** Alt-Texte (kein KI, „TODO") und setzt **auto `approved`** (`accessibility_fix_saver.py:109`) — umgeht die Human-Review-Queue, die `alt_text_routes.py` korrekt hat. → auf den KI+Review-Pfad vereinheitlichen.
3. **🟠 Model-IDs prüfen:** `patch_service.py:41,155` nutzt `anthropic/claude-sonnet-4-20250514` (wirkt veraltet); Alt-Text `claude-haiku-4.5`; Review `claude-3-5-sonnet-20241022`. → gegen aktuelle IDs verifizieren (z. B. Sonnet 4.6 = `claude-sonnet-4-6`).
4. **🟡 Kein E2E-Test** „Patch anwenden → re-scannen → Issue weg". → mit `LiveValidator` schließen.

---

## 9. Roadmap (Reihenfolge)

| Phase | Inhalt | Ergebnis |
|---|---|---|
| **0. Hygiene** | Schema-Konflikt (#8.1) lösen, Alt-Text-Pfad vereinheitlichen (#8.2), Model-IDs (#8.3) | stabile Basis |
| **1. WP-MVP Alt-Text** | Fix-Map-Endpoint + Cron-Sync + `_wp_attachment_image_alt`-Persistenz | erster echter Quell-Fix |
| **2. WP DOMDocument-Rewriter** | lang/Landmarks/Skip-Links/ARIA im Buffer (DOMDocument) | breitere Auto-Fixes WP |
| **3. HITL + Re-Scan** | Review-Worklist + `LiveValidator`-Verifikation + E2E-Test (#8.4) | Verlässlichkeit, Nachweis |
| **4. Lücken** | 2.4.4 Link-Zweck-Fix, weitere Kriterien (#7) | höhere Abdeckung |
| **5. HTML/Nicht-WP** | CLI/Build-Patcher (vorhandene Diffs) | zweiter Kanal |
| **6. Monitoring** | periodischer Re-Scan + auto-aktualisierte Erklärung | „dauerhaft konform" |

---

## 10. Ehrlicher Aufwand & Grenzen

- **AT-Testing** (NVDA/JAWS/VoiceOver) ist nicht automatisierbar → Stichproben / Experten-Partner für Sign-off.
- Auch serverseitiges Patchen eines schlecht gebauten Themes hat Grenzen; **Goldstandard bleibt das Fixen der Templates**.
- Marketing: **kein „100 %"** — sondern „Quell-Remediation + KI-Alt-Texte + Audit + Maßnahmenplan + Erklärung + Monitoring".
- Gute Nachricht: Erkennung, Kategorisierung, LLM-Patches, KI-Alt-Text-Review, Erklärung und sogar Re-Scan **existieren bereits** — es fehlt im Kern die **Quell-Persistenz** (Phase 1–2), nicht die Intelligenz.

---

## 11. Multi-Channel-Auslieferung (WordPress / HTML / React) — „alles bedienen"

**Kerngedanke:** EIN Scan-/Fix-Kern, EIN Fix-Speicher, EIN Review-Workflow — und **mehrere Auslieferungs-Adapter**. Der Adapter wird pro Kunde anhand der erkannten Plattform gewählt (CMS-Erkennung existiert in `website_crawler.py`).

### Das verbindende Stück: das „Fix-Manifest"
Ein pro Site normalisiertes, content-adressiertes Set **freigegebener** Fixes, das ALLE Adapter konsumieren — generalisiert aus der gerade angelegten `accessibility_alt_text_fixes`-Tabelle:
- **Alt-Texte** je `image_url_hash` + `image_filename` + `image_src`
- **Attribut-Fixes** je Selektor/Heuristik: `aria-label`, `role`, `lang`, Label-Zuordnung, Skip-Links, Landmarks
- **CSS-Regeln** (Kontrast/Fokus)
- jeweils mit `status` (nur `approved` wird ausgeliefert), `confidence`, `source`
- Endpoint: `GET /api/widgets/fixes/{site_id}` (Erweiterung des bestehenden `/alt-text-fixes`)

### Adapter 1 — WordPress (bester Weg, quellseitig)
- Manifest per **Cron** holen + `update_option`-Cache (Muster `local-fonts.php:209`).
- **Alt-Texte an der Quelle:** `update_post_meta(_wp_attachment_image_alt)` / `the_content`- + `wp_get_attachment_image_attributes`-Filter.
- **Rest im DOMDocument-Rewrite** im bestehenden `ob_start`-Buffer (lang, Landmarks, Skip-Links, ARIA).
- ✅ echt, screenreader-korrekt, **funktioniert ohne JS**.

### Adapter 2 — Statisches HTML (build-time bevorzugt)
- **CLI/Build-Patcher** (`@complyo/a11y-cli`): konsumiert Manifest/Diffs (die `.patch`-Diffs existieren bereits in `accessibility_patch_generator.py`), patcht `.html`-Dateien **im Quellcode** → echte Remediation, eingecheckt.
- **Runtime-Loader** (kleines Script) als Fallback für nicht neu baubare Seiten — wirkt auf das bereits vorhandene Server-HTML.

### Adapter 3 — React / Vue / Angular / SPA (der schwierige Fall)
Server-HTML-Rewrite ist **wirkungslos** (gerendertes `<div id="root">` ist leer). Zwei Schichten:
- **Runtime-SDK** (`@complyo/a11y` als npm-Paket **oder** `<script>`): läuft **nach Hydration**, wendet das Manifest **semantisch** auf das Live-DOM an und re-appliziert via **MutationObserver** bei jedem Re-Render (Fixes überleben React-Renders). Das ist **Runtime-Remediation** — korrigiert echte Semantik (alt/aria/lang/Labels), nicht nur Kosmetik wie das Overlay. Ehrliche Grenze: weiterhin Runtime, nicht Quelle.
- **Dev-/Build-Integration** (Goldstandard für Teams, die es wollen):
  - ESLint-Plugin (jsx-a11y-Stil) + Codemods → Fix an der Quelle.
  - Komponenten/Hooks (`<A11yImage>`, `useAltText`) + Babel/SWC-Plugin, das Alt-Texte aus dem Manifest **zur Build-Zeit** injiziert.

### Ehrliche Matrix
| Channel | Mechanismus | Quellseitig? | Ohne JS? | Aufwand |
|---|---|---|---|---|
| WordPress | Plugin: Quell-Meta + DOM-Rewrite | ✅ alt / ⚠️ Rest | ✅ | mittel |
| HTML build | CLI-Patch | ✅ | ✅ | niedrig (Diffs da) |
| HTML runtime | Loader-Script | ❌ | ❌ | niedrig |
| SPA runtime | SDK + MutationObserver | ❌ | ❌ | mittel |
| SPA dev | ESLint + Codemod + Babel | ✅ | ✅ | hoch |

**Empfehlung:** pro Plattform zwei Geschwindigkeiten anbieten — sofort wirksame Runtime-Lösung (SDK/Loader/Plugin-DOM) **+** quellseitige Lösung (WP-Meta / CLI / Codemod) als „richtig fixen". Marketing-ehrlich: Runtime = sofort, Quelle = dauerhaft & WCAG-belastbar.

---

## 12. Status & nächste Schritte (Phase 0 läuft)

**✅ erledigt:**
- Blocker #1 verifiziert: `accessibility_alt_text_fixes` fehlte komplett → Live-Alt-Text-Pfad war stiller No-Op.
- Kanonisches Schema = `migrations/create_accessibility_alt_text_fixes.sql` (Saver-Schema; vom Live-Widget-Pfad genutzt) → **in Prod-DB angelegt**, Endpoint liefert wieder `success:true`.

**🔲 offen in Phase 0:**
- Dashboard-**View** `accessibility_fixes_overview` neu anlegen (users.id INTEGER vs. user_id UUID — Cast nötig). *Braucht Prod-DB-Freigabe.*
- **`alt_text_routes.py` reconcilen:** nutzt abweichendes Schema (UUID/`generated_alt`/`is_approved`) → auf kanonisches Schema vereinheitlichen ODER als deprecated entfernen. Entscheidung: KI-Vision+Review als kanonischer Schreibpfad.
- **Post-Scan-Processor** vom heuristischen Auto-Approve auf den KI+Review-Pfad umstellen (`accessibility_post_scan_processor.py:293`, `accessibility_fix_saver.py:109`).
- **Migrationen werden beim Deploy nicht automatisch angewendet** (Tabelle fehlte trotz vorhandener SQL) → Migrations-Runner in den Startup/Deploy hängen (auch `ai_scheduled_scans` fehlt → `ai_compliance_worker` im Dauerfehler).
- **Model-IDs** prüfen (`patch_service.py:41` `claude-sonnet-4-20250514`).
