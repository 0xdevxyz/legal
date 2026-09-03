# Vorher / Nachher — gemessene Fixes

Erzeugt 06.08.2026 · Pruefer: axe-core 4.11.4 (WCAG 2.1 AA + best-practice)

Beide Messungen laufen unter identischen Bedingungen (lokale Kopie der
gerenderten Seite, `<base href>` auf die Originaldomain). Der Fix-Schritt ist
derselbe Produktionscode wie hinter dem PR-Knopf.

Das complyo-Laufzeit-Widget ist bei der Aufnahme **blockiert**. Sonst haette
es die Seite im Browser bereits repariert und das "Vorher" waere geschoent —
gemessen wird der Zustand, den ein Besucher ohne complyo vorfindet.

## Bilder ohne Textalternative

Die Kennzahl, um die es beim BFSG geht: wie viele Bilder ein
Screenreader stumm uebergeht. `alt=""` zaehlt hier als stumm — axe
wertet es als gueltig, WordPress setzt es aber an jedes Bild ohne
hinterlegten Alt-Text.

| Seite | Bilder | stumm vorher | stumm nachher | beschrieben |
|---|---:|---:|---:|---:|
| panoart360-de | 13 | 0 | 0 | 0 |
| spedition-mahn-de | 37 | 20 | 2 | 18 |
| ferienpark-waldenburg-de | 45 | 19 | 0 | 19 |
| zua-zwickau-de | 12 | 1 | 0 | 1 |

## axe-core-Verstoesse

Zum Vergleich das Standardmass. Es bewegt sich durch Alt-Texte kaum —
axe prueft die Existenz des Attributs, nicht ob der Text etwas sagt.

| Seite | Verstoesse vorher | nachher | behoben | davon kritisch/ernst |
|---|---:|---:|---:|---:|
| panoart360-de | 50 | 50 | 0 | 0 |
| spedition-mahn-de | 35 | 35 | 0 | 0 |
| ferienpark-waldenburg-de | 2 | 2 | 0 | 0 |
| zua-zwickau-de | 1 | 1 | 0 | 0 |

## Je Fall

### panoart360-de — https://panoart360.de

- gemessen: 2026-08-06 22:34 · Manifest-Status: `approved`
- angewendet: keine Aenderung
- Bilder: 13 gesamt · stumm 0 → 0 (davon leeres `alt` vorher: 0)
- brauchbare Alt-Text-Vorschlaege: 0
- keine Aenderung

### spedition-mahn-de — https://spedition-mahn.de

- gemessen: 2026-08-06 22:34 · Manifest-Status: `pending`
- angewendet: Alt-Texte für 18 Bild(er)
- Bilder: 37 gesamt · stumm 20 → 2 (davon leeres `alt` vorher: 20)
- brauchbare Alt-Text-Vorschlaege: 9
- **verworfen (nichtssagend): 5** — `Bild: Image 1`, `Bild: Image 20`, `Bild: Image 21`, `Bild: Image 22`, `Bild: Image 23`
- axe-Regeln unveraendert — die Verbesserung liegt in den Alt-Texten, die axe nicht bewertet

### ferienpark-waldenburg-de — https://ferienpark-waldenburg.de

- gemessen: 2026-08-06 22:34 · Manifest-Status: `approved`
- angewendet: Alt-Texte für 19 Bild(er)
- Bilder: 45 gesamt · stumm 19 → 0 (davon leeres `alt` vorher: 18)
- brauchbare Alt-Text-Vorschlaege: 17
- axe-Regeln unveraendert — die Verbesserung liegt in den Alt-Texten, die axe nicht bewertet

### zua-zwickau-de — https://zua-zwickau.de

- gemessen: 2026-08-06 22:34 · Manifest-Status: `approved`
- angewendet: Alt-Texte für 1 Bild(er)
- Bilder: 12 gesamt · stumm 1 → 0 (davon leeres `alt` vorher: 1)
- brauchbare Alt-Text-Vorschlaege: 1
- axe-Regeln unveraendert — die Verbesserung liegt in den Alt-Texten, die axe nicht bewertet
