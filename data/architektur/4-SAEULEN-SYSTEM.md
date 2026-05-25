# 🛡️ Das Complyo 4-Säulen-System

## Überblick

Complyo analysiert Websites nach **4 fundamentalen Compliance-Säulen** des deutschen Rechts. Jede Säule repräsentiert einen kritischen Bereich der Website-Compliance mit spezifischen Prüfpunkten, Rechtsgrundlagen und automatisierten Lösungen.

---

## 📊 Die 4 Säulen im Detail

```
┌─────────────────────────────────────────────────────────────┐
│  ♿ Barrierefreiheit  │  🍪 Cookie Compliance                │
│  (BFSG, WCAG 2.1)    │  (TTDSG §25, DSGVO)                  │
├──────────────────────┼──────────────────────────────────────┤
│  📄 Rechtstexte      │  🔒 DSGVO                            │
│  (TMG §5)            │  (Datenschutzerklärung)              │
└─────────────────────────────────────────────────────────────┘
```

---

# Säule 1: ♿ Barrierefreiheit (BFSG/WCAG 2.1)

## 📋 Überblick

Seit dem **28. Juni 2025** gilt das **Barrierefreiheitsstärkungsgesetz (BFSG)** für alle wirtschaftlich tätigen Unternehmen in Deutschland. Websites müssen barrierefrei gestaltet sein, um allen Menschen – unabhängig von Behinderungen – den Zugang zu ermöglichen.

### Rechtsgrundlagen
- **BFSG §§ 12-15** - Barrierefreiheitsstärkungsgesetz
- **WCAG 2.1 Level AA** - Web Content Accessibility Guidelines
- **BITV 2.0** - Barrierefreie-Informationstechnik-Verordnung (für öffentliche Stellen)
- **BGG § 12a** - Behindertengleichstellungsgesetz

### Bußgelder & Strafen
- **Bis zu 100.000 €** Bußgeld bei Nicht-Einhaltung (BFSG § 22)
- **Abmahnungen** durch Wettbewerber und Verbände möglich
- **Schadensersatzansprüche** betroffener Nutzer

---

## 🔍 Prüfpunkte im Detail

### 1.1 Accessibility-Widget/Tool

**Was wird geprüft:**
- Vorhandensein eines Accessibility-Widgets (z.B. UserWay, AccessiBe, Eye-Able)
- Sichtbarkeit und Erreichbarkeit des Tools
- Funktionalität (Schriftvergrößerung, Kontrast, Vorlese-Funktion)

**Rechtsgrundlage:**
- BFSG § 12 Abs. 1 - Barrierefreie Gestaltung

**Risikobewertung:**
- **Schwere:** Critical
- **Bußgeld:** 5.000 - 8.000 €
- **Begründung:** Ohne Accessibility-Tool ist die gesamte Website schwer zugänglich

**Auto-Fix verfügbar:** ✅ Ja
- Widget-Integration (UserWay, AccessiBe)
- JavaScript-Snippet + Konfiguration
- Automatische Aktivierung nach Einbau

**Beispiel-Issue:**
```json
{
  "category": "barrierefreiheit",
  "severity": "critical",
  "title": "Kein Barrierefreiheits-Tool/Widget gefunden",
  "description": "Es wurde kein Accessibility-Widget gefunden. Solche Tools erleichtern die Barrierefreiheit erheblich.",
  "risk_euro": 8000,
  "legal_basis": "BFSG §12-15",
  "auto_fixable": true
}
```

---

### 1.2 Text-Alternativen für Bilder (WCAG 1.1.1)

**Was wird geprüft:**
- Alle `<img>`-Tags haben `alt`-Attribute
- Alt-Texte sind beschreibend und aussagekräftig
- Dekorative Bilder sind als solche gekennzeichnet (`role="presentation"` oder `aria-hidden="true"`)

**Rechtsgrundlage:**
- WCAG 2.1 Success Criterion 1.1.1 (Level A)
- BFSG § 12 Abs. 3

**Risikobewertung:**
- **Schwere:** Warning bis Critical (je nach Anzahl)
- **Bußgeld:** 500 € pro fehlendem Alt-Text (max. 2.500 €)
- **Begründung:** Screenreader können Bilder ohne Alt-Text nicht vorlesen

**Auto-Fix verfügbar:** 🔄 Teilweise
- AI-generierte Alt-Texte via GPT-4 Vision
- Kontext-basierte Vorschläge
- Manuelle Review empfohlen

**Beispiel-Issue:**
```json
{
  "category": "barrierefreiheit",
  "severity": "warning",
  "title": "5 Bilder ohne Alt-Text",
  "description": "5 Bilder haben keinen Alt-Text für Screenreader. Beispiele: hero-image.jpg, product-1.png...",
  "risk_euro": 2500,
  "legal_basis": "WCAG 2.1 Level A (1.1.1), BFSG §12",
  "auto_fixable": true,
  "suggested_alt": "Team-Meeting im modernen Büro",
  "image_src": "/images/hero-image.jpg"
}
```

---

### 1.3 Farbkontraste (WCAG 1.4.3)

**Was wird geprüft:**
- Kontrastverhältnis Text/Hintergrund mindestens 4.5:1 (normaler Text)
- Kontrastverhältnis mindestens 3:1 für großen Text (≥18pt oder ≥14pt bold)
- Kontrastverhältnis für UI-Komponenten und Grafiken mindestens 3:1

