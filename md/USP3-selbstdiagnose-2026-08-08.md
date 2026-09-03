# USP 3: complyo sagt Ihnen, wenn complyo nicht wirkt

*Stand 08.08.2026 — entstanden aus einem Testtag, nicht aus einem Workshop.*

## Der Satz

> **Jeder Anbieter zeigt Ihnen, was er kann. Wir zeigen Ihnen auch, was wir nicht
> können — automatisch, bei jedem Seitenaufruf, in einem Dokument, das jeder
> aufrufen kann.**

## Warum das ein Verkaufsargument ist und keine Bescheidenheit

Ein Compliance-Käufer kauft keine Reparatur. Er kauft die Gewissheit, im
Ernstfall nicht dazustehen wie jemand, der etwas geglaubt hat. Genau diese
Gewissheit kann ein Anbieter nur geben, der auch das Gegenteil meldet.

Overlays melden nie ein Problem — deshalb weiß niemand, wann sie aufgehört
haben zu wirken. Scanner sind beim Seitenaufruf nicht dabei. Agenturen liefern
ein PDF, das mit dem nächsten Theme-Update falsch wird.

## Die drei Stufen

**1. Wir merken, wenn wir falsch eingebaut sind.**
Das Manifest sagt dem Widget, ob complyo diese Kennung überhaupt kennt. Steht
im Skript-Tag etwas Falsches, warnt das Widget in der Konsole und meldet es
uns. Der Betreiber erfährt, dass sein Einbau ins Leere läuft — statt monatelang
zu glauben, es liefe.

*Belegt am 08.08.2026 an einer echten Seite: loqal.io lud das Cookie-Widget
unter `loqal-io` und das Barrierefreiheits-Widget daneben unter einer
Scan-Kennung. Der Server antwortete mit „200, nichts zu tun". Die Seite hätte
auch nach jeder Freigabe nie eine Reparatur bekommen.*

**2. Wir merken, wenn eine Reparatur nicht mehr ankommt.**
Bei jedem Seitenaufruf zählt das Widget, wie viele ausgelieferte Reparaturen
ihr Ziel gefunden haben — und wie viele ins Leere liefen. Ein Selektor, der
nichts mehr trifft, ist das Bild eines Theme-Updates. Das steht in der
Barrierefreiheitserklärung, bevor es jemand anders bemerkt.

Neu und wichtig: **drei Zustände, nicht zwei.** Eine Seite, die ihren
Hauptbereich selbst mitbringt, ist „unnötig" — kein Fehlschlag. Wer beides
zusammenwirft, erzeugt Alarme, denen niemand mehr glaubt.

**3. Wir benennen, was wir nicht reparieren können.**
Nicht als Kleingedrucktes, sondern als Zeile im öffentlichen Protokoll, mit
Grund. Ein Text in einem Web Component ist von außen mit CSS nicht erreichbar —
dann steht das da, statt ihn stillschweigend mitzuzählen.

## Was das dem Käufer wert ist

| Frage im Ernstfall | Ohne complyo | Mit complyo |
|---|---|---|
| „Seit wann besteht der Mangel?" | Unbekannt | Auf den Tag, aus dem Protokoll |
| „Wussten Sie davon?" | Nein — schlechteste Antwort | Ja, es steht öffentlich seit … |
| „Was haben Sie getan?" | Ein PDF von damals | Messung, Reparatur, Nachmessung, laufende Kontrolle |
| „Wirkt es heute noch?" | Niemand weiß es | Zuletzt bestätigt vor N Stunden |

**49 €/Monat** kauft nicht „ein Werkzeug prüft meine Seite", sondern „ich kann
jederzeit belegen, was ich wusste und was ich getan habe". Eine einzelne
Agenturprüfung mit Erklärung kostet vierstellig — **und altert ab dem
Übergabetag.**

**299 €/Monat Agentur** kauft dasselbe über das ganze Portfolio, inklusive der
Warnliste „hier läuft ein Einbau ins Leere". Diese Liste kann kein Scanner
erzeugen: er ist nicht dabei, wenn die Seite geladen wird.

## Die unbequeme Ehrlichkeit, die dazugehört

Dieser USP ist nur belastbar, solange complyo ihn auf sich selbst anwendet.
An einem einzigen Testtag sind gefunden worden:

- Ein Web Component brachte die **gesamte** Farbreparatur einer Seite zum
  Absturz — fail-open, ohne Spur. Cookie-Banner wie Usercentrics und Cookiebot
  benutzen diese Technik.
- Eine erteilte Freigabe überlebte den nächsten Scan nicht: Bildbeschreibungen
  wurden durch neue KI-Vorschläge ersetzt und gingen **als freigegeben** live,
  Farbfreigaben fielen auf „offen" zurück und verschwanden von der Website.
- Drei von sechs Kundenseiten hatten gar keinen Prüfnachweis.
- Der Scanner hätte eine Fehlerseite des Hosters als Kundenseite vermessen.

Alle vier sind behoben und durch Wächtertests festgenagelt. Keiner davon wäre
bei einem einzelnen Scan je aufgefallen — sie brauchten den **zweiten** Lauf,
den **falschen** Seitentyp, den **echten** Browser.

Das ist der eigentliche Satz für ein Verkaufsgespräch:

> **Wir haben unser eigenes Produkt einen Tag lang auseinandergenommen und vier
> Fehler gefunden, die niemandem aufgefallen wären. Genau diese Sorte Fehler
> hat Ihr jetziger Anbieter auch — er merkt sie nur nicht.**

## Offen

- Kachel im Dashboard für den Betriebszustand („N Reparaturen wirken, M laufen
  ins Leere, K Einbauten unter falscher Kennung")
- E-Mail bei Regression
- Hübsche Nachweis-Adresse unter `complyo.de` statt `api.complyo.de`
- **loqal.io: falsche `data-site-id` im Skript-Tag korrigieren** (Kundenseite,
  ein Wort ändern)
