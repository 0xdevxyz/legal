---
befundtyp: linktext-ohne-bedeutung
gilt_fuer: []
verfahren: vorschlag
niemals_bei:
  - Der bestehende Linktext beschreibt das Ziel bereits
  - Das Linkziel ist nicht abrufbar (der Vorschlag wäre geraten)
  - Der Link trägt bereits ein aria-label
belege: {}
status: vorschlag
freigegeben_von: null
quelle: knowledge/patterns/barrierefreiheit-check-patterns.md
---

# Linktext ohne Bedeutung

**Rechtsgrundlage:** WCAG 2.1, Kriterium 2.4.4 (Linkzweck im Kontext).

## Verfahren

Für Links wie „hier", „mehr" oder „weiterlesen" wird ein `aria-label`
vorgeschlagen, das aus dem Linkziel und dem umgebenden Text gebildet wird. Der
sichtbare Text bleibt unverändert — er ist eine Gestaltungsentscheidung.

## Grenzen

Ist das Ziel nicht abrufbar, entsteht kein Vorschlag. Ein aus dem Dateinamen
geratenes Label ist schlechter als keins: es klingt richtig und ist es nicht.

## Belege

**Keine.** Stand 05.09.2026: 0 Vorschläge in der Datenbank. Der Weg ist seit
dem 04.09. verkabelt, aber noch nie gelaufen.
