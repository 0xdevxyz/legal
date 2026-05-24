# 🏗️ Complyo Architektur & Fix-Engine

## Überblick

Dieses Dokument beschreibt die technische Architektur der Complyo Compliance-Engine, einschließlich des modularen Scanner-Systems, der autonomen Fix-Engine und der API-Integration.

---

## 📐 System-Architektur

```
┌──────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                       │
│  Dashboard │ Landing Page │ Preview System │ Analytics      │
└────────────┬─────────────────────────────────────────────────┘
             │
             │ HTTP/REST API
             │
┌────────────▼─────────────────────────────────────────────────┐
│                    API Gateway (Nginx)                        │
│            SSL Termination │ Load Balancing                  │
└────────────┬─────────────────────────────────────────────────┘
             │
             │
┌────────────▼─────────────────────────────────────────────────┐
│                   Backend (FastAPI)                           │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Compliance Engine (Core)                     │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │ Scanner  │  │  Fixer   │  │ Preview  │          │   │
│  │  └──────────┘  └──────────┘  └──────────┘          │   │
│  │                                                      │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │    Modulare Check-Systeme (Säulen)          │  │   │
│  │  │  • Barrierefreiheit  • Cookie Compliance    │  │   │
│  │  │  • Rechtstexte       • DSGVO                │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  │                                                      │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │        AI Services & Generators              │  │   │
│  │  │  • OpenRouter/GPT-4  • Vision API           │  │   │
│  │  │  • Code Generator    • Template Engine      │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              API Routes Layer                        │   │
│  │  • public_routes   • fix_routes   • auth_routes    │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────┬──────────────────────────────────┬──────────────┘
             │                                   │
             │                                   │ External APIs
┌────────────▼─────────────┐    ┌──────────────▼──────────────┐
│   PostgreSQL Database    │    │  • OpenRouter (AI)          │
│   • Users  • Scans       │    │  • eRecht24 (Legal Texts)   │
│   • Fixes  • Websites    │    │  • Stripe (Payments)        │
└──────────────────────────┘    └─────────────────────────────┘
```

---

## 🔍 Compliance Engine - Kern-Komponenten

### 1. Scanner-System

**Zweck:** Analysiert Websites auf Compliance-Probleme nach den 4 Säulen.

**Architektur:**
```
ComplianceScanner
├── scanner.py (Hauptklasse)
│   ├── scan_website() - Entry Point
│   ├── _fetch_page() - HTML abrufen
│   └── _enrich_with_erecht24_descriptions() - Anreicherung
│
└── checks/ (Modulare Check-Systeme)
    ├── barrierefreiheit_check.py
    │   ├── check_barrierefreiheit_compliance()
    │   ├── _check_accessibility_widget()
    │   ├── _check_alt_texts_enhanced()
    │   ├── _check_aria_labels()
    │   ├── _check_semantic_html()
    │   ├── _check_keyboard_navigation()
    │   └── _check_color_contrast()
    │
    ├── cookie_check.py
    │   ├── check_cookie_compliance()
    │   └── _check_tracking_scripts()
    │
    ├── impressum_check.py
    │   ├── check_impressum_compliance()
    │   └── _validate_impressum_content()
    │
    └── datenschutz_check.py
        ├── check_datenschutz_compliance()
        └── _validate_privacy_content()
```

**Workflow:**

```python
# 1. Initialisierung
async with ComplianceScanner() as scanner:
    # 2. Website abrufen
    html = await scanner._fetch_page(url)
    soup = BeautifulSoup(html['content'], 'html.parser')
    
    # 3. Alle Checks parallel ausführen
    issues = []
    issues.extend(await check_barrierefreiheit_compliance(url, soup, session))
    issues.extend(await check_impressum_compliance(url, soup, session))
    issues.extend(await check_datenschutz_compliance(url, soup, session))
    issues.extend(await check_cookie_compliance(url, soup, session))
    
    # 4. Anreicherung mit eRecht24-Daten (optional)
    issues = await scanner._enrich_with_erecht24_descriptions(issues)
    
    # 5. Score-Berechnung
    compliance_score = calculate_score(issues)
    
    # 6. Ergebnis zurückgeben
    return {
        "url": url,
        "compliance_score": compliance_score,
        "issues": issues,
        "recommendations": generate_recommendations(issues)
    }
```

