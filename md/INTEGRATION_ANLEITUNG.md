# 🔌 Integration der neuen Features

> ⚠️ **DEPRECATED 2026-05-23:** Diese Anleitung beschreibt die entfernte eRecht24-Integration.
> Die aktuelle Integration nutzt den internen KI-Rechtstexte-Generator (`backend/legal_text_generator.py`).
> Neue Routen: `/api/legal-texts/*` statt `/api/erecht24/*`

## ✅ Status: BEREIT ZUR INTEGRATION

Alle neuen Features sind implementiert und **warten nur auf Aktivierung**. Sie können schrittweise aktiviert werden, ohne bestehenden Code zu überschreiben.

---

## 🎯 Wichtigste Regel

### ℹ️ Interner KI-Generator hat Vorrang bei Rechtstexten

Die neue Integration respektiert diese Hierarchie:

**Rechtstexte (Impressum, Datenschutz):**
1. ✅ **Interner KI-Generator** (knowledge/laws/ + Templates)
2. 🔄 **Bestehende Templates** (Fallback)
3. 🤖 **KI-Generated** (Notfall-Fallback)

**Andere Kategorien (Cookies, Barrierefreiheit):**
1. ✅ **Bestehender Fix Generator** (Priorität)
2. 🔄 **Basic Fallback**

---

## 📦 Was wurde erstellt?

### 1. **Dokumentation** (Fertig, nutzbar)
```
docs/
├── 4-SAEULEN-SYSTEM.md          ← Compliance-Säulen erklärt
├── ARCHITEKTUR-FIX-ENGINE.md    ← Technische Architektur
└── USER-GUIDE-AUTO-FIX.md       ← Anleitung für Endnutzer
```

### 2. **KI-Prompts** (Bereit zur Nutzung)
```
backend/compliance_engine/prompts/
├── impressum_prompt.txt         ← TMG §5 optimiert
├── datenschutz_prompt.txt       ← DSGVO-konform
├── accessibility_prompt.txt     ← WCAG 2.1 Level AA
└── cookie_consent_prompt.txt    ← TTDSG §25
```

### 3. **Neue Module** (Warten auf Aktivierung)
```
backend/compliance_engine/
├── preview_engine.py            ← Side-by-Side Preview
├── deployment_engine.py         ← FTP/SFTP/WordPress/Netlify/Vercel
├── github_integration.py        ← Automatische PR-Erstellung
├── enhanced_fixer.py            ← Integration Layer (NEU!)
└── checks/
    └── aria_checker.py          ← Erweiterte ARIA-Validierung
```

### 4. **Neue API-Routes** (Optional einbinden)
```
backend/
└── enhanced_fix_routes.py       ← Erweiterte Endpoints
```

### 5. **Tests** (Lokal ausführbar)
```
backend/tests/
├── test_barrierefreiheit.py
├── test_cookies.py
├── test_impressum.py
└── test_datenschutz.py
```

---

## 🚀 Schritt-für-Schritt Integration

### OPTION A: Nur Preview aktivieren (empfohlen zum Start)

**1. In `main_production.py` beim Startup hinzufügen:**

```python
# Nach den bestehenden Importen
from compliance_engine.enhanced_fixer import initialize_enhanced_fixer
from enhanced_fix_routes import enhanced_router

# Nach Initialisierung von erecht24_service und fix_generator
enhanced_fixer = initialize_enhanced_fixer(
    # DEPRECATED: erecht24_service=erecht24_service,
    fix_generator=smart_fix_generator,
    enable_preview=True,    # ✅ Preview aktivieren
    enable_deployment=False, # ❌ Deployment noch deaktiviert
    enable_github=False      # ❌ GitHub noch deaktiviert
)

# Enhanced Fixer in enhanced_fix_routes verfügbar machen
import enhanced_fix_routes
enhanced_fix_routes.enhanced_fixer = enhanced_fixer
enhanced_fix_routes.db_pool = db_pool
enhanced_fix_routes.auth_service = firebase_auth

# Router einbinden
app.include_router(enhanced_router)

logger.info("✅ Enhanced Fixer mit Preview aktiviert")
```

**2. Neu starten:**
```bash
docker-compose restart backend
```

**3. Testen:**
```bash
curl http://localhost:8002/api/v2/enhanced-fixes/status
```

---

### OPTION B: Alle Features aktivieren

**1. Alle Features aktivieren:**

```python
enhanced_fixer = initialize_enhanced_fixer(
    # DEPRECATED: erecht24_service=erecht24_service,
    fix_generator=smart_fix_generator,
    enable_preview=True,     # ✅ Preview
    enable_deployment=True,  # ✅ Deployment
    enable_github=True       # ✅ GitHub
)
```

**2. Umgebungsvariablen setzen (falls nötig):**

```bash
# In .env hinzufügen (nur wenn GitHub-Integration gewünscht)
GITHUB_APP_ID=your_app_id
GITHUB_PRIVATE_KEY=your_private_key
```

**3. Neu starten & testen**

---

### OPTION C: Schrittweise aktivieren

Sie können Features einzeln aktivieren:

```python
# Woche 1: Nur Preview
enhanced_fixer = initialize_enhanced_fixer(
    enable_preview=True,
    enable_deployment=False,
    enable_github=False
)

# Woche 2: Preview + Deployment
enhanced_fixer = initialize_enhanced_fixer(
    enable_preview=True,
    enable_deployment=True,  # NEU
    enable_github=False
)

# Woche 3: Alle Features
enhanced_fixer = initialize_enhanced_fixer(
    enable_preview=True,
    enable_deployment=True,
    enable_github=True       # NEU
)
```

---

## 📍 Neue API-Endpoints

