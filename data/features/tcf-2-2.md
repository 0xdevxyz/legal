# TCF 2.2 (IAB Transparency & Consent Framework)

**Stand:** 2026-07-17 · **Status:** 🟡 in Arbeit

## Ziel
IAB-TCF-Unterstützung in drei Teilen: Global Vendor List (GVL) abfragen, TCF-Konfiguration
pro Site pflegen, und im Scan erkennen, ob eine Website ein CMP/TC-String/TCF-Vendoren
einsetzt. **Kein registriertes CMP** — der `__tcfapi`-Teil im Banner ist ein Stub
([[cookie-consent-widget]]).

## Architektur (end-to-end)
- **Router `backend/tcf_routes.py`** (Prefix **`/api/tcf`**, nicht `/api/v2`).
  - Registrierung hängt an `try/except ImportError` mit `TCF_ROUTES_AVAILABLE`
    (`main_production.py:104-109`), Include in `main_production.py:624-625`.
  - **Produktiv geladen — verifiziert:** alle 6 Routen stehen im live `openapi.json`
    (`/api/tcf/status/{scan_id}`, `/vendors/{scan_id}`, `/consent-string/{scan_id}`,
    `/compliance/{scan_id}`, `/gvl/vendors`, `/gvl/purposes`). Das Flag ist also `True`.
  - Auth: die vier `{scan_id}`-Routen über `get_current_user_id` →
    `dependencies.get_current_user`; Ownership durch `WHERE id = $1 AND user_id = $2` gegen
    `analysis_results` (live 401 ohne Token). `gvl/*` bewusst öffentlich (Docstring:
    „Öffentlich zugänglich").
- **Analyzer `backend/compliance_engine/tcf_vendor_analyzer.py`** (Singleton `tcf_vendor_analyzer`).
  - `load_global_vendor_list()` — `httpx` gegen `GVL_URL = https://vendor-list.consensu.org/v2/vendor-list.json`,
    24 h Prozess-Cache (`GVL_CACHE_DURATION`), bei Fehler `_get_fallback_gvl()` (10 Purposes,
    10 Vendoren, hartkodiert).
  - `parse_tc_string_basic()`, `get_vendor_by_id()`, `get_vendor_purposes()`,
    `analyze_vendors_on_page(soup, content)`, `generate_vendor_report()`.
- **Scan-Integration:** `backend/compliance_engine/scanner.py:287-296` — hinter `TCF_AVAILABLE`;
  `check_tcf_compliance()` + `analyze_vendors_on_page()` schreiben `tcf_data`
  (`has_tcf`, `cmp_name`, `cmp_id`, `tc_string_found`, `detected_vendors`, `vendor_count`)
  in `analysis_results.scan_results`. Fehler werden geschluckt →
  `tcf_data = {"has_tcf": False, "error": ...}` ([[scan-analyze-kern]]).
- **Site-Config-Block `backend/cookie_compliance_routes.py:2423-2560`** (Prefix
  `/api/cookie-compliance`):
  - `GET /tcf/vendors` — liest Tabelle `tcf_vendors`, bewusst öffentlich (live 200).
  - `GET /tcf/config/{site_id}` — seit 2026-07-17 durch `await require_site_access(site_id, credentials)`
    geschützt (live 401).
  - `POST /tcf/config` — `require_site_access` nach `site_id`-Extraktion; schreibt
    `tcf_enabled`/`tcf_vendors` mit `COALESCE`. `tcf_vendors` wird korrekt per
    `json.dumps(...)` übergeben (asyncpg-JSONB-Regel: Pool ohne json-Codec) und beim Lesen
    mit `json.loads()` entpackt.
- **Frontend:**
  - `dashboard-react/src/components/dashboard/TCFComplianceWidget.tsx` — ruft
    `/api/tcf/status/{scanId}`; gerendert aus `components/dashboard/WebsiteAnalysis.tsx:807`
    in einer `ErrorBoundary`.
  - `dashboard-react/src/components/cookie-compliance/TCFManager.tsx` — TCF-Config pro Site.
- **Banner:** `data-tcf="true"` aktiviert einen `__tcfapi`-Stub in `cookie_banner_v2.js`;
  WP- und Joomla-Plugin haben die Checkbox ([[wordpress-plugin]], [[joomla-plugin]]).

## DB
- `tcf_vendors` — Teil der Alembic-Baseline (`backend/alembic/baseline_schema.sql:2900`),
  PK `vendor_id`, Indizes `idx_tcf_vendors_active`, `idx_tcf_vendors_name`.
  **1169 Zeilen** in der Live-DB.
- `tcf_enabled` / `tcf_vendors` (JSONB) auf der Cookie-Banner-Config-Tabelle.
- Scan-TCF-Daten liegen als `tcf_data` im JSONB `analysis_results.scan_results` — keine
  eigene Tabelle.
- Migrationen ausschließlich als neue Alembic-Revision neben
  `backend/alembic/versions/20260717_baseline_2026_07.py`; `backend/migrations/_archive_pre_baseline/`
  ist gesperrt.

## Bekannte Lücken / Offen
- **[BEHOBEN 2026-07-17] OneTrust-Erkennung im Scan-Check** (`checks/tcf_check.py`): OneTrust
  wurde nur über den String `onetrust` erkannt, liefert real aber fast immer über
  `cdn.cookielaw.org` / Optanon-Bundles aus → der String tauchte in der Script-`src` nie auf,
  das Info-Issue „TCF 2.2 nicht implementiert" blieb bei OneTrust-Seiten stillschweigend aus.
  Fix: Signatur→Anzeigename-Map ergänzt um `cookielaw` und `optanon` (beide → „OneTrust"),
  plus saubere Anzeigenamen für Usercentrics/CookieFirst/Osano/Complianz. Abgesichert durch
  `tests/test_tcf_compliance.py`. Die IAB-Registrierung bleibt offen (s. u.).
- **Keine IAB-Registrierung** (`TODO_TCF_REGISTRIERUNG.md`): keine CMP-ID, kein
  TC-String-Generator, kein bestandener CMP Validation Test. Ohne CMP-ID ist der
  `__tcfapi`-Stub für AdSense/Ad-Manager-Kunden **nicht** verwertbar. Kosten €1.575/Jahr;
  Entscheidung laut TODO vertagt („sobald Kundenbedarf da ist"). Zwischenlösung für
  AdSense-Kunden: Googles eigenes CMP (ID 300).
- **Versions-Widerspruch:** Feature heißt „TCF 2.2", die GVL-Quelle ist der **v2-Endpoint**;
  live geladen: `vendorListVersion: 224`, `tcfPolicyVersion: 2`, `lastUpdated: 2023-11-16`
  (1007 Vendoren) — also eine eingefrorene TCF-2.0-Liste, keine 2.2-Policy. Das TODO nennt
  zusätzlich die TCF-2.3-Migration (Deadline Feb 2026) als bei Registrierung sofort zu
  adressieren. Quelle/Version müssen vor jeder Registrierung neu gesetzt werden.
- `cookie_compliance/tcf/vendors` (DB, 1169 Zeilen) und `tcf/gvl/vendors` (HTTP, 1007) sind
  zwei unabhängige Vendor-Quellen ohne Sync. Woher `tcf_vendors` befüllt wird und wie aktuell
  die Zeilen sind: **unklar, zu prüfen**.
- `_get_fallback_gvl()` greift still (nur Log) — bei Netzwerkfehler zeigt die UI 10 statt
  ~1000 Vendoren, ohne dass das im Response erkennbar wäre.
- Der GVL-Cache ist reiner Prozess-Speicher (Modul-Globals): jeder Worker-Neustart lädt neu.
- Der `try/except ImportError` verschleiert echte Importfehler als „nicht verfügbar";
  aktuell greift er nicht, ein späterer Fehler wäre aber nur an einer `print`-Zeile sichtbar.