**Datenmodell:**

```python
@dataclass
class ComplianceIssue:
    category: str           # "barrierefreiheit", "cookies", "impressum", "datenschutz"
    severity: str           # "critical", "warning", "info"
    title: str              # Kurze Beschreibung
    description: str        # Detaillierte Erklärung
    risk_euro: int          # Geschätztes Bußgeld in €
    recommendation: str     # Handlungsempfehlung
    legal_basis: str        # Rechtsgrundlage (z.B. "WCAG 2.1, BFSG §12")
    auto_fixable: bool      # Kann automatisch behoben werden?
    is_missing: bool        # Hauptelement fehlt komplett?
    
    # Erweiterte Metadaten (optional)
    screenshot_url: Optional[str] = None
    element_html: Optional[str] = None
    fix_code: Optional[str] = None
    suggested_alt: Optional[str] = None
    image_src: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
```

---

### 2. AI Compliance Fixer

**Zweck:** Generiert automatisierte Fixes für erkannte Compliance-Probleme.

**Datei:** `/opt/projects/saas-project-2/backend/compliance_engine/fixer.py`

**Architektur:**

```python
class AIComplianceFixer:
    def __init__(self):
        self.openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
        self.legal_templates = self._load_legal_templates()
    
    async def fix_compliance_issues(
        self, 
        scan_id: str, 
        violations: List[Dict[str, Any]],
        company_info: Dict[str, str] = None
    ) -> AIFixResult:
        """
        Hauptmethode für Fix-Generierung
        """
        fixes_applied = []
        generated_files = {}
        
        # Gruppiere Issues nach Kategorie
        violations_by_category = self._group_violations_by_category(violations)
        
        # Verarbeite jede Kategorie
        for category, category_violations in violations_by_category.items():
            if category in ['impressum', 'datenschutz']:
                fix = await self._generate_legal_text(category, violations, company_info)
            
            elif category in ['cookie-compliance', 'cookies']:
                fix = await self._generate_cookie_banner(violations)
            
            elif category in ['barrierefreiheit', 'accessibility']:
                fix = await self._generate_accessibility_fixes(violations)
            
            else:
                fix = await self._generate_generic_fix(category, violations)
            
            if fix:
                fixes_applied.append(fix)
        
        return AIFixResult(
            scan_id=scan_id,
            total_issues_fixed=len(fixes_applied),
            fixes_applied=fixes_applied,
            generated_files=generated_files
        )
```

**Fix-Typen:**

| Kategorie | Fix-Methode | Technologie | Automatisierung |
|-----------|-------------|-------------|-----------------|
| Impressum | `_generate_legal_text()` | Jinja2 Templates | 70% auto |
| Datenschutz | `_generate_legal_text()` + AI | GPT-4 Enhancement | 80% auto |
| Cookies | `_generate_cookie_banner()` | HTML+JS+CSS | 95% auto |
| Barrierefreiheit | `_generate_accessibility_fixes()` | CSS+JS | 60% auto |
| Generisch | `_generate_generic_fix()` | GPT-4 | 50% auto |

**Template-System:**

```python
# Impressum-Template (vereinfacht)
IMPRESSUM_TEMPLATE = """
# Impressum

## Angaben gemäß § 5 TMG

**Verantwortlich für den Inhalt:**
{company_name}
{address}
{postal_code} {city}

**Kontakt:**
Telefon: {phone}
E-Mail: {email}

{registration_info}

**Umsatzsteuer-Identifikationsnummer:**
{vat_id}
"""

# Verwendung
generated_content = IMPRESSUM_TEMPLATE.format(
    company_name=company_info.get("company_name", "[FIRMENNAME]"),
    address=company_info.get("address", "[ADRESSE]"),
    # ... weitere Felder
)
```

