# Aktueller Kontext (Iteration 2)

## Bisher gemachte Fixes
1. `dashboard-react/src/app/page.tsx` - Layout neu strukturiert, OptimizationProcessWidget + AIComplianceCard entfernt
2. `backend/compliance_engine/scanner.py` - pillar_scores in scan_results eingefügt
3. `backend/main_production.py` - get_latest_scan() gibt pillar_scores zurück
4. `backend/dashboard_routes.py` - DISTINCT ON COALESCE(website_id::text, url) Fix
5. Container neu gebaut + neu gestartet

## Aktuelle User-Probleme (3)
1. **Layout-Anpassung**: Die Cards (MetricsCards = Gesamt-Score, Websites, KI-Optimierungen, Kritische Issues) sollen UNTER der Compliance-Analyse über die GANZE BREITE laufen, NICHT mehr neben der ComplianceGauge in der rechten Spalte
2. **AI-Upgrade-Karte 99€/Monat**: Soll dort hin wo die Cards aktuell sind (also rechte Spalte unter ComplianceGauge?)
3. **Rechtliche Updates fehlerhaft**: "Fehler beim Laden der Gesetzesänderungen" - LegalNews-Komponente
4. **ComplianceFlowWidget zeigt 0**: DSGVO/Cookie-Compliance/Barrierefreiheit/Legal alle Striche/0, Output 65 - die Werte stimmen nicht überein. User sagt mehrere 0 macht keinen Sinn

## Console Errors gesehen
- 401 Unauthorized auf:
  - /api/scans/latest
  - /api/v2/websites
  - /api/v2/dashboard/metrics
  - /api/legal-notifications/stats
  - /api/fix-jobs/active
  - /api/stripe/subscription-status
- "getTrackedWebsites failed" mit 401
- "Latest scan nicht verfügbar"
- "Active jobs nicht verfügbar"

## Dateien
- /home/clawd/saas/legal/dashboard-react/src/app/page.tsx
- /home/clawd/saas/legal/dashboard-react/src/components/dashboard/ComplianceGauge.tsx
- /home/clawd/saas/legal/dashboard-react/src/components/dashboard/ComplianceFlowWidget.tsx
- /home/clawd/saas/legal/dashboard-react/src/components/dashboard/MetricsCards.tsx
- /home/clawd/saas/legal/dashboard-react/src/components/dashboard/LegalNews.tsx
- /home/clawd/saas/legal/dashboard-react/src/components/dashboard/AIComplianceCard.tsx (entfernt aus page, könnte für Upgrade wieder rein)

## Nächste Schritte
1. Layout in page.tsx umbauen:
   - Row 2: WebsiteAnalysis (links) + ComplianceGauge + AI-Upgrade-Karte 99€ (rechts)
   - Row 2b: MetricsCards (full width)
2. ComplianceFlowWidget Pillar-Scores Bug: 0 obwohl Output 65 - prüfen ob pillar_scores im Frontend ankommt
3. LegalNews "Fehler beim Laden" untersuchen - vermutlich auch 401, aber dann sollte stiller Fallback gezeigt werden

## User-Status
- Plan: Kostenlos (sieht "PanoArt360 / Kostenlos" oben rechts)
- 401-Errors deuten auf Auth-Token-Problem oder fehlende Plan-Berechtigung hin
- Score 65 wird angezeigt, aber Pillar-Scores zeigen 0 → Backend liefert pillar_scores noch nicht (alter Scan im Cache?)

## AIComplianceCard hat schon 99€-Upgrade-Sektion
- Datei: /home/clawd/saas/legal/dashboard-react/src/components/dashboard/AIComplianceCard.tsx
- Zeile 126: `<div className="text-2xl font-bold text-white">99€</div>`
- Zeile 131: onClick → router.push('/ai-compliance/upgrade')
- Wenn user.plan_type !== 'ai' → zeigt Upgrade-Card mit 99€
- Wenn user.plan_type === 'ai' → zeigt AI Stats

## Geplante Layout-Änderung in page.tsx
```
Row 1: DomainHeroSection (full)
Row 2 (3-col grid):
  - col-span-2: WebsiteAnalysis
  - col-span-1: 
      ComplianceGauge
      AIComplianceCard (zeigt automatisch 99€ Upgrade da plan=free)
Row 3 (full width): MetricsCards
Row 4 (full width): ComplianceFlowWidget
Row 5 (full width): LegalNews
Row 6 (full width): CookieComplianceWidget
```

## ComplianceFlowWidget Bug
- /home/clawd/saas/legal/dashboard-react/src/components/dashboard/ComplianceFlowWidget.tsx
- Zeigt OUTPUT 65 (richtig) aber DSGVO/Cookie/Barriere = 0
- Liest pillar_scores aus analysisData.pillar_scores
- Backend gab vorher pillar_scores nicht zurück → muss neu gescannt werden
- ABER: Im neuen Backend wird pillar_scores nun korrekt gespeichert
- Problem: Alte Scans haben kein pillar_scores im scan_data
- Fallback: Wenn pillar_scores fehlt, sollte aus issues clientseitig berechnet werden

## LegalNews Fehler
- "Fehler beim Laden der Gesetzesänderungen"
- Datei: /home/clawd/saas/legal/dashboard-react/src/components/dashboard/LegalNews.tsx
- 401-Errors auf /api/legal-notifications/stats
- Endpoint muss möglicherweise auch ohne Auth funktionieren oder Fehler stiller behandeln