Wenn aktiviert, sind folgende Endpoints verfügbar:

### Status prüfen
```bash
GET /api/v2/enhanced-fixes/status
```

**Response:**
```json
{
  "enhanced_fixer_active": true,
  "features": {
    "preview": {"enabled": true, "loaded": true},
    "deployment": {"enabled": false, "loaded": false},
    "github": {"enabled": false, "loaded": false}
  },
  "priority_system": {
    "rechtstexte": {
      "1_priority": "Complyo Internal Generator",
      "2_fallback": "Complyo Templates",
      "3_emergency": "KI-Generated"
    }
  }
}
```

### Fix mit Priorität generieren
```bash
POST /api/v2/enhanced-fixes/generate-with-priority
Authorization: Bearer <token>

{
  "issue_id": "abc123",
  "issue_category": "impressum",
  "company_info": {
    "company_name": "Musterfirma GmbH",
    "address": "Musterstraße 123",
    "postal_code": "12345",
    "city": "Berlin",
    "phone": "+49 30 12345678",
    "email": "info@musterfirma.de"
  },
  "enable_preview": true,
  // "erecht24_project_id": "optional_project_id" // DEPRECATED
}
```

**Response:**
```json
{
  "success": true,
  "fix": {
    "category": "impressum",
    "source": "complyo-internal",
    "content": "...",
    "priority_used": 1,
    "metadata": {
      "rechtssicher": true,
      "risk_reduced": true,
      "provider": "Complyo KI"
    }
  },
  "preview": {
    "preview_id": "abc123def456",
    "preview_url": "/api/v2/previews/abc123def456"
  }
}
```

### Preview ansehen
```bash
GET /api/v2/enhanced-fixes/preview/{preview_id}
Authorization: Bearer <token>
```

→ Gibt HTML-Seite mit Side-by-Side Vergleich zurück

---

## 🧪 Tests ausführen (lokal)

**1. Test-Dependencies installieren:**
```bash
cd /opt/projects/saas-project-2/backend
pip install -r tests/requirements.txt
```

**2. Tests ausführen:**
```bash
# Alle Tests
pytest tests/ -v

# Nur Barrierefreiheit
pytest tests/test_barrierefreiheit.py -v

# Nur Cookies
pytest tests/test_cookies.py -v

# Mit Coverage
pytest tests/ --cov=compliance_engine --cov-report=html
```

**3. Ergebnis prüfen:**
```
tests/test_barrierefreiheit.py::TestARIAChecker::test_button_without_label PASSED
tests/test_barrierefreiheit.py::TestARIAChecker::test_button_with_text_passes PASSED
tests/test_cookies.py::TestCookieDetection::test_no_cookie_banner_detected PASSED
...
====== 40 passed in 2.34s ======
```

---

## ⚠️ Wichtige Hinweise

### Interner Generator hat Vorrang
- Bei Rechtstexten wird IMMER zuerst der interne Generator genutzt
- Fallbacks werden versioniert nachvollziehbar gespeichert
- Interner Generator-Content wird versioniert gespeichert.

### 2. Bestehende Routen unverändert
- Bestehende `/api/v2/fixes/*` Routen bleiben wie sie sind
- Neue Routes unter `/api/v2/enhanced-fixes/*`
- Kein Konflikt möglich

### 3. Feature-Flags
- Alle Features sind optional
- Können einzeln aktiviert/deaktiviert werden
- Keine Auswirkung auf bestehenden Code wenn deaktiviert

### 4. Schrittweises Rollout
- Empfehlung: Zuerst nur Preview aktivieren
- Nach Testing: Deployment & GitHub aktivieren
- Jederzeit rollback möglich (einfach deaktivieren)

---

## 🔄 Rollback (falls nötig)

Falls Probleme auftreten:

**1. Features deaktivieren:**
```python
enhanced_fixer = initialize_enhanced_fixer(
    enable_preview=False,     # Alles deaktivieren
    enable_deployment=False,
    enable_github=False
)
```

**2. Router entfernen:**
```python
# In main_production.py
# app.include_router(enhanced_router)  # Auskommentieren
```

**3. Neu starten:**
```bash
docker-compose restart backend
```

→ System läuft wie vorher, ohne neue Features

---

## 📊 Monitoring

Nach Aktivierung überwachen:

**1. Logs prüfen:**
```bash
docker-compose logs -f backend | grep -i "enhanced"
```

Erwartete Logs:
```
✅ Enhanced Fixer initialisiert (Preview: True, Deploy: False, GitHub: False)
✅ Preview Engine geladen
🔧 Generiere Fix für Kategorie: impressum
🔑 Versuche eRecht24 API für impressum
✅ eRecht24 Content erfolgreich geholt
```

**2. Status-Endpoint nutzen:**
```bash
curl http://localhost:8002/api/v2/enhanced-fixes/status | jq
```

**3. Health-Check:**
```bash
curl http://localhost:8002/api/v2/enhanced-fixes/health
```

---

## 🎓 Next Steps

Nach erfolgreicher Integration:

1. ✅ Dokumentation reviewen (`docs/`)
2. ✅ Tests lokal ausführen
3. ✅ Preview-Feature testen
4. ⏰ Deployment & GitHub nach Bedarf aktivieren
5. 📊 Monitoring-Dashboard aufsetzen (optional)

---

## 🆘 Support

Bei Fragen:
- 📧 Logs checken: `docker-compose logs -f backend`
- 🔍 Status prüfen: `GET /api/v2/enhanced-fixes/status`
- 📚 Dokumentation: `docs/ARCHITEKTUR-FIX-ENGINE.md`

---

**Stand:** November 2025  
**Version:** 1.0  
**Status:** ✅ Ready for Integration