---

### 3. Code Generator

**Zweck:** Generiert Framework-spezifische Code-Snippets für Barrierefreiheits-Fixes.

**Datei:** `/opt/projects/saas-project-2/backend/compliance_engine/code_generator.py`

**Unterstützte Frameworks:**
- React
- Vue
- Angular
- HTML/Vanilla JS

**Beispiel:**

```python
class AccessibilityCodeGenerator:
    def generate_fixes(self, scan_results, framework='html'):
        fixes = {'react': [], 'vue': [], 'html': [], 'css': []}
        
        for issue in scan_results['issues']:
            if 'alt' in issue['title'].lower():
                snippet = self._generate_alt_text_fix(issue, framework)
                fixes[framework].append(snippet)
            
            elif 'kontrast' in issue['title'].lower():
                snippet = self._generate_contrast_fix(issue)
                fixes['css'].append(snippet)
        
        return {
            'code_snippets': fixes,
            'integration_guide': self._generate_integration_guide(fixes, framework)
        }
```

**Generierter Code (React-Beispiel):**

```jsx
// Alt-Text Fix für React
<Image 
  src="/images/hero.jpg" 
  alt="Team-Meeting im modernen Büro" 
/>
```

---

### 4. Hilfs-Module

#### 4.1 Kontrast-Analyzer

**Datei:** `/opt/projects/saas-project-2/backend/compliance_engine/contrast_analyzer.py`

**Funktionen:**
- WCAG 2.1 Kontrast-Berechnung
- Farb-Parsing (Hex, RGB, Named Colors)
- Automatische Farb-Korrektur mit minimaler Abweichung

```python
class ContrastAnalyzer:
    WCAG_AA_NORMAL = 4.5  # Normaler Text
    WCAG_AA_LARGE = 3.0   # Großer Text
    
    def analyze_color_pair(self, foreground, background, text_size='normal'):
        fg_color = self._parse_color(foreground)
        bg_color = self._parse_color(background)
        
        contrast_ratio = self._calculate_contrast(
            fg_color.luminance, 
            bg_color.luminance
        )
        
        required_ratio = self._get_required_ratio(text_size)
        passes = contrast_ratio >= required_ratio
        
        if not passes:
            suggestions = self._generate_suggestions(
                fg_color, bg_color, required_ratio
            )
        
        return {
            'contrast_ratio': round(contrast_ratio, 2),
            'passes': passes,
            'suggestions': suggestions
        }
```

**WCAG-Kontrast-Formel:**

```python
def _calculate_luminance(self, r, g, b):
    """Relative Luminanz nach WCAG"""
    # Normalisieren auf 0-1
    r_srgb = r / 255.0
    g_srgb = g / 255.0
    b_srgb = b / 255.0
    
    # Linearisieren
    def linearize(channel):
        if channel <= 0.03928:
            return channel / 12.92
        else:
            return ((channel + 0.055) / 1.055) ** 2.4
    
    r_linear = linearize(r_srgb)
    g_linear = linearize(g_srgb)
    b_linear = linearize(b_srgb)
    
    # Luminanz berechnen
    return 0.2126 * r_linear + 0.7152 * g_linear + 0.0722 * b_linear

def _calculate_contrast(self, lum1, lum2):
    """Kontrastverhältnis nach WCAG"""
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)
```

#### 4.2 Cookie-Analyzer

**Datei:** `/opt/projects/saas-project-2/backend/compliance_engine/cookie_analyzer.py`

**Funktionen:**
- Tracking-Script-Erkennung (Google Analytics, Facebook Pixel, etc.)
- Cookie-Kategorisierung (necessary, analytics, marketing, preferences)
- Cookie-Banner-Konfiguration generieren

