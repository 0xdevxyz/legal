# Der USP: complyo beweist, was es behauptet

*Entwurf 07.08.2026 · Grundlage: Messung an 24 echten deutschen KMU-Websites*

---

## Die eine Frage, die den Markt sortiert

> **„Zeigen Sie mir, dass es wirkt."**

Diese Frage stellt jeder Käufer irgendwann. Was die Anbieter darauf antworten können:

| Anbieter | Antwort auf „zeigen Sie mir, dass es wirkt" |
|---|---|
| **Scanner** (Hugo, Siteimprove, Cookiebot) | „Hier ist die Liste der Fehler." — Es gibt kein Nachher. Sie reparieren nicht. |
| **Overlays** (accessiBe, UserWay, Eye-Able) | „Unser Widget behebt das." — Nicht überprüfbar. accessiBe musste sich 2025 mit der US-FTC über irreführende Konformitätsversprechen vergleichen. |
| **Agenturen** | „Hier ist das Audit-PDF." — Ein Zeitpunkt, kein Zustand. Nach dem nächsten Theme-Update falsch. |
| **complyo** | **„Hier ist das Protokoll. Prüfen Sie es nach."** |

Das ist der USP. Nicht *dass* complyo repariert — das ließe sich behaupten. Sondern dass jede Reparatur **im Browser nachgemessen** wurde und das Ergebnis **öffentlich einsehbar** ist, samt der Lücken.

---

## In einem Satz

> **complyo ist der einzige Anbieter, dessen Reparaturen im Browser nachgemessen sind — und der seine eigenen Lücken veröffentlicht.**

Kurzform fürs Gespräch:

> **„Andere zeigen Ihnen Fehler. Wir zeigen Ihnen ein Protokoll."**

---

## Warum das kein Marketing ist, sondern Architektur

Der Ablauf ist nicht „scannen, reparieren, hoffen", sondern:

1. Seite im Browser laden, mit axe-core prüfen → **Vorher-Messung**
2. Reparatur einspielen
3. **Dieselbe Prüfung erneut ausführen** → Nachher-Messung
4. **Ausgeliefert wird nur, was die zweite Messung bestanden hat**

Schritt 4 ist der Punkt. Ein Fix, der nicht gewirkt hat, geht nicht raus — er wird verworfen und im Protokoll als offen ausgewiesen.

Das hat während der Entwicklung dreimal etwas verhindert, das sonst live gegangen wäre:

- Ein `role="main"` landete auf der **Kopfzeile** einer Kundenseite. Sichtbar wäre das nie geworden — ein Screenreader-Nutzer wäre in die Navigation gesprungen statt in den Inhalt. Die Nachmessung hat es abgelehnt.
- Eine Kontrastfarbe kam wegen einer Deckkraft **gedämpft** an und verfehlte die Vorgabe trotz korrekter Rechnung. Die Nachmessung hat nachgelegt.
- Fünf von vierzehn Alt-Text-Vorschlägen lauteten **„Bild: Image 20"**. Sie hätten jede automatische Prüfung bestanden und keinem Menschen geholfen. Sie werden aussortiert.

Kein Anbieter, der nur scannt, kann so etwas überhaupt bemerken.

---

## Das Produkt daraus: der Prüfnachweis

Jede Website bekommt eine **öffentliche, dauerhafte Protokoll-Adresse**. Darauf steht:

- **Was geprüft wurde** — Werkzeug, Version, Regelsatz, Zeitpunkt
- **Was vorher da war** — je Regel, mit Fundstellenzahl
- **Was geändert wurde** — jede Reparatur mit Ort, Art und Begründung
- **Was nicht behoben wurde — und warum nicht**

Der letzte Punkt macht den Unterschied zwischen einem Nachweis und einem Siegel. Ein Siegel behauptet ein Ergebnis; jeder kann eins malen. Hugo vergibt seins ab Score 60 — das ist eine Note, keine Nachprüfbarkeit.

**Ein Protokoll, das seine eigenen Lücken benennt, ist glaubwürdig. Genau das kauft ein Compliance-Käufer.**

---

## Warum ausgerechnet jetzt: die Erklärung ist Pflicht

Das BFSG verlangt von betroffenen Anbietern eine **Barrierefreiheitserklärung** mit Konformitätsstatus, bekannten Ausnahmen und Datum der Bewertung.

Heute wird sie von Hand geschrieben, selbst erklärt, von niemandem geprüft — und ist nach dem nächsten Theme-Update falsch.

**Bei complyo entsteht sie aus der Messung.** Jede Zahl darin ist auf ein Protokoll zurückführbar, das jederzeit neu erzeugt werden kann. Sie enthält die geforderten Angaben, benennt die offenen Punkte mit Begründung, und trägt einen Link, unter dem sich alles nachprüfen lässt.

