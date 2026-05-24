# AP2: Autonome Empfehlungs-Engine für Compliance-Fixes

## 1. Executive Summary

Die Complyo Auto-Fix-Engine ist eine wissenschaftliche Innovation, weil sie juristische Compliance-Prüfung, technische Website-Kontextanalyse und kontrollierte KI-Generierung in einer validierbaren Multi-Stage-Pipeline verbindet. Im Gegensatz zu klassischen Checkern erzeugt das System nicht nur Befunde, sondern kontextabhängige, umsetzbare Fix-Pakete für Code, Rechtstexte, Cookie-Consent, Accessibility und Handlungsanleitungen. Die Innovation liegt besonders in der Kombination aus Handler-Routing, LLM-Constrained Generation und anschließendem Quality-Gate, das Syntax-, Sicherheits-, Rechts- und Regressionsrisiken systematisch prüft. Dadurch entsteht ein geschlossenes System zur AI-assisted Legal Compliance Automation: Analyse, Empfehlung, Generierung, Validierung und Messung der Akzeptanz werden datenbasiert verbunden. Für EFRE ist dies relevant, weil daraus ein skalierbares, messbares und potenziell patentierbares Verfahren für automatisierte Rechtskonformitätsunterstützung entsteht.

## 2. Technische Innovation: Multi-Stage-Pipeline

### Stage 1: Kontextanalyse

Die Pipeline beginnt mit der Kontextanalyse einer Ziel-URL. Aus Scan- und Crawling-Daten werden Website-Kontext, Unternehmensdaten, technische Plattform und vorhandene Compliance-Elemente extrahiert. Der aktuelle IST-Stand im Code zeigt insbesondere folgende Kontextfelder:

- URL der geprüften Website
- Unternehmensdaten: Name, Adresse, E-Mail, Telefon
- vorhandenes Impressum und vorhandene Datenschutzerklärung
- Shop-System und E-Commerce-Indikatoren
- Tech-Stack: CMS, Frameworks, Analytics-Tools
- Strukturinformationen: Navigation, Footer, geschätzte Seitenanzahl
- SEO- und Accessibility-Indikatoren, z. B. Bilder ohne Alt-Text
- erkannte Cookies und Tracking-Dienste
- Compliance-Score

Diese Kontextanalyse ist die Voraussetzung für kontextadaptive Empfehlungen. Ein Cookie-Fix für eine WordPress-Seite mit Analytics-Cookies unterscheidet sich technisch und rechtlich von einem Accessibility-Fix für eine React-Anwendung oder einem Impressums-Fix für einen Online-Shop.

### Stage 2: Issue-Analyse und Handler-Routing

Im zweiten Schritt werden Compliance-Issues nach Kategorie, Titel und Schweregrad analysiert. Die Engine ordnet Issues in Fix-Typen und Handler-Klassen ein. Im IST-Stand sind Routing-Regeln für folgende Bereiche erkennbar:

- Rechtstexte: Impressum, Datenschutz, AGB, Widerruf, rechtliche Shop-Texte
- Cookie- und Consent-Themen: Cookie-Banner, Tracking, Consent
- Accessibility: Barrierefreiheit, WCAG, ARIA, Alt-Texte, Kontrast
- Code- und Security-Themen: HTML, CSS, Header, HTTPS, HSTS, CSP, Mixed Content
- Guide-Themen: strategische, prozessuale und juristisch organisatorische Maßnahmen

Das Routing reduziert LLM-Unsicherheit, weil jede Problemklasse in einen spezialisierten Prompt-, Schema- und Validierungsraum überführt wird.

### Stage 3: Template-Selektion und domänenspezifische Handler

Die Template-Selektion wählt abhängig von Fix-Typ und Rechtsgebiet einen spezialisierten Handler:

1. Cookie-Handler für TTDSG-/DSGVO-konforme Consent-Integration
2. Legal-Text-Handler für Impressum, Datenschutzerklärung, AGB und Widerruf
3. Code-Handler für HTML/CSS/JavaScript- oder Security-nahe Fixes
4. Accessibility-Handler für WCAG/BFSG-orientierte HTML-, ARIA- und UX-Fixes
5. Guide-Handler für nicht sicher automatisierbare oder organisatorische Maßnahmen

Diese Handler erzeugen unterschiedliche Output-Formate: Code-Snippets, Rechtstexte, Widget-Integrationen, strukturierte Schritt-für-Schritt-Anleitungen oder exportierbare Fix-Pakete. Im Fallback-Fall werden template-basierte Lösungen erzeugt, damit die Pipeline auch ohne erfolgreiche KI-Antwort robust bleibt.

### Stage 4: LLM-Constrained Generation

Die Generierung erfolgt nicht als freier Chatbot-Dialog, sondern mit constraintspezifischen Prompts und erwarteten JSON-Strukturen. Die Prompts enthalten fachliche und technische Einschränkungen, z. B.:

- DSGVO-, TMG-/DDG-, TTDSG- und BFSG-/WCAG-Konformität
- direkte Nutzbarkeit des Codes
- keine Accessibility-Overlays als Ersatz für echten Code
- WCAG 2.1 Level AA bzw. ARIA-konforme Semantik
- valide HTML-/CSS-/JavaScript-Strukturen
- konkrete Integrationsanweisungen und geschätzte Umsetzungszeit
- Nutzung realer Kontextdaten, soweit verfügbar
- Platzhalter nur bei fehlenden Unternehmensdaten
- JSON-Struktur mit fix_id, title, content/code/text/steps und Metadaten

Die Engine nutzt Retry-Logik und Modell-Fallbacks. Dadurch wird die Generierung kontrolliert, reproduzierbarer und operationalisierbar.

### Stage 5: Quality-Gate mit multidimensionaler Validierung

Das Quality-Gate prüft generierte Fixes in mehreren Dimensionen:

1. Schema-Validierung gegen erwartete JSON-Strukturen
2. typspezifische Code-, Text-, Widget- oder Guide-Validierung
3. Syntax- und Safety-Prüfung für HTML/CSS/JavaScript
4. juristische Keyword- und Pflichtangaben-Prüfung für Datenschutz und Impressum
5. Re-Scanner mit Vorher-/Nachher-Heuristik
6. Regressionstest gegen bekannte Accessibility- und Sicherheitsmuster

Ein Fix erhält nur dann den Status `validated`, wenn die automatischen Stufen bestanden werden. Andernfalls wird `pending_review` gesetzt und eine manuelle Prüfung empfohlen. Dieses Prinzip ist wissenschaftlich relevant, weil LLM-Ausgaben nicht ungeprüft als Wahrheit behandelt werden, sondern als Hypothesen, die durch formale und heuristische Prüfer validiert werden.

### Stage 6: Deployment-Paketierung

Die finale Paketierung transformiert den validierten oder teilvalidierten Fix in ein nutzbares Deployment-Artefakt. Aktuell sind folgende Formen vorgesehen bzw. erkennbar:

- Code-Snippet mit Sprache, Before-/After-Code und Integrationshinweis
- Rechtstext-Paket mit HTML-Format, Quelle und Download-Optionen
- Widget-Integration für Cookie-Consent oder Accessibility-Tools
- Schritt-für-Schritt-Guide mit Validierungsschritten
- Export als HTML/PDF/TXT
- GitHub-PR-Workflow über repository_dispatch und Patch-Payload

Damit wird aus einer Empfehlung ein operativ einsetzbares Umsetzungspaket.

## 3. Constraint-Taxonomie der Quality-Gate-Checks