**Rechtsgrundlage:**
- WCAG 2.1 Success Criterion 1.4.3 (Level AA)
- BFSG § 12 Abs. 1

**Risikobewertung:**
- **Schwere:** Critical
- **Bußgeld:** 1.500 - 2.000 €
- **Begründung:** Sehbehinderte Nutzer können Text nicht lesen

**Auto-Fix verfügbar:** ✅ Ja
- Automatische Farb-Anpassung
- Minimale Abweichung von Original-Design
- CSS-Fixes generiert

**Technische Details:**
```javascript
// Kontrast-Berechnung nach WCAG-Formel
const luminance = 0.2126 * R + 0.7152 * G + 0.0722 * B;
const contrast = (lighter + 0.05) / (darker + 0.05);
// Mindestens 4.5:1 für Level AA
```

**Beispiel-Issue:**
```json
{
  "category": "kontraste",
  "severity": "critical",
  "title": "Unzureichendes Kontrastverhältnis: 2.8:1",
  "description": "Der Text hat nur ein Kontrastverhältnis von 2.8:1 (erforderlich: 4.5:1)",
  "risk_euro": 2000,
  "legal_basis": "WCAG 2.1 Level AA (1.4.3), BFSG §12",
  "auto_fixable": true,
  "foreground": "#999999",
  "background": "#ffffff",
  "suggested_foreground": "#595959"
}
```

---

### 1.4 Tastaturbedienung (WCAG 2.1.1)

**Was wird geprüft:**
- Alle Funktionen per Tastatur erreichbar
- Keine Keyboard-Traps (man kommt überall wieder raus)
- Logische Tab-Reihenfolge
- Keine Elemente mit `tabindex="-1"` (außer absichtlich)

**Rechtsgrundlage:**
- WCAG 2.1 Success Criterion 2.1.1 (Level A)
- BFSG § 12 Abs. 2

**Risikobewertung:**
- **Schwere:** Critical
- **Bußgeld:** 2.000 - 2.500 €
- **Begründung:** Motorisch eingeschränkte Nutzer können Website nicht bedienen

**Auto-Fix verfügbar:** ⚠️ Eingeschränkt
- Entfernung von problematischen `tabindex="-1"`
- Empfehlungen für Verbesserungen
- Manuelle Anpassung oft nötig

**Beispiel-Issue:**
```json
{
  "category": "tastaturbedienung",
  "severity": "critical",
  "title": "3 Elemente nicht per Tastatur erreichbar",
  "description": "3 interaktive Elemente haben tabindex=-1 und sind nicht per Tastatur erreichbar",
  "risk_euro": 2500,
  "legal_basis": "WCAG 2.1 Level A (2.1.1), BFSG §12",
  "auto_fixable": false
}
```

---

### 1.5 Focus-Sichtbarkeit (WCAG 2.4.7)

**Was wird geprüft:**
- Tastaturfokus ist klar sichtbar
- Focus-Indikator hat ausreichenden Kontrast
- Focus-Indikator ist nicht durch CSS entfernt (`outline: none` ohne Alternative)

**Rechtsgrundlage:**
- WCAG 2.1 Success Criterion 2.4.7 (Level AA)
- BFSG § 12 Abs. 1

**Risikobewertung:**
- **Schwere:** Critical
- **Bußgeld:** 1.500 €
- **Begründung:** Tastatur-Nutzer wissen nicht, wo sie sich befinden

**Auto-Fix verfügbar:** ✅ Ja
- CSS Focus-Indikator generiert
- Mindestens 3px solid mit High-Contrast Farbe

**Beispiel CSS-Fix:**
```css
/* Complyo Auto-Fix: Focus-Indikatoren */
*:focus-visible {
  outline: 3px solid #3b82f6;
  outline-offset: 2px;
}

button:focus-visible,
a:focus-visible {
  outline: 3px solid #3b82f6;
  outline-offset: 2px;
}
```

---

### 1.6 ARIA-Labels und semantische Rollen (WCAG 4.1.2)

**Was wird geprüft:**
- Alle interaktiven Elemente haben Namen (Text, aria-label, aria-labelledby)
- Korrekte ARIA-Rollen verwendet
- ARIA-Properties korrekt eingesetzt (aria-expanded, aria-hidden, etc.)

**Rechtsgrundlage:**
- WCAG 2.1 Success Criterion 4.1.2 (Level A)
- BFSG § 12 Abs. 3

**Risikobewertung:**
- **Schwere:** Warning
- **Bußgeld:** 1.000 - 1.500 €
- **Begründung:** Screenreader können Funktion nicht erkennen

**Auto-Fix verfügbar:** ⚠️ Eingeschränkt
- Generische aria-labels für Buttons ohne Text
- Empfehlungen für bessere Labels
- Manuelle Anpassung empfohlen

**Beispiel-Issue:**
```json
{
  "category": "barrierefreiheit",
  "severity": "warning",
  "title": "7 Buttons ohne Label",
  "description": "7 interaktive Elemente (Buttons) haben weder Text noch ARIA-Label",
  "risk_euro": 1500,
  "legal_basis": "WCAG 2.1 (4.1.2), BFSG §12",
  "auto_fixable": false
}
```

---

### 1.7 Semantisches HTML5 (WCAG 1.3.1)

