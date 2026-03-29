# Coding Conventions

**Analysis Date:** 2026-03-29

## Naming Patterns

**Files:**
- React components: PascalCase (e.g., `ComplianceIssueCard.tsx`, `WebsiteAnalysis.tsx`)
- React pages: `page.tsx` inside route directories (Next.js App Router convention)
- Hooks: camelCase prefixed with `use` (e.g., `useCompliance.ts`, `useAuth.ts`)
- Stores: camelCase noun (e.g., `dashboard.ts` in `src/stores/`)
- Utility/lib files: camelCase (e.g., `api-utils.ts`, `constants.ts`)
- Python backend files: snake_case (e.g., `auth_routes.py`, `legal_notification_service.py`)
- Python test files: `test_` prefix (e.g., `test_auth.py`, `test_barrierefreiheit.py`)

**Functions:**
- TypeScript: camelCase (e.g., `analyzeWebsite`, `validateAndNormalizeUrl`, `getFixTypeForIssue`)
- JSDoc-style docstrings used on exported API functions (German prose): `/** Erstellt... */`
- Python: snake_case (e.g., `get_user_by_email`, `register_user`, `create_access_token`)

**Variables:**
- TypeScript: camelCase
- Python: snake_case
- Constants: SCREAMING_SNAKE_CASE in Python; camelCase `const` in TypeScript

**Types/Interfaces:**
- TypeScript: PascalCase interfaces and types (e.g., `AuthContextType`, `TrackedWebsite`, `CheckoutResponse`)
- Python data models: PascalCase Pydantic `BaseModel` subclasses

**React Components:**
- Named exports preferred (`export const Footer: React.FC = ...`)
- Typed with `React.FC` or `React.FC<Props>` where props are defined in a local interface above the component

## Code Style

**Formatting:**
- No Prettier config file detected at project level; `lint-staged` in `dashboard-react/package.json` runs `prettier --write` on commit, implying default Prettier settings
- Tailwind classes used for all visual styling (no CSS modules or Sass)
- `cn()` utility (clsx + tailwind-merge) used throughout components for conditional class merging: `src/lib/utils.ts`

**Linting:**
- ESLint via `eslint-config-next` (`next/core-web-vitals`) in both `dashboard-react` and `landing-react`
- Rules enforced: `no-console: warn`, `no-unused-vars: warn`, `react-hooks/exhaustive-deps: warn`, `react/no-unescaped-entities: warn`
- Landing adds: `@typescript-eslint/no-explicit-any: warn`
- TypeScript strict mode enabled in `dashboard-react/tsconfig.json`

**TypeScript:**
- `strict: true` in `dashboard-react/tsconfig.json`
- `any` usage present but warned against; mixed use of typed generics (e.g., `AxiosResponse<ComplianceAnalysis>`) alongside `any` parameters in older code
- Type-only imports used: `import type { ComplianceIssue } from '@/types/api'`

**Python:**
- Standard Python 3 idioms; `asyncpg` for async database access
- Type hints used in function signatures: `async def get_user_by_email(self, email: str) -> Optional[Dict]`
- `logging.getLogger(__name__)` pattern used in all service files

## Import Organization

**TypeScript order (observed pattern):**
1. React and framework imports (`react`, `next/*`)
2. Third-party libraries (`axios`, `@tanstack/react-query`, `lucide-react`, etc.)
3. Internal UI components (`@/components/ui/*`)
4. Internal feature components (`@/components/dashboard/*`)
5. Hooks and stores (`@/hooks/*`, `@/stores/*`)
6. Types and utilities (`@/types/*`, `@/lib/*`)
7. Relative local imports

**Path Aliases (dashboard-react):**
- `@/*` → `./src/*`
- `@/components/*` → `./src/components/*`
- `@/lib/*` → `./src/lib/*`
- `@/types/*` → `./src/types/*`
- `@/hooks/*` → `./src/hooks/*`

