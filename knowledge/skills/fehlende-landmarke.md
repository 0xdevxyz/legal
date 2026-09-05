---
befundtyp: fehlende-landmarke
gilt_fuer: []
verfahren: mechanisch
niemals_bei:
  - Es gibt bereits eine main-Landmarke (nie eine zweite setzen)
  - Der gemessene Container liegt in einem Randbereich (Kopf, Fuß, Navigation)
  - Der Selektor trifft auf der Unterseite mehr als ein Element
belege: {}
status: vorschlag
freigegeben_von: null
quelle: knowledge/patterns/barrierefreiheit-check-patterns.md
---

# Fehlende Landmarke / Skip-Link

**Rechtsgrundlage:** WCAG 2.1, Kriterien 1.3.1 und 2.4.1.

## Verfahren

`role="main"` wird an den **gemessenen** Container gesetzt, nicht an einen aus
einer Rateliste. Für Unterseiten misst der Scanner seitenstabile
Alternativselektoren (`data-elementor-type`, Klassenkette ohne volatile
ID-Klassen) und prüft sie auf der gemessenen Seite nach.

Das Widget löst in dieser Reihenfolge auf: exakter Selektor, dann
Alternativen, dann Ableitung — und nur bei genau einem Treffer.

## Grenzen

Eine zweite `main`-Landmarke ist schlimmer als keine. Deshalb zählt das Widget
Fälle, in denen es nicht eingreift, als eigenen Zähler (`struktur.unnoetig`).
**Ein nicht angewandter Fix ist kein Fehlschlag.**

## Belege

**Keine.** Stand 05.09.2026: 6 skip-link und 6 landmark-main, alle angenommen —
aber bis zum 04.09. wurde niemand gefragt, sie gingen automatisch live. Eine
Zustimmungsquote ohne Frage ist keine Zustimmung.