**Was wird geprüft:**
- Verwendung von `<header>`, `<nav>`, `<main>`, `<aside>`, `<footer>`
- Korrekte Heading-Hierarchie (H1 → H2 → H3, keine Sprünge)
- Listen für Listen-Inhalte (`<ul>`, `<ol>`)

**Rechtsgrundlage:**
- WCAG 2.1 Success Criterion 1.3.1 (Level A)
- BFSG § 12 Abs. 3

**Risikobewertung:**
- **Schwere:** Warning
- **Bußgeld:** 800 - 1.000 €
- **Begründung:** Screenreader können Struktur nicht erkennen

**Auto-Fix verfügbar:** ❌ Nein
- Strukturelle Änderungen erfordern manuelles Refactoring

**Beispiel-Issue:**
```json
{
  "category": "barrierefreiheit",
  "severity": "warning",
  "title": "Fehlende semantische HTML-Elemente",
  "description": "Die Seite verwendet nicht alle wichtigen semantischen HTML5-Elemente: <main>, <nav>",
  "risk_euro": 800,
  "legal_basis": "WCAG 2.1 (1.3.1), BFSG §12",
  "auto_fixable": false
}
```

---

### 1.8 Screenreader-Kompatibilität

**Was wird geprüft:**
- Skip-Links vorhanden ("Zum Hauptinhalt springen")
- Landmark-Regions korrekt definiert
- Dynamische Inhalte mit `aria-live` angekündigt
- Versteckter Text für Screenreader (`sr-only` class)

**Rechtsgrundlage:**
- WCAG 2.1 Multiple Criteria
- BFSG § 12

**Risikobewertung:**
- **Schwere:** Warning
- **Bußgeld:** 500 - 1.000 €

**Auto-Fix verfügbar:** ✅ Teilweise
- Skip-Link automatisch generiert
- sr-only CSS-Klasse hinzugefügt

---

## 🤖 Autonome Fix-Funktionen

### Was kann automatisch behoben werden?

| Prüfpunkt | Auto-Fix | Qualität | Hinweise |
|-----------|----------|----------|----------|
| Accessibility-Widget | ✅ Vollständig | 95% | Widget-Einbau via Script |
| Alt-Texte | 🔄 AI-gestützt | 80% | Review empfohlen |
| Farbkontraste | ✅ Vollständig | 90% | Minimale Design-Änderung |
| Focus-Indikatoren | ✅ Vollständig | 95% | CSS-basiert |
| ARIA-Labels | ⚠️ Eingeschränkt | 60% | Generische Labels |
| Tastaturbedienung | ❌ Manuell | - | Strukturelle Änderungen |
| Semantisches HTML | ❌ Manuell | - | Refactoring nötig |

---

## 📚 Best Practices

### Do's ✅
- Accessibility-Widget früh implementieren
- Alt-Texte beschreibend und kontextbezogen
- Ausreichende Kontraste von Anfang an einplanen
- Tastatur-Tests regelmäßig durchführen
- ARIA sparsam und korrekt einsetzen

### Don'ts ❌
- Nicht `outline: none` ohne Alternative
- Nicht rein dekorative Bilder mit langen Alt-Texten
- Nicht zu viele ARIA-Attribute (keep it simple)
- Nicht Accessibility als Nachgedanke behandeln

---

# Säule 2: 🍪 Cookie Compliance (TTDSG §25)

## 📋 Überblick

Das **Telekommunikation-Telemedien-Datenschutz-Gesetz (TTDSG)** regelt seit dem 1. Dezember 2021 die Verwendung von Cookies. Alle nicht-essentiellen Cookies erfordern eine **ausdrückliche Einwilligung (Opt-In)** des Nutzers.

### Rechtsgrundlagen
- **TTDSG § 25** - Schutz der Privatsphäre bei Endeinrichtungen
- **DSGVO Art. 7** - Bedingungen für die Einwilligung
- **DSGVO Art. 13** - Informationspflichten

### Bußgelder & Strafen
- **Bis zu 300.000 €** Bußgeld (TTDSG § 28)
- **Bis zu 20 Mio. € oder 4% Jahresumsatz** (DSGVO Art. 83)
- **Abmahnungen** durch Wettbewerber (durchschnittlich 1.500 € + Anwaltskosten)

---

## 🔍 Prüfpunkte im Detail

### 2.1 Cookie-Consent-Banner vorhanden

**Was wird geprüft:**
- Cookie-Banner ist sichtbar und funktional
- Banner erscheint vor dem Setzen nicht-essentieller Cookies
- Bekannte Tools erkannt (Cookiebot, Usercentrics, OneTrust, CookieFirst)

**Rechtsgrundlage:**
- TTDSG § 25 Abs. 1 - Einwilligung erforderlich
- DSGVO Art. 7 Abs. 1 - Nachweispflicht

**Risikobewertung:**
- **Schwere:** Critical
- **Bußgeld:** 4.000 - 5.000 € (ohne Tracking), 10.000+ € (mit Tracking ohne Consent)
- **Begründung:** Illegales Tracking, Datenschutzverstoß

**Auto-Fix verfügbar:** ✅ Ja
- Complyo Cookie-Banner Generator
- DSGVO/TTDSG-konform
- Opt-In/Opt-Out Funktionalität

