---
title: complyo Knowledge Vault
category: index
tags: [index, root]
---

# complyo Knowledge Vault

> Selbstlernendes Compliance-Wissenssystem – automatisch aktualisiert täglich um 07:00 Uhr

## Bereiche

| Bereich | Beschreibung | Link |
|---------|-------------|------|
| Updates | Täglich neue Rechtsänderungen | [[updates-index]] |
| Gesetze | Stammwissen je Gesetz | [[laws-index]] |
| Muster | Gelernte Compliance-Fehler | `patterns/` |

## Vault-Statistiken

```dataview
TABLE length(rows) as Anzahl
FROM "updates" OR "laws" OR "patterns"
GROUP BY category
```

## Letzte High-Impact Updates

```dataview
TABLE date, title, law_areas
FROM "updates"
WHERE impact = "high"
SORT date DESC
LIMIT 5
```

## Alle Gesetze

```dataview
TABLE law_areas, affected_checks
FROM "laws"
SORT title ASC
```
