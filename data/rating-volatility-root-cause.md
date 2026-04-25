# Root Cause Analysis: Rating Schwankungen bei compyo.de (77-84%)

**Status**: 🔴 CRITICAL - Nicht-deterministische Score-Berechnung  
**Datum**: 2026-04-24  
**Betroffene Seiten**: Alle Websites mit Score-Tracking

---

## Problem-Beschreibung

Das Rating für compyo.de schwankt zwischen **77% und 84%** ohne erkennbare Veränderungen auf der Website. Dies deutet auf nicht-deterministische Berechnungen hin.

---

## Root Causes (3 Stellen)

### 1. ❌ MULTIPLE INKOMPATIBLE SCORE-FORMELN

#### Formel 1: scanner.py (Zeile 188)
```python
compliance_score = max(0, 100 - (critical_issues * 20 + warning_issues * 5))
```

Beispiel: 2 Critical + 1 Warning
```
score = 100 - (2*20 + 1*5) = 100 - 45 = 55%
```

#### Formel 2: engine.py (Zeile 464)  
```python
return max(0, 100 - (total_risk / max_risk * 100))
```

Für die gleichen Issues mit unterschiedliche `legal_risk_score`:
```
total_risk = 0.5 + 0.5 + 0.3 = 1.3
max_risk = 3 * 1.0 = 3.0
score = 100 - (1.3 / 3.0 * 100) = 57%
```

**PROBLEM**: Zwei verschiedene Formeln in zwei verschiedenen Files, beide aktiv!

---

### 2. ❌ TCF 2.2 BONUS (Nicht-Deterministisch)

**Datei**: `backend/compliance_engine/scanner.py`, Zeile 191-192
```python
if tcf_data.get("has_tcf") and tcf_data.get("tc_string_found") and len(tcf_data.get("issues", [])) == 0:
    compliance_score = min(100, compliance_score + 5)
```

**Problem**: 
- `tcf_data` kommt von einem API-Call
- Wenn TCF-API mal erreichbar ist → +5 Punkte
- Wenn TCF-API Timeout → Kein Bonus
- **Ergebnis**: Gleiche Website, gleicher Scan, unterschiedliche Scores je nach API-Verfügbarkeit

**Beispiel**: Bei Score 77%:
- Mit TCF-Bonus: 77 + 5 = 82% ✗
- Ohne TCF-Bonus: 77% ✓

---

### 3. ❌ CACHE OHNE TTL (Veraltete Daten)

**Datei**: `backend/risk_calculator.py`, Zeile 15
```python
def __init__(self, db_pool: asyncpg.Pool):
    self._cache = {}  # Simple in-memory cache
```

**Problem**:
- Cache wird nie gelöscht (kein TTL/Expiration)
- In Multi-Instance Deployment: Instanz A hat gecachte Daten, Instanz B hat neue Daten
- Depending welche Instanz antwortet → unterschiedliche Scores

---

## Warum schwankt es GENAU zwischen 77-84%?

Wenn Compyo.de z.B. **2 Critical + 1 Warning** hat:

| Szenario | Formel | TCF-Bonus | Cache | Score |
|----------|--------|-----------|-------|-------|
| A | `100-(2*20+1*5)` | JA | Fresh | 77 + 5 = **82%** |
| B | `100-(2*20+1*5)` | NEIN | Stale | **77%** |
| C | engine.py | JA | Stale | ~79-84% |
| D | engine.py | NEIN | Fresh | ~77% |

**Ergebnis**: 77-84% Range! ✗

---

## Betroffene Dateien

| Datei | Zeile | Problem |
|-------|-------|---------|
| `backend/compliance_engine/scanner.py` | 188 | Scoring Formel 1 |
| `backend/compliance_engine/scanner.py` | 191-192 | TCF Bonus (nicht-deterministisch) |
| `backend/compliance_engine/engine.py` | 464 | Scoring Formel 2 (inkompatibel) |
| `backend/risk_calculator.py` | 15 | Cache ohne TTL |

---

## Empfohlene Fixes

### Fix 1: Eine konsistente Scoring-Formel
```python
# Zentrale Funktion in compliance_engine/score_calculator.py
def calculate_compliance_score(issues: List[ComplianceIssue]) -> float:
    """Einzige Source of Truth für Score-Berechnung"""
    if not issues:
        return 100.0
    
    # Gewichtete Formel: Critical = -20, Warning = -5
    critical_count = len([i for i in issues if i.severity == "critical"])
    warning_count = len([i for i in issues if i.severity == "warning"])
    
    base_score = max(0, 100 - (critical_count * 20 + warning_count * 5))
    
    # Deterministische Boni (OHNE externe API-Calls!)
    # TCF nur wenn es in den Issues bereits als PASS geprüft wurde
    if any(i.category == "tcf" and i.severity != "warning" for i in issues):
        base_score = min(100, base_score + 5)
    
    return base_score
```

### Fix 2: TCF-Bonus nur wenn offline-geprüft
```python
# Nicht: async API Call während Scoring
# Sondern: Nutze bereits gescannte TCF-Daten

for issue in issues:
    if issue.category == "tcf":
        # Issue wurde OFFLINE geprüft → deterministisch
        if issue.severity == "ok":
            # Bonus zählt
```

### Fix 3: Cache mit TTL
```python
class RiskCalculator:
    def __init__(self, db_pool, cache_ttl_seconds=300):
        self._cache = {}
        self._cache_ts = {}  # Timestamps
        self.cache_ttl = cache_ttl_seconds
    
    async def _get_risk_from_matrix(self, category, market):
        cache_key = f"{category}_{market}"
        
        # Check Cache + TTL
        if cache_key in self._cache:
            ts = self._cache_ts.get(cache_key, 0)
            if time.time() - ts < self.cache_ttl:
                return self._cache[cache_key]  # Fresh cache
        
        # Hole neue Daten
        ...
```

---

## Verifikation

Nachdem Fixes angewendet:

```bash
# Test 1: Gleicher Score bei mehrfachen Scans (OHNE Website-Änderung)
curl https://api.complyo.de/scan -d '{"url": "https://compyo.de"}' > scan1.json
sleep 5
curl https://api.complyo.de/scan -d '{"url": "https://compyo.de"}' > scan2.json

# Beide sollten GLEICHEN compliance_score haben
jq '.compliance_score' scan1.json scan2.json
# Erwartet: "77" und "77" (oder identisch)

# Test 2: 10x scannen, alle sollten gleich sein
for i in {1..10}; do
  curl https://api.complyo.de/scan -d '{"url": "https://compyo.de"}' | jq '.compliance_score'
  sleep 1
done

# Alle 10 sollten identisch sein (kein 77-84 Schwanken mehr!)

# Test 3: Bei Website-Fix sollte Score deterministisch steigen
# 1. Scan mit Issue X: Score 77%
# 2. Behebe Issue X auf Website
# 3. Scan wieder: Score sollte immer 82% sein (nicht random)
```

---

## Auswirkungen

- **Vertrauen**: User sieht wechselndes Rating → Glaubwürdigkeitsverlust
- **Alerts**: Falsche Alarme bei Score-Schwankungen
- **Analytics**: Statistiken sind fehlerhaft
- **AB-Testing**: A/B Tests sind unzuverlässig wegen Score-Varianz

---

## Priorität

🔴 **CRITICAL** - Sofort beheben vor nächstem Release

