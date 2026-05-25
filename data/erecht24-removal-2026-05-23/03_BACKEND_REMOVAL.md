# Backend-Entfernung — Protokoll

**Status:** Phase 3 läuft
**Datum:** 2026-05-23

## Erledigte Schritte

### 3.1 main_production.py cleanup
- [x] Zeilen 80, 88-89: `erecht24_rechtstexte_service`, `erecht24_service`, `erecht24_webhook_router` Imports entfernt
- [x] Zeilen 131-132: `erecht24_v2_router` Import entfernt → ersetzt durch `legal_text_router` + `risk_radar_router`
- [x] Zeilen 325-332: `init_erecht24_projects.sql` aus Schema-Init entfernt
- [x] Zeilen 505-507: `erecht24_webhook_routes.db_pool`-Block entfernt
- [x] Zeilen 529-530: `erecht24_webhook_router` + `erecht24_v2_router` Router-Includes entfernt → ersetzt durch neue Router
- [x] Zeilen 839-840: `smart_fix_generator.set_erecht24_service()` entfernt
- [ ] Zeilen 1769-1977: `/api/erecht24/*`-Endpoints-Block NOCH ZU ENTFERNEN

### 3.2 Module gelöscht (in _archive/ gesichert)
- [x] backend/erecht24_integration.py
- [x] backend/erecht24_manager.py
- [x] backend/erecht24_rechtstexte_service.py
- [x] backend/erecht24_routes_v2.py
- [x] backend/erecht24_service.py
- [x] backend/erecht24_webhook_routes.py
- [x] backend/setup_erecht24_webhook.py

### 3.3 smart_fix_generator.py
- [ ] set_erecht24_service()-Methode entfernen
- [ ] erecht24_service.*-Calls entfernen (Zeilen 21-23, 99-115)

### 3.4 compliance_engine/enhanced_fixer.py
- [x] ERLEDIGT (via Subagent)

## Offene Schritte

### main_production.py: eRecht24 Endpoints-Block
- [x] ERLEDIGT — gesamter `/api/erecht24/*`-Block entfernt, py_compile OK

### smart_fix_generator.py Cleanup
- [x] ERLEDIGT — `set_erecht24_service()` und erecht24-Block entfernt, py_compile OK

## Nächste Phasen nach Phase 3
- Phase 4: Frontend ERecht24ToolsPanel, ERecht24Setup, AbmahnschutzStatus löschen
  - Dateien: dashboard-react/src/components/dashboard/ERecht24ToolsPanel.tsx
  - Dateien: dashboard-react/src/components/setup/ERecht24Setup.tsx
  - Dateien: dashboard-react/src/components/dashboard/AbmahnschutzStatus.tsx
  - Importstellen finden und auf RiskRadarStatus.tsx umlenken
  - ComplianceIssueCard.tsx + ComplianceIssueGroup.tsx: /api/erecht24/* → /api/legal-texts/*
  - ComplyoCookieManager.tsx: handleOpenErecht24 Block entfernen
  - KnowledgeFeed.tsx:34: `erecht24: "eRecht24"` entfernen
  - AIAssistant.tsx:119: eRecht24-Hinweis ersetzen
  - StripePaywallModal.tsx:105: Wording anpassen
  - subscription/page.tsx:57: Feature-Text ersetzen
  - privacy/page.tsx:208: eRecht24-Sektion entfernen

- Phase 5: DB Soft-Deprecation
  - Neue Migration: migration_deprecate_erecht24.sql
  - Backup-Skript: export_erecht24_data.py

- Phase 6: Landing/Marketing Wording
  - landing-react/src/components/modern-landing/ModernHero.tsx:96
  - landing-react/src/components/modern-landing/FeaturesShowcase.tsx:27
  - landing-react/src/components/ComplyoOriginalLanding.tsx:150
  - landing-react/src/components/ComplyoViralLanding.tsx:309
  - landing-react/src/components/alfima-landing/ProductFeatures.tsx:89
  - dashboard-react/src/components/dashboard/DomainHeroSection.tsx:478,536

- Phase 7: Globaler Audit + Final Report
