---
befundtyp: kontrast-zu-schwach
gilt_fuer: []
verfahren: vorschlag
niemals_bei:
  - Farbe wird an anderer Stelle als Markenfarbe gebraucht
  - Element ist zum Messzeitpunkt noch eingeblendet (Deckkraft unter 100 %)
  - Vorschlag erreicht die geforderte Ratio selbst nicht
belege: {}
status: vorschlag
freigegeben_von: null
quelle: knowledge/patterns/barrierefreiheit-check-patterns.md
---

# Kontrast zu schwach

**Rechtsgrundlage:** WCAG 2.1, Kriterium 1.4.3 (Kontrast Minimum 4,5:1).

## Verfahren

Je Farbpaar eine Entscheidung, nicht je Website. Eine Website trägt oft ein
Dutzend Paare; der Betreiber will vielleicht die Linkfarbe ändern und die
Schriftfarbe behalten. Eine eigene Farbe ist erlaubt und wird nachgerechnet:
erreicht sie die Ratio nicht, lehnt der Endpunkt ab. Sonst wäre „erfüllt
WCAG 2.1 AA" eine Behauptung, die der nächste Klick widerlegt.

## Grenzen

**Der Messzeitpunkt ist die häufigste Fehlerquelle.** Am 01.09.2026 stand eine
Überschrift in #111827 zum Messzeitpunkt bei 48 % Deckkraft — der Scanner
meldete einen Kontrastfehler an einer gut lesbaren Stelle. Netzwerkruhe sagt
nichts über laufende Einblendungen.

## Belege

**Keine.** Stand 05.09.2026: 12 Entscheidungen, 3 angenommen, 0 abgelehnt,
9 offen. Ohne Ablehnung ist nicht erkennbar, wo das Verfahren danebenliegt.