| Check-ID | Kategorie | Beschreibung | Rechtsgrundlage |
|---|---|---|---|
| QG-01 | JSON-Schema | AI-Output muss dem erwarteten JSON-Schema für Code, Text, Widget oder Guide entsprechen. | Nachvollziehbarkeit/Auditierbarkeit nach DSGVO Art. 5 Abs. 2 als Organisationsprinzip |
| QG-02 | Pflichtfeld | `fix_id` muss vorhanden sein oder sanitisiert ergänzt werden. | Audit-Trail und Rechenschaftspflicht, DSGVO Art. 5 Abs. 2 |
| QG-03 | Pflichtfeld | `title` muss vorhanden sein, damit Nutzer den Fix eindeutig verstehen. | Transparenzprinzip, DSGVO Art. 5 Abs. 1 lit. a |
| QG-04 | HTML-Syntax | HTML-Code darf nicht leer sein und sollte geschlossene Tags enthalten. | WCAG 2.1 Erfolgskriterium 4.1.1 Parsing; BFSG/EN 301 549 |
| QG-05 | HTML-Safety | Script-, iframe-, object-, embed- und Inline-Event-Konstrukte werden als gefährlich markiert. | IT-Sicherheit als TOM, DSGVO Art. 32; XSS-Risikoreduktion |
| QG-06 | JavaScript-Safety | `eval()`, `document.write()`, `innerHTML =` und `.exec()` werden erkannt und blockierend bewertet. | DSGVO Art. 32; sichere Verarbeitung personenbezogener Daten |
| QG-07 | ARIA-Rollen | ARIA-Role-Werte müssen in der Liste zulässiger Rollen enthalten sein. | WCAG 2.1/2.2 4.1.2 Name, Role, Value; BFSG |
| QG-08 | Unclosed-Tags-Heuristik | Starkes Ungleichgewicht zwischen öffnenden und schließenden HTML-Tags erzeugt Warnungen. | WCAG 4.1.1 Parsing; technische Barrierefreiheit |
| QG-09 | CSS-Syntax | CSS-Klammern müssen balanciert sein; Selektoren und Properties dürfen nicht leer oder syntaktisch defekt sein. | WCAG 1.4.x Wahrnehmbarkeit mittelbar; BFSG |
| QG-10 | JavaScript-Syntax | Klammern, eckige Klammern und Braces müssen balanciert sein. | Betriebssicherheit und Verfügbarkeit, DSGVO Art. 32 |
| QG-11 | Externe Skripte | Externe Script-Quellen über HTTP statt HTTPS werden als Sicherheitsproblem markiert. | DSGVO Art. 32; Integrität und Vertraulichkeit |
| QG-12 | PHP-Basics | PHP-Code sollte mit `<?php` beginnen; deprecated `mysql_*` wird beanstandet. | Stand der Technik, DSGVO Art. 32 |
| QG-13 | Datenschutz-Pflichtabschnitte | Datenschutzerklärungen werden auf Betroffenenrechte, Verantwortlichen, Rechtsgrundlagen, Speicherdauer und Beschwerderecht geprüft. | DSGVO Art. 12, 13, 15-21, 77 |
| QG-14 | Datenschutz-Mindestlänge | Datenschutzerklärung unter 500 Zeichen wird als zu kurz bewertet. | Informationspflichten, DSGVO Art. 13 |
| QG-15 | DSGVO-Artikel-Hinweise | Fehlende Nennung von DSGVO-Artikeln erzeugt Warnungen. | Transparenz und Rechtsgrundlagen, DSGVO Art. 6, 12, 13 |
| QG-16 | Impressum-Pflichtangaben | Anbieter, Adresse und Kontakt werden als kritische Impressumsangaben geprüft. | § 5 TMG/Anbieterkennzeichnung, künftig DDG-relevante Informationspflichten |
| QG-17 | Impressum-E-Mail | Eine gültige E-Mail-Adresse muss im Impressum gefunden werden. | § 5 TMG; schnelle elektronische Kontaktaufnahme |
| QG-18 | Impressum-Mindestlänge | Impressum unter 200 Zeichen wird als zu kurz bewertet. | § 5 TMG Pflichtinformationen |
| QG-19 | Platzhalter-Erkennung | `[PLACEHOLDER]`, `[TODO]`, `[YOUR_]`, `{...}`, `XXX`, `FIXME`, `TBD` werden erkannt. | Rechtliche Richtigkeit und Transparenz, DSGVO Art. 5 Abs. 1 lit. a |
| QG-20 | Widget-Code | Widget-Fixes müssen Integration-Code enthalten. | Nachweisbare Consent-Umsetzung, TTDSG § 25; DSGVO Art. 7 |
| QG-21 | Guide-Struktur | Guide-Fixes müssen mindestens einen Schritt mit Titel und Beschreibung enthalten. | Nachvollziehbarkeit und organisatorische Compliance |
| QG-22 | Re-Scanner Score | Vorher-/Nachher-Heuristik darf den Accessibility-Score nicht relevant verschlechtern. | WCAG/BFSG; EN 301 549 |
| QG-23 | Bild-Regression | Fix darf keine Bilder ohne Alt-Attribut einführen. | WCAG 1.1.1 Non-text Content; BFSG |
| QG-24 | Interactive-Regression | Leere Buttons oder Links ohne Label werden erkannt. | WCAG 2.4.4 Link Purpose; 4.1.2 Name, Role, Value |
| QG-25 | Table-Regression | Tabellen ohne Header, Caption oder semantische Struktur werden gewarnt. | WCAG 1.3.1 Info and Relationships |
| QG-26 | Contrast-Regression | CSS-Muster mit potenziell problematischem Vorder-/Hintergrund-Kontrast werden gewarnt. | WCAG 1.4.3 Contrast Minimum |
| QG-27 | Form-Label-Heuristik | Mehr Inputs als Labels reduzieren den Accessibility-Score. | WCAG 3.3.2 Labels or Instructions; 4.1.2 |
| QG-28 | HTML-lang-Heuristik | Fehlendes `lang`-Attribut am HTML-Element reduziert den Score. | WCAG 3.1.1 Language of Page |

