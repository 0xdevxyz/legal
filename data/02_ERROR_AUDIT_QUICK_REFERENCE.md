# 02_ERROR_AUDIT_QUICK_REFERENCE.md

## Schnellreferenz: Top 30 Fehler mit direkten Fixes

### Kategorie: Data Persistence (localStorage)

#### FEHLER 1: JSON Parse Error bei Corrupted User Data
```
FILE: /dashboard-react/src/contexts/AuthContext.tsx:154-162
SEVERITY: HIGH
CURRENT:
    try {
        setAccessToken(token);
        setUser(JSON.parse(userData));  // ❌ Fehler wenn userData malformed
        setIsLoading(false);
        return;
    } catch (e) {
        localStorage.removeItem('access_token');
    }

FIX:
    try {
        if (!userData) throw new Error('No user data stored');
        const parsed = JSON.parse(userData);
        if (!parsed.id) throw new Error('Invalid user object');
        setUser(parsed);
        setIsLoading(false);
        return;
    } catch (e) {
        console.error('Session restore failed:', e.message);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
    }
```

#### FEHLER 2: SSR localStorage Access ohne Browser-Check
```
FILE: /dashboard-react/src/contexts/ThemeContext.tsx:22
SEVERITY: MEDIUM
CURRENT:
    const savedTheme = localStorage.getItem('complyo-theme');

FIX:
    const savedTheme = typeof window !== 'undefined' 
        ? localStorage.getItem('complyo-theme') 
        : null;
```

#### FEHLER 3: localStorage Write ohne Error Handling
```
FILE: /dashboard-react/src/stores/dashboard.ts:62-65
SEVERITY: MEDIUM
CURRENT:
    setCurrentWebsite: (website) => {
        if (typeof localStorage !== 'undefined' && website) {
            localStorage.setItem('complyo_current_website', JSON.stringify(website));
        }
        return set({ currentWebsite: website });
    },

FIX:
    setCurrentWebsite: (website) => {
        if (typeof localStorage !== 'undefined' && website) {
            try {
                const serialized = JSON.stringify(website);
                localStorage.setItem('complyo_current_website', serialized);
            } catch (e) {
                if (e instanceof Error && e.name === 'QuotaExceededError') {
                    console.warn('localStorage quota exceeded');
                } else {
                    console.error('Failed to persist website:', e);
                }
            }
        }
        return set({ currentWebsite: website });
    },
```

---

### Kategorie: API/Network

#### FEHLER 6: Request Interceptor Error ohne Filterung
```
FILE: /dashboard-react/src/lib/api.ts:28-31
SEVERITY: MEDIUM
CURRENT:
    (error) => {
        console.error('💥 API Request Error:', error);
        return Promise.reject(error);
    }

FIX:
    (error) => {
        // Only log if not a timeout/connection issue
        if (error.code === 'ECONNABORTED' || 
            error.code === 'ECONNREFUSED' ||
            error.code === 'ERR_NETWORK') {
            console.debug('Network connectivity issue:', error.code);
        } else if (error.code === 'ERR_INVALID_ARG_TYPE') {
            console.error('Invalid request argument:', error.message);
        } else {
            console.error('API Request Error:', error.message);
        }
        return Promise.reject(error);
    }
```

#### FEHLER 7: Network Retry ohne Exponential Backoff
```
FILE: /dashboard-react/src/lib/api.ts:41-46
SEVERITY: MEDIUM
CURRENT:
    if ((error.code === 'ERR_NETWORK' || error.code === 'ERR_NETWORK_CHANGED') && !originalRequest._retry) {
        originalRequest._retry = true;
        console.log('Network error detected, retrying request...');
        await new Promise(resolve => setTimeout(resolve, 1000));
        return apiClient(originalRequest);
    }

FIX:
    const retryCount = (originalRequest._retryCount || 0) + 1;
    if (retryCount <= 3 && (error.code === 'ERR_NETWORK' || error.code === 'ERR_NETWORK_CHANGED')) {
        originalRequest._retryCount = retryCount;
        // Exponential backoff: 1s, 2s, 4s
        const delay = Math.pow(2, retryCount - 1) * 1000;
        console.log(`Network error, retrying in ${delay}ms (attempt ${retryCount}/3)`);
        await new Promise(resolve => setTimeout(resolve, delay));
        return apiClient(originalRequest);
    }
```

#### FEHLER 8: Token Refresh ohne State Preservation
```
FILE: /dashboard-react/src/lib/api.ts:65-78
SEVERITY: HIGH
CURRENT:
    catch (refreshError) {
        console.error('Token refresh failed in interceptor:', refreshError);
        localStorage.removeItem('access_token');
        if (typeof window !== 'undefined') {
            window.location.href = '/login';
        }
        return Promise.reject(refreshError);
    }

FIX:
    catch (refreshError) {
        console.error('Token refresh failed:', refreshError);
        // Clear all auth state
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        
        if (typeof window !== 'undefined') {
            // Preserve current path for redirect after re-login
            const currentPath = window.location.pathname;
            if (currentPath !== '/login') {
                sessionStorage.setItem('redirectAfterLogin', currentPath);
            }
            // Soft redirect (gibt dem browser time zum cleanup)
            window.location.href = '/login?reason=session_expired';
        }
        
        return Promise.reject(refreshError);
    }
```

