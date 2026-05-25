# Phase 6 + 7 — Offene Arbeiten (Checkpoint)

## Noch zu tun: md/ Doku-Dateien

### COMPLYO_FEATURES_COMPLETE.md
- Zeile 194: `- **eRecht24-Integration:**` → `- **KI-Rechtstexte-Generator:**`
- Zeilen 392-396: Sektion "6.1 eRecht24 API" + Dateiliste → als `~~DEPRECATED~~` markieren
- Zeile 466: `AbmahnschutzStatus.tsx` → `RiskRadarStatus.tsx`
- Zeile 559: `erecht24_routes_v2.py – eRecht24-Integration` → `legal_text_routes.py – Interner KI-Generator`
- Zeilen 683-684: Disclaimer + "eRecht24-Integration nutzen" → neuen Disclaimer-Text
- Zeilen 877-879: Webhook-Sektion → entfernen oder als deprecated markieren
- Zeile 919: `✅ eRecht24-Integration` → `✅ KI-Rechtstexte mit Auto-Update`

### COMPLYO_TERMS_LIABILITY.md
- Zeilen 107-122: Sektion "4.1 eRecht24-Integration (Priorität)" vollständig ersetzen durch neue Sektion
  ```
  ### 4.1 Interner KI-Rechtstexte-Generator
  Für Impressum, Datenschutz, AGB und Cookie-Policy nutzen wir ausschließlich unseren internen 
  KI-Generator (knowledge/laws/ + Templates).
  **WICHTIG:** Diese Texte sind KI-generierte Vorlagen — keine Rechtsberatung.
  Für rechtsverbindliche Texte empfehlen wir die Konsultation eines Rechtsanwalts.
  ```
- Zeile 197: `✅ Nutzen Sie eRecht24 für Rechtstexte` → `✅ Nutzen Sie Complyo's KI-Rechtstexte-Generator`
- Zeile 322: `✅ Rechtstexte: eRecht24 (abmahnsicher) > KI (nur Vorlage...)` → 
  `✅ Rechtstexte: Interner KI-Generator (Vorlage, juristische Prüfung empfohlen)`

### PLATTFORM_UEBERSICHT.md
- Zeile 17: `Rechtssichere Texte via eRecht24-Integration` → `KI-Rechtstexte mit automatischer Gesetzesüberwachung`
- Zeile 172: `eRecht24-Integration (abmahnsicher)` → `Interner KI-Generator (Risiko-Radar)`
- Zeilen 292-294: Sektion "eRecht24 API:" mit Code → ersetzen durch "Interner Generator:"
- Zeile 462: `✅ Rechtssichere Texte via eRecht24-Integration` → `✅ KI-Rechtstexte mit Auto-Update`

### INTEGRATION_ANLEITUNG.md
- Als DEPRECATED markieren, da Anleitung für eRecht24-Integration war
  → Neuer Header: `> ⚠️ DEPRECATED 2026-05-23: Diese Anleitung beschreibt die entfernte eRecht24-Integration.`
  → Zeile 11-16: Prioritätsliste anpassen (kein eRecht24 mehr)
  → Zeilen 84-87, 123: erecht24_service-Injection-Code kommentieren/entfernen
  → Zeilen 192-233: Response-Beispiel anpassen (source: "complyo-internal")

## TOS-Seite (Terms)
Suche: find /home/clawd/saas/legal/dashboard-react/src/app -name "*.tsx" | xargs grep -l "terms\|Nutzungsbedingungen\|AGB"
→ TOS-Passus einfügen: "Complyo bietet Hinweis-/Frühwarnsystem, KEINE Abmahnschutz-Garantie"

## Phase 7 — Globaler Wording-Audit
```bash
grep -rn "eRecht24\|erecht24\|ERecht24\|Abmahnschutz\|abmahnschutz\|abmahnsicher" \
  /home/clawd/saas/legal/backend \
  /home/clawd/saas/legal/dashboard-react/src \
  /home/clawd/saas/legal/landing-react/src \
  --include="*.py" --include="*.ts" --include="*.tsx" \
  | grep -v "_archive\|Ersetzt\|ersetzt\|entfernt\|DEPRECATED\|white_label\|kein.*Versprechen\|Historisch"
```
Erwartet: nur noch white_label.py (legitim als Branding-Filter)

## Final Report erstellen: data/erecht24-removal-2026-05-23/99_FINAL_REPORT.md

## Neue Dateien (Gesamtliste)
- backend/legal_disclaimer.py
- backend/legal_text_generator.py
- backend/legal_text_routes.py
- backend/risk_radar_routes.py
- backend/migrations/add_legal_update_ref_to_generated_documents.sql
- backend/migrations/migration_deprecate_erecht24.sql
- backend/migrations/migration_deprecate_erecht24_rollback.sql
- backend/scripts/export_erecht24_data.py
- backend/scripts/regenerate_legal_texts_for_existing_users.py
- knowledge/templates/legal/imprint_de.md
- knowledge/templates/legal/imprint_en.md
- knowledge/templates/legal/privacy_de.md
- knowledge/templates/legal/privacy_en.md
- knowledge/templates/legal/tos_de.md
- knowledge/templates/legal/cookie_policy_de.md
- dashboard-react/src/components/dashboard/RiskRadarStatus.tsx
- dashboard-react/src/components/dashboard/EarlyWarningFeed.tsx

## Gelöschte Dateien
- backend/erecht24_integration.py (→ _archive)
- backend/erecht24_manager.py (→ _archive)
- backend/erecht24_rechtstexte_service.py (→ _archive)
- backend/erecht24_routes_v2.py (→ _archive)
- backend/erecht24_service.py (→ _archive)
- backend/erecht24_webhook_routes.py (→ _archive)
- backend/setup_erecht24_webhook.py (→ _archive)
- dashboard-react/src/components/dashboard/ERecht24ToolsPanel.tsx
- dashboard-react/src/components/setup/ERecht24Setup.tsx
- dashboard-react/src/components/dashboard/AbmahnschutzStatus.tsx