## 4. Handler-Übersicht

| Handler | Zweck | Input | Output | Rechtsgebiete |
|---|---|---|---|---|
| accessibility | Erzeugt konkrete Code- und Struktur-Fixes für Barrierefreiheitsprobleme. | Issue-Titel, Beschreibung, WCAG-/ARIA-Hinweise, CMS/Framework, HTML-Kontext, Anzahl Bilder ohne Alt-Text. | HTML/CSS/ARIA-Code, Before-/After-Code, Erklärung, Validierungshinweise. | BFSG, WCAG 2.1/2.2 AA, EN 301 549 |
| code | Behebt technische Compliance- und Security-nahe Issues. | Issue-Daten, Kategorie, URL, Tech-Stack, betroffene Datei oder Snippet. | Valider HTML/CSS/JS/PHP-Code, Integrationsanleitung, Sicherheitswarnungen. | DSGVO Art. 32, technische Datenschutzmaßnahmen, Security-Best-Practices |
| cookie | Generiert Cookie-Consent- und Tracking-Compliance-Lösungen. | erkannte Cookies, Analytics-Tools, Consent-Issues, Website-Kontext, Site-ID. | Widget-Code, Cookie-Inventar-Hinweise, Consent-Integration, Blocking-Anleitung. | TTDSG § 25, DSGVO Art. 6, Art. 7, ePrivacy-Anforderungen |
| guide | Liefert strukturierte Handlungsanleitungen für nicht sicher automatisierbare Maßnahmen. | Issue-Daten, Empfehlung, Nutzer-Skill-Level, Website-Kontext. | Schritt-für-Schritt-Anleitung, Aufwandsschätzung, Validierungsschritte. | organisatorische Compliance, DSGVO Rechenschaftspflicht, UWG/PAngV/AVV je nach Issue |
| legal_text | Erstellt oder ergänzt Rechtstexte, ggf. mit eRecht24-Quelle und Platzhalterfüllung. | Rechtstexttyp, Unternehmensdaten, Kontakt, Shop-Kontext, bestehende Empfehlungen. | HTML-Rechtstext, Quelle, Download-Optionen, Integrationsanleitung, Disclaimer. | DSGVO Art. 12/13, § 5 TMG/DDG, AGB-Recht, Widerrufsrecht, Verbraucherrecht |