**Python order:**
1. Standard library imports
2. Third-party (fastapi, pydantic, asyncpg, jwt, bcrypt, etc.)
3. Local module imports (services, routers, engines)

## Error Handling

**TypeScript/Frontend:**
- All API functions in `src/lib/api.ts` follow a consistent try/catch pattern:
  ```typescript
  try {
    const response = await apiClient.post(...);
    return response.data;
  } catch (error) {
    console.error('💥 functionName failed:', error);
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.detail || error.message;
      throw new Error(`Context Error: ${message}`);
    }
    throw error;
  }
  ```
- HTTP status codes mapped to user-facing German error messages (422, 400, 401, 500, 503, 504)
- Custom error properties attached for domain-specific cases (e.g., `err.code = 'FIX_LIMIT_REACHED'`)
- Axios interceptors handle 401 token refresh automatically; redirect to `/login` on refresh failure
- Network errors trigger one retry with 1-second delay in the interceptor

**Python/Backend:**
- `raise HTTPException(status_code=XXX, detail="...")` pattern used uniformly across all route files
- Service classes (`AuthService`, etc.) raise `HTTPException` directly or let exceptions propagate to route handlers
- Route handlers catch exceptions and re-raise as `HTTPException` with appropriate status codes
- `logger.error(f"...", exc_info=True)` used for server-side error logging

## Logging

**Frontend:**
- `console.error('💥 ...')` convention for API/async errors with emoji prefix indicating error severity
- `console.warn('⚠️ ...')` for warnings (e.g., DEV_MODE payment simulation)
- `console.log(...)` used heavily for debug output (presence of debug logs not stripped in production — flagged by ESLint `no-console: warn` but not enforced as error)

**Backend:**
- `logger = logging.getLogger(__name__)` in each module
- `logger.info(...)` for successful operations and state changes
- `logger.error(f"...: {e}", exc_info=True)` for caught exceptions with stack traces
- Sentry SDK integrated for production error tracking: `backend/main_production.py` lines 22–29

## Comments

**When to Comment:**
- German-language inline comments used heavily throughout codebase for business logic explanation
- Emoji prefix convention for inline comments marking important areas: `# ✅ FIX:`, `# ⚠️`, `# TODO:`
- JSDoc-style docstrings on exported TypeScript functions and Python service methods
- Test docstrings follow: `"""Test: [behavior description]"""`

**Multilingual:**
- Comments and docstrings are in German (most) and English (some utility comments)
- UI-facing strings and error messages are in German

## Function Design

**Size:**
- API layer functions in `src/lib/api.ts` kept to single responsibility (one HTTP call each)
- Complex page components in `src/app/` can be large (up to 539 lines in `[id]/page.tsx`)
- Python service methods aim for single responsibility but some route handlers are complex

**Parameters:**
- TypeScript: typed parameter objects for complex inputs; primitives for simple calls
- Python: keyword arguments with type hints; `Optional[str]` for optional params defaulting to `None`

**Return Values:**
- TypeScript API functions return typed Promises: `Promise<TrackedWebsite[]>`, `Promise<void>`
- Python service methods return `Optional[Dict]` or typed Pydantic models

## Module Design

**Exports:**
- Named exports preferred over default exports in component files
- Exception: Next.js page files use `export default function PageName()` as required by the framework
- Barrel files (`index.ts`) used in some component subdirectories (e.g., `src/components/accessibility/`)

**Barrel Files:**
- Used selectively: `src/components/accessibility/index.ts` re-exports components and types
- Not universally applied — most component directories are imported directly by path

## State Management

- Zustand stores used for global client state: `src/stores/dashboard.ts`
- TanStack Query (`@tanstack/react-query`) used for server state/data fetching via custom hooks in `src/hooks/`
- React Context used for auth state: `src/contexts/AuthContext.tsx`
- Local component state via `useState` for UI-only state

---

*Convention analysis: 2026-03-29*
