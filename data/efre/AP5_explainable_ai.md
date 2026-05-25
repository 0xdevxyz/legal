# AP5: Explainable AI für Compliance

## Executive Summary

Explainable AI (XAI) ist für Compliance-Systeme wissenschaftlich relevant, weil regulatorische Entscheidungen nicht nur korrekt, sondern nachvollziehbar, auditierbar und überprüfbar sein müssen. Klassische KI-Klassifikationen liefern oft nur ein Ergebnis mit Freitextbegründung. Für Rechts- und Compliance-Kontexte reicht dies nicht aus: Nutzer, Prüfer und menschliche Aufsichtspersonen müssen erkennen können, welche Normen herangezogen wurden, welche Faktoren die Entscheidung ausgelöst haben und unter welchen Bedingungen die Einschätzung anders ausgefallen wäre.

Für EFRE ist AP5 förderungswürdig, weil es eine innovative, strukturierte Erklärschicht für KI-gestützte Compliance-Entscheidungen schafft. Die Entwicklung verbindet RAG-basierte Normzitation, Confidence-Decomposition und Counterfactual-Erklärungen zu einem produktnahen Verfahren, das Transparenz, Nachvollziehbarkeit und menschliche Kontrollfähigkeit verbessert.

## IST-Stand

Der bisherige Stand im System besteht aus drei zentralen Elementen:

- `reasoning` als Freitextbegründung der KI-Klassifizierung
- Audit- und Logging-Strukturen, die Klassifizierungen und Entscheidungen nachvollziehbar speichern
- `confidence_score` beziehungsweise Confidence-Angaben zur Einschätzung der Modellzuverlässigkeit

Diese Elemente sind wertvoll, aber nur begrenzt strukturiert. Ein Freitext kann fachlich hilfreich sein, ist jedoch schwer maschinell auswertbar, schwer vergleichbar und nur eingeschränkt geeignet für systematische Audits oder regulatorische Transparenzberichte.

## Innovation: strukturierte XAI statt Freitext-Begründungen

AP5 erweitert die bisherige Freitext-Erklärung um ein strukturiertes XAI-Dokument. Dadurch wird eine Compliance-Klassifizierung nicht nur verbal begründet, sondern in einzelne erklärbare Komponenten zerlegt:

- zitierte Normen mit Relevanzwerten
- auslösende Faktoren mit Gewichtung
- Confidence Breakdown nach Begründungskomponenten
- Counterfactuals als alternative Szenarien
- explizite XAI-Versionierung

Die Innovation liegt in der Verbindung von juristischer Retrieval-Logik mit erklärbaren KI-Ausgaben. Die Erklärung wird dadurch nicht als nachträglicher Kommentar behandelt, sondern als eigenständiges, versioniertes Datenobjekt.

## Technische Architektur

### NormReference / ExplanationDoc Schema

| Struktur | Feld | Typ | Zweck |
|----------|------|-----|-------|
| `NormReference` | `law` | `str` | Name des Gesetzes oder Rechtsbereichs |
| `NormReference` | `article` | `str` | Artikel oder Paragraphenreferenz |
| `NormReference` | `paragraph` | `str` | Optionaler Absatz oder Unterpunkt |
| `NormReference` | `url` | `str` | Link zur Quelle oder Norm |
| `NormReference` | `relevance_score` | `float` | Relevanz der Norm für die Klassifizierung |
| `NormReference` | `quote` | `str` | Optionales Zitat aus der Quelle |
| `Factor` | `factor` | `str` | Name des auslösenden Faktors |
| `Factor` | `weight` | `float` | Gewicht des Faktors in der Erklärung |
| `Factor` | `description` | `str` | Menschlich lesbare Beschreibung |
| `ExplanationDoc` | `cited_norms` | `List[NormReference]` | Zitierte Normen |
| `ExplanationDoc` | `triggering_factors` | `List[Factor]` | Entscheidungsrelevante Faktoren |
| `ExplanationDoc` | `confidence_breakdown` | `Dict[str, float]` | Zerlegung der Confidence |
| `ExplanationDoc` | `counterfactuals` | `List[str]` | Alternative Szenarien |
| `ExplanationDoc` | `xai_version` | `str` | Version der XAI-Struktur |

