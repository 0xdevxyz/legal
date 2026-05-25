---
title: Gesetze Index
category: index
tags: [index, laws]
---

# Rechtsgebiete Index

```dataview
TABLE law_areas, affected_checks
FROM "laws"
SORT title ASC
```

## Schnellzugriff

- [[DSGVO]] – Datenschutz-Grundverordnung
- [[BFSG]] – Barrierefreiheitsstärkungsgesetz
- [[NIS2]] – Netz- und Informationssicherheitsrichtlinie
- [[TTDSG]] – Telekommunikations-Telemedien-Datenschutz-Gesetz
- [[UWG]] – Gesetz gegen unlauteren Wettbewerb
- [[AGB-Recht]] – §§ 305 ff. BGB
- [[Impressumspflicht]] – § 5 TMG / § 18 MStV

## Updates je Gesetz

```dataview
TABLE date, impact
FROM "updates"
FLATTEN law_areas as area
GROUP BY area
SORT rows.date DESC
```