**Beispiel-Issue:**
```json
{
  "category": "cookies",
  "severity": "critical",
  "title": "Kein Cookie-Consent-Banner vorhanden",
  "description": "Es wurde kein Cookie-Consent-Banner gefunden. ⚠️ Es wurden Tracking-Scripts gefunden - Tracking ohne Einwilligung ist illegal!",
  "risk_euro": 5000,
  "legal_basis": "TTDSG §25, DSGVO Art. 7",
  "auto_fixable": true
}
```

---

### 2.2 Opt-In Mechanismus

**Was wird geprüft:**
- Cookies werden NICHT vor Einwilligung gesetzt
- "Alle akzeptieren" Button vorhanden
- Kein Pre-Check von Checkboxen (außer "Notwendige")
- Keine Cookie-Walls (Zugang zur Website auch ohne Zustimmung)

**Rechtsgrundlage:**
- TTDSG § 25 Abs. 1 - Einwilligung muss vorher erfolgen
- DSGVO Art. 7 Abs. 4 - Freiwilligkeit

**Risikobewertung:**
- **Schwere:** Critical
- **Bußgeld:** 3.000 €
- **Begründung:** Unzulässiger Pre-Consent, Cookie-Wall

**Auto-Fix verfügbar:** ✅ Ja
- Opt-In Banner mit korrekter Logik
- Cookies erst nach Zustimmung

---

### 2.3 Ablehnungsmöglichkeit

**Was wird geprüft:**
- "Ablehnen" oder "Nur notwendige Cookies" Button deutlich sichtbar
- Ablehnen ist genauso einfach wie Akzeptieren
- Keine Dark Patterns (Nutzer-Täuschung)

**Rechtsgrundlage:**
- DSGVO Art. 7 Abs. 3 - Widerruf muss so einfach sein wie Erteilung
- TTDSG § 25 Abs. 1

**Risikobewertung:**
- **Schwere:** Critical
- **Bußgeld:** 2.500 €
- **Begründung:** Keine echte Wahlfreiheit

**Auto-Fix verfügbar:** ✅ Ja
- Gleichwertige Ablehnen/Akzeptieren Buttons

**Beispiel-Code:**
```html
<div id="cookie-banner">
  <button id="accept-all">Alle akzeptieren</button>
  <button id="accept-selected">Auswahl akzeptieren</button>
  <button id="reject-all">Nur notwendige</button>
</div>
```

---

### 2.4 Cookie-Informationspflicht

**Was wird geprüft:**
- Auflistung aller verwendeten Cookies
- Zweck jedes Cookies erklärt
- Speicherdauer angegeben
- Anbieter genannt (First-Party / Third-Party)

**Rechtsgrundlage:**
- DSGVO Art. 13 - Informationspflichten
- TTDSG § 25 Abs. 2

**Risikobewertung:**
- **Schwere:** Critical
- **Bußgeld:** 2.000 €
- **Begründung:** Intransparenz, fehlende Information

**Auto-Fix verfügbar:** 🔄 Teilweise
- Cookie-Liste aus Tracking-Scripts generiert
- Manuelle Ergänzung empfohlen

**Beispiel Cookie-Information:**
```json
{
  "name": "_ga",
  "provider": "Google Analytics",
  "purpose": "Unterscheidung von Benutzern",
  "duration": "2 Jahre",
  "category": "Analytics",
  "legal_basis": "Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)"
}
```

---

### 2.5 Widerrufsmöglichkeit

**Was wird geprüft:**
- Link zur erneuten Cookie-Einstellung (z.B. im Footer)
- Nutzer kann Einwilligung jederzeit widerrufen
- Widerruf ist genauso einfach wie Erteilung

**Rechtsgrundlage:**
- DSGVO Art. 7 Abs. 3 - Recht auf Widerruf
- TTDSG § 25 Abs. 1

**Risikobewertung:**
- **Schwere:** Warning
- **Bußgeld:** 1.500 €

**Auto-Fix verfügbar:** ✅ Ja
- "Cookie-Einstellungen" Link im Footer
- Funktion zum Zurücksetzen der Einwilligung

---

### 2.6 Einwilligungsnachweis (Consent-Logs)

**Was wird geprüft:**
- System zur Dokumentation von Einwilligungen
- Timestamp, IP-Adresse, gewählte Optionen gespeichert
- Nachweis für Aufsichtsbehörden verfügbar

**Rechtsgrundlage:**
- DSGVO Art. 7 Abs. 1 - Nachweispflicht

**Risikobewertung:**
- **Schwere:** Warning
- **Bußgeld:** 1.500 €
- **Begründung:** Fehlender Nachweis bei Prüfung

**Auto-Fix verfügbar:** ✅ Ja
- LocalStorage-basierter Consent-Log
- Server-seitiges Logging optional

---

### 2.7 Tracking ohne Consent

**Was wird geprüft:**
- Google Analytics, Facebook Pixel, Hotjar ohne Consent
- Tracking-Scripts laden erst nach Einwilligung
- Google Consent Mode korrekt implementiert

**Rechtsgrundlage:**
- TTDSG § 25 Abs. 1 - Einwilligung VOR Zugriff/Speicherung

**Risikobewertung:**
- **Schwere:** Critical
- **Bußgeld:** 5.000 - 10.000 €
- **Begründung:** Illegales Tracking, schwerwiegender Datenschutzverstoß

