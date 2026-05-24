# Baseline-Inventar: Alle eRecht24 & Abmahnschutz-Referenzen

**Erstellt:** 2026-05-23  
**Zweck:** Vollständige Bestandsaufnahme vor der Entfernung

---

## A. Backend-Module (zu löschen / archivieren)

| Datei | Beschreibung |
|---|---|
| `backend/erecht24_integration.py` | Basis-Integration eRecht24 |
| `backend/erecht24_manager.py` | Manager-Layer eRecht24 |
| `backend/erecht24_rechtstexte_service.py` | Service für Rechtstexte-Abruf |
| `backend/erecht24_routes_v2.py` | V2-API-Router `/api/v2/erecht24/*` |
| `backend/erecht24_service.py` | Haupt-Service-Klasse |
| `backend/erecht24_webhook_routes.py` | Webhook-Empfänger für Push-Notifications |
| `backend/setup_erecht24_webhook.py` | Einmal-Setup-Skript |

---

## B. `main_production.py` — betroffene Zeilen

| Zeile(n) | Inhalt | Aktion |
|---|---|---|
| 80 | `from erecht24_rechtstexte_service import ...` | Import entfernen |
| 88 | `from erecht24_service import erecht24_service` | Import entfernen |
| 89 | `from erecht24_webhook_routes import router as erecht24_webhook_router` | Import entfernen |
| 131–132 | `from erecht24_routes_v2 import router as erecht24_v2_router` | Import entfernen |
| 329, 332 | `'init_erecht24_projects.sql'` in Schema-Init | Entfernen |
| 511–513 | `import erecht24_webhook_routes; ...db_pool = db_pool` | Block entfernen |
| 535–536 | `app.include_router(erecht24_webhook_router)` + v2 | Entfernen |
| 849–850 | `smart_fix_generator.set_erecht24_service(erecht24_service)` | Entfernen |
| 1784–1923+ | Alle `/api/erecht24/*`-Endpoints | Block entfernen |

---

## C. Backend — "Abmahnschutz"-Strings

| Datei | Zeile | Inhalt | Aktion |
|---|---|---|---|
| `backend/fix_generator.py` | 1062 | `'✅ Rechtssicherer Text von eRecht24 - Abmahnschutz inklusive!'` | → `'Compliance-Hinweis: KI-generierte Vorlage (kein Rechtsberatungs-Ersatz)'` |
| `backend/enhanced_fix_routes.py` | 35, 104, 120 | `erecht24_project_id`, "ABMAHNSCHUTZ!" | eRecht24-Feld entfernen; Wording anpassen |
| `backend/compliance_engine/enhanced_fixer.py` | 29,39,45,147–196,211,394 | `erecht24_service`-Parameter, `abmahnschutz: True/False` | Service entfernen; Felder → `risk_reduced`, `risk_note` |
| `backend/public_routes.py` | 1030 | `'5. AGB von Rechtsanwalt prüfen (Abmahnschutz)'` | → `'(juristische Prüfung empfohlen)'` |
| `backend/public_routes.py` | 1573 | `'4. AGB prüfen lassen (Abmahnschutz)'` | gleich |

---

## D. DB-Artefakte (Soft-Deprecation)

| Datei | Aktion |
|---|---|
| `backend/init_erecht24_projects.sql` | Aus Schema-Init entfernen; Tabellen → `_archived_`-Prefix |
| `backend/migration_erecht24_fixed.sql` | Als deprecated markieren |
| `backend/migration_erecht24_full.sql` | Als deprecated markieren |

---

## E. Frontend-Komponenten (zu löschen / ersetzen)

| Datei | Beschreibung | Aktion |
|---|---|---|
| `dashboard-react/src/components/dashboard/ERecht24ToolsPanel.tsx` | eRecht24-Tool-Panel | Löschen |
| `dashboard-react/src/components/setup/ERecht24Setup.tsx` | Setup-Wizard eRecht24 | Löschen |
| `dashboard-react/src/components/dashboard/AbmahnschutzStatus.tsx` | Abmahnschutz-Status-Karte | → `RiskRadarStatus.tsx` ersetzen |

---

## F. Frontend — eRecht24-Nutzung in bestehenden Komponenten

