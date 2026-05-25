# .md Schema-Spezifikation – complyo Knowledge Vault

## Frontmatter-Schema (YAML)

Jede `.md`-Wissensdatei beginnt mit standardisiertem YAML-Frontmatter:

```yaml
---
title: "NIS2-Richtlinie: Neue Meldepflichten ab 2026"
date: 2026-05-15
category: law-update
law_areas: [NIS2, BFSG, DSGVO]
relevance_score: 0.92
impact: high
source_url: "https://eur-lex.europa.eu/..."
source_type: eulex
affected_checks: [impressum_check, datenschutz_check]
tags: [NIS2, Cybersicherheit, Meldepflicht, 2026]
obsidian_links: ["[[NIS2]]", "[[DSGVO-Art-33]]"]
status: active
embedding_hash: "sha256:abc123..."
last_embedded: 2026-05-15T07:00:00
---
```

## Feldspezifikation

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|--------------|
| `title` | string | ja | Sprechender Titel |
| `date` | YYYY-MM-DD | ja | Erstellungsdatum |
| `category` | enum | ja | `law-update` / `court-ruling` / `pattern` / `index` / `law` |
| `law_areas` | list | ja | Betroffene Rechtsgebiete |
| `relevance_score` | float 0-1 | ja | KI-Bewertung (>=0.6 für Speicherung) |
| `impact` | enum | ja | `high` / `medium` / `low` |
| `source_url` | string | nein | Original-URL der Quelle |
| `source_type` | enum | nein | `eulex` / `erecht24` / `bfdi` / `web` / `internal` |
| `affected_checks` | list | nein | complyo-Checks die betroffen sind |
| `tags` | list | ja | Obsidian-Tags für Filter |
| `obsidian_links` | list | nein | WikiLinks `[[...]]]` zu verwandten Dateien |
| `status` | enum | ja | `active` / `superseded` / `draft` |
| `embedding_hash` | string | nein | SHA256 des Inhalts beim letzten Embedding |
| `last_embedded` | datetime | nein | Zeitstempel letztes RAG-Embedding |

## Datei-Inhaltsstruktur

### Typ: `law-update`
```markdown
## Zusammenfassung
[2-3 Sätze KI-Zusammenfassung auf Deutsch]

## Was ändert sich?
- [Konkrete Änderung 1]
- [Konkrete Änderung 2]

## Wer ist betroffen?
[Zielgruppe / Branchen / Unternehmensgrößen]

## Fristen
| Maßnahme | Frist |
|----------|-------|
| ...      | ...   |

## Handlungsempfehlungen für complyo
1. [Konkreter Schritt für complyo-Nutzer]
2. [Konkreter Schritt]

## Betroffene complyo-Checks
- [[{check-name}]]

## Quellen
- [Titel](URL)
```

### Typ: `law`
```markdown
## Überblick
[Gesetz / Richtlinie – Grundlagen]

## Für complyo relevante Artikel
| Artikel | Titel | Relevanz |
|---------|-------|---------|

## Aktuelle Auslegungen
[Letzte EuGH/BfDI-Entscheidungen]

## complyo-Checks die dieses Gesetz prüfen
- [[{check-name}]]

## Update-Historie
| Datum | Update | Link |
|-------|--------|------|
```

### Typ: `pattern`
```markdown
## Erkanntes Muster
[Beschreibung des häufigen Compliance-Fehlers]

## Häufigkeit
- Erkannt in: X% der gescannten Websites
- Trend: steigend / fallend / stabil

## Typischer Code
```html
<!-- Fehlerhafte Implementierung -->
```

## Lösung
```html
<!-- Korrekte Implementierung -->
```

## Verbundene Gesetze
- [[DSGVO]] Art. X
```

## Kategorie-Werte

- `law-update` – Neue Gesetzesänderungen, EU-Verordnungen, Richtlinien
- `court-ruling` – EuGH, BGH, OLG-Urteile mit Compliance-Relevanz
- `pattern` – Aus internen Scan-Daten gelernte Fehlermuster
- `index` – Auto-generierte Übersichtsfiles (nie manuell bearbeiten)
- `law` – Stammwissen-Seiten pro Gesetz (manuell + KI-angereichert)

## Impact-Berechnung

| Score-Bereich | Impact | Aktion |
|--------------|--------|--------|
| 0.85 - 1.0 | `high` | Rule-Review-Task erstellen + Admin-Benachrichtigung |
| 0.70 - 0.84 | `medium` | .md schreiben, keine Sofort-Aktion |
| 0.60 - 0.69 | `low` | .md schreiben, in Index aufnehmen |
| < 0.60 | – | Nicht gespeichert, nur geloggt |
