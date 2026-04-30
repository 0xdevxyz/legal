# Phase 1: Critical Compliance Fixes - Context

**Gathered:** 2026-04-30
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

Eliminiert alle kritischen Compliance-Risiken die im Audit-Bericht vom 2026-04-30 als KRITISCH eingestuft wurden:
1. BFSG-Deadline (28.06.2025) klar auf Landing Page kommunizieren — Complyo bietet Forward-Looking-Compliance, keine Retroaktiv-Zertifizierung
2. TCF 2.2 Stub in Cookie-Banner-Dashboard als "Coming Soon" markieren, __tcfapi Produktiv-Stub deaktivieren
3. User-Agent-String in Consent-Logs auf Browser-Familie + Version kürzen (DSGVO-konform, kein full UA-String der PII enthält)
4. Strict-Transport-Security Header für api.complyo.de in nginx-Config setzen

</domain>

<decisions>
## Implementation Decisions

### BFSG Disclaimer (AUDIT-01)
- Disclaimer als hervorgehobene Info-Box auf Landing Page, nicht nur Footer
- Text klar und verständlich: "Deadline war 28.06.2025, Complyo hilft dir ab jetzt compliant zu werden"
- Kein Verstecken oder Kleindrucken — rechtlich und ethisch geboten
- Deutsch als Primärsprache (Zielmarkt DE/AT/CH)

### TCF 2.2 "Coming Soon" (AUDIT-02)
- In Cookie-Banner-Dashboard TCF-2.2-Option visuell als Badge "Coming Soon" markieren
- __tcfapi Stub in cookie_banner_v2.js: keine false-positive Signale — entweder entfernen oder als no-op markieren
- Klare Kommunikation: "Für Google Ad Manager / AdSense-Publisher — in Entwicklung"

### PII User-Agent Anonymisierung (AUDIT-03)
- Backend: cookie_compliance_routes.py — User-Agent vor Speicherung auf Browser-Familie + Version kürzen
- Ziel-Format: "Chrome/120" statt "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36..."
- Python-Bibliothek user-agents nutzen (bereits installiert?) oder regex-Pattern
- Bestehende Consent-Logs NICHT rückwirkend anonymisieren (zu aufwändig, kein Mehrwert für vergangene Daten)

### STS Header (AUDIT-04)
- nginx-Config für api.complyo.de: add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
- Prüfen ob bereits gesetzt — falls ja, max-age erhöhen auf 1 Jahr
- In nginx/sites-available/api.complyo.de oder nginx/sites-enabled/ eintragen

### Claude's Discretion
- Styling des BFSG-Disclaimers (Farbe, Position) — konsistent mit bestehendem Design-System
- Ob TCF 2.2 Stub komplett entfernt oder als no-op belassen wird

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- Landing Page: /home/clawd/saas/legal/landing-react/src/ (Next.js/React)
- Cookie Banner v2 Widget: /home/clawd/saas/legal/backend/widgets/cookie_banner_v2.js
- Cookie Compliance Routes: /home/clawd/saas/legal/backend/cookie_compliance_routes.py (Consent-Logging)
- nginx Config: /home/clawd/saas/legal/nginx/ oder /etc/nginx/sites-available/

### Established Patterns
- Landing Page verwendet React-Komponenten in landing-react/src/components/
- Backend ist FastAPI in backend/
- nginx-Configs liegen in /etc/nginx/sites-available/ oder /home/clawd/saas/legal/nginx/

### Integration Points
- BFSG-Disclaimer: landing-react/src/app/ (Next.js App Router) oder landing-react/src/components/
- TCF 2.2: backend/widgets/cookie_banner_v2.js (Zeile ~197-200) + dashboard-react TCF-Settings-UI
- User-Agent: backend/cookie_compliance_routes.py — Consent-Log-Endpoint
- STS-Header: nginx-Konfiguration für api.complyo.de

</code_context>

<specifics>
## Specific Ideas

- BFSG-Disclaimer ähnlich wie "Cookie Notice" Banner — prominent aber nicht störend
- TCF 2.2: Badge-Komponente wie in modernen SaaS-Dashboards ("Coming Soon" / "Beta")
- User-Agent Parsing: Regex `r'([A-Za-z]+)/(\d+)'` extrahiert Browser-Name + Major-Version

</specifics>

<deferred>
## Deferred Ideas

- Rückwirkende Anonymisierung bestehender Consent-Logs (zu aufwändig, niedrige Priorität)
- HPKP (HTTP Public Key Pinning) — deprecated, nicht implementieren
- TCF 2.2 vollständige Implementierung (IAB-Registrierung €1.575/Jahr — Business-Entscheidung, Phase > 7)

</deferred>
