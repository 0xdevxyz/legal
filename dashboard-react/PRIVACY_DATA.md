# Datenschutz & Cookie-Dokumentation - Complyo

Diese Datei dokumentiert alle von Complyo gesp eicherten Daten, Cookies und API-Aufrufe an Dritte.
Sie dient als Basis für unsere öffentliche Datenschutzerklärung.

## 1. Verantwortlicher

**Complyo.tech**  
[Adresse wird eingetragen]  
E-Mail: contact@complyo.tech

## 2. Gespeicherte Nutzerdaten

### 2.1 User-Account-Daten

| Datentyp | Zweck | Speicherdauer | Rechtsgrundlage |
|----------|-------|---------------|-----------------|
| E-Mail-Adresse | Account-Identifikation, Login | Bis Account-Löschung | Vertragserfüllung (Art. 6 Abs. 1 lit. b DSGVO) |
| Passwort (gehasht) | Authentifizierung | Bis Account-Löschung | Vertragserfüllung |
| Vollständiger Name | Personalisierung | Bis Account-Löschung | Vertragserfüllung |
| Plan-Typ (Free/AI/Expert) | Feature-Zugriff | Bis Account-Löschung | Vertragserfüllung |
| Registrierungsdatum | Account-Management | Bis Account-Löschung | Vertragserfüllung |

### 2.2 Website-Scan-Daten

| Datentyp | Zweck | Speicherdauer | Rechtsgrundlage |
|----------|-------|---------------|-----------------|
| Gescannte URL/Domain | Service-Bereitstellung | Bis Account-Löschung | Vertragserfüllung |
| Scan-Ergebnisse (Issues) | Compliance-Analyse | 90 Tage | Vertragserfüllung |
| Scan-Historie | Verlauf & Vergleich | 90 Tage | Vertragserfüllung |
| Compliance-Score | Übersicht | 90 Tage | Vertragserfüllung |

### 2.3 Fix-History-Daten

| Datentyp | Zweck | Speicherdauer | Rechtsgrundlage |
|----------|-------|---------------|-----------------|
| Generierte Fixes (Code/Text) | Service-Bereitstellung | 90 Tage | Vertragserfüllung |
| Fix-Status | Fortschrittsverfolgung | 90 Tage | Vertragserfüllung |
| AI-Fix-Jobs | Hintergrund-Verarbeitung | 30 Tage | Vertragserfüllung |

### 2.4 Zahlungsdaten (über Stripe)

| Datentyp | Zweck | Speicherdauer | Rechtsgrundlage |
|----------|-------|---------------|-----------------|
| Stripe Customer ID | Zahlungsabwicklung | Bis Account-Löschung | Vertragserfüllung |
| Stripe Subscription ID | Abo-Management | Bis Abo-Ende + 7 Jahre | Gesetzliche Aufbewahrungspflicht |
| Zahlungshistorie | Rechnungsstellung | 10 Jahre | Gesetzliche Aufbewahrungspflicht (§ 147 AO) |

**Hinweis:** Kreditkartendaten werden NICHT bei uns gespeichert, sondern ausschließlich bei Stripe (PCI-DSS-zertifiziert).

## 3. Cookies & lokale Speicherung

### 3.1 Notwendige Cookies (Session)

Diese Cookies sind für die Funktionsfähigkeit der Plattform erforderlich.

| Cookie-Name | Zweck | Typ | Speicherdauer | Daten |
|-------------|-------|-----|---------------|-------|
| `access_token` | Authentifizierung | HTTP-Only Cookie | 24 Stunden | JWT-Token mit User-ID |
| `refresh_token` | Token-Erneuerung | HTTP-Only Cookie | 7 Tage | Refresh-Token |
| `session_id` | Session-Management | HTTP-Only Cookie | Session-Ende | Zufällige ID |

### 3.2 Funktionale Cookies (localStorage)

Diese Cookies speichern Nutzer-Präferenzen und sind nicht essentiell.

| Schlüssel | Zweck | Speicherdauer | Daten |
|-----------|-------|---------------|-------|
| `token` | Alternative Token-Speicherung | 24 Stunden | JWT-Token (Kopie) |
| `user_preferences` | UI-Einstellungen (Theme, Sprache) | Unbegrenzt | JSON-Objekt |
| `cookie_consent` | Cookie-Einwilligung | 1 Jahr | `{accepted: boolean, timestamp: string}` |
| `dashboard_state` | Dashboard-Zustand | Session | Temporäre UI-Stati |

### 3.3 Analytics-Cookies (Optional)

**Status:** Aktuell NICHT im Einsatz. Falls zukünftig implementiert, erfolgt dies nur mit ausdrücklicher Einwilligung.

## 4. API-Aufrufe an Dritte

### 4.1 eRecht24 API

