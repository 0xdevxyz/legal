# AP1: Semantische Klassifikation härten

## Executive Summary
AP1 erweitert die bestehende Legal-Classification-Pipeline um semantische Suche, Multi-Label-Rechtsgebietszuordnung und reproduzierbare Evaluation. Die neue Architektur kombiniert keyword-basiertes Retrieval mit Embedding-Similarity und liefert pro Klassifikation betroffene Gesetze inklusive Konfidenzen. Damit wird eine belastbare Grundlage für EFRE-fähige wissenschaftliche Validierung der automatisierten Website-Compliance-Klassifikation geschaffen.

## IST-Stand
- `knowledge_retriever.py`: Lädt Knowledge-Vault-Dokumente, erzeugt Embeddings über OpenAI und bewertet Treffer bisher per Cosine Similarity oder Keyword-Fallback.
- `ai_legal_classifier.py`: Klassifiziert Gesetzesänderungen nach Handlungsbedarf, Schweregrad, Impact und empfohlenen Aktionen über LLM-JSON-Responses.
- `risk_calculator.py`: Ergänzt die Klassifikation durch Risikobewertungen und priorisierte Compliance-Einschätzung im bestehenden Backend-Kontext.

## Neue Komponenten
- pgvector: Datenbank-Migration für persistente Knowledge-Embeddings mit ivfflat-Cosine-Index.
- Hybrid-Retrieval: Kombination aus BM25-ähnlichem Keyword-Matching und Embedding-Cosine-Similarity mit Gewichtung 0.4 / 0.6.
- Multi-Label: Erweiterung der Klassifikation um `applicable_laws` und `law_confidence`.
- Benchmark: JSONL-Testset und pytest-kompatible Evaluation für Precision, Recall, F1, Brier Score und ECE.

## Technische Architektur

```text
Input: Gesetzesänderung / Compliance-Text
        |
        v
BM25 Keyword Matching + Embedding Cosine Similarity
        |
        v
Hybrid Retrieval aus Knowledge Vault / pgvector Index
        |
        v
LLM-Klassifikation mit Kontext und JSON-Schema
        |
        v
Multi-Label-Output: action_required, severity, applicable_laws, law_confidence
        |
        v
Benchmark-Logging und wissenschaftliche Validierung
```

## Wissenschaftliche Methodik
Hybrid-Retrieval kombiniert lexikalische Evidenz mit semantischer Ähnlichkeit. Keyword-Matching stellt sicher, dass explizite Gesetzesbegriffe wie DSGVO, TTDSG, BFSG oder NIS2 zuverlässig erkannt werden, während Embeddings semantisch verwandte Fälle erfassen, die keine identischen Begriffe enthalten.

Die Evaluation nutzt manuell annotierte Ground-Truth-Fälle und berechnet Precision, Recall und F1 für Multi-Label-Rechtsgebietszuordnung. Zusätzlich bewertet der Brier Score die Güte probabilistischer Vorhersagen, während Expected Calibration Error (ECE) prüft, ob Modellkonfidenzen mit tatsächlicher Trefferwahrscheinlichkeit übereinstimmen.

Reproduzierbarkeit wird durch versionierte JSONL-Benchmarkdaten, feste Testschwellen, dokumentierte Modellversionen und die Tabelle `classification_benchmark_runs` gewährleistet. Jeder Lauf kann mit Testset-Version, Modellversion und Metriken persistent protokolliert werden.

## Benchmark-Spezifikation
Das Ziel-Benchmark umfasst 100 anwaltlich annotierte Fälle aus deutschem und europäischem Website-Compliance-Recht. Jeder Fall enthält ID, Titel, Beschreibung, erwarteten Handlungsbedarf, Severity, betroffene Gesetze, Risikokategorie, Annotator und Annotierungsdatum.

Sampling-Strategie:
- Abdeckung zentraler Rechtsgebiete: DSGVO, TTDSG, BFSG, DDG, UWG, NIS2, EU AI Act, PAngV.
- Mischung aus positiven und negativen Fällen für `action_required`.
- Ausgewogene Severity-Verteilung über high, medium und low.
- Realistische Website-Szenarien wie Cookie-Consent, Auskunftsrecht, Barrierefreiheit, Impressumspflicht und Auftragsverarbeitung.

## Erwartete Ergebnisse
- Precision ≥ 0.85
- Recall ≥ 0.80
- F1 ≥ 0.82

## EFRE-Innovationsnachweis
Die Komponente adressiert die erste Anwendung von Hybrid-Retrieval auf deutsches Website-Compliance-Recht. Neuartig ist die Kombination aus semantischem Knowledge-Retrieval, gesetzesspezifischer Multi-Label-Klassifikation und kalibrierter wissenschaftlicher Evaluation für operative Compliance-Automatisierung. Dadurch entsteht ein nachvollziehbarer, messbarer und erweiterbarer Forschungsbeitrag für KI-gestützte Rechtsklassifikation in mittelständischen Web-Compliance-Prozessen.

## Zeitplan
3 Monate F&E, Monate 1 bis 3 des Förderzeitraums.

## Aufwandsschätzung
45 Personentage.
