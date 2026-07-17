# Compliance-Scanner-Kern (Scan & Analyse)

**Stand:** 2026-07-17 · **Status:** 🟢 live

## Ziel
Eine öffentlich erreichbare Website in einem Durchlauf auf DSGVO-, TTDSG-, TMG-, UWG-,
Shop- und BFSG-Pflichten prüfen und daraus ein für den Kunden nachvollziehbares Ergebnis
erzeugen: **4 Säulen-Scores + Gesamtscore, Issues mit Rechtsgrundlage und `risk_euro`,
Gruppierung, Priorisierung, nächste Schritte**. Der Scan ist Eingangspunkt für alle
Folgeprodukte ([[ai-fix-engine]], [[accessibility-remediation]], [[cookie-consent-management]]).
Leitprinzip seit v4.0: **Evidenz statt Abwesenheit** — was nicht geprüft werden konnte,
gilt nicht als bestanden, sondern als `unverified`.

## Architektur (end-to-end)
- **Endpunkte** (alle in `backend/main_production.py`, außer den beiden public):
  - `POST /api/v2/analyze` (Zeile ~1180) — Auth; `ComplianceScanner.scan_website()` mit
    `asyncio.wait_for(..., 120.0)`; persistiert `scan_history` + (bei getrackter Site)
    `score_history` und `tracked_websites.last_score/last_scan_date/scan_count`.
  - `POST /api/v2/analyze/quick` (~1124) — Auth; `QuickScanner.quick_scan()`, 4 Checks
    (SSL, Impressum, Cookie, Datenschutz) rein auf statischem HTML, **kein Browser-Render,
    kein `ScoreCalculator`** (eigene Formel `100 - crit*25 - warn*10`), `is_complete: false`.
  - `POST /api/v2/analyze/complete` (~866) — Auth, `@limiter.limit("30/minute")`;
    `DeepScanner.comprehensive_scan()` = voller `scan_website()` + Kontext-Extraktion
    (`website_data`, `seo_data`, `tech_stack`, `structure`) + `DataValidator` +
    `IntelligentAnalyzer` (KI-Fixes).
  - `POST /api/analyze` (`backend/public_routes.py:105`) — trotz `public_router` **auth-
    pflichtig**; DNS-/Private-IP-Vorabprüfung, dann `ComplianceScanner.scan_website()` und
    `WebsiteCrawler.crawl_website()` (`backend/website_crawler.py`) parallel via
    `asyncio.gather`; Priorisierung über `priority_engine.calculate_fix_priority()`.
  - `POST /api/analyze-preview` (`backend/public_routes.py:1883`) — **ohne Auth**; voller
    Scan, liefert nur Score + Risiko-Range je Kategorie (Paywall), Fallback auf Mock.
- **Kern:** `backend/compliance_engine/scanner.py` → `ComplianceScanner.scan_website(url)`
  (async Context-Manager, geteilte `aiohttp`-Session):
  1. `_fetch_page()` — liefert Status **und** Body auch bei 4xx/5xx.
  2. Scanbarkeits-Gate: 401/403/404/502/503/504 → `_create_error_response` mit `reason`
     (`blocked` | `not_found` | `maintenance` | `http_error`); ein 5xx **mit** vollständig
     geliefertem Body (>3000 Bytes, `</html>`, `<body>`, Titel) wird als scanbar behandelt.
  3. Render-Entscheidung (siehe unten), `_detect_cms()`, `_detect_placeholder()` → `scan_notice`.
  4. 11 Checks parallel (`asyncio.gather(return_exceptions=True)`): barrierefreiheit,
     impressum, datenschutz, cookie, agb, shop, **declarative**, uwg, `_check_ssl_security`,
     `_check_contact_data`, `_check_social_media_plugins`; optional TCF
     (`checks/tcf_check.py` + `tcf_vendor_analyzer.py`).
  5. Crasht der **Primär-Check** einer Säule → Säule landet in `unverified_pillars`;
     `_ai_verify_unverified_pillars()` prüft nur diese per KI nach (Kostenkontrolle).
  6. `_enrich_with_internal_descriptions()`, `ScoreCalculator.classify_effort()`,
     `ScoreCalculator.compute_with_status()`, `legal_update_integration`, `IssueGrouper`.
