# Plan: Cookie-Erkennung wasserdicht machen

## Status Quo
`backend/compliance_engine/checks/cookie_check.py`:
- ✅ Erkennt Cookie-Banner (CookieConsent.js, Didomi, Klaro, etc.)
- ✅ Erkennt Cookie-Service-Links
- ❌ Erkennt NICHT: Tracking ohne Banner (GA, Matomo, Pixel, etc.)

**Problem**: Website könnte GA + Matomo haben, aber ohne Banner → wird als "OK" gemeldet

---

## Plan: Vierstufige Cookie-Intelligenz

### Phase 1: Tracking-Erkennung (Backend)
**Datei**: `backend/compliance_engine/checks/cookie_check.py`

Hinzufügen:
```python
TRACKING_PATTERNS = {
    'google_analytics': [
        r'google-analytics',
        r'googletagmanager\.com',
        r'ga\.js',
        r'gtag\(',
        r'_gaq\.push'
    ],
    'matomo': [
        r'matomo\.js',
        r'piwik\.js',
        r'pk\.min\.js',
        r'/matomo/',
        r'/piwik/'
    ],
    'facebook_pixel': [
        r'facebook\.com/tr',
        r'fbq\(',
        r'facebook-pixel'
    ],
    'hotjar': [
        r'hjid\.js',
        r'heatmap\.js',
        r'hotjar\.js'
    ],
    'mixpanel': [
        r'mixpanel\.com',
        r'mixpanel\.js'
    ],
    'segment': [
        r'segment\.com',
        r'analytics\.js',
        r'segment\.com/analytics'
    ],
    'amplitude': [
        r'amplitude\.com',
        r'amplitude\.js'
    ]
}

def _detect_tracking_services(html: str, scripts: List) -> Dict[str, bool]:
    """Erkennt Tracking-Services"""
    html_lower = html.lower()
    detected = {}
    
    for service, patterns in TRACKING_PATTERNS.items():
        detected[service] = any(
            bool(re.search(p, html_lower, re.IGNORECASE)) 
            for p in patterns
        )
    
    return {k: v for k, v in detected.items() if v}
```

### Phase 2: Kategorisierter Response
**Output-Struktur**:
```python
{
    "has_cookie_banner": True/False,
    "has_cookie_services": ["Didomi", "Klaro"],
    "tracking_services": {
        "google_analytics": True,
        "matomo": False,
        "facebook_pixel": True
    },
    "requires_banner": True,  # Neue Logik
    "compliance_status": "...",  # Siehe unten
    "recommendations": [...]
}
```

### Phase 3: Intelligente Compliance-Logik
```python
def determine_compliance_status(has_banner, tracking_services):
    """
    ✅ COMPLIANT: 
        - Keine Tracking-Services, ODER
        - Hat Banner + Tracking-Services erkannt
    
    ⚠️ WARNING:
        - Hat Tracking OHNE Banner (größter DSGVO-Verstoß)
    
    ℹ️ INFO:
        - Keine Tracking-Services erkannt
        - Optional: AGB hinzufügen empfohlen
    """
    has_tracking = bool(tracking_services)
    
    if not has_tracking:
        return "no_tracking", 0  # Kein Problem
    
    if has_tracking and has_banner:
        return "tracking_with_banner", 0  # OK
    
    if has_tracking and not has_banner:
        return "tracking_without_banner", 85  # DSGVO-Verstoß!
```

### Phase 4: Frontend-Anzeige
**Komponente**: `ComplianceIssueCard.tsx`

Für Cookie-Issues:
```tsx
// Wenn tracking_without_banner:
<div className="bg-red-50 border border-red-300 rounded-lg p-4 mb-4">
  <h4 className="font-bold text-red-800">🚨 Kritisch: Tracking ohne Cookie-Banner</h4>
  <p className="text-sm text-red-700 mt-2">
    Ihre Website verwendet folgende Tracking-Services ohne Cookie-Banner:
  </p>
  <ul className="list-disc list-inside mt-2 text-sm text-red-700">
    {issue.detected_tracking_services.map(service => (
      <li key={service}>{service}</li>
    ))}
  </ul>
  <p className="text-xs text-red-600 mt-3 font-semibold">
    ⚠️ Verstoß gegen DSGVO Art. 7 (Einwilligung)
    Bußgeld bis zu 20.000.000 € möglich!
  </p>
</div>

// Wenn no_tracking:
<div className="bg-green-50 border border-green-300 rounded-lg p-4 mb-4">
  <h4 className="font-bold text-green-800">✅ Keine Tracking-Services erkannt</h4>
  <p className="text-sm text-green-700">
    Ihre Website verwendet kein Cookie-Tracking. 
    Ein Banner ist nicht erforderlich.
  </p>
</div>
```

---

## Implementierungs-Schritte

### 1. Backend erweitern (cookie_check.py)
- [ ] `TRACKING_PATTERNS` dict hinzufügen
- [ ] `_detect_tracking_services()` implementieren
- [ ] `check_cookie_compliance()` um `tracking_services` erweitern
- [ ] `determine_compliance_status()` hinzufügen
- [ ] Return-Schema aktualisieren
- [ ] Tests schreiben

**Datei**: `/home/clawd/saas/legal/backend/compliance_engine/checks/cookie_check.py`

### 2. API-Response anpassen (scanner.py oder engine.py)
- [ ] Cookie-Issue mit `tracking_services`, `compliance_status`, `recommendations` erweitern
- [ ] `risk_euro` neu berechnen basierend auf Compliance-Status

**Datei**: `/home/clawd/saas/legal/backend/compliance_engine/engine.py`

### 3. Frontend-UI verbessern (ComplianceIssueCard.tsx)
- [ ] Spezielle Rendering-Logik für Cookie-Issues
- [ ] 3 Szenarien: No Tracking / Tracking with Banner / Tracking without Banner
- [ ] Badges + Farben + Risiko-Anzeigen
- [ ] Fix-Button Texte anpassen

**Datei**: `/home/clawd/saas/legal/dashboard-react/src/components/dashboard/ComplianceIssueCard.tsx`

### 4. Typen aktualisieren (types/api.ts)
- [ ] `ComplianceIssue` um `detected_tracking_services`, `compliance_status` erweitern

**Datei**: `/home/clawd/saas/legal/dashboard-react/src/types/api.ts`

---

## Nutzen

| Szenario | Vorher | Nachher |
|----------|--------|---------|
| Website mit GA aber ohne Banner | "Cookie-Compliance OK" ❌ | "DSGVO-Verstoß! Risk: 85" 🚨 |
| Website ohne Tracking | "Cookie-Compliance Issue" ❌ | "Keine Tracking-Services. Banner nicht erforderlich" ✅ |
| Website mit Banner + GA | "Cookie-Compliance OK" ✅ | "Cookie-Compliance OK + Google Analytics erkannt" ✅ |
| Website mit Cookie-Service | "Cookie-Compliance OK" ✅ | "Didomi + Facebook Pixel erkannt. Compliant" ✅ |

---

## Priorität

**Hoch**: Tracking-Erkennung ist ein kritischer DSGVO-Punkt. Aktuell werden die schlimmsten Verstöße nicht erkannt.

**Zeitaufwand**: ~3-4 Stunden (Backend + Frontend + Tests)
