# Der zweite USP: Barrierefreiheit, die sich selbst überwacht

*Entwurf 07.08.2026 · ergänzt [USP-pruefnachweis](USP-pruefnachweis-2026-08-07.md)*

---

## Das Problem, das jeder Anbieter hat und keiner anspricht

Barrierefreiheit ist kein Zustand, sondern ein Zustand **von gestern**.

Ein Audit misst am Dienstag. Am Donnerstag aktualisiert WordPress das Theme,
eine CSS-Klasse heißt anders, und die Reparatur, für die jemand bezahlt hat,
greift nicht mehr. Niemand merkt es. Das Zertifikat hängt weiter an der Wand,
die Barrierefreiheitserklärung nennt weiter ihre Zahl — und beide sind falsch.

Das gilt für alle:

| | Wie oft wird gemessen? | Wer merkt eine Regression? |
|---|---|---|
| **Agentur-Audit** | einmal | niemand |
| **Scanner** (Hugo, Siteimprove) | wöchentlich, Stichprobe | erst beim nächsten Lauf |
| **Overlays** | nie — sie messen nicht | niemand |
| **complyo bisher** | je Scan, Startseite | erst beim nächsten Scan |
| **complyo jetzt** | **bei jedem Seitenaufruf, auf jeder Seite** | **sofort** |

---

## In einem Satz

> **complyo prüft nicht wöchentlich eine Seite, sondern bei jedem Aufruf jede Seite.**

Kurzform fürs Gespräch:

> **„Jeder Besucher ist eine Prüfung."**

---

## Wie das geht — und warum nur complyo es kann

Das eingebundene Element ist bei jedem Seitenaufruf ohnehin da: es setzt die
freigegebenen Alt-Texte, die Farben, die Struktur. Dabei weiß es zwangsläufig
zweierlei:

1. **Wie viele Reparaturen angekommen sind.**
2. **Wie viele ins Leere liefen** — weil das Ziel nicht mehr existiert.

Punkt 2 ist der eigentliche Wert. Ein Selektor ohne Treffer ist exakt das Bild
eines Theme-Updates. Das Element meldet es zurück, und im Prüfnachweis steht
danach nicht mehr „alles gut", sondern:

> *„Bei 2 Reparaturen wurde das Ziel nicht mehr gefunden. Das deutet auf eine
> Änderung an der Website hin und wird geprüft."*

**Ein Scanner kann das strukturell nicht.** Er ist nicht dabei, wenn ein
Besucher die Seite öffnet. Er sieht die Startseite und vielleicht zehn
Unterseiten, einmal die Woche. Er weiß nicht, welche Seiten überhaupt besucht
werden.

**Ein Overlay könnte es — und tut es nicht.** Es hat keinen Grund dazu: wer
nicht misst, muss auch nicht erklären, warum eine Zahl gefallen ist. Genau
diese Lücke ist der Grund, warum sich accessiBe 2025 mit der US-FTC über
irreführende Konformitätsversprechen vergleichen musste.

---

## Was das für den Kunden ändert

**Die Abdeckung.** Der Scan misst die Startseite. Das Element ist auf jeder
Seite — auch auf denen, die nie gescannt wurden, und ausgerechnet die
Kontaktseite ist die, auf der Barrieren wehtun.

**Die Aktualität.** Die Barrierefreiheitserklärung trägt nicht mehr das Datum
des letzten Audits, sondern *„zuletzt bestätigt am 7. August, 12:06 Uhr"*.

**Die Warnung.** Wenn ein Update etwas zerlegt, steht es im Nachweis, bevor es
jemand anders bemerkt. Für eine Agentur mit zwanzig Kundenwebsites ist das der
Unterschied zwischen „wir haben das gebaut" und „wir passen darauf auf".

---

## Was ausdrücklich nicht passiert

Diese Liste gehört ins Verkaufsgespräch, nicht ins Kleingedruckte. Ein
Compliance-Anbieter, der nebenbei Besucher verfolgt, verkauft sich selbst ab.