**Auto-Fix verfügbar:** ✅ Ja
- Tracking-Scripts in Consent-Management einbinden
- Conditional Loading implementieren

---

## 🤖 Autonome Fix-Funktionen

### Complyo Cookie-Banner Generator

**Features:**
- ✅ TTDSG/DSGVO-konform
- ✅ Opt-In/Opt-Out Funktionalität
- ✅ Cookie-Kategorisierung (Notwendig, Analytics, Marketing, Präferenzen)
- ✅ Consent-Speicherung (LocalStorage)
- ✅ Google Analytics/Facebook Pixel Integration
- ✅ Responsive Design

**Generierter Code:**
```javascript
// Complyo Cookie Consent Manager
class ComplyoCookieManager {
  constructor() {
    this.consentKey = 'complyo-cookie-consent';
    this.init();
  }
  
  setConsent(consent) {
    localStorage.setItem(this.consentKey, JSON.stringify(consent));
    this.applyConsent(consent);
  }
  
  applyConsent(consent) {
    if (consent.analytics) {
      this.enableGoogleAnalytics();
    }
    if (consent.marketing) {
      this.enableMarketingCookies();
    }
  }
}
```

---

## 📚 Best Practices

### Do's ✅
- Cookie-Banner vor allem anderen Content zeigen
- Einfache, klare Sprache verwenden
- "Ablehnen" genauso prominent wie "Akzeptieren"
- Regelmäßig Cookie-Liste aktualisieren
- Consent-Logs für 3 Jahre aufbewahren

### Don'ts ❌
- Keine Cookie-Walls (Zugang blockieren)
- Keine Pre-Checks (außer "Notwendige")
- Keine Dark Patterns (getäuschte Nutzerführung)
- Nicht Tracking vor Consent laden
- Nicht "Ablehnen" verstecken oder erschweren

---

# Säule 3: 📄 Rechtstexte (TMG §5 Impressum)

## 📋 Überblick

Das **Telemediengesetz (TMG) § 5** verpflichtet alle geschäftsmäßigen Telemedien zur Anbieterkennzeichnung (Impressum). Die Impressumspflicht gilt für fast alle Websites mit kommerziellem Hintergrund.

### Rechtsgrundlagen
- **TMG § 5** - Allgemeine Informationspflichten
- **§ 5 TMG** gilt für alle geschäftsmäßigen Angebote
- **RStV § 55** - Inhaltlich Verantwortlicher

### Bußgelder & Strafen
- **Bis zu 50.000 €** Bußgeld (OWiG)
- **Abmahnungen** durch Wettbewerber (durchschnittlich 1.000 € + Anwaltskosten)
- **Unterlassungsklagen** möglich

---

## 🔍 Prüfpunkte im Detail

### 3.1 Impressum-Link vorhanden

**Was wird geprüft:**
- Link mit Text "Impressum" oder "Imprint" im Footer
- Impressum ist mit maximal 2 Klicks erreichbar
- Link ist auf allen Seiten verfügbar

**Rechtsgrundlage:**
- TMG § 5 Abs. 1 - Leicht erkennbar und unmittelbar erreichbar

**Risikobewertung:**
- **Schwere:** Critical
- **Bußgeld:** 3.000 €
- **Begründung:** Fehlende Anbieterkennzeichnung

**Auto-Fix verfügbar:** ✅ Ja
- Impressum-Seite generieren
- Footer-Link automatisch einfügen

---

### 3.2 Firmenname / Vollständiger Name

**Was wird geprüft:**
- Bei Unternehmen: Vollständiger Firmenname
- Bei Einzelpersonen: Vor- und Nachname
- Bei GmbH: "GmbH" im Namen
- Bei AG: "AG" im Namen

**Rechtsgrundlage:**
- TMG § 5 Abs. 1 Nr. 1 - Name des Diensteanbieters

**Risikobewertung:**
- **Schwere:** Critical
- **Bußgeld:** 2.000 €

**Auto-Fix verfügbar:** 🔄 Teilweise
- Platzhalter im Template
- Automatisches Ausfüllen aus User-Profil (geplant)

**Beispiel:**
```
✅ Korrekt: "Mustermann GmbH"
❌ Falsch: "Mustermann" (bei GmbH)
```

---

### 3.3 Vollständige Postanschrift

**Was wird geprüft:**
- Straße und Hausnummer
- Postleitzahl und Ort
- Land (bei internationalen Geschäften)
- **KEINE Postfächer** (außer zusätzlich zur ladungsfähigen Anschrift)

**Rechtsgrundlage:**
- TMG § 5 Abs. 1 Nr. 2 - Anschrift (ladungsfähige Anschrift)

**Risikobewertung:**
- **Schwere:** Critical
- **Bußgeld:** 2.000 €

**Auto-Fix verfügbar:** 🔄 Teilweise
- Platzhalter im Template

**Beispiel:**
```
✅ Korrekt:
Musterstraße 123
12345 Musterstadt

❌ Falsch:
Postfach 456
12345 Musterstadt
```

---

### 3.4 Kontaktdaten (E-Mail & Telefon)

**Was wird geprüft:**
- E-Mail-Adresse angegeben
- Telefonnummer angegeben
- Beide müssen zu Geschäftszeiten erreichbar sein

**Rechtsgrundlage:**
- TMG § 5 Abs. 1 Nr. 2 - Angaben zur schnellen Kontaktaufnahme

