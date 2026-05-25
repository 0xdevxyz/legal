# Entscheidungen & Strategie

**Datum:** 2026-05-23  
**Status:** Finalisiert

---

## 1. eRecht24-Code — Clean Cut

**Entscheidung:** Vollständige Entfernung aller eRecht24-Module, Routen, Imports und UI-Komponenten.

**Begründung:**
- eRecht24-API wird nicht mehr genutzt/bezahlt
- Das Versprechen "Abmahnschutz via eRecht24" greift rechtlich nicht zuverlässig
- Eigene KI-Generierung über Update-Pipeline ist nachhaltiger und unabhängig

**Vorgehen:** Archive-Snapshot → Entfernung → neue Routen stattdessen

---

## 2. eRecht24-DB-Tabellen — Soft-Deprecation

**Entscheidung:** Tabellen umbenennen (Prefix `_archived_`), **kein** sofortiger DROP.

**Begründung:** Mögliche Bestandsdaten von Usern; 90 Tage Retention, danach Folge-Ticket für DROP.

**Tabellen betroffen:**
- `erecht24_projects` → `_archived_erecht24_projects`
- `erecht24_legal_texts` → `_archived_erecht24_legal_texts` (falls vorhanden)
- `erecht24_clients` → `_archived_erecht24_clients` (falls vorhanden)

---

## 3. Wording-Strategie: "Abmahnschutz" → "Risiko-Radar"

**Entscheidung:** Mehrstufiger Ersatz.

| Alt | Neu | Kontext |
|---|---|---|
| "Abmahnschutz" | "Risiko-Radar" | UI-Header, Feature-Karten |
| "Abmahnschutz AKTIV" | "Compliance-Ziel erreicht" | Status-Anzeige |
| "Noch X Punkte bis zum Abmahnschutz" | "Noch X Punkte bis zum Compliance-Ziel" | Hero-Section |
| "Abmahn-Schutz: Vermeiden Sie teure Strafen" | "Abmahnrisiko reduzieren: Frühwarnung & Compliance-Hinweise" | Landing |
| "ABMAHNSCHUTZ!" (Backend-Code) | "Risiko-Reduktion" | Kommentare |
| `abmahnschutz: True` | `risk_reduced: True` | API-Felder |

---

## 4. Kanonischer Disclaimer-Text

Dieser Text wird **überall** einheitlich verwendet (Backend + Frontend):

**Kurz (für Inline-Hinweise):**
> Hinweis: KI-generierte Vorlage auf Basis aktueller Rechtslage — kein Ersatz für Rechtsberatung.

**Lang (für Footer von Dokumenten und Haupt-Disclaimer):**
> Diese Texte wurden KI-gestützt auf Basis aktueller Rechtsgrundlagen erzeugt und stellen keine Rechtsberatung dar. Complyo übernimmt keine Haftung für die rechtliche Vollständigkeit oder Abmahnsicherheit. Für eine rechtsverbindliche Prüfung empfehlen wir die Konsultation eines Rechtsanwalts.

**TOS-Passus (für Nutzungsbedingungen):**
> Complyo bietet ein Hinweis- und Frühwarnsystem für Compliance-Risiken. Wir geben KEINE Garantie auf Abmahnsicherheit. Die generierten Rechtstexte sind Vorlagen auf Basis der zum Zeitpunkt der Generierung geltenden Rechtslage und ersetzen keine individuelle Rechtsberatung.

---

## 5. Rechtstexte-Generierung — Ersatz-Strategie

**Entscheidung:** Interner KI-Generator (`legal_text_generator.py`) auf Basis von:
1. `knowledge/laws/{language}/` — aktuelle Gesetzestexte
2. `knowledge/templates/legal/` — strukturierte Vorlagen mit Variablen-Slots
3. `ai_document_generator.py` — bereits vorhandene OpenRouter/Claude-Integration
4. Auto-Trigger via `legal_change_monitor` bei `severity >= MEDIUM`

**Generierte Dokumente werden versioniert** in `generated_documents`-Tabelle (mit `is_active`-Flag).

---

## 6. Backup-Strategie für Bestandsdaten

- **eRecht24-API-Keys** der User: werden als inaktiv markiert, nicht gelöscht (90 Tage)
- **Generierte Texte** aus eRecht24 (falls vorhanden in `generated_documents`): bleiben mit `status='archived'` erhalten
- **Re-Generation**: Skript `regenerate_legal_texts_for_existing_users.py` läuft einmalig nach Deployment
- **Notification** an betroffene User: "Ihre Rechtstexte wurden auf unser neues KI-System migriert"

---

## 7. Anwalts-Review-Marketplace

**Entscheidung:** Außerhalb dieses Tickets — Folge-Ticket.

Vorbereitend wird hier nur das Wording `(juristische Prüfung empfohlen)` an sinnvollen Stellen platziert, das später auf den Marketplace verlinken kann.

---

## 8. Feature-Flag

**`ENABLE_ERECHT24=false`** wird in `.env.example` als Default gesetzt.

Zweck: Sicherer Übergang — alle eRecht24-Imports werden erst mit Flag geprüft, dann bei finalem Cleanup vollständig entfernt.
