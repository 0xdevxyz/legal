# Dashboard Pillar-Scores & Layout Fix — 2026-05-23

## Geänderte Dateien

### 1. `dashboard-react/src/app/page.tsx`
- `OptimizationProcessWidget` entfernt (redundant zu WebsiteAnalysis)
- `AIComplianceCard` entfernt (war neben WebsiteAnalysis)
- Neues Layout:
  - Row 1: DomainHeroSection
  - Row 2: WebsiteAnalysis (2 cols) + ComplianceGauge + MetricsCards (1 col)
  - Row 3: ComplianceFlowWidget
  - Row 4: LegalNews
  - Row 5: CookieComplianceWidget

### 2. `backend/compliance_engine/scanner.py`
- `pillar_scores` direkt in `scan_results` eingefügt
- Format: `[{"pillar": str, "score": int}]`
- Wird via `ScoreCalculator.calculate_pillar_scores()` berechnet
- Pillar-IDs: `datenschutz`, `cookies`, `impressum`, `barrierefreiheit`

### 3. `backend/main_production.py` — `get_latest_scan()`
- `pillar_scores` aus `scan_data` extrahiert und in API-Response aufgenommen
- Fix für: Beim Seiten-Reload wurden `pillar_scores` nicht zurückgegeben

## Root Causes

### Pillar-Scores = 0
- `scanner.py` speicherte kein `pillar_scores` in `scan_results`
- `get_latest_scan()` extrahierte `pillar_scores` nicht aus `scan_data`
- `public_routes.py` hatte separate Berechnung, aber nur für `/analyze`-Endpoint

### Layout-Redundanz
- `OptimizationProcessWidget` und `WebsiteAnalysis` zeigten dieselben Issues
- Der 5-Schritt-Widget referenzierte die WebsiteAnalysis und scrollte dorthin

## Bekannte offene Issues
- `MetricsCards` "Gesamt-Score: 0": Kommt vom `/api/v2/dashboard/metrics`-Endpoint
  der den DB-Durchschnitt berechnet. Falls der Scan nicht in `scan_history` landet 
  (z.B. bei Quick-Scan ohne korrektem User-ID-Mapping), bleibt der Wert 0.
  Separater Bug, nicht in diesem Fix adressiert.

## Update: MetricsCards "Gesamt-Score: 0" Fix

### Root Cause
`scan_history.website_id` wird beim Scan nicht gesetzt → bleibt `NULL`.
Die Query `SELECT DISTINCT ON (website_id) ... ORDER BY website_id, scan_timestamp DESC`
behandelt alle Scans als "dieselbe Website" wenn `website_id` NULL ist —
PostgreSQL gibt nur einen Datensatz zurück (oft den ältesten oder einen mit Score 0).

### Fix in `backend/dashboard_routes.py`
- `latest_scans` Query: `DISTINCT ON (COALESCE(website_id::text, url))`
- `old_scans` Query: gleicher Fallback auf `url`
- Damit wird pro URL der neueste Scan korrekt aggregiert

### Effekt
- `avg_score` (= `totalScore` in MetricsCards) zeigt jetzt den Durchschnitt
  der neuesten Scans pro URL statt fehlerhaft 0.
- `total_critical` und `total_risk` ebenfalls korrigiert.

## Iteration 2 — 2026-05-23 (Layout + Pillar-Fallback + LegalNews)

### Geänderte Dateien
1. `dashboard-react/src/app/page.tsx`
   - AIComplianceCard wieder importiert
   - Layout: Row 2 = WebsiteAnalysis (2-col) + ComplianceGauge & AIComplianceCard (1-col)
   - Row 2b: MetricsCards (full-width)
   - AIComplianceCard zeigt automatisch 99€-Upgrade wenn user.plan_type !== 'ai'

2. `dashboard-react/src/components/dashboard/ComplianceFlowWidget.tsx`
   - Clientseitiger Fallback für Pillar-Scores
   - Wenn pillar_scores aus Backend fehlt → berechnet aus issues mit category-Matching
   - Severity-Gewichtung: critical=25, warning=10, info=0
   - Pillar mit 0 Issues = 100 (nicht 0)

3. `dashboard-react/src/components/dashboard/ComplianceGauge.tsx`
   - Gleicher clientseitiger Fallback
   - DSGVO/Cookie/Barriere Mini-Cards zeigen jetzt sinnvolle Werte

4. `dashboard-react/src/components/dashboard/LegalNews.tsx`
   - Fehler-Handling robuster:
     - 401/403/404 → still leeres Array (keine Fehlermeldung)
     - Nur 5xx → "Fehler beim Laden"-Banner
     - Netzwerkfehler → still

### Container neu gebaut + neu gestartet ✅

## Iteration 3 — 2026-05-23 (Rechtstexte-Säule)

### Problem
ComplianceGauge zeigte nur 3 Säulen (DSGVO, Cookie, Barriere). Rechtstexte (Impressum/AGB) fehlte.

### Fix in `ComplianceGauge.tsx`
- `dsgvoScore`: war Mittelwert aus DSGVO + Impressum → jetzt nur DSGVO/Datenschutz
- `rechtstexteScore`: neu, = `getPillarScore('legal', 'impressum')`
- `tabs`: 5. Tab "Rechtstexte" hinzugefügt
- Breakdown-Row: `grid-cols-3` → `grid-cols-4`, 4. Eintrag "Rechtstexte" ergänzt
