# AP3: Adaptive Compliance-Remediation — Closed-Loop-Lernsystem

## Executive Summary

Ein geschlossener Lern-Kreislauf für Compliance-Remediation ist eine Forschungsherausforderung, weil das System nicht nur einzelne Verstöße erkennen muss, sondern aus realem Nutzerfeedback, Re-Scans und Fix-Ergebnissen belastbare Verbesserungen ableiten soll. Compliance-Kontexte verändern sich durch neue Rechtslage, technische Website-Änderungen und unterschiedliche Nutzerentscheidungen. Deshalb reicht eine statische KI-Klassifikation nicht aus: Das System muss laufend messen, wann Klassifikationen nicht akzeptiert werden, wann Fixes nach einem Re-Scan tatsächlich wirken und ob sich die Verteilung der Fälle über Zeit verschiebt.

## IST-Stand

### ai_feedback_learning.py

Die bestehende Datei `/home/clawd/saas/legal/backend/ai_feedback_learning.py` enthält bereits ein selbstlernendes Feedback-System für KI-Klassifizierungen. Vorhanden sind:

- `AIFeedbackLearning` als zentrale Klasse für Feedback-Aufzeichnung und Auswertung
- Speicherung von Feedback-Events in `ai_classification_feedback`
- Performance-Analyse einzelner Klassifizierungen über `analyze_classification_performance`
- Aggregierte Lern-Erkenntnisse über `get_learning_insights`
- Optimierungsvorschläge über `get_optimization_suggestions`
- Basis-Learning-Cycle über `_run_learning_cycle`

### FeedbackType

`FeedbackType` bildet explizites und implizites Feedback ab:

- `implicit_click`
- `implicit_ignore`
- `implicit_dismiss`
- `explicit_helpful`
- `explicit_not_helpful`
- `explicit_wrong`
- `action_completed`
- `action_skipped`

Damit existiert bereits die Grundlage, um Nutzerverhalten als Signal für Modellqualität und Remediation-Wirksamkeit zu verwenden.

### reclassify_with_feedback

Der gelesene Klassifizierer `/home/clawd/saas/legal/backend/ai_legal_classifier.py` stellt die KI-basierte Klassifikation von Gesetzesänderungen bereit. Die ersten 200 Zeilen zeigen insbesondere:

- Datenmodelle für Aktionen, Normreferenzen, Faktoren und Klassifikationsergebnisse
- `AILegalClassifier` mit Prompt-Aufbau, KI-Aufruf und Response-Parsing
- Fallback-Logik bei Klassifizierungsfehlern

Die Feedback-Daten können damit genutzt werden, um künftige Klassifikationen und Prompt-Versionen gezielter zu bewerten und anzupassen.

### A/B-Test-Infrastruktur

Im Projekt existiert bereits A/B-Test-Infrastruktur, unter anderem über Migrations- und Routing-Dateien wie `ab_testing_tables.sql` und `ab_test_routes.py`. AP3 ergänzt diese Grundlage um Prompt-Versioning und Performance-Messung, sodass Prompt-Varianten nicht nur ausgespielt, sondern auch anhand von Outcome- und Feedback-Signalen bewertet werden können.

## Lücken-Analyse

Vor AP3 fehlten für ein belastbares Closed-Loop-Lernsystem insbesondere folgende Bausteine:

1. **Outcome-Pipeline**
   - Feedback zeigte, ob Nutzer eine Klassifikation hilfreich fanden.
   - Es fehlte aber eine strukturierte Messung, ob ein ausgerollter Fix nach Re-Scan tatsächlich die Compliance verbessert.

2. **Drift-Detection**
   - Das System konnte noch nicht erkennen, ob sich die Verteilung der Klassifikationen über Zeit signifikant verändert.
   - Ohne Drift-Erkennung besteht das Risiko, dass alte Prompt- oder Klassifikationsannahmen unbemerkt schlechter werden.

3. **Prompt-Versioning**
   - Prompt-Templates waren nicht versioniert messbar.
   - Es fehlte eine DB-Struktur, um aktive/baseline Prompt-Versionen, Performance-Scores und A/B-Test-Bezüge dauerhaft zu speichern.

## Implementierte Lösung

### Feedback-Trigger-Mechanismus

In `/home/clawd/saas/legal/backend/ai_feedback_learning.py` wurde `_trigger_learning_if_needed()` vollständig ausimplementiert.

Der neue Mechanismus:

- zählt negative Feedbacks seit dem letzten relevanten Drift-/Learning-Zeitpunkt
- nutzt einen Schwellwert von 10 negativen Feedbacks
- triggert bei Erreichen des Schwellwerts eine Prompt-Adaption
- protokolliert, wenn noch kein Trigger ausgelöst wird

Negative Feedbacktypen im neuen Trigger:

- `rejected`
- `action_ignored`
- `incorrect`

### Prompt-Versioning-System

Die Migration `/home/clawd/saas/legal/backend/migrations/add_prompt_versioning.sql` erstellt die Tabelle `prompt_versions`.

