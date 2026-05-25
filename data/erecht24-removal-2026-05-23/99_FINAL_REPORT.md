# Final Report — eRecht24-Entfernung & Risiko-Radar

**Datum:** 2026-05-23  
**Status:** ✅ Abgeschlossen  
**Ticket:** eRecht24-Removal + Abmahnschutz → Risiko-Radar

---

## Ausgangssituation

Die Plattform hatte eine tiefe Abhängigkeit zu **eRecht24** (externe API) für die Generierung von Rechtstexten und machte das rechtlich riskante Versprechen **"Abmahnschutz"** gegenüber Nutzern.

**Probleme:**
- eRecht24-Integration wurde nicht mehr genutzt/bezahlt
- "Abmahnschutz"-Versprechen ist rechtlich nicht haltbar
- 7 eRecht24-Backend-Module als Altlasten
- ~52 Stellen im Code mit eRecht24/Abmahnschutz-Referenzen

---

## Ergebnis

| Bereich | Vorher | Nachher |
|---|---|---|
| Rechtstexte-Quelle | eRecht24 API (extern) | Interner KI-Generator (knowledge/laws/) |
| Auto-Update | Manuell / eRecht24-Webhook | Trigger-getrieben via legal_change_monitor |
| Marketing-Versprechen | "Abmahnschutz" | "Risiko-Radar + Frühwarner + Disclaimer" |
| Backend-Module | 7 erecht24_*.py Dateien | 1 legal_text_generator.py + 1 risk_radar_routes.py |
| DB | erecht24_projects aktiv | _archived_erecht24_* (Soft-Deprecation) |
| Frontend | ERecht24Setup, AbmahnschutzStatus | RiskRadarStatus.tsx, EarlyWarningFeed.tsx |
| Rechtliche Position | Hartes Versprechen (riskant) | Hinweissystem mit klarem Disclaimer |
| Externe API-Abhängigkeit | eRecht24 (kostenpflichtig) | Keine (vollständig intern) |

---

## Gelöschte Dateien (→ _archive/ gesichert)

| Datei | Archiv |
|---|---|
| backend/erecht24_integration.py | _archive/ ✅ |
| backend/erecht24_manager.py | _archive/ ✅ |
| backend/erecht24_rechtstexte_service.py | _archive/ ✅ |
| backend/erecht24_routes_v2.py | _archive/ ✅ |
| backend/erecht24_service.py | _archive/ ✅ |
| backend/erecht24_webhook_routes.py | _archive/ ✅ |
| backend/setup_erecht24_webhook.py | _archive/ ✅ |
| dashboard-react/src/components/dashboard/ERecht24ToolsPanel.tsx | ❌ (kein Archiv, TSX) |
| dashboard-react/src/components/setup/ERecht24Setup.tsx | ❌ (kein Archiv, TSX) |
| dashboard-react/src/components/dashboard/AbmahnschutzStatus.tsx | ❌ (kein Archiv, TSX) |

---

## Neue Dateien

