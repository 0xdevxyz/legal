# Plan: AVV (Art. 28 DSGVO) verpflichtend ins Onboarding

## Problem / Ausgangslage

Sobald ein Kunde Complyo einsetzt (Cookie-Consent-Banner, Barrierefreiheits-
Assistent), wird **Complyo zum Auftragsverarbeiter** des Kunden i.S.d. Art. 28
DSGVO. Damit ist ein **Auftragsverarbeitungsvertrag (AVV)** zwischen dem Kunden
(Verantwortlicher) und der Complyo GmbH (Auftragsverarbeiter) **gesetzlich
zwingend** — ohne AVV ist die Verarbeitung rechtswidrig (Bußgeldrisiko für beide
Seiten).

Der neue Datenschutz-Passus (`complyo_privacy_clause.py`) nennt den AVV bewusst
neutral: *„… stellt Complyo einen AVV bereit, der … abzuschließen ist."* Diese
Formulierung ist nur so lange korrekt, wie der Abschluss nicht erzwungen wird.
Sobald der AVV verpflichtend im Onboarding liegt, kann der Passus auf die
stärkere Aussage *„… wurde ein AVV geschlossen"* umgestellt werden.

**Bestehende Bausteine, die wiederverwendet werden:**
- `legal_document_routes.py` → `POST /api/legal-documents/generate-dpa` rendert
  bereits einen vollständigen AVV (Art. 28) als HTML (Jinja-Template
  `DPA_TEMPLATE_HTML`). Auftragnehmer-Daten (Complyo GmbH) sind dort einzusetzen.
- Stammdaten des Kunden (controller_name/address/contact) liegen bereits in
  `generated_documents.metadata.user_data` bzw. in den Profil-/Website-Daten.

## Ziel

Jeder aktive Complyo-Kunde hat **vor produktivem Einsatz** einen dokumentiert
angenommenen AVV. Annahme + Zeitpunkt + Version sind revisionssicher gespeichert.

## Umsetzungsschritte

### 1. Persistenz: AVV-Annahme speichern
- Neue Tabelle `dpa_acceptances` (oder Spalten an bestehender Onboarding-Tabelle):
  - `user_id`, `accepted_at`, `dpa_version`, `controller_snapshot` (JSONB der zum
    Zeitpunkt gültigen Verantwortlichen-Daten), `ip`, `user_agent`, `document_html`
    (oder Hash + Referenz auf `generated_documents`).
  - Eindeutigkeit: ein gültiger Datensatz pro `user_id` + `dpa_version`.
- AVV als versioniertes Dokument: `DPA_VERSION`-Konstante einführen; bei
  Änderung des Vertragstexts muss erneut akzeptiert werden.

### 2. Onboarding-Gate
- Im Dashboard-Onboarding einen **Pflichtschritt „Auftragsverarbeitung (AVV)"**
  ergänzen: AVV anzeigen (Render via `generate-dpa`), Checkbox „Ich schließe den
  AVV im Namen des Verantwortlichen ab" + Bestätigungs-Button.
- **Gate-Logik:** Aktivierung des Cookie-Banners / A11y-Assistenten
  (`cookie_banner_configs.is_active = true`, Fix-Package-Deploy) erst möglich,
  wenn ein gültiger `dpa_acceptances`-Eintrag existiert. Backend-seitig erzwingen
  (nicht nur UI), damit der API-Weg das Gate nicht umgeht.

### 3. Bestandskunden-Migration
- Einmaliger Aufruf/Banner für bereits aktive Kunden ohne AVV: beim nächsten
  Dashboard-Login AVV-Schritt nachholen (sanftes Gate mit Frist, dann hartes
  Gate).
- Report: Liste aktiver Kunden ohne `dpa_acceptances` (Compliance-Monitoring).

### 4. Datenschutz-Passus nachziehen
- In `complyo_privacy_clause.py` `COMPLYO_AVV_HINT` umstellen auf:
  *„Über diese Auftragsverarbeitung wurde zwischen dem Betreiber dieser Website
  und der Complyo GmbH ein AVV gemäß Art. 28 DSGVO geschlossen."*
- Optional: nur diese starke Formulierung ausspielen, wenn für den User ein
  gültiger `dpa_acceptances`-Eintrag vorliegt (sonst die neutrale Variante) —
  d.h. den Annahme-Status in den `complyo_context` aufnehmen.

### 5. Verfügbarkeit & Nachweis
- AVV jederzeit im Dashboard herunterladbar (PDF/HTML) inkl. Annahme-Datum.
- Im Verarbeitungsverzeichnis-/Compliance-Bereich verlinken.

## Offene Entscheidungen
- Rechtsform-/Firmierungs-Check: Codebase nutzt durchgängig **„Complyo GmbH"**;
  die für die ladungsfähige Anschrift gelieferte Bezeichnung war nur „Complyo".
  Vor Produktivstellung verbindlich klären (Handelsregister) und ggf. die
  Konstanten in `complyo_privacy_clause.py` + `DPA_TEMPLATE_HTML` angleichen.
- Wer ist Unterauftragnehmer (Hosting, KI-Provider OpenRouter/Anthropic, E-Mail)?
  Diese in § 4 des AVV (`subprocessors`) sauber auflisten.
- Hartes vs. weiches Gate für Bestandskunden + Übergangsfrist.

## Betroffene Dateien (Schätzung)
- `backend/legal_document_routes.py` (AVV-Versionierung, Auftragnehmer-Defaults)
- `backend/migrations/` (neue Tabelle `dpa_acceptances`)
- `backend/cookie_compliance_routes.py` (Aktivierungs-Gate)
- `backend/accessibility_fix_routes.py` (Deploy-Gate)
- `dashboard-react/` (Onboarding-Pflichtschritt + AVV-Download)
- `backend/complyo_privacy_clause.py` (Wortlaut-Upgrade nach Gate-Einführung)