#### FEHLER 9: URL Validation ohne Type Guard
```
FILE: /dashboard-react/src/lib/api.ts:101-106
SEVERITY: MEDIUM
CURRENT:
    if (!url || typeof url !== 'string') {
        console.error('❌ validateAndNormalizeUrl: Invalid input:', typeof url, url);
        throw new Error('URL must be a non-empty string');
    }

FIX:
    if (!url || typeof url !== 'string') {
        const errorMsg = `Invalid URL input: type=${typeof url}, value=${String(url).slice(0, 50)}`;
        console.error(errorMsg);
        throw new Error('URL must be a non-empty string');
    }
    
    const trimmed = String(url).trim();
    if (trimmed.length === 0) {
        throw new Error('URL cannot be empty or whitespace only');
    }
```

---

### Kategorie: Component Rendering

#### FEHLER 55: Missing Issue Groups ohne Fallback
```
FILE: /dashboard-react/src/components/dashboard/WebsiteAnalysis.tsx:76-78
SEVERITY: HIGH
CURRENT:
    if (analysisData.issue_groups) {
        console.log('🎯 Issue Groups gefunden:', analysisData.issue_groups);
    } else {
        console.warn('⚠️ Keine issue_groups in analysisData!', analysisData);
    }

FIX:
    const issueGroups = normalizeIssueGroups(analysisData.issue_groups || []);
    if (!issueGroups || issueGroups.length === 0) {
        console.warn('No issue groups in analysis data');
        return (
            <div className="p-4 text-center text-gray-500">
                <p>Keine Compliance-Probleme gefunden oder Daten nicht verfügbar</p>
            </div>
        );
    }
    // ... render with issueGroups
```

#### FEHLER 56: Batch Fix Error ohne User Notification
```
FILE: /dashboard-react/src/components/dashboard/ComplianceIssueGroup.tsx:192
SEVERITY: HIGH
CURRENT:
    } catch (error) {
        console.error('Batch-Fix Fehler:', error);
    }

FIX:
    } catch (error) {
        const errorMsg = error instanceof Error 
            ? error.message 
            : 'Batch-Fix fehlgeschlagen';
        setError(errorMsg);
        setIsGenerating(false);
        
        // Show toast notification to user
        showToast({
            type: 'error',
            message: errorMsg,
            duration: 5000
        });
        
        console.error('Batch-Fix failed:', error);
    }
```

#### FEHLER 57: localStorage Parse Error ohne Recovery
```
FILE: /dashboard-react/src/components/dashboard/DomainHeroSection.tsx:86-90
SEVERITY: MEDIUM
CURRENT:
    try {
        console.log('✅ Lade Analysedaten aus localStorage');
        // Missing implementation
    } catch (e) {
        console.error('localStorage parse error:', e);
    }

FIX:
    try {
        const stored = localStorage.getItem('complyo_last_analysis');
        if (!stored) return;
        
        const data = JSON.parse(stored);
        if (!data.scan_id) throw new Error('Invalid analysis data');
        
        setAnalysisData(data);
        console.log('Analysis restored from cache');
    } catch (e) {
        console.error('Failed to restore analysis:', e);
        // Clear corrupted cache
        localStorage.removeItem('complyo_last_analysis');
        // Trigger fresh scan instead of staying in loading state
        setAnalysisData(null);
    }
```

---

### Kategorie: Auth/Token

#### FEHLER 91: Token Invalid ohne User Notification
```
FILE: /dashboard-react/src/contexts/AuthContext.tsx:106-109
SEVERITY: HIGH
CURRENT:
    if (response.status === 401) {
        console.log('Refresh token invalid, logging out');
        logout();
        return false;
    }

FIX:
    if (response.status === 401) {
        console.log('Refresh token invalid - session expired');
        logout();
        
        // Notify UI via custom event
        if (typeof window !== 'undefined') {
            const event = new CustomEvent('complyo:auth-expired', {
                detail: { reason: 'token_invalid' }
            });
            window.dispatchEvent(event);
        }
        
        return false;
    }
```

#### FEHLER 93: Token Read ohne SSR Check
```
FILE: /dashboard-react/src/lib/api.ts:18-19
SEVERITY: MEDIUM
CURRENT:
    const token = localStorage.getItem('access_token');

FIX:
    const token = typeof window !== 'undefined' 
        ? localStorage.getItem('access_token')
        : null;
```

---

### Kategorie: Null/Undefined