### Backend
| Datei | Beschreibung |
|---|---|
| backend/legal_disclaimer.py | Kanonischer Disclaimer-Baustein |
| backend/legal_text_generator.py | Interner Rechtstexte-Generator (4 Dokumenttypen) |
| backend/legal_text_routes.py | API: /api/legal-texts/* |
| backend/risk_radar_routes.py | API: /api/risk-radar/* |
| backend/migrations/add_legal_update_ref_to_generated_documents.sql | DB-Schema-Erweiterung |
| backend/migrations/migration_deprecate_erecht24.sql | Soft-Deprecation-Migration |
| backend/migrations/migration_deprecate_erecht24_rollback.sql | Rollback-Script |
| backend/scripts/export_erecht24_data.py | Daten-Export (90 Tage Retention) |
| backend/scripts/regenerate_legal_texts_for_existing_users.py | Bestandsuser-Migration |

### Knowledge-Templates
| Datei |
|---|
| knowledge/templates/legal/imprint_de.md |
| knowledge/templates/legal/imprint_en.md |
| knowledge/templates/legal/privacy_de.md |
| knowledge/templates/legal/privacy_en.md |
| knowledge/templates/legal/tos_de.md |
| knowledge/templates/legal/cookie_policy_de.md |

### Frontend
| Datei | Beschreibung |
|---|---|
| dashboard-react/src/components/dashboard/RiskRadarStatus.tsx | Risiko-Radar Karte |
| dashboard-react/src/components/dashboard/EarlyWarningFeed.tsx | Abmahnfallen-Frühwarner |

---

## Modifizierte Schlüsseldateien

| Datei | Änderung |
|---|---|
| backend/main_production.py | Alle eRecht24-Imports/Router/Endpoints entfernt; neue Router eingebunden |
| backend/fix_generator.py | _get_erecht24_content → _get_internal_legal_content |
| backend/enhanced_fix_routes.py | erecht24_project_id + ABMAHNSCHUTZ-Wording entfernt |
| backend/compliance_engine/enhanced_fixer.py | Vollständig entkoppelt; initialize_enhanced_fixer ohne eRecht24 |
| backend/compliance_engine/scanner.py | _enrich_with_erecht24_descriptions → _enrich_with_internal_descriptions |
| backend/compliance_engine/solution_generator.py | Empfehlungen → interner Generator |
| backend/compliance_engine/enhanced_fixer.py | Docstring + abmahnschutz-Felder entfernt |
| backend/legal_change_monitor.py | on_legal_change() Hook hinzugefügt + monitor_and_persist() erweitert |
| backend/ai_fix_engine/smart_fix_generator.py | Kommentare + set_erecht24_service() entfernt |
| backend/ai_fix_engine/handlers/legal_text_handler.py | eRecht24-Logik vollständig entfernt |
| backend/ai_fix_engine/white_label.py | Docstring klargestellt (Branding-Filter, nicht Integration) |
| backend/website_routes.py | eRecht24-Projekt-Creation → Legal Text Generator init |
| backend/knowledge/knowledge_ingestion_service.py | eRecht24-RSS → LTO Legal Tribune Online |
| backend/public_routes.py | "(Abmahnschutz)" × 2 → "(juristische Prüfung empfohlen)" |
| dashboard-react/src/lib/api.ts | eRecht24-Funktionen entfernt; neue: getLegalText, getRiskRadarScore, getEarlyWarnings |
| dashboard-react/src/components/dashboard/DomainHeroSection.tsx | "Abmahnschutz" → "Compliance-Ziel" / "Risiko-Radar" |
| landing-react/src/components/modern-landing/ModernHero.tsx | Wording |
| landing-react/src/components/modern-landing/FeaturesShowcase.tsx | "Abmahn-Schutz" → "Risiko-Radar" |
| landing-react/src/components/modern-landing/PricingModern.tsx | "eRecht24 Integration" → "KI-Rechtstexte" |
| landing-react/src/components/ComplyoOriginalLanding.tsx | document.title |
| landing-react/src/components/ComplyoViralLanding.tsx | 4 Stellen |
| landing-react/src/components/alfima-landing/ProductFeatures.tsx | "Abmahn-Schutz" → "Risiko-Radar" |
| landing-react/src/components/alfima-landing/PricingTable.tsx | Feature-Text |
| landing-react/src/components/landing/InteractiveDemo.tsx | eRecht24-Tab → KI-Rechtstexte |
| md/COMPLYO_TERMS_LIABILITY.md | Sektion 4.1 komplett neu + Liability-Position |
| md/PLATTFORM_UEBERSICHT.md | eRecht24-Refs entfernt |
| md/COMPLYO_FEATURES_COMPLETE.md | Features + Disclaimer aktualisiert |
| md/INTEGRATION_ANLEITUNG.md | Als DEPRECATED markiert |
| .env.example | ENABLE_ERECHT24=false gesetzt |

---

## Kanonischer Disclaimer (in Produktion)

**Kurz:**
> Hinweis: KI-generierte Vorlage auf Basis aktueller Rechtslage — kein Ersatz für individuelle Rechtsberatung.

**Lang:**
> Diese Texte wurden KI-gestützt auf Basis aktueller Rechtsgrundlagen erzeugt und stellen keine Rechtsberatung dar. Complyo übernimmt keine Haftung für die rechtliche Vollständigkeit oder Abmahnsicherheit. Für eine rechtsverbindliche Prüfung empfehlen wir die Konsultation eines Rechtsanwalts.

---

## Neue API-Endpunkte

| Endpoint | Beschreibung |
|---|---|
| GET /api/legal-texts/{type} | Aktives Dokument holen (imprint/privacy/tos/cookie-policy) |
| POST /api/legal-texts/{type}/generate | KI-Generierung auslösen |
| GET /api/legal-texts/{type}/history | Versionshistorie |
| GET /api/legal-texts/{type}/preview | Preview ohne Speichern |
| GET /api/risk-radar/score | Aggregierter Risiko-Score mit Kategorien |
| GET /api/risk-radar/early-warnings | Abmahnfallen-Frühwarnungen |
| GET /api/risk-radar/summary | Kompakte Dashboard-Zusammenfassung |

**Entfernte Endpunkte (alle /api/erecht24/* und /api/v2/erecht24/*):**
- /api/erecht24/setup, /api/erecht24/legal-text/*, /api/erecht24/cookie-config
- /api/v2/erecht24/projects, /api/v2/erecht24/legal-text/*, etc.

---

## Globaler Wording-Audit — Ergebnis

**Erlaubte Verbleibende Treffer** (alle legitim):
- `backend/ai_fix_engine/white_label.py` — Branding-Filter-Utility (entfernt eRecht24-HTML-Branding aus importierten Texten)
- `backend/scripts/export_erecht24_data.py` — Skript-Docstrings und Tabellennamen (Backup-Zweck)
- `backend/scripts/regenerate_legal_texts_for_existing_users.py` — Migrations-Beschreibung
- Kommentare in py-Dateien die beschreiben was entfernt wurde ("keine eRecht24-Abhängigkeit mehr", "ersetzt _get_erecht24_content")

**Unerwünschte Treffer in Produktions-Code:** 0 ✅

---

## Ausstehende Folge-Tickets

1. **Harter DB-DROP** — nach 90 Tagen (2026-08-21): `_archived_erecht24_*` Tabellen droppen
2. **Anwalts-Review-Marketplace** — Premium-Add-on via `expert_service_requests`
3. **Mehrsprachigkeit** — FR/IT/PL über erweiterten Generator
4. **Public-API Risk-Radar-Score** — für Drittsysteme
5. **Pre-Commit-Hook** — blockiert neue eRecht24/Abmahnschutz-Vorkommen in Git

---

## Deployment-Checkliste

- [ ] `python3 backend/scripts/export_erecht24_data.py` — Daten sichern
- [ ] DB-Migration `migration_deprecate_erecht24.sql` ausführen
- [ ] DB-Migration `add_legal_update_ref_to_generated_documents.sql` ausführen
- [ ] `python3 backend/scripts/regenerate_legal_texts_for_existing_users.py --dry-run` — prüfen
- [ ] `python3 backend/scripts/regenerate_legal_texts_for_existing_users.py` — ausführen
- [ ] Backend-Start ohne ImportError prüfen
- [ ] `/api/legal-texts/imprint/preview?company_name=Test` aufrufen
- [ ] `/api/risk-radar/summary` aufrufen
- [ ] Frontend-Build: `npm run build` (kein TS-Fehler)
- [ ] Dashboard: RiskRadarStatus-Karte sichtbar
- [ ] Dashboard: EarlyWarningFeed sichtbar
- [ ] Alten `/api/erecht24/` Routen → 404 (nicht 500)
