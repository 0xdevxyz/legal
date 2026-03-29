# Testing Patterns

**Analysis Date:** 2026-03-29

## Test Framework

### Backend (Python)

**Runner:**
- pytest with pytest-asyncio for async tests
- Config: no dedicated `pytest.ini` or `pyproject.toml` found — pytest run directly from `backend/tests/`
- Requirements: `backend/tests/requirements.txt`

**Key Packages:**
- `pytest>=7.4.0`
- `pytest-asyncio>=0.21.0`
- `pytest-cov>=4.1.0`
- `pytest-mock>=3.11.1`
- `responses>=0.23.0` (HTTP mocking)
- `faker>=19.0.0`
- `beautifulsoup4>=4.12.0` (HTML parsing for compliance tests)
- `pytest-flake8`, `pytest-black`, `pytest-mypy` (code quality checks)

**Run Commands:**
```bash
cd backend/tests
pytest                     # Run all tests
pytest test_auth.py        # Run specific test file
pytest --cov=..            # Coverage report
pytest -v                  # Verbose output
```

### Frontend (React)

**Runner:**
- No test framework detected for `dashboard-react` or `landing-react`
- No `jest.config.*`, `vitest.config.*`, or test files exist under `dashboard-react/src/` or `landing-react/src/`
- TypeScript type-checking available via: `npm run type-check` (runs `tsc --noEmit`)

### get-shit-done tooling (internal)

**Runner:**
- Vitest — config at `get-shit-done/vitest.config.ts` and `get-shit-done/sdk/vitest.config.ts`
- Test files: `get-shit-done/tests/*.test.cjs` (CommonJS format)
- 40+ test files covering internal CLI tool behavior

---

## Test File Organization

**Location (Backend):**
- All backend tests in `backend/tests/` directory (separate from source)
- Not co-located with source modules

**Naming (Backend):**
- `test_<feature>.py` pattern: `test_auth.py`, `test_barrierefreiheit.py`, `test_cookies.py`, `test_tcf_compliance.py`
- Test classes: `Test<Domain>` (e.g., `TestARIAChecker`, `TestTCFDetection`, `TestCookieDetection`)
- Test methods: `test_<behavior>_<condition>` (e.g., `test_button_without_label`, `test_detect_cookiebot_tcf`)

**Structure:**
```
backend/
└── tests/
    ├── __init__.py
    ├── requirements.txt
    ├── test_auth.py
    ├── test_barrierefreiheit.py
    ├── test_bfsg_features.py
    ├── test_cookies.py
    ├── test_datenschutz.py
    ├── test_i18n.py
    ├── test_impressum.py
    └── test_tcf_compliance.py
```

---

## Test Structure

**Class-based organization** (most common pattern):
```python
class TestARIAChecker:
    """Tests für ARIA-Compliance-Checks"""

    def setup_method(self):
        """Setup für jeden Test"""
        self.checker = ARIAChecker()

    def test_button_without_label(self):
        """Test: Button ohne Label wird erkannt"""
        html = """<html><body><button></button></body></html>"""
        soup = BeautifulSoup(html, 'html.parser')
        issues = self.checker.check_aria_compliance(soup, 'https://test.com')
        button_issues = [i for i in issues if 'BUTTON' in i['title']]
        assert len(button_issues) > 0
        assert button_issues[0]['severity'] == 'warning'
```

**Module-level function tests** (also used, especially in `test_bfsg_features.py`):
```python
def test_feature_engine_categorization():
    """Test: Feature-Engine kategorisiert Issues korrekt"""
    from compliance_engine.feature_engine import feature_engine, FeatureId, Difficulty
    # ... arrange, act, assert
    assert result.feature_id == FeatureId.ALT_TEXT
```

**Async tests:**
```python
class TestTCFDetection:
    @pytest.mark.asyncio
    async def test_detect_cookiebot_tcf(self):
        html = """..."""
        soup = BeautifulSoup(html, 'html.parser')
        result = await check_tcf_compliance("https://example.com", soup, html)
        assert result["has_tcf"] == True
        assert result["cmp_name"] == "Cookiebot"
```

**Patterns:**
- `setup_method(self)` for per-test instance setup (not `setUp` — pytest style)
- No `teardown_method` usage observed
- HTML fixtures constructed inline as multiline strings
- Assertions use plain `assert` (not `assertEqual`) — pytest style

---

## Mocking

**Framework:** `unittest.mock` (standard library) — used in `test_auth.py`