| Datei | Zeile(n) | Inhalt | Aktion |
|---|---|---|---|
| `dashboard-react/src/lib/api.ts` | 580–700 | `ERecht24Project`, `createERecht24Project`, `getERecht24LegalText`, `validateImprint`, `getCookieConfig` | Entfernen; neue Funktionen hinzufügen |
| `dashboard-react/src/components/dashboard/ComplianceIssueGroup.tsx` | 110–121 | `/api/erecht24/imprint`, `/api/erecht24/privacy-policy` | → `/api/legal-texts/imprint` etc. |
| `dashboard-react/src/components/dashboard/ComplianceIssueCard.tsx` | 179–189 | Gleiche eRecht24-Routen | → interne Routen |
| `dashboard-react/src/components/dashboard/ComplyoCookieManager.tsx` | 23, 43, 93 | `handleOpenErecht24`, "Warum eRecht24?", "Abmahnschutz inklusive" | Block entfernen |
| `dashboard-react/src/components/dashboard/LegalDocumentGenerator.tsx` | mehrere | eRecht24-Logik | → interner Generator |
| `dashboard-react/src/components/dashboard/LegalTextWizard.tsx` | mehrere | eRecht24-Logik | → interner Generator |
| `dashboard-react/src/components/dashboard/KnowledgeFeed.tsx` | 34 | `erecht24: "eRecht24"` Source-Mapping | Entfernen |
| `dashboard-react/src/components/ai/AIAssistant.tsx` | 119 | "Generator wie eRecht24" | → "interne Rechtstexte-Generierung" |
| `dashboard-react/src/components/dashboard/ERecht24ToolsPanel.tsx` | 182 | "eRecht24-Rechtstexte für Abmahnschutz" | Komponente gelöscht |
| `dashboard-react/src/components/dashboard/StripePaywallModal.tsx` | 105 | "eRecht24 Integration für rechtssichere Texte" | → "KI-Rechtstexte mit Auto-Update" |

---

## G. App-Pages

| Datei | Zeile | Inhalt | Aktion |
|---|---|---|---|
| `dashboard-react/src/app/subscription/page.tsx` | 57 | `'eRecht24 Integration'` im Features-Array | → `'KI-Rechtstexte mit Auto-Update'` |
| `dashboard-react/src/app/privacy/page.tsx` | 208 | `<h3>eRecht24 API</h3>` | Sektion entfernen/ersetzen |

---

## H. Marketing / Landing

| Datei | Zeile | Inhalt | Aktion |
|---|---|---|---|
| `landing-react/src/components/modern-landing/ModernHero.tsx` | 96 | "Abmahn-Schutz: Vermeiden Sie teure Strafen" | → "Abmahnrisiko reduzieren: Frühwarnung & Compliance-Hinweise" |
| `landing-react/src/components/modern-landing/FeaturesShowcase.tsx` | 27 | `title: 'Abmahn-Schutz'` | → `title: 'Risiko-Radar'` |
| `landing-react/src/components/ComplyoOriginalLanding.tsx` | 150 | `document.title = '... & Abmahnschutz'` | → `'... & Risiko-Radar'` |
| `landing-react/src/components/ComplyoViralLanding.tsx` | 309 | `'Abmahnschutz'` in Feature-Liste | → `'Risiko-Radar'` |
| `landing-react/src/components/alfima-landing/ProductFeatures.tsx` | 89 | "Abmahn-Schutz" | → "Risiko-Radar" |
| `dashboard-react/src/components/dashboard/DomainHeroSection.tsx` | 478 | "Noch X Punkte bis zum Abmahnschutz" | → "Noch X Punkte bis zum Compliance-Ziel" |
| `dashboard-react/src/components/dashboard/DomainHeroSection.tsx` | 536 | Header "Abmahnschutz" | → "Risiko-Radar" |

---

## I. Doku-Dateien (`md/`)

| Datei | Zeilen | Aktion |
|---|---|---|
| `md/COMPLYO_FEATURES_COMPLETE.md` | 195, 399, 466, 683 | Wording aktualisieren |
| `md/COMPLYO_TERMS_LIABILITY.md` | 112, 122, 322 | Liability-Position überarbeiten |
| `md/PLATTFORM_UEBERSICHT.md` | 172, 294 | eRecht24/Abmahnschutz-Refs entfernen |
| `md/INTEGRATION_ANLEITUNG.md` | 16, 232 | eRecht24-Hinweise entfernen |

---

## Zusammenfassung Zählung

| Kategorie | Anzahl Dateien/Stellen |
|---|---|
| Backend-Module (zu löschen) | 7 |
| main_production.py Zeilen-Blöcke | 9 Blöcke |
| Backend-Wording-Stellen | 7 |
| DB-Artefakte | 3 |
| Frontend-Komponenten (löschen/ersetzen) | 3 |
| Frontend-Stellen in bestehenden Komponenten | 10 |
| App-Pages | 2 |
| Landing/Marketing | 7 |
| Doku-Dateien | 4 |
| **GESAMT** | **~52 Stellen** |
