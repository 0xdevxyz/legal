---
befundtyp: bild-ohne-alt-text
gilt_fuer: []
verfahren: vorschlag
niemals_bei:
  - alt-Attribut ist bereits gesetzt und nicht leer
  - Bildadresse nicht ermittelbar (der Fix hätte kein Ziel)
  - Dekorationsgrafik, die nur über CSS eingebunden ist
belege: {}
status: vorschlag
freigegeben_von: null
quelle: knowledge/patterns/barrierefreiheit-check-patterns.md
---

# Bild ohne Alt-Text

**Rechtsgrundlage:** WCAG 2.1, Kriterium 1.1.1 (Nicht-Text-Inhalte), BFSG.

## Verfahren

Alt-Text wird vorgeschlagen, nicht gesetzt. Der Betreiber gibt jeden einzeln
frei; das Widget liefert nur Freigegebenes aus.

`alt=""` wird als fehlend behandelt und gefüllt. Das ist eine bewusste
Abweichung von der reinen Lehre: in WordPress entsteht ein leeres
`alt`-Attribut standardmäßig beim Hochladen, es bedeutet dort fast nie
„dekorativ".

## Grenzen

Ein Befund ohne ermittelbare Bildadresse wird übersprungen — ein Fix ohne Ziel
wäre keiner. Deshalb erzeugte complyo.de selbst null Alt-Texte, obwohl der
Scanner Befunde meldete.

## Belege

**Keine.** Dieser Skill ist aus einer Musterdatei überführt, nicht aus
Entscheidungen gewachsen. Er darf deshalb nicht `aktiv` werden — siehe
`skills.darf_aktiv_sein()`.

Stand 05.09.2026: 24 Vorschläge, 23 angenommen, **0 abgelehnt**. Eine Quote
von 100 % ohne eine einzige Ablehnung sagt nichts darüber, wo das Verfahren
danebenliegt.