Und sie behauptet ausdrücklich **keine** vollständige Konformität — weil eine automatisierte Prüfung sie nicht tragen kann. Diese Zurückhaltung ist Teil des Verkaufsarguments: Wer ehrlich ist, wo er unsicher ist, dem glaubt man dort, wo er sicher ist.

---

## Die Preisrechnung

### 49 € — Einzelwebsite

| Position | Marktüblich | complyo |
|---|---|---|
| Barrierefreiheits-Audit | 600–2.000 € einmalig | inbegriffen |
| Barrierefreiheitserklärung | 300–1.000 € einmalig | inbegriffen |
| Reparatur der Befunde | 800–3.000 € einmalig | inbegriffen |
| Aktualität nach Theme-Update | erneut zahlen | automatisch |
| **Summe erstes Jahr** | **1.700–6.000 €** | **588 €** |

Die eigentliche Zahl ist aber nicht der Preis, sondern der Aufwand: **rund drei bis vier Freigaben je Website** räumen 89 % der Rechtspflicht ab (gemessen: 289 → 32 Fundstellen über 24 echte Seiten).

> „Sie klicken viermal. Wir haben 257 von 289 Verstößen behoben — und Ihnen aufgeschrieben, welche 32 übrig sind und warum."

### 299 € — Agentur

Zwanzig Kundenwebsites:

| | einzeln | Agentur |
|---|---:|---:|
| complyo-Lizenzen | 980 €/Monat | **299 €/Monat** |
| Marktübliche Erstausstattung | 34.000–120.000 € | — |
| Arbeitsschritte je Monat | 20 Logins, 20 Listen | **eine Liste, ein Klick** |

Und zwanzig Prüfnachweise, die die Agentur ihren Kunden weiterreichen kann — als Beleg für die eigene Arbeit.

---

## Die Sätze fürs Gespräch

**Gegen Scanner:**
> „Hugo zeigt Ihnen 194 Kontrastfehler. Wir zeigen Ihnen drei Farben zum Bestätigen — und danach ein Protokoll, dass es gewirkt hat."

**Gegen Overlays:**
> „Overlays legen eine Schicht über Ihre Seite. Wir ändern den Code — und messen nach, ob es geholfen hat. Fragen Sie die anderen nach ihrem Protokoll."

**Gegen Agenturen:**
> „Ein Audit ist ein Foto. Sie brauchen einen Film."

**Wenn jemand nach Beweisen fragt:**
> „Hier ist die Adresse des Protokolls. Es steht auch in Ihrer Barrierefreiheitserklärung — jeder kann es aufrufen, auch eine Prüfstelle."

**Wenn jemand fragt, ob complyo alles behebt:**
> „Nein. 89 % der Pflichtverstöße, gemessen an 24 echten Kundenseiten. Die restlichen stehen mit Begründung im Protokoll. Wer Ihnen 100 % verspricht, hat entweder nicht gemessen oder erzählt Ihnen etwas."

---

## Was ausdrücklich nicht behauptet werden darf

Diese Liste ist Teil des USP, nicht seine Einschränkung. Ein Compliance-Anbieter, der sich verhebt, verliert genau das, was er verkauft.

- **Keine „vollständige Barrierefreiheit"** und keine Konformitätszusage. Eine automatisierte Prüfung deckt einen Teil der WCAG-Kriterien ab; Verständlichkeit und Angemessenheit von Alternativtexten kann sie nicht bewerten.
- **Keine „Abmahnsicherheit"**. Das ist eine Rechtsfolge, keine Produkteigenschaft.
- **Keine Prozentzahl ohne Bezugsgröße.** „89 %" heißt: der WCAG-2.1-AA-Pflichtverstöße, gemessen an 24 Startseiten, mit axe-core. Ohne diesen Satz ist die Zahl wertlos.
- **Keine Bußgeldbeträge als Druckmittel.** Sie gehören in den Report, nicht in die Werbung.

---

## Was als Nächstes gebraucht wird

1. **Die Protokoll-Adresse öffentlich sichtbar machen** — eine lesbare Seite unter `complyo.de/nachweis/…`, nicht nur die JSON-Antwort. Das ist der Beleg, den man verschickt.
2. **`COMPLYO_NACHWEIS_SECRET` setzen.** Ohne das Geheimnis bleibt der Nachweis aus — bewusst, aber damit fehlt aktuell der halbe USP.
3. **Drei Kunden fragen**, ob ihr Protokoll öffentlich verlinkt werden darf. Ein echter, aufrufbarer Nachweis überzeugt mehr als jede Beschreibung davon.
