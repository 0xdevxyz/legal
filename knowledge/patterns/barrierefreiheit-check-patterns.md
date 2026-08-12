---
affected_checks:
- barrierefreiheit_check
category: pattern
date: '2026-08-12'
embedding_hash: ''
impact: high
last_embedded: ''
law_areas:
- BFSG
obsidian_links:
- '[[BFSG]]'
relevance_score: 0.9
source_type: internal
source_url: ''
status: active
tags:
- pattern
- BFSG
title: 'Muster: Barrierefreiheit Fehler'
---

# Muster: Barrierefreiheit Fehler

Häufige WCAG-Verstöße nach BFSG-Prüfung

## Muster 1: Bilder ohne Alt-Text

**Häufigkeit:** sehr häufig

**Rechtsgrundlage:** WCAG 2.1 Kriterium 1.1.1 – Nicht-Text-Inhalte

### Fehlerhafte Implementierung

```html
<img src="produkt.jpg">
```

### Korrekte Implementierung

```html
<img src="produkt.jpg" alt="Rotes T-Shirt aus Bio-Baumwolle">
```

## Muster 2: Zu geringer Kontrast

**Häufigkeit:** häufig

**Rechtsgrundlage:** WCAG 2.1 Kriterium 1.4.3 – Kontrast Minimum 4.5:1

### Fehlerhafte Implementierung

```html
/* Text: #999999 auf #FFFFFF = Kontrast 2.85:1 (Minimum: 4.5:1) */
color: #999999;
```

### Korrekte Implementierung

```html
/* Text: #595959 auf #FFFFFF = Kontrast 7.0:1 */
color: #595959;
```

## Muster 3: Formularfelder ohne Label

**Häufigkeit:** häufig

**Rechtsgrundlage:** WCAG 2.1 Kriterium 1.3.1 – Info und Beziehungen

### Fehlerhafte Implementierung

```html
<input type="email" placeholder="E-Mail">
```

### Korrekte Implementierung

```html
<label for="email">E-Mail-Adresse</label>
<input type="email" id="email" placeholder="name@beispiel.de">
```

## Betroffene complyo-Checks

- [[barrierefreiheit_check]]

## Verwandte Gesetze

[[BFSG]]

---
*Automatisch generiert am 2026-08-12 durch complyo Pattern Extractor*