- **Check-System:** `backend/compliance_engine/checks/` — Python-Module, je eine
  `async check_*_compliance(url, soup, session, ...)`, Rückgabe Issue-Dicts/Dataclasses
  im einheitlichen Format (`category`, `severity`, `title`, `risk_euro`, `legal_basis`,
  `is_missing`, `auto_fixable`). Exportiert über `checks/__init__.py`.
- **Deklaratives Check-Registry:** `backend/compliance_engine/declarative_check_runner.py`
  - Checks als **Daten** in der Tabelle `compliance_checks` (`applies_when` + `detection`
    als JSONB) statt als Code → der Legal-Change-Monitor (`check_generator.py`) kann neue
    Prüfungen ohne Deploy anlegen.
  - `DeclarativeCheckRegistry` (TTL-Cache 300s) wird in `main_production.py:650` via
    `init_declarative_check_registry(db_pool)` initialisiert; `run_declarative_checks()`
    läuft **gleichberechtigt neben** den Python-Checks im selben `gather` und liefert
    dasselbe Issue-Format (mit `metadata.declarative_check_slug`).
  - Gate: `always` | `site_type: shop` (via `detect_shop`) | `keywords_any/all`.
    Detektion: nur `type: "required_element"` (HTML-Regex → Links/aria/title → Kandidaten-
    Pfade per HTTP 200), optional `content_requirements` → Issue „unvollständig" (60 % `risk_euro`).
  - Live sind u. a. `widerrufsbutton`, `bfsg-barrierefreiheitserklaerung`,
    `ttdsg-cookie-consent-mechanism`, `omnibus-preisangabe-30-tage`.
- **Score:** `backend/compliance_engine/score_calculator.py`
  - `PILLAR_IDS = ["accessibility", "gdpr", "legal", "cookies"]`; Zuordnung über
    `PILLAR_CATEGORY_KEYWORDS` (erste Übereinstimmung gewinnt, Default `legal`).
    Bewusst: Security/Header → `gdpr` (Art. 32), Shop-Pflichttexte → `legal`.
  - Säule: `100 - crit*25 - warn*8`, aber **0** bei `has_missing_core`
    (`is_missing` + `critical`). Gesamt = **ungewichteter Mittelwert der 4 Säulen**.
  - `compute_with_status()` liefert je Säule `PillarStatus` (`compliant` | `partial` |
    `non_compliant` | `unverified`); `unverified` **ohne** Issues → Score 0.
  - `risk_euro` = pro Issue vom jeweiligen Check gesetzter Bußgeld-/Abmahn-Schätzwert;
    `total_risk_euro` = simple Summe über alle Issues.
- **Risiko/Priorisierung:** `priority_engine.py` (`PriorityEngine`, Score aus Risiko ×
  Aufwand × Häufigkeit, Quick-Wins) — nur von `public_routes.py:344` genutzt.
  `backend/risk_calculator.py` (Top-Level, in `main_production.py:84` importiert) ist der
  aktive Risiko-Rechner der Preview-Aggregation; `compliance_engine/risk_calculator.py`
  ist eine **zweite, eigenständige Implementierung** — zu prüfen, wer sie noch nutzt.
- **Grouping:** `issue_grouper.py` → `IssueGrouper.enrich_scan_results()` hängt Gruppen +
  `grouping_stats` an; Fehler sind nicht fatal.
- **Browser/Screenshots:** `browser_renderer.py` (Playwright/Chromium)
  - `detect_client_rendering(html)` — statische Heuristik (Next.js/`__next`, leerer Root,
    wenig Body-Text + Framework-Marker, Webpack/Vite).
  - **Zusätzlicher Trigger:** `consent_render_needed(soup)` aus `checks/cookie_check.py` —
    erkennt an `<script src>`/Inline-JS/`<link href>`, dass ein CMP/Consent-/Tracking-
    Loader existiert, ohne dass ein sichtbarer Banner-Container im statischen HTML steht →
    `smart_fetch_html(url, html, force=True)`. Genau das löst das Problem aus
    [[cookie-banner-detection]] (JS-injizierte Banner). **Nur `scan_website()`** rendert so;
    `QuickScanner` tut es nicht.
  - Das Render liefert zusätzlich `consent_buttons` (Dark-Pattern-Prüfung) und
    `request_urls` (echte Netzwerk-Requests → [[drittlandtransfer-erkennung]]).
    Gerendert wird **einmal**, das `soup` teilen sich alle Checks.
  - `screenshot_service.py` (`capture_page_images`) wird ausschließlich lazy aus
    `checks/barrierefreiheit_check.py` für Alt-Text-Vorschläge geladen, nicht vom Scan-Kern.