```python
class CookieAnalyzer:
    def analyze_cookies(self, url, html=None, session=None):
        cookies = []
        
        # Analyse von Tracking-Scripts
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            cookies.extend(self._analyze_tracking_scripts(soup))
        
        # Analyse von gesetzten Cookies
        if session and hasattr(session, 'cookies'):
            cookies.extend(self._analyze_session_cookies(session.cookies))
        
        return self._deduplicate(cookies)
    
    def _analyze_tracking_scripts(self, soup):
        cookies = []
        
        # Google Analytics
        if self._has_google_analytics(soup):
            cookies.append({
                'name': '_ga',
                'category': 'analytics',
                'provider': 'Google Analytics',
                'duration': '2 Jahre'
            })
        
        # Facebook Pixel
        if self._has_facebook_pixel(soup):
            cookies.append({
                'name': '_fbp',
                'category': 'marketing',
                'provider': 'Facebook',
                'duration': '3 Monate'
            })
        
        return cookies
```

---

## 🔄 Workflow: Scan → Fix → Deploy

```
┌─────────────┐
│   1. Scan   │  User gibt URL ein
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│  2. ComplianceScanner.scan_website() │
│  • HTML fetchen                      │
│  • Alle 4 Säulen-Checks ausführen   │
│  • Issues sammeln                    │
│  • Score berechnen                   │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  3. Issues in DB speichern           │
│  • scans-Tabelle                     │
│  • Verknüpfung mit User              │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  4. User wählt Issues für Fix aus    │
│  • Frontend zeigt Issues an          │
│  • User klickt "Fix generieren"      │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  5. AIComplianceFixer.fix_issues()   │
│  • Kategorisierung                   │
│  • Template-basiert + AI             │
│  • Code/HTML/CSS generieren          │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  6. Generated Fixes in DB speichern  │
│  • generated_fixes-Tabelle           │
│  • Fix-Counter erhöhen               │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  7. Preview (geplant)                │
│  • Side-by-Side Vergleich            │
│  • Diff-Ansicht                      │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  8. Deployment (geplant)             │
│  • One-Click Deploy                  │
│  • GitHub PR                         │
│  • FTP/SFTP Upload                   │
│  • WordPress Integration             │
└─────────────────────────────────────┘
```

---

## 🌐 API-Endpunkte

### Public Routes (ohne Auth)

**Datei:** `/opt/projects/saas-project-2/backend/public_routes.py`

```python
# POST /api/public/analyze
async def analyze_website_public(request: AnalyzeRequest):
    """
    Führt Quick-Scan für öffentliche Nutzer durch
    - Limitiert auf 10 Issues
    - Kein Deep-Scan
    - Kein Fix-Zugriff
    """
    async with ComplianceScanner() as scanner:
        result = await scanner.scan_website(request.url)
    
    return {
        "url": result["url"],
        "compliance_score": result["compliance_score"],
        "issues": result["issues"][:10],  # Limitiert
        "upgrade_message": "Upgrade für vollständigen Scan"
    }

# POST /api/public/analyze-preview
async def analyze_preview(request: PreviewRequest):
    """
    Generiert Preview ohne vollständigen Scan
    - Mock-Daten
    - Säulen-Aggregation
    """
    return _generate_preview_mock(request.url, risk_calculator)
```

### Authenticated Routes

**Datei:** `/opt/projects/saas-project-2/backend/fix_routes.py`