#### FEHLER 101: Error Details Log ohne Null-Check
```
FILE: /dashboard-react/src/components/dashboard/ComplianceIssueCard.tsx:260-261
SEVERITY: MEDIUM
CURRENT:
    console.error('Error details:', {
        response: error.response,
        data: error.response?.data
    });

FIX:
    const errorDetails = {
        message: error instanceof Error ? error.message : String(error),
        response: error?.response?.status,
        data: error?.response?.data?.detail || error?.response?.data
    };
    console.error('Error details:', errorDetails);
```

---

### Kategorie: Event Listener/DOM

#### FEHLER 119: matchMedia ohne Browser Check
```
FILE: /dashboard-react/src/contexts/ThemeContext.tsx:27
SEVERITY: MEDIUM
CURRENT:
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

FIX:
    if (typeof window === 'undefined') {
        setThemeState('dark');  // SSR default
        return;
    }
    
    try {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        setThemeState(prefersDark ? 'dark' : 'light');
    } catch (e) {
        console.warn('matchMedia not available, defaulting to dark');
        setThemeState('dark');
    }
```

---

## Reusable Helper Functions

### Safe localStorage Wrapper
```typescript
// lib/storage.ts
export const safeStorage = {
    getItem: (key: string): string | null => {
        try {
            if (typeof window === 'undefined') return null;
            return localStorage.getItem(key);
        } catch (e) {
            console.error(`Storage read error [${key}]:`, e);
            return null;
        }
    },

    setItem: (key: string, value: string): boolean => {
        try {
            if (typeof window === 'undefined') return false;
            localStorage.setItem(key, value);
            return true;
        } catch (e) {
            if (e instanceof Error && e.name === 'QuotaExceededError') {
                console.warn(`Storage quota exceeded [${key}]`);
            } else {
                console.error(`Storage write error [${key}]:`, e);
            }
            return false;
        }
    },

    removeItem: (key: string): void => {
        try {
            if (typeof window !== 'undefined') {
                localStorage.removeItem(key);
            }
        } catch (e) {
            console.warn(`Storage remove error [${key}]:`, e);
        }
    },

    getJSON: <T,>(key: string, fallback: T): T => {
        try {
            const item = safeStorage.getItem(key);
            if (!item) return fallback;
            return JSON.parse(item);
        } catch (e) {
            console.warn(`Storage JSON parse error [${key}]:`, e);
            safeStorage.removeItem(key);  // Clear corrupted data
            return fallback;
        }
    },

    setJSON: <T,>(key: string, value: T): boolean => {
        try {
            return safeStorage.setItem(key, JSON.stringify(value));
        } catch (e) {
            console.error(`Storage JSON stringify error [${key}]:`, e);
            return false;
        }
    }
};
```

### API Error Handler Factory
```typescript
// lib/errorHandler.ts
interface ApiErrorContext {
    endpoint: string;
    status?: number;
    message?: string;
}

export const createApiErrorMessage = (error: unknown, context: ApiErrorContext): string => {
    if (axios.isAxiosError(error)) {
        const status = error.response?.status;
        const data = error.response?.data;

        switch (status) {
            case 400:
                return typeof data?.detail === 'string' ? data.detail : 'Ungültige Anfrage';
            case 401:
                return 'Autorisierung erforderlich. Bitte melden Sie sich erneut an.';
            case 402:
                return 'Plan-Limit erreicht. Bitte upgraden Sie Ihren Plan.';
            case 403:
                return 'Sie haben keine Berechtigung für diese Aktion.';
            case 404:
                return 'Ressource nicht gefunden.';
            case 429:
                return 'Zu viele Anfragen. Bitte versuchen Sie es später erneut.';
            case 500:
                return 'Interner Serverfehler. Bitte kontaktieren Sie den Support.';
            case 503:
                return 'Service ist vorübergehend nicht verfügbar.';
            default:
                return `Fehler: ${error.message}`;
        }
    }

    if (error instanceof Error) {
        return error.message;
    }

    return 'Ein unbekannter Fehler ist aufgetreten';
};

export const logApiError = (error: unknown, context: ApiErrorContext): void => {
    const message = createApiErrorMessage(error, context);
    console.error(`[${context.endpoint}] ${message}`, { context });
};
```

---

## Implementation Timeline

### Week 1: Critical Fixes
- Day 1-2: Auth token handling (Fehler 1, 8, 91)
- Day 3: API error handling refactoring (Fehler 6-10)
- Day 4: Component error boundaries (Fehler 55, 56)
- Day 5: localStorage safety wrapper (Fehler 2-5)

### Week 2: High Priority
- Day 1: SSR compatibility (Fehler 93, 119)
- Day 2-3: Input validation (Fehler 21)
- Day 4-5: Async state management (Fehler 59)

### Week 3: Medium Priority
- Weitere MEDIUM severity Fehler
- Unit/E2E testing

---

## Testing Checklist

- [ ] localStorage functions work without errors in SSR
- [ ] API errors show user-friendly messages
- [ ] Token refresh failure doesn't break UI
- [ ] Network errors retry with exponential backoff
- [ ] Component errors render fallback UI
- [ ] Null values don't cause crashes
- [ ] Session persists across page reloads
- [ ] Invalid URLs show clear error messages