**Patterns:**
```python
from unittest.mock import AsyncMock, MagicMock, patch

class TestAuthService:
    def test_create_access_token(self):
        mock_pool = MagicMock()
        with patch.object(AuthService, '__init__', lambda self, pool: None):
            service = AuthService.__new__(AuthService)
            service.jwt_secret = "test-secret"
            service.jwt_issuer = "https://complyo.tech"
            service.jwt_audience = "complyo-api"
            service.access_token_expire = 60
            token = service.create_access_token("user-123")
            assert token is not None
```

**Environment variable setup (in `backend/tests/__init__.py`):**
```python
import os
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")
```

**What is mocked:**
- Database pool (`MagicMock` substituting `asyncpg.Pool`)
- Service `__init__` when only testing pure logic methods
- Environment variables via `os.environ.setdefault` at module load

**What is NOT mocked:**
- HTML parsing logic (real `BeautifulSoup` used with inline HTML strings)
- Compliance engine classes (instantiated directly: `ARIAChecker()`, `check_tcf_compliance(...)`)
- JWT operations (real `jwt` library used in auth tests)

---

## Fixtures and Factories

**Test Data:**
- HTML fixtures defined as inline multiline strings in each test method — no shared fixtures file
- No factory libraries detected (Faker is in requirements but not observed in test files)
- Direct class instantiation for service objects in `setup_method`

**Example inline HTML fixture pattern:**
```python
html = """
<html>
<body>
    <button aria-label="Menü öffnen">
        <svg>...</svg>
    </button>
</body>
</html>
"""
soup = BeautifulSoup(html, 'html.parser')
```

**Location:**
- No separate fixtures directory; all fixtures are inline within test classes/functions
- `backend/tests/__init__.py` handles environment variable setup as global test precondition

---

## Coverage

**Requirements:** `pytest-cov>=4.1.0` installed — no enforced threshold configured

**View Coverage:**
```bash
pytest --cov=.. --cov-report=html
```

**Current coverage assessment:**
- Backend: compliance engine checks (ARIA, TCF, cookie detection, impressum, datenschutz) have targeted unit tests
- Backend: auth service tested for JWT token creation/verification
- Frontend: zero test coverage — no test files exist in `dashboard-react/` or `landing-react/`

---

## Test Types

**Unit Tests (Backend):**
- Scope: individual compliance check functions and service methods
- Approach: instantiate checker class, pass HTML soup + URL string, assert on returned issue dicts
- Location: `backend/tests/test_*.py`

**Integration Tests:**
- None found — no database or HTTP integration tests exist

**E2E Tests:**
- Not used for main application
- `dashboard-react/tsconfig.json` excludes `playwright.config.ts` and `tests/**` — Playwright config referenced but no test files found

---

## Common Patterns

**Async Testing:**
```python
@pytest.mark.asyncio
async def test_detect_sourcepoint_tcf(self):
    html = """..."""
    soup = BeautifulSoup(html, 'html.parser')
    result = await check_tcf_compliance("https://example.com", soup, html)
    assert result["has_tcf"] == True
```

**Negative Testing (asserting absence of issues):**
```python
def test_button_with_text_passes(self):
    """Test: Button mit Text ist OK"""
    html = """<html><body><button>Absenden</button></body></html>"""
    soup = BeautifulSoup(html, 'html.parser')
    issues = self.checker.check_aria_compliance(soup, 'https://test.com')
    button_issues = [i for i in issues if 'BUTTON' in i['title']]
    assert len(button_issues) == 0
```

**Issue property assertions (dict-based issue format):**
```python
assert button_issues[0]['severity'] == 'warning'
assert result["cmp_name"] == "Cookiebot"
assert result["cmp_id"] == 11
```

**Debug print in tests (observed pattern — not recommended for CI):**
```python
print(f"✅ Alt-Text Issue korrekt kategorisiert: {result.feature_id.value}")
```

---

## Test Gaps

**Frontend:** No automated testing exists for React components, hooks, or API utilities in `dashboard-react/` or `landing-react/`. The `tsconfig.json` excludes Playwright configs, suggesting E2E was planned but not implemented.

**Backend integration:** No tests exercise database interactions, HTTP endpoints (FastAPI test client), or external service calls (Stripe, eRecht24).

**Backend async routes:** Most FastAPI route handlers are untested — only the underlying service logic is covered for auth and compliance checks.

---

*Testing analysis: 2026-03-29*