```python
# POST /api/v2/fixes/generate
async def generate_fix(
    request: FixRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generiert KI-Fix für ein Issue
    - Prüft User-Limits (Freemium Model)
    - Generiert Fix via AIComplianceFixer
    - Speichert in generated_fixes-Tabelle
    - Erhöht fixes_used Counter
    """
    user_id = current_user['user_id']
    plan_type = current_user.get('plan', 'free')
    
    # Limit-Check
    async with db_pool.acquire() as conn:
        user_limits = await conn.fetchrow(
            "SELECT fixes_used, fixes_limit FROM user_limits WHERE user_id = $1",
            user_id
        )
        
        if user_limits['fixes_used'] >= user_limits['fixes_limit']:
            raise HTTPException(status_code=402, detail="Fix-Limit erreicht")
    
    # Fix generieren
    fix_data = await fix_generator.generate_fix(
        issue_id=request.issue_id,
        issue_category=request.issue_category,
        user_id=user_id,
        plan_type=plan_type
    )
    
    # Counter erhöhen
    async with db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE user_limits SET fixes_used = fixes_used + 1 WHERE user_id = $1",
            user_id
        )
    
    return {'success': True, 'fix': fix_data}

# POST /api/v2/fixes/export
async def export_fix(request: ExportRequest):
    """
    Exportiert Fix als HTML/PDF/TXT
    - AI Plan: 10 Exports/Monat
    - Expert Plan: Unbegrenzt
    """
    pass

# GET /api/v2/fixes/history
async def get_fix_history():
    """Gibt Fix-Historie des Users zurück"""
    pass

# GET /api/v2/fixes/limits
async def get_user_limits():
    """Gibt aktuelle Plan-Limits zurück"""
    pass
```

### GitHub Integration Route

```python
# POST /api/v2/fixes/propose-pr
async def propose_pr_via_github(
    request: ProposePRRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Triggert GitHub Actions Workflow für automatische PR-Erstellung
    
    Workflow:
    1. Holt Fix-Daten aus DB
    2. Generiert Unified Diff
    3. Sendet repository_dispatch an GitHub
    4. GitHub Actions erstellt PR mit dem Patch
    """
    # 1. Fix-Daten holen
    async with db_pool.acquire() as conn:
        fix_record = await conn.fetchrow(
            "SELECT * FROM generated_fixes WHERE id = $1 AND user_id = $2",
            request.fix_id, current_user['user_id']
        )
    
    # 2. Patch generieren
    patch = generate_unified_diff(fix_record)
    patch_b64 = base64.b64encode(patch.encode()).decode()
    
    # 3. GitHub Actions triggern
    github_url = f"https://api.github.com/repos/{request.target_repo}/dispatches"
    payload = {
        "event_type": "ai-fix-proposal",
        "client_payload": {
            "title": f"🤖 Fix: {fix_record['issue_category'].title()} Compliance",
            "patch_b64": patch_b64,
            "branch": f"complyo-fix-{request.fix_id}"
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(github_url, json=payload, headers=headers)
    
    return {"success": True, "branch": f"complyo-fix-{request.fix_id}"}
```

---

## 🗄️ Datenbankschema

### Relevante Tabellen

```sql
-- Users mit Limits
CREATE TABLE user_limits (
    user_id UUID PRIMARY KEY,
    plan_type VARCHAR(50) DEFAULT 'free',
    fixes_used INT DEFAULT 0,
    fixes_limit INT DEFAULT 1,
    websites_count INT DEFAULT 0,
    websites_max INT DEFAULT 1,
    exports_this_month INT DEFAULT 0,
    exports_max INT DEFAULT 10,
    fix_started BOOLEAN DEFAULT FALSE,
    money_back_eligible BOOLEAN DEFAULT TRUE,
    subscription_start TIMESTAMP
);

-- Scan-Resultate
CREATE TABLE scans (
    scan_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    website_id UUID REFERENCES websites(id),
    url TEXT NOT NULL,
    scan_data JSONB NOT NULL,  -- Vollständige Issues
    compliance_score INT,
    critical_issues INT,
    warning_issues INT,
    total_issues INT,
    scan_timestamp TIMESTAMP DEFAULT NOW()
);

-- Generierte Fixes
CREATE TABLE generated_fixes (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    issue_id TEXT NOT NULL,
    issue_category VARCHAR(50) NOT NULL,
    fix_type VARCHAR(50) NOT NULL,  -- 'code_snippet', 'document', 'template'
    plan_type VARCHAR(50),
    generated_at TIMESTAMP DEFAULT NOW(),
    exported BOOLEAN DEFAULT FALSE,
    exported_at TIMESTAMP,
    export_format VARCHAR(20)
);

-- Websites
CREATE TABLE websites (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    url TEXT NOT NULL,
    domain TEXT,
    last_scan_id UUID REFERENCES scans(scan_id),
    last_scan_timestamp TIMESTAMP,
    last_compliance_score INT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🔐 Authentifizierung & Autorisierung

### Firebase Auth Integration

**Datei:** `/opt/projects/saas-project-2/backend/firebase_auth.py`

```python
class FirebaseAuth:
    def __init__(self):
        self.firebase_credentials = json.loads(
            os.environ.get('FIREBASE_SERVICE_ACCOUNT_KEY', '{}')
        )
        firebase_admin.initialize_app(
            credentials.Certificate(self.firebase_credentials)
        )
    
    async def verify_token(self, id_token: str) -> Dict[str, Any]:
        """
        Verifiziert Firebase ID Token
        Returns: User-Daten (uid, email, etc.)
        """
        try:
            decoded_token = auth.verify_id_token(id_token)
            return {
                'user_id': decoded_token['uid'],
                'email': decoded_token.get('email'),
                'email_verified': decoded_token.get('email_verified', False)
            }
        except Exception as e:
            raise HTTPException(status_code=401, detail="Invalid token")
