# Dashboard Säulen & Score Fix — 2026-05-23

## Probleme (aus Screenshot)

### 1. Vier Säulen im ComplianceGauge zeigen 0
Im `ComplianceGauge` werden die Sub-Scores (DSGVO, Cookie, Barriere) aus `analysisData.pillar_scores` gelesen:
- `dsgvoScore`: Mittel aus `getPillarScore('gdpr', 'datenschutz')` + `getPillarScore('legal', 'impressum')` / 2
- `cookieScore`: `getPillarScore('cookies', 'cookie')`
- `barriereScore`: `getPillarScore('accessibility', 'barrierefreiheit')`

Das Backend liefert `pillar_scores` als Array von `{pillar, score}`.
Die pillar-IDs im Backend (`score_calculator.py`) sind:
- `datenschutz`, `cookies`, `impressum`, `barrierefreiheit`

Frontend sucht nach: `gdpr`, `datenschutz`, `legal`, `impressum`, `cookies`, `cookie`, `accessibility`, `barrierefreiheit`

**Root cause**: Das Backend liefert `pillar_scores` möglicherweise nicht in der API-Response oder die Pillar-IDs stimmen nicht überein. Außerdem: Wenn `analysisData` aus dem `latestScan`-Endpoint kommt, ist `pillar_scores` u.U. nicht enthalten.

### 2. Score zeigt 65 aber im Dashboard steht 0
- `ComplianceGauge` zeigt `gesamtScore = currentWebsite?.complianceScore ?? metrics.totalScore ?? 0`
- Dashboard-Metrics zeigt "Gesamt-Score: 0" (MetricsCards)
- Das passiert weil `metrics.totalScore` aus dem `/api/v2/dashboard/metrics`-Endpoint kommt
- Dieser Endpoint gibt den **durchschnittlichen** Score aller Websites zurück
- Die Gauge selbst zeigt den Score der aktuell gewählten Website → 65 ist korrekt
- Die MetricsCards "Gesamt-Score: 0" bezieht sich auf den API-Metrics-Endpoint (kein Scan vorhanden oder nicht gespeichert)

### 3. OptimizationProcessWidget — benötigt?
Der User fragt ob dieser Widget (5-Schritte-Prozess) + die "Compliance-Analyse"-Sektion (WebsiteAnalysis) beide gebraucht werden.

Das `OptimizationProcessWidget` ist ein vereinfachter 5-Schritt-Guide.
Die `WebsiteAnalysis`-Komponente zeigt die echten Issues in 4 Säulen.

**Fazit**: OptimizationProcessWidget ist redundant — es zeigt dieselben Infos wie die WebsiteAnalysis, nur weniger detailliert. User will wissen ob es benötigt wird.

## Geplante Fixes

1. Pillar-Scores: Debug warum die Werte 0 sind im Gauge
2. Gesamt-Score in MetricsCards: Warum zeigt es 0?
3. User-Entscheidung: OptimizationProcessWidget & Compliance-Analyse-Sektion entfernen?

## Status
- [ ] Pillar-Score-Herkunft im Backend prüfen (scan_history speichert pillar_scores?)
- [ ] MetricsCards-Score-Bug
- [ ] User entscheidet über OptimizationProcessWidget
