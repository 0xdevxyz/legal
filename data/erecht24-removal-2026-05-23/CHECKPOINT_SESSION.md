# Zwischenstand-Checkpoint — eRecht24 Removal

**Datum:** 2026-05-23  
**Nächste Session-Fortführung ab:** Phase 4, Task 4.1

---

## AKTUELLER STAND (2026-05-23 — letzte Aktualisierung)

### Phasen-Status
- Phase 0 ✅ (Workspace + Baseline + Decisions + Feature-Flag)
- Phase 1 ✅ (legal_text_generator.py, legal_disclaimer.py, Templates x6, Migration, Routen, legal_change_monitor Hook)
- Phase 2 ✅ (risk_radar_routes.py, RiskRadarStatus.tsx, EarlyWarningFeed.tsx, api.ts neue Funktionen, Backend-Strings)
- Phase 3 ✅ (7 Module gelöscht + archiviert, main_production.py cleanup, smart_fix_generator + enhanced_fixer entkoppelt)
- Phase 4 ✅ (ERecht24*, AbmahnschutzStatus gelöscht; DomainHeroSection, Landing-Pages, all backend py files bereinigt)
- Phase 5 ✅ (migration_deprecate_erecht24.sql + rollback, export_erecht24_data.py, regenerate_legal_texts.py)
- Phase 6 ✅ (md/-Dateien bereinigt: TERMS_LIABILITY, PLATTFORM_UEBERSICHT, FEATURES_COMPLETE, INTEGRATION_ANLEITUNG)
- Phase 7 OFFEN (Globaler Audit + Final Report erstellen)

### Was noch zu tun ist

#### Phase 7.1 — Finaler Globaler Audit
```bash
grep -rn "eRecht24\|erecht24\|ERecht24\|Abmahnschutz\|abmahnschutz\|abmahnsicher" \
  /home/clawd/saas/legal/backend \
  /home/clawd/saas/legal/dashboard-react/src \
  /home/clawd/saas/legal/landing-react/src \
  --include="*.py" --include="*.ts" --include="*.tsx" \
  | grep -v "_archive\|Ersetzt\|ersetzt\|entfernt\|DEPRECATED\|white_label\|kein.*Versprechen\|Historisch\|Interner Ersatz\|Ersatz für"
```
Erwartet: nur white_label.py (legitim — Branding-Filter-Utility) und eigene Kommentare

#### Phase 7.2 — 99_FINAL_REPORT.md erstellen
Datei: data/erecht24-removal-2026-05-23/99_FINAL_REPORT.md

#### Phase 7.3 — 05_REPLACEMENT_GENERATOR.md erstellen
Datei: data/erecht24-removal-2026-05-23/05_REPLACEMENT_GENERATOR.md

#### Phase 7.4 — 06_RISIKO_RADAR.md erstellen
Datei: data/erecht24-removal-2026-05-23/06_RISIKO_RADAR.md

#### Phase 7.5 — 00_INDEX.md Status aktualisieren (alle Phasen ✅)

### Neue Dateien (komplett)
- backend/legal_disclaimer.py ✅
- backend/legal_text_generator.py ✅
- backend/legal_text_routes.py ✅
- backend/risk_radar_routes.py ✅
- backend/migrations/add_legal_update_ref_to_generated_documents.sql ✅
- backend/migrations/migration_deprecate_erecht24.sql ✅
- backend/migrations/migration_deprecate_erecht24_rollback.sql ✅
- backend/scripts/export_erecht24_data.py ✅
- backend/scripts/regenerate_legal_texts_for_existing_users.py ✅
- knowledge/templates/legal/imprint_de.md ✅
- knowledge/templates/legal/imprint_en.md ✅
- knowledge/templates/legal/privacy_de.md ✅
- knowledge/templates/legal/privacy_en.md ✅
- knowledge/templates/legal/tos_de.md ✅
- knowledge/templates/legal/cookie_policy_de.md ✅
- dashboard-react/src/components/dashboard/RiskRadarStatus.tsx ✅
- dashboard-react/src/components/dashboard/EarlyWarningFeed.tsx ✅

