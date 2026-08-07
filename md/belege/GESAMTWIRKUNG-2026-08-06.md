# Was complyo repariert — gemessen, nicht behauptet

Gemessen 06.08.2026 an **24 echten deutschen KMU-Websites** (eigene
Hosting-Kunden, Startseite). Prüfer: axe-core 4.11.4, Regelsatz WCAG 2.1 AA
plus best-practice. Das complyo-Widget war bei der Aufnahme blockiert — gemessen
wird der Zustand, den ein Besucher ohne complyo vorfindet.

**Alle Reparaturen in einem Lauf**, nicht aus getrennten Läufen addiert: Fixes
beeinflussen einander (ein `role="main"` verändert die `region`-Zählung, ein
Alt-Text löst zugleich `link-name`).

| | vorher | nachher | behoben |
|---|---:|---:|---:|
| **Pflicht (WCAG 2.1 AA)** | **291** | **39** | **252 — 87 %** |
| Empfehlung (best-practice) | 424 | 213 | 211 — 50 % |

## Je Regel

| Regel | vorher | nachher | behoben | Rang |
|---|---:|---:|---:|---|
| `color-contrast` | 194 | 7 | **187** | Pflicht |
| `region` | 331 | 126 | 205 | Empfehlung |
| `link-name` | 56 | 4 | **52** | Pflicht |
| `landmark-one-main` | 12 | 1 | 11 | Empfehlung |
| `meta-viewport` | 7 | 0 | **7** | Pflicht |
| `link-in-text-block` | 3 | 0 | **3** | Pflicht |
| `button-name` | 1 | 0 | **1** | Pflicht |
| `frame-title` | 1 | 0 | **1** | Pflicht |
| `scrollable-region-focusable` | 1 | 0 | **1** | Pflicht |

## Was bewusst offen bleibt

| Regel | Fundstellen | Warum nicht mechanisch |
|---|---:|---|
| `nested-interactive` | 9 | Ein Link im Button ist ein Strukturfehler; die Auflösung baut Inhalt um |
| `image-alt` | 6 | Läuft über den Alt-Text-Weg mit KI-Vorschlag und menschlicher Freigabe — in diesem Lauf nicht mitgemessen |
| `label` | 5 | Welche Beschriftung ein Feld braucht, hängt am Formularzweck |
| `select-name` | 3 | dito |
| `aria-required-parent` | 3 | Die fehlende Rolle hängt am Bauplan des Bedienelements |
| `heading-order` | 42 | Welche Zeile welche Ebene ist, ist redaktionell |
| `page-has-heading-one` | 8 | dito |

Diese Liste ist kein Rückstand, sondern eine Grenze: Mechanik hat kein Urteil.
Wo eines nötig ist, schlägt complyo vor und ein Mensch entscheidet — oder es
bleibt liegen.

## Der Aufwand für den Kunden

Die 252 behobenen Pflicht-Fundstellen kosten **rund drei bis vier Freigaben je
Website**: die Farbentscheidungen (im Schnitt 2,6 je Seite, eine deckt 3,1
Fundstellen ab), dazu die Link-Beschriftungen. Struktur-Fixes (Hauptinhalt,
Zoom-Sperre, Einbettungstitel) ändern das Aussehen nicht und gehen ohne
Rückfrage raus.

## Was axe nicht misst

`alt=""` gilt für axe als gültige Dekorativ-Markierung — WordPress schreibt es
aber an jedes Bild ohne Mediathek-Alt-Text. Auf denselben 24 Seiten sind
**190 von 384 Bildern stumm**, ohne dass axe einen einzigen Verstoß meldet.
Wer nur axe-Zahlen vergleicht, misst ausgerechnet den Teil nicht, der
Screenreader-Nutzern am meisten bringt.

## Wie das nachzurechnen ist

```bash
docker run --rm -v $(pwd)/backend:/src -v /tmp/bestand:/out -w /src legal-backend python tools/bestandsaufnahme.py --datei /sites.txt --out /out
```

```bash
docker run --rm -v $(pwd)/backend:/src -v /tmp/bestand:/out -w /src legal-backend python tools/gesamtwirkung.py --ordner /out
```
