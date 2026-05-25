# AP4: Multilinguale regulatorische Wissensmodelle

## Executive Summary

Mehrsprachige Rechtswissensmodelle sind eine offene Forschungsfrage, weil Rechtsnormen nicht nur sprachliche Informationen enthalten, sondern kontextabhängige juristische Bedeutungen, nationale Umsetzungsspielräume und dynamische Auslegung durch Behörden und Gerichte. Eine einfache Übersetzung reicht für Compliance-Systeme nicht aus: dieselbe EU-Norm kann in verschiedenen Sprachfassungen unterschiedliche Formulierungen haben, während nationale Gesetze zusätzliche Pflichten oder Begriffe einführen.

AP4 schafft deshalb eine mehrsprachige Wissensbasis, die EU-Rechtsakte, nationale Referenzen, Sprachvarianten und Norm-Äquivalenzen strukturiert zusammenführt. Ziel ist ein Retrieval-System, das Nutzeranfragen in einer Sprache erkennt, passende Quellen in mehreren Sprachen berücksichtigen kann und die gefundenen Normen über eine Mapping-Ontologie aufeinander bezieht.

## IST-Stand

- Wissensbasis bisher primär DE/EN orientiert.
- Viele Begriffe sind hartkodiert und nicht systematisch über Sprachen hinweg modelliert.
- Der Bestand umfasst aktuell 7 zentrale Gesetze bzw. Rechtsbereiche, aber ohne vollständige EU-Äquivalenzstruktur.
- Es gibt keine durchgängige Norm-Ontologie, die deutsche Normen mit EU-Originalnormen und anderen Sprachfassungen verbindet.
- Retrieval und UI-Übersetzungen sind nur begrenzt multilingual.

## Forschungs-Herausforderungen

### 1. Rechtliche Äquivalenz

Gleiche Norm bedeutet nicht zwingend identischer Text. EU-Rechtsakte sind in allen Amtssprachen verbindlich, können aber terminologische Abweichungen enthalten. Bei Richtlinien kommen nationale Umsetzungsbesonderheiten hinzu, z. B. beim BFSG als Umsetzung des European Accessibility Act oder beim TTDSG als nationale Einordnung von ePrivacy-Vorgaben.

### 2. Cross-lingual Retrieval

Eine deutsch formulierte Query soll nicht nur deutsche Dokumente finden, sondern bei Bedarf auch englische oder französische EU-Dokumente. Dafür muss das System Sprache erkennen, sprachspezifisch suchen und bei fehlenden Treffern auf andere Sprachen oder den allgemeinen Index zurückfallen.

### 3. Norm-Mapping

Für belastbare Compliance-Ausgaben muss das System automatisch erkennen, dass etwa Art. 6 DSGVO, Art. 6 GDPR und Art. 6 RGPD dieselbe EU-Norm adressieren. Diese Äquivalenz ist nicht nur lexikalisch, sondern fachlich-juristisch zu modellieren.

## Implementierte Lösung

- Mehrsprachige Korpus-Struktur mit Ordnern für `de`, `en`, `fr`, `it`, `pl` unter `knowledge/laws/`.
- Norm-Mapping-Ontologie in `knowledge/laws/_mapping.yaml` mit Zuordnung deutscher Normen zu EU-Normen und Übersetzungen.
- Language-Aware Retriever als neues Backend-Modul mit heuristischer Spracherkennung, sprachspezifischer Suche und Fallback-Retrieval.
- EUR-Lex-Crawler für automatische Aktualisierung von EU-Rechtsakten in fünf Sprachen.
- Erweiterung des i18n-Service auf fünf Sprachen mit Kernbegriffen für Compliance-Ausgaben.

## Technische Architektur

```text
User Query
    |
    v
Spracherkennung
    |
    v
Sprachspezifischer Index (de/en/fr/it/pl)
    |
    v
Cross-lingual Fallback
    |
    v
Norm-Mapping-Ontologie (_mapping.yaml)
    |
    v
Compliance Output mit Norm-Referenzen und Sprache
```

## Abdeckung nach Umsetzung

| Sprache | Gesetze | Status |
|---------|---------|--------|
| Deutsch (de) | DSGVO initial migriert; Mapping für DSGVO, BFSG, TTDSG, NIS2 | Grundstruktur vorhanden, weitere Migration erforderlich |
| Englisch (en) | GDPR, DSA, AI Act als kompakte Compliance-Stubs | Kernabdeckung für EU-Website-Compliance vorhanden |
| Französisch (fr) | RGPD als kompakter Compliance-Stub | Initiale RGPD-Abdeckung vorhanden |
| Italienisch (it) | Ordnerstruktur und EUR-Lex-Crawler-Ziel | Korpus vorbereitet, automatische Befüllung vorgesehen |
| Polnisch (pl) | Ordnerstruktur und EUR-Lex-Crawler-Ziel | Korpus vorbereitet, automatische Befüllung vorgesehen |

## Wissenschaftliche Abgrenzung

Der Ansatz unterscheidet sich von maschineller Übersetzung, weil nicht die Übersetzung einzelner Sätze im Vordergrund steht, sondern die juristische Referenzierbarkeit und Äquivalenz von Normen. Spezialisierte Rechtsmodelle sind nötig, weil Compliance-Systeme konkrete Pflichten, Ausnahmen, Rechtsfolgen und nationale Umsetzungen erkennen müssen. Ein allgemeines Übersetzungssystem kann nicht zuverlässig entscheiden, ob zwei Normtexte funktional äquivalent sind oder ob nationale Abweichungen bestehen.

## EUR-Lex-Datenquellen

EUR-Lex stellt EU-Rechtsakte öffentlich bereit und bietet stabile CELEX-IDs für Rechtsakte wie DSGVO, DSA, AI Act, NIS2 und EAA. Der implementierte Crawler ruft HTML-Fassungen über EUR-Lex-URLs ab und speichert Markdown-Auszüge im mehrsprachigen Korpus. EU-Recht ist öffentlich zugänglich; die Nutzung erfolgt als public domain EU-Recht bzw. auf Basis der öffentlichen Verfügbarkeit amtlicher Rechtsakte. Die geplante Update-Frequenz ist monatlich, jeweils am 1. des Monats um 02:00 Uhr.

## Zeitplan

AP4 ist als eigenständige Forschungs- und Implementierungsphase in den Monaten 6 bis 18 vorgesehen. Der Aufwand beträgt 70 Personentage und ist damit der höchste Einzelaufwand, weil Modellierung, juristische Validierung, technische Integration und Qualitätssicherung parallel erforderlich sind.

## Budget

Das höhere Budget ist begründet durch:

- Rechtsexpertise für die Validierung cross-lingualer Norm-Äquivalenzen.
- Annotationskosten für mehrsprachige Trainings- und Evaluationsdaten.
- Aufbau und Pflege einer Norm-Mapping-Ontologie.
- Qualitätssicherung bei EU-Sprachfassungen und nationalen Umsetzungsgesetzen.
- Technische Integration von Retriever, Crawler, i18n-Service und Compliance-Engine.