### RAG-with-Citation Pipeline

Die RAG-with-Citation Pipeline verbindet die Klassifizierung von Rechtsänderungen mit Dokumenten aus dem Knowledge-Retrieval. Relevante Dokumente werden anhand des Update-Textes gesucht, mit Scores versehen und anschließend in `NormReference`-Objekte überführt. Dadurch kann die KI-Einschätzung mit konkreten Rechtsbereichen und Quellen verknüpft werden.

Ablauf:

1. Legal Update wird klassifiziert.
2. Relevante Dokumente werden aus dem Knowledge-System abgerufen.
3. Rechtsreferenzen aus `law_refs` werden extrahiert.
4. Normen werden mit `relevance_score` und URL als `NormReference` gespeichert.
5. Die strukturierte Erklärung wird zusammen mit der Klassifizierung persistiert.

### Counterfactual-Generierung

Counterfactuals beantworten die Frage: Was müsste anders sein, damit die Klassifizierung anders ausfällt? Für Compliance ist dies besonders relevant, weil Nutzer nicht nur wissen wollen, dass Handlungsbedarf besteht, sondern auch warum keine mildere Einschätzung möglich war.

Beispiel:

> Wenn die Änderung nur redaktionelle Klarstellungen ohne neue Betreiberpflichten enthielte, dann wäre die Klassifizierung information_only.

Diese Form der Erklärung unterstützt menschliche Prüfung, Training, interne Qualitätssicherung und Nutzerverständnis.

### Confidence-Decomposition

Die Confidence-Decomposition zerlegt die Gesamtsicherheit in mehrere erklärbare Teilkomponenten:

- `law_match_score`: Übereinstimmung mit gefundenen Normen
- `severity_keywords`: Schweregrad durch Schlüsselbegriffe
- `historical_precedent`: Ähnlichkeit zu bekannten Fällen
- `context_clarity`: Klarheit des regulatorischen Kontextes

Dadurch wird sichtbar, ob eine hohe Confidence beispielsweise aus starken Normtreffern oder aus klaren Severity-Hinweisen resultiert.

## EU AI Act Konformität

| Anforderung | Art. | Erfüllung durch Complyo |
|-------------|------|-------------------------|
| Transparente Information über Zweck und Funktionsweise | Art. 13 | XAIExplanationCard zeigt Gründe, Confidence und verwendete Normen direkt im Interface. |
| Verständliche und nutzergeeignete Ausgabe | Art. 13 | Erklärungen werden als strukturierte, visuelle Komponenten statt nur als Rohtext dargestellt. |
| Nachvollziehbarkeit der Systementscheidung | Art. 13 | `ExplanationDoc` speichert Normen, Faktoren, Breakdown und Counterfactuals auditierbar. |
| Angabe von Genauigkeit und Leistungsgrenzen | Art. 13 | Confidence und Confidence-Decomposition machen Unsicherheiten sichtbar. |
| Ermöglichung menschlicher Aufsicht | Art. 14 | Menschen können Triggering-Factors und zitierte Normen prüfen und Entscheidungen hinterfragen. |
| Unterstützung von Intervention und Korrektur | Art. 14 | Counterfactuals und strukturierte Faktoren zeigen, welche Annahmen korrigiert oder überprüft werden müssen. |
| Erkennung potenzieller Fehlentscheidungen | Art. 14 | Abweichende oder schwache Confidence-Komponenten können als Review-Signal genutzt werden. |
| Dokumentierte Entscheidungsgrundlagen | Art. 13/14 | XAI-Felder werden per Migration persistierbar in `ai_compliance_logs` ergänzt. |