**Risikobewertung:**
- **Schwere:** Critical
- **Bußgeld:** 1.500 € pro fehlender Angabe

**Auto-Fix verfügbar:** 🔄 Teilweise

**Beispiel:**
```
✅ Korrekt:
E-Mail: info@beispiel.de
Telefon: +49 30 12345678

❌ Falsch:
"Kontaktieren Sie uns über das Kontaktformular"
```

---

### 3.5 Handelsregister / Registernummer

**Was wird geprüft:**
- Registergericht angegeben
- Registernummer (HRB, HRA)
- Bei Vereinen: Vereinsregister-Nummer
- Bei Freiberuflern: Berufsbezeichnung, Kammer

**Rechtsgrundlage:**
- TMG § 5 Abs. 1 Nr. 3-4 - Registereintragungen

**Risikobewertung:**
- **Schwere:** Warning
- **Bußgeld:** 1.000 €

**Auto-Fix verfügbar:** ❌ Nein
- Spezifische Firmendaten erforderlich

**Beispiel:**
```
Registergericht: Amtsgericht Berlin-Charlottenburg
Registernummer: HRB 12345 B
```

---

### 3.6 Umsatzsteuer-ID

**Was wird geprüft:**
- USt-IdNr. angegeben (falls vorhanden)
- Format: DE123456789

**Rechtsgrundlage:**
- TMG § 5 Abs. 1 Nr. 6
- UStG § 27a - Angabepflicht bei innergemeinschaftlichen Lieferungen

**Risikobewertung:**
- **Schwere:** Warning
- **Bußgeld:** 1.000 €

**Auto-Fix verfügbar:** ❌ Nein

**Beispiel:**
```
Umsatzsteuer-Identifikationsnummer: DE123456789
```

---

### 3.7 Verantwortlicher für Inhalte (RStV § 55)

**Was wird geprüft:**
- Name des inhaltlich Verantwortlichen
- Anschrift des Verantwortlichen

**Rechtsgrundlage:**
- RStV § 55 Abs. 2 (jetzt MStV)

**Risikobewertung:**
- **Schwere:** Warning
- **Bußgeld:** 500 €

**Auto-Fix verfügbar:** 🔄 Teilweise

**Beispiel:**
```
Verantwortlich für den Inhalt nach § 55 Abs. 2 RStV:
Max Mustermann
Musterstraße 123
12345 Musterstadt
```

---

## 🤖 Autonome Fix-Funktionen

### Complyo Impressum-Generator

**Features:**
- ✅ TMG-konformes Template
- ✅ Alle Pflichtangaben inkludiert
- ✅ Platzhalter für individuelle Daten
- 🔄 Automatisches Ausfüllen (geplant)

**Generiertes Template:**
```html
<h1>Impressum</h1>

<h2>Angaben gemäß § 5 TMG</h2>
<p>
  <strong>Verantwortlich für den Inhalt:</strong><br>
  [FIRMENNAME]<br>
  [STRASSE HAUSNUMMER]<br>
  [PLZ] [ORT]
</p>

<h2>Kontakt</h2>
<p>
  Telefon: [TELEFON]<br>
  E-Mail: [EMAIL]
</p>

<h2>Registereintrag</h2>
<p>
  Registergericht: [REGISTERGERICHT]<br>
  Registernummer: [HRB/HRA NUMMER]
</p>

<h2>Umsatzsteuer-ID</h2>
<p>
  Umsatzsteuer-Identifikationsnummer gemäß §27a UStG:<br>
  [UST-ID]
</p>

<h2>Verantwortlich für den Inhalt nach § 55 Abs. 2 RStV</h2>
<p>
  [VERANTWORTLICHE PERSON]<br>
  [ADRESSE]
</p>
```

---

## 📚 Best Practices

### Do's ✅
- Impressum auf jeder Seite verlinken
- "Impressum" als Linktext verwenden
- Alle Pflichtangaben vollständig angeben
- Impressum aktuell halten
- Klare, strukturierte Darstellung

### Don'ts ❌
- Nicht verstecken oder schwer auffindbar machen
- Nicht nur als Grafik (muss durchsuchbar sein)
- Nicht Postfach als einzige Adresse
- Nicht veraltete Daten stehen lassen
- Nicht nur Kontaktformular anbieten

---

# Säule 4: 🔒 DSGVO (Datenschutzerklärung)

## 📋 Überblick

Die **Datenschutz-Grundverordnung (DSGVO)** verpflichtet alle Websites zur Information über die Datenverarbeitung. Die Datenschutzerklärung muss transparent, verständlich und vollständig sein.

### Rechtsgrundlagen
- **DSGVO Art. 12** - Transparente Information
- **DSGVO Art. 13-14** - Informationspflichten
- **DSGVO Art. 15-22** - Betroffenenrechte

### Bußgelder & Strafen
- **Bis zu 20 Mio. € oder 4% des Jahresumsatzes** (je nachdem, welcher Betrag höher ist)
- **Schadensersatzansprüche** Betroffener
- **Abmahnungen** durch Wettbewerber und Verbände

---

## 🔍 Prüfpunkte im Detail

### 4.1 Datenschutzerklärung vorhanden und verlinkt

**Was wird geprüft:**
- Link zur Datenschutzerklärung im Footer
- Link auf allen Seiten verfügbar
- Datenschutzerklärung ist erreichbar