### Gelöschte Dateien (→ _archive)
- backend/erecht24_integration.py ✅
- backend/erecht24_manager.py ✅
- backend/erecht24_rechtstexte_service.py ✅
- backend/erecht24_routes_v2.py ✅
- backend/erecht24_service.py ✅
- backend/erecht24_webhook_routes.py ✅
- backend/setup_erecht24_webhook.py ✅
- dashboard-react/src/components/dashboard/ERecht24ToolsPanel.tsx ✅
- dashboard-react/src/components/setup/ERecht24Setup.tsx ✅
- dashboard-react/src/components/dashboard/AbmahnschutzStatus.tsx ✅

### Modifizierte Schlüsseldateien
- backend/main_production.py — alle eRecht24-Imports/Routen/Endpoints entfernt, neue Router hinzugefügt
- backend/fix_generator.py — _get_erecht24_content → _get_internal_legal_content
- backend/enhanced_fix_routes.py — erecht24_project_id + ABMAHNSCHUTZ-Wording entfernt
- backend/compliance_engine/enhanced_fixer.py — vollständig entkoppelt
- backend/compliance_engine/scanner.py — _enrich_with_erecht24_descriptions → _enrich_with_internal_descriptions
- backend/compliance_engine/solution_generator.py — eRecht24-Empfehlungen → interner Generator
- backend/legal_change_monitor.py — on_legal_change() Hook + erweiterte monitor_and_persist()
- backend/ai_fix_engine/smart_fix_generator.py — Kommentare bereinigt
- backend/ai_fix_engine/handlers/legal_text_handler.py — eRecht24-Logik entfernt
- backend/ai_fix_engine/white_label.py — Docstring klargestellt (legitimer Branding-Filter)
- backend/website_routes.py — eRecht24-Projekt-Creation → Legal Text Generator init
- backend/knowledge/knowledge_ingestion_service.py — eRecht24-RSS → LTO Legal Tribune
- backend/public_routes.py — "(Abmahnschutz)" → "(juristische Prüfung empfohlen)"
- dashboard-react/src/lib/api.ts — eRecht24-Funktionen entfernt, neue hinzugefügt
- dashboard-react/src/components/dashboard/DomainHeroSection.tsx — Wording
- dashboard-react/src/components/dashboard/ComplyoViralLanding.tsx — Wording
- landing-react/src/components/* — alle Wording-Updates
- md/COMPLYO_TERMS_LIABILITY.md — neue Sektion 4.1, Liability-Position
- md/PLATTFORM_UEBERSICHT.md — eRecht24-Refs entfernt
- md/COMPLYO_FEATURES_COMPLETE.md — Features aktualisiert
- md/INTEGRATION_ANLEITUNG.md — als DEPRECATED markiert
- .env.example — ENABLE_ERECHT24=false gesetzt

### Phase 0 ✅
- `data/erecht24-removal-2026-05-23/00_INDEX.md` — Phasen-Index
- `data/erecht24-removal-2026-05-23/01_BASELINE.md` — vollständiges Inventar (~52 Stellen)
- `data/erecht24-removal-2026-05-23/02_DECISIONS.md` — Entscheidungen + Disclaimer-Texte
- `.env.example` — `ENABLE_ERECHT24=false` gesetzt, alte eRecht24-Vars entfernt

### Phase 1 ✅
- `backend/legal_disclaimer.py` — kanonischer Disclaimer-Baustein
- `backend/legal_text_generator.py` — neuer Service (alle 4 Dokumenttypen, Auto-Regen, DB-Save)
- `knowledge/templates/legal/` — 6 Templates: imprint_de/en, privacy_de/en, tos_de, cookie_policy_de
- `backend/migrations/add_legal_update_ref_to_generated_documents.sql` — DB-Migration
- `backend/legal_text_routes.py` — /api/legal-texts/* Routen (GET/POST/history/preview)
- `backend/legal_change_monitor.py` — `on_legal_change()`-Hook + erweiterte `monitor_and_persist()` mit Re-Generation
- `data/erecht24-removal-2026-05-23/05_REPLACEMENT_GENERATOR.md` NOCH NICHT ERSTELLT

### Phase 2 ✅
- `backend/risk_radar_routes.py` — /api/risk-radar/score + early-warnings + summary
- `dashboard-react/src/components/dashboard/RiskRadarStatus.tsx` — neue Risiko-Radar-Karte (ersetzt AbmahnschutzStatus)
- `dashboard-react/src/components/dashboard/EarlyWarningFeed.tsx` — Frühwarner-Feed
- `dashboard-react/src/lib/api.ts` — eRecht24-Funktionen entfernt, neue Funktionen: `getLegalText`, `generateLegalText`, `getLegalTextHistory`, `previewLegalText`, `getRiskRadarScore`, `getEarlyWarnings`
- Backend-Strings bereinigt: fix_generator.py, enhanced_fix_routes.py, compliance_engine/enhanced_fixer.py, public_routes.py

### Phase 3 ✅
- `backend/_archive/` — alle 7 eRecht24-Module gesichert
- 7 eRecht24-Module gelöscht
- `main_production.py` — alle eRecht24-Imports, Router-Includes, DB-Init, set_erecht24_service, /api/erecht24/*-Endpoints entfernt
- Neue Router hinzugefügt: `legal_text_router`, `risk_radar_router`
- `ai_fix_engine/smart_fix_generator.py` — `set_erecht24_service()` und eRecht24-Block entfernt
- `compliance_engine/enhanced_fixer.py` — vollständig entkoppelt

---

## Was noch zu tun ist

### Phase 4 — Frontend-Entfernung (NÄCHSTES)

#### 4.1 Komponenten löschen + Imports finden
```bash
# Erst Imports suchen:
grep -rn "ERecht24ToolsPanel\|ERecht24Setup\|AbmahnschutzStatus" \
  /home/clawd/saas/legal/dashboard-react/src \
  --include="*.tsx" --include="*.ts"
```
- Löschen: `dashboard-react/src/components/dashboard/ERecht24ToolsPanel.tsx`
- Löschen: `dashboard-react/src/components/setup/ERecht24Setup.tsx`
- Löschen: `dashboard-react/src/components/dashboard/AbmahnschutzStatus.tsx`
- Alle Stellen wo `<AbmahnschutzStatus />` genutzt wird → auf `<RiskRadarStatus />` umlenken

#### 4.2 ComplianceIssueCard.tsx + ComplianceIssueGroup.tsx
- Datei: `dashboard-react/src/components/dashboard/ComplianceIssueCard.tsx` Zeilen ~179-189
  - `/api/erecht24/imprint` → `/api/legal-texts/imprint`
  - `/api/erecht24/privacy-policy` → `/api/legal-texts/privacy`
- Datei: `dashboard-react/src/components/dashboard/ComplianceIssueGroup.tsx` Zeilen ~110-121
  - Gleiche Umleitung

#### 4.3 ComplyoCookieManager.tsx
- `handleOpenErecht24` + "Warum eRecht24?"-Block + "Abmahnschutz inklusive" entfernen

#### 4.4 KnowledgeFeed.tsx:34
- `erecht24: "eRecht24"` aus SOURCE_LABELS-Objekt entfernen

#### 4.5 AIAssistant.tsx:119
- "Generator wie eRecht24" → "interner Rechtstexte-Generator"

#### 4.6 StripePaywallModal.tsx:105
- "eRecht24 Integration für rechtssichere Texte" → "KI-Rechtstexte mit Auto-Update"

#### 4.7 App-Pages
- `subscription/page.tsx:57` → 'eRecht24 Integration' → 'KI-Rechtstexte mit Auto-Update'
- `privacy/page.tsx:208` → eRecht24-API-Sektion entfernen

### Phase 5 — DB Migration

#### 5.1 Migration erstellen: `backend/migrations/migration_deprecate_erecht24.sql`
Prüfe erst welche eRecht24-Tabellen existieren:
```sql
SELECT tablename FROM pg_tables WHERE tablename LIKE '%erecht24%' OR tablename LIKE '%erecht%';
```
Dann Tabellen umbenennen: `erecht24_projects` → `_archived_erecht24_projects` etc.

#### 5.2 Export-Skript
- `backend/scripts/export_erecht24_data.py` erstellen

### Phase 6 — Landing/Marketing Wording

Dateien + Zeilen:
- `landing-react/src/components/modern-landing/ModernHero.tsx:96`
  "Abmahn-Schutz: Vermeiden Sie teure Strafen" → "Abmahnrisiko reduzieren: Frühwarnung & Compliance-Hinweise"
- `landing-react/src/components/modern-landing/FeaturesShowcase.tsx:27`
  `title: 'Abmahn-Schutz'` → `title: 'Risiko-Radar'`
- `landing-react/src/components/ComplyoOriginalLanding.tsx:150`
  `document.title = 'Complyo - Website Compliance & Abmahnschutz'` → `... & Risiko-Radar`
- `landing-react/src/components/ComplyoViralLanding.tsx:309`
  `'Abmahnschutz'` → `'Risiko-Radar'`
- `landing-react/src/components/alfima-landing/ProductFeatures.tsx:89`
  "Abmahn-Schutz" → "Risiko-Radar"
- `dashboard-react/src/components/dashboard/DomainHeroSection.tsx:478`
  "Noch X Punkte bis zum Abmahnschutz" → "Noch X Punkte bis zum Compliance-Ziel"
- `dashboard-react/src/components/dashboard/DomainHeroSection.tsx:536`
  Header "Abmahnschutz" → "Risiko-Radar"
- TOS: suche `dashboard-react/src/app/terms/page.tsx` oder `legal/page.tsx` für Disclaimer-Update
- md/ Doku: COMPLYO_FEATURES_COMPLETE.md, COMPLYO_TERMS_LIABILITY.md, PLATTFORM_UEBERSICHT.md, INTEGRATION_ANLEITUNG.md

### Phase 7 — Globaler Audit + Final Report
- Globale Suche nach verbleibenden eRecht24/Abmahnschutz-Stellen
- `data/erecht24-removal-2026-05-23/99_FINAL_REPORT.md` erstellen

---

## Neue Dateien erstellt (Gesamtliste)
- backend/legal_disclaimer.py
- backend/legal_text_generator.py
- backend/legal_text_routes.py
- backend/risk_radar_routes.py
- backend/migrations/add_legal_update_ref_to_generated_documents.sql
- knowledge/templates/legal/imprint_de.md
- knowledge/templates/legal/imprint_en.md
- knowledge/templates/legal/privacy_de.md
- knowledge/templates/legal/privacy_en.md
- knowledge/templates/legal/tos_de.md
- knowledge/templates/legal/cookie_policy_de.md
- dashboard-react/src/components/dashboard/RiskRadarStatus.tsx
- dashboard-react/src/components/dashboard/EarlyWarningFeed.tsx
- data/erecht24-removal-2026-05-23/_archive/ (7 archivierte Module)

## Gelöschte Dateien
- backend/erecht24_integration.py (→ _archive)
- backend/erecht24_manager.py (→ _archive)
- backend/erecht24_rechtstexte_service.py (→ _archive)
- backend/erecht24_routes_v2.py (→ _archive)
- backend/erecht24_service.py (→ _archive)
- backend/erecht24_webhook_routes.py (→ _archive)
- backend/setup_erecht24_webhook.py (→ _archive)
