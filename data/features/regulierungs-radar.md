# Regulierungs-Radar (BFSG-Report + AI-Act-Transparenz-Check)

**Stand:** 2026-07-17 · **Status:** 🟢 live (Stufe 7.1 des Pflichtenradar-Plans)

## Ziel
Erste Stufe der „Pflichtenradar"-Evolution (planning/STRUKTUR_FIXES_LAUNCH_PLAN.md,
Phase 7): Der bestehende Scan beantwortet für zwei aktuelle Regulierungen explizit
„gilt das für mich, wie stehe ich da, was droht?" — als Lead-Magnet im kostenlosen
Scan. **Haftungs-Design ist Kern-Feature:** jede Erkennung trägt `confidence` +
`evidence` (Fundstelle), Formulierungen sind Selbst-Check, nie Rechtsberatung (RDG).

## Architektur
- **AI-Act-Transparenz-Check:** `backend/compliance_engine/checks/ai_act_transparency_check.py`
  - Signatur-Katalog `CHATBOT_SIGNATURES` (~20 Anbieter): Regex auf script/iframe/link-src,
    Inline-Script-Objekte und echte Netzwerk-Requests (`request_urls` vom Browser-Render).
  - Zwei Klassen: **KI-nativ** (Chatbase, Botpress, Voiceflow …) → ohne erkennbaren
    KI-Hinweis auf der Seite (`DISCLOSURE_PATTERNS`) `warning` mit `risk_euro=5000`,
    sonst `info`. **Chat-Plattform mit KI-Option** (Intercom, Tidio, HubSpot …) →
    immer `info` „KI-Modus prüfen".
  - Issue-Format: `category="ai_act_transparency"` (→ Säule `legal`),
    `legal_basis="Art. 50 Abs. 1 KI-VO (VO (EU) 2024/1689)"`,
    `metadata={provider, confidence, evidence, disclosure_found}`.
  - Läuft als 12. Check im Scanner-`gather` (`scanner.py`), non-fatal.
- **Scan-Response-Blöcke** (`ComplianceScanner._build_bfsg_report` / `_build_ai_act_report`
  in `backend/compliance_engine/scanner.py`), Felder `bfsg_report` + `ai_act_report`:
  - `bfsg_report`: Anwendbarkeits-Indiz über `detect_shop()` (`likely_in_scope`,
    mit Kleinstunternehmen-Hinweis), Accessibility-Säule (Score/Status/Counts/
    `risk_euro` nur aus A11y-Issues via `ScoreCalculator.categorize`),
    `statement_found` (fehlende Barrierefreiheitserklärung aus Issues),
    Deadline-/Bußgeld-Framing (28.06.2025, § 37 BFSG bis 100.000 €), Disclaimer.
  - `ai_act_report`: Provider-Liste mit confidence/evidence/`action_needed`,
    Bußgeld-Hinweis Art. 99 KI-VO, Disclaimer.
- **Lead-Magnet-Ausspielung:**
  - `POST /api/analyze-preview` (`backend/public_routes.py`) reicht beide Blöcke
    durch; Endpoint hat seit 7.1 `rate_limit("analyze_preview", 3, 60)` (vorher
    ungedrosselter Voll-Scan ohne Auth!).
  - Landing `landing-react/src/components/landing/WebsiteScanner.tsx`: Block
    „Regulierungs-Radar" über der Score-Karte — BFSG-Karte (immer) + AI-Act-Karte
    (nur wenn Systeme erkannt), rot bei Handlungsbedarf.

## Tests
`backend/tests/test_ai_act_transparency.py` (8 Tests): warning ohne Disclosure,
info mit Disclosure, Plattform-Prüfhinweis, Erkennung über Netzwerk-Requests,
Negativfall, BFSG-Report-Zahlen (nur A11y-Issues), fehlende Erklärung,
AI-Act-Aggregation. Live verifiziert: intercom.com → „Intercom (Fin AI möglich)",
complyo.de → 0 Systeme, BFSG-Block vorhanden.

## Bewusste Grenzen / nächste Stufen
- Kein KI-Einsatz im Check selbst (rein signaturbasiert) — falsch-positive arm,
  aber blind für unbekannte/self-hosted Bots. Erweiterung des Katalogs ist ein
  Datenpflege-Thema, kein Code-Thema.
- Disclosure-Erkennung ist Seitentext-Heuristik; Hinweise, die nur im
  Chat-Widget-DOM (iframe) stehen, werden nicht gesehen → deshalb nie härter
  als „fehlt offenbar" formulieren.
- Stufe 7.2 (Pflichten-Report mit Firmenprofil) und 7.3 (lebender Graph) sind
  per Fokus-Regel gesperrt bis zahlende Kunden da sind; RDG-Klärung vor 7.2.