```

### Auth Middleware

```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Dependency für geschützte Routen"""
    token = credentials.credentials
    user_data = auth_service.verify_token(token)
    
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return user_data
```

---

## 🧪 Testing-Architektur

### Test-Struktur

```
backend/tests/
├── test_barrierefreiheit.py    # Unit-Tests für Säule 1
├── test_cookies.py              # Unit-Tests für Säule 2
├── test_impressum.py            # Unit-Tests für Säule 3
├── test_datenschutz.py          # Unit-Tests für Säule 4
├── test_scanner.py              # Integration-Tests Scanner
├── test_fixer.py                # Integration-Tests Fixer
├── test_api.py                  # API-Endpunkt-Tests
└── fixtures/                    # Mock-HTML-Daten
    ├── compliant_website.html
    ├── non_compliant_website.html
    └── partial_compliant_website.html
```

### Beispiel Unit-Test

```python
import pytest
from compliance_engine.checks.barrierefreiheit_check import (
    check_barrierefreiheit_compliance
)
from bs4 import BeautifulSoup

@pytest.mark.asyncio
async def test_accessibility_widget_detection():
    """Test: Erkennt fehlendes Accessibility-Widget"""
    
    # Mock-HTML ohne Widget
    html = """
    <html>
    <body>
        <h1>Test</h1>
        <p>Kein Accessibility-Widget vorhanden</p>
    </body>
    </html>
    """
    
    soup = BeautifulSoup(html, 'html.parser')
    issues = await check_barrierefreiheit_compliance(
        url="https://test.com",
        soup=soup,
        session=None
    )
    
    # Assert: Widget-Issue wurde erkannt
    assert len(issues) > 0
    widget_issue = next(
        (i for i in issues if 'Widget' in i['title']), None
    )
    assert widget_issue is not None
    assert widget_issue['severity'] == 'critical'
    assert widget_issue['auto_fixable'] == True

@pytest.mark.asyncio
async def test_alt_text_detection():
    """Test: Erkennt Bilder ohne Alt-Text"""
    
    html = """
    <html>
    <body>
        <img src="test.jpg">
        <img src="test2.jpg" alt="">
        <img src="test3.jpg" alt="Guter Alt-Text">
    </body>
    </html>
    """
    
    soup = BeautifulSoup(html, 'html.parser')
    issues = await check_barrierefreiheit_compliance(
        url="https://test.com", soup=soup, session=None
    )
    
    # 2 Bilder ohne Alt-Text sollten erkannt werden
    alt_issues = [i for i in issues if 'Alt-Text' in i['title']]
    assert len(alt_issues) > 0
```

---

## 🚀 Performance-Optimierungen

### 1. Parallele Check-Ausführung

```python
# Alle Säulen-Checks parallel ausführen
import asyncio

async def scan_website(self, url: str):
    soup = BeautifulSoup(html, 'html.parser')
    
    # Parallel execution
    results = await asyncio.gather(
        check_barrierefreiheit_compliance(url, soup, self.session),
        check_impressum_compliance(url, soup, self.session),
        check_datenschutz_compliance(url, soup, self.session),
        check_cookie_compliance(url, soup, self.session)
    )
    
    # Flatten results
    issues = [issue for result in results for issue in result]
    return issues
```

### 2. Caching

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def get_erecht24_description(category: str):
    """Cache für eRecht24-API-Calls"""
    return erecht24_service.get_compliance_description(category)

def cache_key(url: str) -> str:
    """Generiert Cache-Key für Scan-Resultate"""
    return hashlib.md5(url.encode()).hexdigest()
```

### 3. Database Connection Pooling

```python
# In main_production.py
db_pool = await asyncpg.create_pool(
    dsn=DATABASE_URL,
    min_size=10,
    max_size=20,
    command_timeout=60
)
```

---

## 📊 Monitoring & Logging

### Logging-Konfiguration

```python
import logging

# Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Usage in Scanner
logger.info(f"✅ Scan completed: {url}, Score: {compliance_score}")
logger.warning(f"⚠️ eRecht24 enrichment failed: {error}")
logger.error(f"❌ Scan failed: {url}, Error: {error}")
```

### Health-Check Endpunkte

```python
@app.get("/health")
async def health_check():
    """System Health Check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": await check_database_connection(),
        "redis": await check_redis_connection(),
        "openrouter": check_openrouter_api_key()
    }