## 5. Wissenschaftliche Abgrenzung

### Abgrenzung zu regelbasierten Systemen

Regelbasierte Compliance-Checker erkennen typischerweise nur Verstöße, z. B. fehlende Alt-Attribute, fehlende Datenschutzlinks oder Tracking ohne Consent. Die Complyo Auto-Fix-Engine geht darüber hinaus: Sie erzeugt kontextabhängige Lösungspakete und entscheidet anhand des Issue-Typs, ob Code, Rechtstext, Widget oder Guide angemessen ist. Damit entsteht ein aktiver Empfehlungs- und Umsetzungskanal statt eines passiven Fehlerberichts.

### Abgrenzung zu LLM-Chatbots

Generische LLM-Chatbots liefern plausible, aber häufig ungeprüfte Antworten. Die Complyo Engine beschränkt die Generierung durch spezialisierte Prompts, erwartete Schemas und typspezifische Validatoren. Anschließend wird jede Ausgabe durch ein Quality-Gate geprüft. Dadurch werden Halluzinationen, unsichere Code-Muster, fehlende Pflichtangaben und Accessibility-Regressionen reduziert.

### Abgrenzung zu statischen Templates

Statische Templates liefern feste Texte oder Snippets ohne hinreichende Kontextanpassung. Complyo nutzt URL-, Tech-Stack-, Cookie-, Unternehmens- und Issue-Kontext, um die Lösung an die konkrete Website anzupassen. Gleichzeitig existieren Fallback-Templates, aber nur als Sicherheitsnetz, nicht als primäres Innovationsprinzip.

## 6. KPI-Framework

| KPI | Definition | Messquelle | Zielwert | Interpretation |
|---|---|---|---|---|
| Fix-Akzeptanzrate | Anteil der präsentierten Fixes, die durch Nutzer akzeptiert werden. | `fix_acceptance_metrics.user_decision` und View `fix_acceptance_rate_by_type` | > 75 % | Misst praktische Nützlichkeit und Vertrauen in die Empfehlungen. |
| Re-Scan-Pass-Rate | Anteil der Fixes mit bestandenem Re-Scan nach Umsetzung. | `rescan_passed`, `rescan_triggered_at`, Score-Felder | > 85 % | Misst objektive Wirksamkeit nach technischer Umsetzung. |
| Time-to-Fix | Zeit von Fix-Generierung bis Entscheidung bzw. bis umsetzbarem Paket. | `generated_at`, `decision_at`, `time_to_decision_seconds`, Engine `generation_time_ms` | < 30 s für Generierung | Misst Automatisierungsgrad und operative Geschwindigkeit. |
| Code-Qualitäts-Score | Aggregat aus Schema-, Syntax-, Safety-, Regression- und Accessibility-Prüfungen. | `quality_gate_status`, `quality_gate_log`, Validator-Metadaten | > 90/100 oder `validated` | Misst technische Robustheit und Sicherheitsniveau. |
| Handler-Erfolgsrate | Erfolgsquote pro Handler/Fix-Typ. | `handler_used`, `fix_type`, `user_decision`, `rescan_passed` | Handler-spezifisch steigend | Identifiziert Stärken und Trainingsbedarf einzelner Handler. |
| Fallback-Rate | Anteil der Fixes, die template-basiert oder über Modell-Fallback generiert wurden. | Engine-Metadaten `fallback_used`, `ai_model_used` | < 15 % | Misst Stabilität der KI-Generierung. |
| Review-Quote | Anteil der Fixes mit `pending_review`. | `quality_gate_status` | sinkend über Projektlaufzeit | Misst Reife der Constraints und Validatoren. |