**Rechtsgrundlage:**
- DSGVO Art. 13 Abs. 1 - Informationspflicht bei Erhebung

**Risikobewertung:**
- **Schwere:** Critical
- **Bußgeld:** 5.000 - 10.000 €

**Auto-Fix verfügbar:** ✅ Ja
- Datenschutzerklärung generieren
- Footer-Link einfügen

---

### 4.2 Verantwortlicher mit Kontaktdaten

**Was wird geprüft:**
- Name des Verantwortlichen genannt
- Kontaktdaten (Adresse, E-Mail, Telefon)
- Ggf. Vertreter in der EU

**Rechtsgrundlage:**
- DSGVO Art. 13 Abs. 1 lit. a - Name und Kontaktdaten des Verantwortlichen

**Risikobewertung:**
- **Schwere:** Critical
- **Bußgeld:** 3.000 €

**Auto-Fix verfügbar:** 🔄 Teilweise
- Template mit Platzhaltern

---

### 4.3 Zwecke der Datenverarbeitung

**Was wird geprüft:**
- Alle Verarbeitungszwecke aufgelistet
- Konkrete Beschreibungen (nicht nur allgemein)
- Z.B.: "Newsletter-Versand", "Kontaktformular", "Analytics"

**Rechtsgrundlage:**
- DSGVO Art. 13 Abs. 1 lit. c - Zwecke der Verarbeitung

**Risikobewertung:**
- **Schwere:** Critical
- **Bußgeld:** 3.000 €

**Auto-Fix verfügbar:** 🔄 AI-gestützt
- Zwecke aus erkannten Scripts ableiten
- Manuelle Ergänzung empfohlen

**Beispiel:**
```
## Datenverarbeitung auf dieser Website

### 1. Kontaktformular
Zweck: Bearbeitung Ihrer Anfrage
Rechtsgrundlage: Art. 6 Abs. 1 lit. b DSGVO (Vertragsanbahnung)
Speicherdauer: 6 Monate

### 2. Google Analytics
Zweck: Analyse des Nutzerverhaltens
Rechtsgrundlage: Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)
Speicherdauer: 14 Monate
```

---

### 4.4 Rechtsgrundlagen nach Art. 6 DSGVO

**Was wird geprüft:**
- Für jeden Zweck ist Rechtsgrundlage genannt
- Korrekte Zuordnung (Einwilligung, Vertrag, berechtigtes Interesse)

**Rechtsgrundlage:**
- DSGVO Art. 13 Abs. 1 lit. c - Rechtsgrundlagen

**Mögliche Rechtsgrundlagen:**
- **Art. 6 Abs. 1 lit. a** - Einwilligung (z.B. Newsletter, Analytics)
- **Art. 6 Abs. 1 lit. b** - Vertragserfüllung (z.B. Bestellabwicklung)
- **Art. 6 Abs. 1 lit. c** - Rechtliche Verpflichtung (z.B. Steuerrecht)
- **Art. 6 Abs. 1 lit. f** - Berechtigtes Interesse (z.B. Fraud Prevention)

**Risikobewertung:**
- **Schwere:** Critical
- **Bußgeld:** 3.000 €

**Auto-Fix verfügbar:** 🔄 AI-gestützt

---

### 4.5 Speicherdauer

**Was wird geprüft:**
- Speicherdauer für jede Datenart angegeben
- Oder Kriterien zur Festlegung der Dauer
- Z.B.: "Bis zur Anfragenbearbeitung", "14 Monate", "Gesetzliche Aufbewahrungsfristen"

**Rechtsgrundlage:**
- DSGVO Art. 13 Abs. 2 lit. a - Dauer der Speicherung

**Risikobewertung:**
- **Schwere:** Critical
- **Bußgeld:** 2.000 €

**Auto-Fix verfügbar:** 🔄 Teilweise
- Standard-Dauern für gängige Tools

---

### 4.6 Betroffenenrechte

**Was wird geprüft:**
- Auskunftsrecht (Art. 15)
- Berichtigungsrecht (Art. 16)
- Löschrecht (Art. 17)
- Recht auf Einschränkung (Art. 18)
- Recht auf Datenübertragbarkeit (Art. 20)
- Widerspruchsrecht (Art. 21)
- Widerruf der Einwilligung (Art. 7 Abs. 3)

**Rechtsgrundlage:**
- DSGVO Art. 13 Abs. 2 lit. b - Betroffenenrechte

**Risikobewertung:**
- **Schwere:** Critical
- **Bußgeld:** 2.500 €

**Auto-Fix verfügbar:** ✅ Ja
- Vollständige Auflistung aller Rechte

**Beispiel-Text:**
```
## Ihre Rechte

Sie haben folgende Rechte:
- Auskunft über Ihre gespeicherten Daten (Art. 15 DSGVO)
- Berichtigung unrichtiger Daten (Art. 16 DSGVO)
- Löschung Ihrer Daten (Art. 17 DSGVO)
- Einschränkung der Verarbeitung (Art. 18 DSGVO)
- Datenübertragbarkeit (Art. 20 DSGVO)
- Widerspruch gegen die Verarbeitung (Art. 21 DSGVO)
- Widerruf Ihrer Einwilligung (Art. 7 Abs. 3 DSGVO)
```

---