## DB
- `compliance_checks` — `backend/init_compliance_checks.sql`, in `init_db()`
  (`main_production.py:379`) bei jedem Start idempotent angewendet. Quelle der
  deklarativen Checks (`status='active'`).
- `scan_history` — voller Scan als JSONB (`scan_data`) + Kennzahlen; DDL uneinheitlich
  (`backend/init_scan_history.sql` vs. `backend/database_setup.sql`).
- `score_history` — Verlauf pro `tracked_websites`-Site. **DDL-Konflikt:** die beim Start
  angewendete `init_score_history.sql` kennt `compliance_score`/`scan_type`, geschrieben
  wird aber `overall_score` + `pillar_scores` (JSONB, `json.dumps`) wie in
  `migrations/complete_migration.sql`. Live-Tabelle ist ein Hybrid (`id` int,
  `website_id` uuid, `user_id` int, `overall_score`, `pillar_scores`) — Quelle der
  Wahrheit ist die Live-DB, nicht die SQL-Dateien.
- `tracked_websites` — `last_score`, `last_scan_date`, `scan_count` werden fortgeschrieben.

## Bekannte Lücken / Offen
- **Kein Rate-Limit auf den Scan-Endpunkten:** nur `/api/v2/analyze/complete` hat
  `@limiter.limit("30/minute")`. `/api/v2/analyze`, `/api/v2/analyze/quick`, `/api/analyze`
  und das **unauthentifizierte** `/api/analyze-preview` sind ungedrosselt — obwohl
  `planning/STRUKTUR_FIXES_LAUNCH_PLAN.md` (1.4, Richtwert Scan 3/min) als erledigt
  markiert ist. `/api/analyze-preview` ist damit eine offene, teure DoS-/Kostenfläche.
- **Kein Plan-Gate:** keine der Scan-Varianten prüft `plan_type` oder ein Kontingent
  (im Gegensatz zu [[deep-cookie-scanner]]).
- **Scanner ist nicht jurisdiction-aware:** `compliance_engine/jurisdictions.py` und
  `context.py` (`ScanContext`, `active_checks()`, `active_pillars()`,
  `get_effective_jurisdiction()`) werden von **keinem** Produktivpfad aufgerufen;
  `scan_website(self, url)` hat keinen `jurisdiction`-Parameter, die Check-Liste und die
  4 Säulen sind hart verdrahtet → [[jurisdiction-kontext]] ist Stufe-1-Vorarbeit ohne Wirkung.
- **Toter/paralleler Code:** `compliance_engine/rule_engine.py` (`ComplianceRuleEngine`) und
  `compliance_engine/engine.py` (`AIComplianceEngine`) werden nirgends importiert;
  `checks/pangv_check.py` und `checks/widerrufsbelehrung_check.py` sind nicht in
  `checks/__init__.py` und nicht im Scan — die aktive Logik liegt in `shop_check.py`
  (`_check_pangv`, `_check_widerruf`).
- **God-Files:** `scanner.py` 1.021 LOC, `checks/barrierefreiheit_check.py` 1.532 LOC,
  `public_routes.py` 2.382 LOC, `main_production.py` 1.903 LOC — im Launch-Plan Phase 6
  (Post-Launch-Backlog).
- **Quick-Scan divergiert:** eigene Score-Formel, eigene Check-Implementierungen, kein
  Render, keine Säulen/`pillar_status` → Score aus `/quick` ist nicht mit dem aus
  `/api/v2/analyze` vergleichbar, wird aber in dieselbe `scan_history` geschrieben.
- `_ai_verify_unverified_pillars()` macht das Scan-Ergebnis vom LLM abhängig; Verhalten bei
  KI-Ausfall ist definiert (Säule bleibt `unverified`), die Trefferquote der Nachprüfung ist
  nicht gemessen — zu prüfen.