**Zweck:** Generierung rechtssicherer Texte (Impressum, Datenschutzerklärung)  
**Daten die übermittelt werden:**
- Domain/URL der zu analysierenden Website
- Firmendaten (Name, Adresse, E-Mail) - nur wenn vom Nutzer eingegeben
- User-ID (intern)

**Rechtsgrundlage:** Vertragserfüllung (Art. 6 Abs. 1 lit. b DSGVO)  
**Datenschutz:** https://www.e-recht24.de/datenschutzerklaerung/

### 4.2 Stripe Payment API

**Zweck:** Zahlungsabwicklung und Abo-Management  
**Daten die übermittelt werden:**
- E-Mail-Adresse
- Name
- Zahlungsinformationen (direkt an Stripe, nicht über unsere Server)

**Rechtsgrundlage:** Vertragserfüllung (Art. 6 Abs. 1 lit. b DSGVO)  
**Datenschutz:** https://stripe.com/de/privacy

### 4.3 OpenAI API (GPT-4)

**Zweck:** AI-Fix-Generierung, Compliance-Analyse  
**Daten die übermittelt werden:**
- Gescannte Website-Inhalte (HTML, CSS-Snippets)
- Issue-Beschreibungen
- KEINE persönlichen Nutzerdaten

**Rechtsgrundlage:** Vertragserfüllung (Art. 6 Abs. 1 lit. b DSGVO)  
**Datenschutz:** https://openai.com/policies/privacy-policy

**Wichtig:** OpenAI nutzt API-Daten NICHT für Training (ab März 2023).

## 5. Server-Logs

**Gespeicherte Daten:**
- IP-Adresse (anonymisiert nach 7 Tagen)
- Zeitstempel
- HTTP-Status-Codes
- User-Agent (Browser-Info)

**Zweck:** Fehleranalyse, Sicherheit  
**Speicherdauer:** 30 Tage  
**Rechtsgrundlage:** Berechtigtes Interesse (Art. 6 Abs. 1 lit. f DSGVO)

## 6. Betroffenenrechte

Nutzer haben jederzeit folgende Rechte:

- **Art. 15 DSGVO:** Auskunft über gespeicherte Daten
- **Art. 16 DSGVO:** Berichtigung unrichtiger Daten
- **Art. 17 DSGVO:** Löschung gespeicherter Daten ("Recht auf Vergessenwerden")
- **Art. 18 DSGVO:** Einschränkung der Verarbeitung
- **Art. 20 DSGVO:** Datenportabilität (Export als JSON/CSV)
- **Art. 21 DSGVO:** Widerspruch gegen Datenverarbeitung
- **Art. 77 DSGVO:** Beschwerde bei Aufsichtsbehörde

**Kontakt für Anfragen:** privacy@complyo.tech

## 7. Datensicherheit

### 7.1 Technische Maßnahmen

- **Verschlüsselung:** TLS 1.3 für alle Verbindungen
- **Passwort-Hashing:** bcrypt (Salted Hashes)
- **Database:** PostgreSQL mit Row-Level Security
- **Backup:** Tägliche verschlüsselte Backups (30 Tage Aufbewahrung)
- **Server:** Gehostet in EU-Rechenzentren (Deutschland)

### 7.2 Organisatorische Maßnahmen

- Zugriff nur für autorisierte Mitarbeiter
- 2FA für Admin-Zugriffe
- Regelmäßige Security-Audits
- Incident-Response-Plan

## 8. Datenübermittlung außerhalb der EU

### 8.1 OpenAI (USA)

**Rechtsgrundlage:** Standardvertragsklauseln (SCCs), Angemessenheitsbeschluss (falls vorhanden)  
**Zusätzliche Schutzmaßnahmen:** 
- Datenminimierung (nur notwendige Daten)
- Keine Übermittlung personenbezogener Daten
- Verschlüsselung bei Übertragung

## 9. Speicherdauer & Löschkonzept

### Automatische Löschung:

| Datentyp | Löschfrist |
|----------|-----------|
| Scan-Historie | 90 Tage nach Scan |
| Fix-History | 90 Tage nach Generierung |
| Server-Logs | 30 Tage |
| AI-Fix-Jobs | 30 Tage nach Abschluss |

### Löschung bei Account-Kündigung:

- **Sofort:** Login-Daten, Tokens, Sessions
- **Nach 30 Tagen:** Alle Scan-Daten, Fix-History, Präferenzen
- **Nach 7 Jahren:** Zahlungshistorie (gesetzliche Aufbewahrungspflicht)

## 10. Kontakt & Datenschutzbeauftragter

**Allgemeine Anfragen:** contact@complyo.tech  
**Datenschutz-Anfragen:** privacy@complyo.tech  
**Datenschutzbeauftragter:** [Wird bestimmt bei > 20 Mitarbeitern]

---

**Letzte Aktualisierung:** 23.11.2025  
**Version:** 1.0