@fix_router.get("/health")
async def fix_service_health():
    """Fix-Service Health Check"""
    return {
        "status": "healthy",
        "service": "fix-generator",
        "fix_generator_initialized": fix_generator is not None,
        "db_pool_initialized": db_pool is not None
    }
```

---

## 🔄 Deployment-Architektur

### Docker Compose Setup

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8002:8002"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_HOST=${REDIS_HOST}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
    depends_on:
      - postgres
      - redis
  
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
  
  gateway:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./gateway/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
```

---

## 🎯 Zusammenfassung

### Kernkomponenten

| Komponente | Zweck | Technologie | Status |
|------------|-------|-------------|--------|
| ComplianceScanner | Website-Analyse | Python/AsyncIO | ✅ Produktiv |
| AIComplianceFixer | Fix-Generierung | OpenRouter/GPT-4 | ✅ Produktiv |
| Code Generator | Framework-Snippets | Jinja2/Templates | ✅ Produktiv |
| Cookie Analyzer | Cookie-Erkennung | BeautifulSoup | ✅ Produktiv |
| Contrast Analyzer | WCAG-Kontraste | Python/Colorsys | ✅ Produktiv |
| Preview Engine | Fix-Vorschau | - | 🔄 Geplant |
| Deployment Engine | One-Click Deploy | - | 🔄 Geplant |

### API-Endpunkte

| Endpunkt | Methode | Auth | Zweck |
|----------|---------|------|-------|
| `/api/public/analyze` | POST | ❌ | Quick-Scan (limitiert) |
| `/api/v2/fixes/generate` | POST | ✅ | Fix generieren |
| `/api/v2/fixes/export` | POST | ✅ | Fix exportieren |
| `/api/v2/fixes/history` | GET | ✅ | Fix-Historie |
| `/api/v2/fixes/propose-pr` | POST | ✅ | GitHub PR erstellen |

### Datenfluss

```
User-Input (URL)
    ↓
ComplianceScanner
    ↓
4 Säulen-Checks (parallel)
    ↓
Issues sammeln & speichern
    ↓
User wählt Issues aus
    ↓
AIComplianceFixer
    ↓
Fixes generieren & speichern
    ↓
(Optional) Preview/Deploy
```

---

**Letzte Aktualisierung:** November 2025  
**Version:** 2.0  
**Status:** Produktiv