## 7. Patentfähigkeits-Einschätzung

### Potenziell patentierbares Element 1: Context-to-Handler Routing für Legal-Compliance-Fixes

Ein patentfähiger Kern könnte in einem Verfahren liegen, das Website-Kontext, Rechtsgebiet, technische Plattform und Issue-Kategorie kombiniert, um automatisch einen spezialisierten Fix-Handler auszuwählen. Entscheidend wäre nicht nur die Klassifikation, sondern die Kopplung an unterschiedliche Output-Artefakte wie Code, Rechtstext, Widget oder Guide.

### Potenziell patentierbares Element 2: LLM-Constrained Generation mit nachgelagertem Legal-Technical Quality-Gate

Ein zweites Element ist die Kombination aus constraintspezifischer LLM-Generierung und multidimensionaler Validierung gegen technische Syntax, Security, Accessibility, juristische Pflichtangaben und Regressionsmuster. Der neuartige Aspekt liegt in der Validierung juristisch-technischer KI-Fixes vor Nutzerfreigabe oder Deployment.

### Potenziell patentierbares Element 3: Acceptance-Feedback-Loop zur Optimierung von Compliance-Fix-Strategien

Die neu angelegte Messlogik für Fix-Akzeptanz, Re-Scan-Pass-Rate, Entscheidungsgeschwindigkeit und Ablehnungsgründe kann als Feedback-System dienen. Patentierbar könnte ein Verfahren sein, das Handler-Auswahl, Prompt-Strategie und Deployment-Paketierung anhand gemessener Akzeptanz- und Wirksamkeitsdaten dynamisch verbessert.

Hinweis: Diese Einschätzung ersetzt keine anwaltliche Prüfung. Für Patentanmeldungen ist eine professionelle Neuheits- und erfinderische-Tätigkeits-Recherche erforderlich.

## 8. Zeitplan

Gesamtaufwand: 30 Personentage über Monate 1-6.

| Monat | Arbeitspaket | Aufwand | Ergebnis |
|---|---|---:|---|
| Monat 1 | Anforderungsanalyse, Stand der Technik, Definition der Handler-Taxonomie | 5 PT | wissenschaftliche Spezifikation und Messkonzept |
| Monat 2 | Kontextanalyse und Handler-Routing konsolidieren | 5 PT | robuste Issue-to-Fix-Pipeline |
| Monat 3 | LLM-Constrained Prompts und Output-Schemas erweitern | 5 PT | reproduzierbare Fix-Artefakte pro Handler |
| Monat 4 | Quality-Gate erweitern und Re-Scanner kalibrieren | 6 PT | validierbarer Fix-Status und Regressionserkennung |
| Monat 5 | KPI-Erfassung, Fix-Acceptance-Metrics und Feedback-Auswertung | 4 PT | datenbasierte Erfolgs- und Akzeptanzmessung |
| Monat 6 | Evaluation, Patentvorbereitung, Publikationsentwurf | 5 PT | Workshop-Paper, Patent-Scoping, Abschlussbericht |

## 9. Erwartete Publikation

Geplant ist ein Workshop-Paper zum Thema **"AI-assisted Legal Compliance Automation"**. Der Beitrag kann die Complyo Auto-Fix-Engine als Fallstudie für die Verbindung von Website-Analyse, Compliance-Issue-Routing, constraintspezifischer LLM-Generierung und Quality-Gate-validierter Umsetzung darstellen. Wissenschaftlich besonders relevant sind die Messung von Fix-Akzeptanz, Re-Scan-Pass-Rate und Review-Quote sowie die Frage, wie juristische Anforderungen in technische Validierungsconstraints übersetzt werden können.
