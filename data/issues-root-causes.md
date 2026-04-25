# Issues & Root Causes (2026-04-24)

## 1. ✅ GELÖST: Refresh verliert Scan-Daten

**Root Cause**: Store hatte keine localStorage-Persistierung

**Lösung**:
- `setCurrentWebsite()` und `setAnalysisData()` speichern jetzt in localStorage
- `DomainHeroSection` versucht beim Mount localStorage zu laden BEVOR API abgefragt wird
- Fallback auf API wenn localStorage leer

**Status**: ✅ In dashboard.ts und DomainHeroSection.tsx implementiert

---

## 2. ❌ NICHT GELÖST: KI generiert nur Platzhalter

**Root Cause**: `OPENROUTER_API_KEY` fehlt in der Umgebung

Der Backend `unified_fix_engine.py` braucht einen gültigen OpenRouter-API-Key um echte KI-Fixes zu generieren. Ohne Key gibt es nur Template-Fallbacks mit `[PLATZHALTER_ERSETZEN]`.

**Zu tun** (DevOps):
```bash
# In der Backend-Umgebung setzen:
export OPENROUTER_API_KEY="sk-or-xxx..."
```

Oder in `.env` oder docker-compose.yml hinzufügen.

**Temporär-Workaround**: Backend könnte bessere Fallbacks generieren statt Platzhalter-Templates.

---

## 3. ❌ NICHT GELÖST: Cookie-Erkennung unvollständig

**Root Cause**: `cookie_check.py` prüft nur auf Banner-Vorhandensein, nicht auf Tracking-Code

Die Website könnte haben:
- Google Analytics
- Facebook Pixel
- Matomo
- Andere Tracking-Services

...aber ohne Cookie-Banner. Der Check würde "Cookies OK" sagen obwohl die Seite Tracking hat.

**Zu tun** (Backend):
1. `cookie_check.py` erweitern: Nach Tracking-Code suchen (GA, Matomo, Pixel etc.)
2. Unterscheiden: "Keine Cookies nötig" vs "Tracking ohne Banner = Verstoß"
3. Im Response `has_tracking_without_banner: true/false` zurückgeben

**Oder** (Frontend):
- Besserer Cookie-Banner-Status im UI:
  - ✅ "Cookies erkannt & Banner gesetzt"
  - ⚠️ "Tracking erkannt, aber kein Banner"
  - ✅ "Keine Cookies auf dieser Seite"
  - ❓ "Konnte nicht ermittelt werden"

---

## Abhängigkeiten

Diese Probleme blockieren sich nicht gegenseitig:
- Problem 1 ist GELÖST ✅
- Problem 2 benötigt DevOps-Umgebungsvariable 🔧
- Problem 3 benötigt Backend-Erweiterung 🔧

**Next Steps**:
1. DevOps: OpenRouter-API-Key konfigurieren
2. Backend: Cookie-Check um Tracking-Erkennung erweitern
3. Teste Refresh: localStorage sollte jetzt funktionieren ✅
