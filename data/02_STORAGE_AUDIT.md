# 02_STORAGE_AUDIT - localStorage/sessionStorage Mapping

**Erstellt:** 2026-05-04  
**Status:** Analyse abgeschlossen

---

## 🔑 Storage Key Registry

| Key | Schreibt | Liest | Error-Handling | Problem |
|-----|---------|-------|---------------|---------|
| `access_token` | AuthContext, useAuth, SocialLoginButtons, api.ts | AuthContext, useAuth, api.ts, 15+ Komponenten | Teilweise | Direktzugriff ohne typeof-window-Check in api.ts |
| `refresh_token` | AuthContext, useAuth, SocialLoginButtons | AuthContext, useAuth, api.ts | Nein | Kein try/catch bei Lesen |
| `user` | AuthContext, useAuth, SocialLoginButtons | AuthContext, useAuth | JSON.parse in try/catch | OK |
| `complyo-theme` | ThemeContext | ThemeContext | Nein | kein typeof-window-Check |
| `complyo_current_website` | dashboard.ts (typeof-check) | DomainHeroSection (try/catch) | Ja | OK |
| `complyo_last_analysis` | dashboard.ts (typeof-check) | DomainHeroSection (try/catch) | Ja | OK |
| `complyo_locked_optimization_url` | dashboard.ts (typeof-check) | dashboard.ts, OptimizationModeLock | Teilweise | OK |
| `complyo_optimization_mode` | dashboard.ts (typeof-check) | OptimizationModeLock | Teilweise | OK |
| `complyo_onboarding_completed` | OnboardingWizard | page.tsx | Nein | Kein try/catch |
| `cookie_consent` | CookieConsentModal (typeof-check) | CookieConsentModal | Ja | OK |
| `cookieConsent` | CookieBannerManagement | CookieBannerManagement | Nein | Kein typeof-window-Check! |
| `auth_token` | - | LegalActionWidget (3x) | Nein | WRONG KEY! Sollte `access_token` sein! |
| `token` | - | TCFManager, ConsentModeSettings, ServiceManager, CookieComplianceWidget | Nein | WRONG KEY! Fallback aber ugly |

---

## 🔴 Kritische Probleme

### 1. api.ts - Direktzugriff ohne SSR-Guard (Zeile 19)
```typescript
// PROBLEM: Crash beim SSR
const token = localStorage.getItem('access_token');

// FIX:
const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
```

### 2. LegalActionWidget.tsx - Falscher Key (Zeilen 68, 112, 139)
```typescript
// PROBLEM: Liest 'auth_token' statt 'access_token'
const token = localStorage.getItem('auth_token');  // gibt immer null zurück!

// FIX:
const token = localStorage.getItem('access_token');
```

### 3. ThemeContext.tsx - Kein SSR-Guard (Zeile 22)
```typescript
// PROBLEM: SSR-Fehler
const savedTheme = localStorage.getItem('complyo-theme');

// FIX:
const savedTheme = typeof window !== 'undefined' ? localStorage.getItem('complyo-theme') : null;
```

### 4. ActiveSiteContext.tsx - Kein SSR-Guard (Zeile 34)
```typescript
// PROBLEM: SSR-Fehler
const savedId = localStorage.getItem(STORAGE_KEY);

// FIX: typeof window check hinzufügen
```

### 5. CookieBannerManagement.tsx - Kein SSR-Guard (Zeile 70)
```typescript
// PROBLEM: SSR-Fehler
if (banner && !localStorage.getItem('cookieConsent')) {

// FIX:
if (banner && typeof window !== 'undefined' && !localStorage.getItem('cookieConsent')) {
```

---

## 🟠 Inkonsistenzen

### Token-Key-Chaos: 3 verschiedene Keys
- `access_token` → AuthContext, useAuth (KORREKT)
- `auth_token` → LegalActionWidget (FALSCH - liest immer null)
- `token` → TCFManager, ConsentModeSettings, etc. (als Fallback auf access_token)

### Lösung: Alle sollen `access_token` verwenden

---

## ✅ Empfohlener Safe-Wrapper

```typescript
// lib/storage.ts - Safe SSR-kompatible Storage Helpers
export const safeStorage = {
  get: (key: string): string | null => {
    try {
      return typeof window !== 'undefined' ? localStorage.getItem(key) : null;
    } catch { return null; }
  },
  set: (key: string, value: string): void => {
    try {
      if (typeof window !== 'undefined') localStorage.setItem(key, value);
    } catch {}
  },
  remove: (key: string): void => {
    try {
      if (typeof window !== 'undefined') localStorage.removeItem(key);
    } catch {}
  },
  getJSON: <T>(key: string, fallback: T): T => {
    try {
      const item = typeof window !== 'undefined' ? localStorage.getItem(key) : null;
      return item ? JSON.parse(item) : fallback;
    } catch { return fallback; }
  }
};

export const getAuthToken = (): string | null => safeStorage.get('access_token');
```