- **Keine Besucherdaten.** Gemeldet werden der Seitenpfad und Zähler. Keine
  IP, keine Kennung, kein Verweis, kein User-Agent, kein Cookie, kein
  `localStorage`-Eintrag zur Wiedererkennung.
- **Keine Abfrageparameter.** `?q=…` und `#anker` werden abgeschnitten —
  zweimal: im Browser und noch einmal auf dem Server, weil ein öffentlicher
  Endpunkt sich nicht auf seinen Aufrufer verlassen darf. In Parametern stehen
  Suchbegriffe und Warenkorb-Inhalte.
- **Keine Einwilligung nötig.** Die Meldung sagt etwas über die **Seite** aus,
  nicht über den Menschen davor. Es sind keine personenbezogenen Daten, also
  greift auch kein Cookie-Banner-Zwang.
- **Die Datenbank kann es gar nicht.** Die Tabelle hat keine Spalte, in die
  ein Besucher passen würde. Ein Test hält das fest — was nicht gespeichert
  werden kann, kann auch nicht auslaufen.
- **Es stört nie.** Der Endpunkt antwortet immer ohne Inhalt, auch im
  Fehlerfall. Eine kaputte Statistik darf keine Kundenseite beeinträchtigen —
  nicht einmal durch einen roten Eintrag im Netzwerk-Reiter.

---

## Die Sätze fürs Gespräch

**Der Kernsatz:**
> „Andere prüfen einmal die Woche eine Seite. Bei uns ist jeder Besucher eine
> Prüfung — auf jeder Seite."

**Auf „wir haben doch schon ein Audit":**
> „Wann war das? Und was ist seitdem an der Website passiert? Genau das ist
> die Frage, die Ihr Audit nicht beantworten kann und unser Nachweis schon."

**Auf „macht das Overlay nicht dasselbe?":**
> „Ein Overlay ändert etwas und schaut nie nach. Unseres schaut nach und sagt
> Ihnen, wenn es nicht mehr passt."

**Für Agenturen:**
> „Sie erfahren von einem kaputten Theme-Update, bevor Ihr Kunde anruft."

**Wenn jemand nach Datenschutz fragt:**
> „Wir erfassen den Seitenpfad und Zähler. Keine IP, keine Kennung, keine
> Parameter. Die Tabelle hat keine Spalte für Besucher — schauen Sie rein."

---

## Wie beide USPs zusammenspielen

| | Der Prüfnachweis | Die Selbstüberwachung |
|---|---|---|
| beantwortet | „Zeigen Sie mir, dass es wirkt." | „Wirkt es **immer noch**?" |
| Beleg | Protokoll mit Vorher/Nachher | „zuletzt bestätigt vor 4 Minuten" |
| Reichweite | die geprüfte Seite | jede besuchte Seite |
| Ohne den anderen | ein Foto | ein Puls ohne Diagnose |

Zusammen ergeben sie den Satz, der beide Preise trägt:

> **„complyo repariert Ihre Website, weist die Reparatur öffentlich nach — und
> merkt es, wenn sie nicht mehr hält."**

Für 49 € im Monat. Ein Audit, das genau eine dieser drei Sachen kann, kostet
das Zwanzigfache und wird nur einmal geliefert.

---

## Was jetzt noch fehlt

1. **Ausrollen.** Der Backend-Container läuft mit dem alten Image; Code und
   Konfiguration liegen bereit. Ohne den Rollout gibt es weder Nachweis noch
   Selbstüberwachung.
2. **Die Nachweis-Adresse hübsch machen** — `complyo.de/nachweis/…` statt
   `api.complyo.de/api/nachweis/…`. Der Link steht in einer Rechtsverbindlichen
   Erklärung; er sollte nach der Marke aussehen, nicht nach einer API.
3. **Eine Kachel im Dashboard**, die den Betriebszustand zeigt — heute steht
   er nur im öffentlichen Nachweis. Der Kunde sollte ihn sehen, ohne den Link
   zu kennen.
4. **Benachrichtigung bei Regression.** Die Daten sind da; was fehlt, ist die
   E-Mail „auf zwei Seiten greift eine Reparatur nicht mehr".