### 4.7 Beschwerderecht bei Aufsichtsbehörde

**Was wird geprüft:**
- Hinweis auf Beschwerderecht
- Nennung der zuständigen Aufsichtsbehörde
- Kontaktdaten der Behörde

**Rechtsgrundlage:**
- DSGVO Art. 13 Abs. 2 lit. d - Beschwerderecht

**Risikobewertung:**
- **Schwere:** Critical
- **Bußgeld:** 2.000 €

**Auto-Fix verfügbar:** ✅ Ja

**Beispiel:**
```
## Beschwerderecht

Sie haben das Recht, Beschwerde bei einer Datenschutz-Aufsichtsbehörde einzulegen.

Zuständige Aufsichtsbehörde:
[Bundesland]-Landesbeauftragte für Datenschutz
[Adresse]
[Kontakt]
```

---

### 4.8 Datenschutzbeauftragter

**Was wird geprüft:**
- Kontaktdaten des Datenschutzbeauftragten (falls erforderlich)
- Benennung ist bei >20 Mitarbeitern Pflicht
- Oder bei sensiblen Daten / umfangreicher Verarbeitung

**Rechtsgrundlage:**
- DSGVO Art. 13 Abs. 1 lit. b - Kontaktdaten DSB
- DSGVO Art. 37-39 - Benennung DSB

**Risikobewertung:**
- **Schwere:** Warning
- **Bußgeld:** 1.500 €

**Auto-Fix verfügbar:** ❌ Nein
- Unternehmensspezifisch

---

## 🤖 Autonome Fix-Funktionen

### Complyo Datenschutzerklärung-Generator

**Features:**
- ✅ DSGVO-konformes Template
- ✅ Alle Pflichtangaben inkludiert
- ✅ AI-Enhanced: Anpassung an erkannte Tracking-Scripts
- ✅ Dynamische Generierung basierend auf Website-Analyse

**AI-Enhancement:**
```python
# Erkannte Scripts automatisch in Datenschutzerklärung aufnehmen
detected_scripts = ["Google Analytics", "Facebook Pixel"]

for script in detected_scripts:
    add_privacy_section(
        name=script,
        purpose=get_purpose(script),
        legal_basis="Art. 6 Abs. 1 lit. a DSGVO",
        duration=get_duration(script)
    )
```

---

## 📚 Best Practices

### Do's ✅
- Datenschutzerklärung auf allen Seiten verlinken
- Klare, verständliche Sprache verwenden
- Regelmäßig aktualisieren (bei Änderungen)
- Alle Tools und Services auflisten
- Betroffenenrechte prominent darstellen

### Don'ts ❌
- Nicht generische Muster-Texte ungeprüft übernehmen
- Nicht veraltete Tools/Services aufführen
- Nicht unverständliche Rechtssprache verwenden
- Nicht verstecken oder schwer auffindbar machen
- Nicht Copy-Paste von anderen Websites

---

# 🎯 Zusammenfassung

## Compliance-Matrix

| Säule | Kritische Prüfpunkte | Auto-Fix Rate | Durchschn. Bußgeld |
|-------|----------------------|---------------|--------------------|
| ♿ Barrierefreiheit | 8 | 60% | 8.000 € |
| 🍪 Cookie Compliance | 7 | 90% | 15.000 € |
| 📄 Rechtstexte | 7 | 70% | 10.000 € |
| 🔒 DSGVO | 8 | 75% | 20.000 € |

## Risiko-Priorität

**Höchste Priorität (sofort beheben):**
1. 🍪 Cookie-Banner fehlt + Tracking aktiv → bis 20.000 € Bußgeld
2. 🔒 Keine Datenschutzerklärung → bis 20.000 € Bußgeld
3. 📄 Kein Impressum → bis 3.000 € + Abmahnungen
4. ♿ Kein Accessibility-Tool → bis 8.000 € Bußgeld

**Mittlere Priorität:**
- Unvollständige Datenschutzerklärung
- Fehlende Impressum-Angaben
- Kontrast-Probleme
- Fehlende Alt-Texte

**Niedrige Priorität:**
- Semantisches HTML
- ARIA-Optimierungen
- Widerrufsmöglichkeiten
- Cookie-Dokumentation

---

## 🤖 Was Complyo automatisch beheben kann

### Vollautomatisch (>90% Erfolgsrate)
- ✅ Cookie-Banner Integration
- ✅ Impressum-Generierung
- ✅ Datenschutzerklärung-Generierung
- ✅ Kontrast-Fixes
- ✅ Focus-Indikatoren

### AI-Gestützt (70-90% Erfolgsrate)
- 🔄 Alt-Text-Generierung
- 🔄 DSGVO-Texte anpassen
- 🔄 Cookie-Informationen

### Empfehlungen (manuelle Umsetzung)
- ⚠️ Semantisches HTML
- ⚠️ ARIA-Labels
- ⚠️ Tastaturbedienung
- ⚠️ Content-Struktur

---

## 📞 Support & Weitere Informationen

Bei Fragen zur Compliance oder den automatischen Fixes:
- 📧 support@complyo.tech
- 📚 [Complyo Dokumentation](https://docs.complyo.tech)
- 🎓 [Compliance Academy](https://academy.complyo.tech)

---

**Letzte Aktualisierung:** November 2025  
**Version:** 2.0  
**Status:** Produktiv