Wichtige Felder:

- `prompt_key`
- `version_tag`
- `template`
- `performance_score`
- `sample_count`
- `positive_rate`
- `is_active`
- `is_baseline`
- `ab_test_id`
- `activated_at`
- `deactivated_at`
- `notes`

Damit können Prompt-Versionen aktiv verwaltet, bewertet und mit A/B-Tests verknüpft werden.

### Drift-Detection

Der neue Cronjob `/home/clawd/saas/legal/backend/cronjobs/drift_detector.py` implementiert eine wöchentliche Drift-Erkennung.

Kernlogik:

- aktuelle 7-Tage-Verteilung der `risk_category` aus `ai_compliance_logs`
- 30-Tage-Baseline mit 7 Tagen Offset
- Berechnung der KL-Divergenz `KL(P||Q)`
- Drift-Alarm bei `KL > 0.1`
- Speicherung in `classification_drift_log`

Damit entsteht ein messbarer Frühindikator für Verteilungsverschiebungen in Klassifikationen.

### Fix-Outcome-Tracking

Die Migration erstellt zusätzlich `fix_outcomes`.

Die Tabelle speichert:

- `fix_job_id`
- `website_id`
- `fix_template_id`
- `fix_type`
- `deployed_at`
- `rescan_at`
- `passed_rescan`
- `score_before`
- `score_after`
- automatisch berechnetes `score_delta`
- `user_accepted`

Damit kann die tatsächliche Wirkung von Remediation-Maßnahmen nachgewiesen werden.

### Modell-Performance über Zeit

Die View `model_performance_timeline` aggregiert:

- Anzahl Fixes pro Woche
- Re-Scan-Pass-Rate
- durchschnittliche Score-Verbesserung
- genutzte aktive Prompt-Versionen

Damit werden Modell- und Fix-Performance langfristig vergleichbar.

## MLOps-Architektur

```text
User Feedback → Feedback-DB → Trigger-Check → Prompt-Adaption
     ↑                                               ↓
Fix-Outcome ←── Re-Scan ←── Deployment ←── Neue Klassifikation
```

## Messbarkeit: Nachweis der Modellverbesserung

Modellverbesserung wird über mehrere Metriken nachweisbar:

1. **KL-Divergenz-Verlauf**
   - zeigt, ob sich Klassifikationsverteilungen stabilisieren oder driften
   - Drift-Events können mit Prompt-Versionen und Rechtsänderungen korreliert werden

2. **Acceptance-Rate-Trend**
   - positive vs. negative Feedbacks je Prompt-Key und Version
   - steigende Akzeptanz deutet auf bessere Klassifikationsqualität hin

3. **Re-Scan-Pass-Rate**
   - Anteil der Fixes, die nach Deployment im Re-Scan bestehen
   - direkter technischer Wirkungsnachweis

4. **Score-Delta**
   - Differenz zwischen Compliance-Score vor und nach Fix
   - quantifiziert Remediation-Verbesserung

5. **Prompt-Performance-Score**
   - automatische Abwertung aktiver Prompt-Versionen bei hoher Ablehnungsrate
   - Grundlage für Prompt-Review und spätere A/B-Test-Entscheidungen

## EFRE-Anforderung

Für einen belastbaren Nachweis werden mindestens 3 Monate Echtdaten benötigt. Deshalb ist ein früher Start der Datenerfassung entscheidend. Je früher Feedback-, Drift- und Outcome-Daten gesammelt werden, desto besser lassen sich im EFRE-Kontext Forschungsfortschritt, Wirksamkeit und technische Neuheit belegen.

## Zeitplan

Zeitraum: Monate 2-9, laufend

Geschätzter Aufwand: 35 Personentage

Geplante Arbeitspakete:

- Monat 2: Prompt-Versioning und Outcome-Schema aktivieren
- Monate 3-4: Drift-Detection regelmäßig ausführen und Datenbasis aufbauen
- Monate 4-6: Feedback-Trigger auswerten und Prompt-Adaption operationalisieren
- Monate 6-8: A/B-Auswertung und Performance-Vergleich über Zeit
- Monat 9: Evaluation, EFRE-Nachweis und Ergebnisaufbereitung

## Abgrenzung zu RLHF

Der implementierte Ansatz ist kein vollständiges RLHF-System. Für ein kleines Team ist der gewählte Closed-Loop-Ansatz praktikabler, weil:

- keine große Menge annotierter Trainingsdaten benötigt wird
- keine eigene Modell-Feinabstimmung erforderlich ist
- bestehende LLM-Prompts versioniert und bewertet werden können
- Feedback und Outcome-Metriken direkt aus dem Produktbetrieb entstehen
- Verbesserungen über Prompt-Adaption, A/B-Tests und Monitoring inkrementell erfolgen

Damit entsteht ein realistisch betreibbares, messbares Lernsystem, ohne die Komplexität und Kosten eines vollständigen RLHF-Trainingsprozesses.