## Wissenschaftliche Abgrenzung: LIME/SHAP vs. prompt-basierte XAI

LIME und SHAP sind etablierte Verfahren, um Modellentscheidungen durch Feature-Beiträge zu erklären. Sie eignen sich besonders für tabellarische Daten, klassische Machine-Learning-Modelle und Szenarien, in denen Features klar definiert und kontrolliert perturbierbar sind.

Für Compliance-KI mit LLMs und RAG gelten andere Anforderungen. Die Eingaben bestehen aus juristischen Texten, Quellen, Kontextinformationen und semantischen Beziehungen. Prompt-basierte XAI kann diese juristische Semantik direkter ausdrücken, indem sie Normen, Begründungsfaktoren und Gegenbeispiele in natürlicher Sprache und strukturierter Form kombiniert.

| Ansatz | Vorteile | Nachteile |
|--------|----------|-----------|
| LIME | Modellagnostisch, lokale Erklärungen, gut für Feature-Beiträge | Für juristische Freitexte schwer interpretierbar, Perturbationen können semantisch unplausibel sein |
| SHAP | Mathematisch fundierte Beitragswerte, vergleichbar | Hoher Rechenaufwand, begrenzte Aussagekraft bei langen LLM-Kontexten |
| Prompt-basierte XAI | Juristisch verständlich, gut mit RAG-Zitaten kombinierbar, produktnah | Abhängig von Prompt-Qualität, benötigt Validierung gegen Quellen |
| RAG-with-Citation XAI | Verbindet Erklärung mit konkreten Normen und Quellen | Retrieval-Qualität beeinflusst Zitierungspräzision |

AP5 positioniert sich daher nicht als Ersatz für LIME/SHAP in allen Bereichen, sondern als domänenspezifische XAI-Schicht für juristische Compliance-Klassifikationen.

## Frontend-Visualisierung

Die Komponente `XAIExplanationCard` visualisiert ein `ExplanationDoc` im Dashboard. Sie zeigt:

1. eine Confidence-Bar mit farbigen Segmenten für `law_match_score`, `severity_keywords`, `historical_precedent` und `context_clarity`
2. zitierte Normen als klickbare Chips mit Link-Icon
3. Triggering-Factors als horizontale, div-basierte Bar-Charts
4. Counterfactuals als aufklappbare Liste

Die Komponente nutzt Tailwind CSS und orientiert sich an bestehenden Card-Patterns des Dashboards mit gerundeten Containern, Schatten, klarer Typografie und Lucide-Icons.

## KPIs

| KPI | Zielwert | Messmethode |
|-----|----------|-------------|
| Erklärungsqualität | User-Zufriedenheit ≥ 70% | Nutzerfeedback nach Anzeige der XAIExplanationCard |
| Norm-Zitierungs-Präzision | ≥ 80% | Stichprobenprüfung durch fachliche Reviewer |
| Counterfactual-Verständlichkeit | ≥ 70% positive Bewertung | Nutzer- und Expertenrating |
| Auditierbarkeit | 100% der XAI-fähigen Klassifizierungen mit `xai_version` | Datenbankauswertung |
| Review-Unterstützung | Reduktion manueller Klärungszeit | Vergleich vor/nach AP5 |

## Zeitplan

| Zeitraum | Arbeitspaket | Aufwand |
|----------|--------------|---------|
| Monat 4 | Schema, Migration, Datenmodell | 6 Personentage |
| Monat 4-5 | RAG-with-Citation Integration | 8 Personentage |
| Monat 5-6 | Counterfactual-Generierung | 7 Personentage |
| Monat 6 | Confidence-Decomposition | 6 Personentage |
| Monat 7 | Frontend-Visualisierung | 6 Personentage |
| Monat 8 | Evaluation, KPI-Messung, Qualitätssicherung | 7 Personentage |
| Gesamt | AP5 Explainable AI | 40 Personentage |
