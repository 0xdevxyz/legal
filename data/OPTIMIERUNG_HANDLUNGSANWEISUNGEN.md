# Optimierungsbereich: Handlungsanweisungen & Fremd-Seiten-Logik

Datum: 2026-05-02

## Geänderte Dateien

### 1. OptimizationBanner.tsx
- Banner wird nur angezeigt wenn `analysisData` vorhanden (kein leerer Banner mehr)
- Neuer "Jetzt optimieren →" Button löst `complyo:scroll-to-first-critical` Event aus
- Event scrollt zur ersten Säule mit kritischen Issues und öffnet sie

### 2. ComplianceIssueCard.tsx
- Neues prop `isAnalysisOnly?: boolean`
- Wenn `isAnalysisOnly === true`: AI-Fix-Buttons und Expert-CTA ausgeblendet, stattdessen Hinweis
- Neue Handlungsanweisungsblöcke für alle Kategorien:
  - **Barrierefreiheit/WCAG**: 4 Schritte + Button scrollt zur Accessibility-Säule
  - **DSGVO allgemein**: 4 Schritte + Button öffnet Datenschutz-Generator via Event
  - **AGB/Widerruf/Rechtssichere Texte**: 3 Schritte + direkt KI-Fix starten
  - **Fallback**: generische 4-Schritte-Anleitung für alle anderen Typen

### 3. ComplianceIssueGroup.tsx
- Neues prop `isAnalysisOnly?: boolean`
- Wenn `isAnalysisOnly === true`: Wizard- und Fix-Buttons ausgeblendet
- `isAnalysisOnly` wird an alle Sub-`ComplianceIssueCard` weitergegeben

### 4. WebsiteAnalysis.tsx
- `isCurrentSiteLocked` und `isAnalysisOnly` Berechnung hinzugefügt
- Event-Listener für `complyo:scroll-to-first-critical` (vom OptimizationBanner)
- Event-Listener für `complyo:scroll-to-pillar` (von Barrierefreiheits-Button)
- Pro Säule: schmaler Analyse-Modus-Banner wenn `isAnalysisOnly === true`
- `isAnalysisOnly` prop an `ComplianceIssueGroup` und `ComplianceIssueCard` übergeben

### 5. OptimizationModeLock.tsx
- "Andere Seite analysiert"-Block von großer Card auf einzeiliges kompaktes Banner reduziert
- Doppelte Kurzwahl-Leiste (bereits in OptimizationQuickNav) entfernt
- Nur noch: Icon + einzeiliger Text + "Zurück"-Link
