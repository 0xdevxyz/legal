# Laws Vault – Initialisierungsplan

## Generierte Stammwissen-Dateien

| Datei | Status | Beschreibung |
|-------|--------|--------------|
| `knowledge/laws/DSGVO.md` | Erstellt | DSGVO Art. 5, 6, 7, 13, 14, 25, 30, 33, 37 |
| `knowledge/laws/BFSG.md` | Erstellt | WCAG-Mapping, Fristen, Ausnahmen |
| `knowledge/laws/NIS2.md` | Erstellt | Meldepflichten, betroffene Sektoren |
| `knowledge/laws/TTDSG.md` | Erstellt | § 25 Cookie-Einwilligung |
| `knowledge/laws/UWG.md` | Erstellt | § 5 Irreführung, Abmahngründe |
| `knowledge/laws/AGB-Recht.md` | Erstellt | §§ 305 ff. BGB |
| `knowledge/laws/Impressumspflicht.md` | Erstellt | § 5 TMG, § 18 MStV |

## Noch zu erstellen (via KI-Generierung)

| Datei | Priorität | Beschreibung |
|-------|-----------|--------------|
| `knowledge/laws/AI-Act.md` | Hoch | EU KI-Verordnung 2024/1689 |
| `knowledge/laws/DSA.md` | Mittel | Digital Services Act |
| `knowledge/laws/PAngV.md` | Mittel | Preisangabenverordnung |
| `knowledge/laws/WCAG.md` | Mittel | Technische WCAG-Kriterien |

## Auto-Update durch Knowledge Updater

Jede Law-Page wird täglich durch den `knowledge_updater.py` Cronjob ergänzt:
- Neue EuGH/BGH-Urteile werden in "Aktuelle Auslegungen" eingetragen
- "Update-Historie" wird automatisch erweitert
- `last_embedded` Timestamp wird nach RAG-Indexierung gesetzt
