# 03_NULL_SAFETY_ANALYSIS - Component Props & Destructuring

**Erstellt:** 2026-05-04

---

## Analysierte Komponenten

### 1. OptimizationProcessWidget.tsx ✅
- `analysisData?.issues` → bereits null-safe
- `criticalIssues.length` → safe (Fallback `[]`)
- **Buttons**: KEINE onClick-Handler → Phase 1.3 nötig

### 2. ComplianceIssueGroup.tsx ⚠️
- `group.sub_issues.slice(0, 3)` → crash wenn `sub_issues` null/undefined
- `group.sub_issues.length > 3` → crash bei null
- `group.parent_issue.id` → crash wenn parent_issue null
- Fix: Default `[]` für sub_issues

### 3. dashboard.ts ✅
- Alle localStorage Zugriffe mit `typeof localStorage !== 'undefined'`
- `analysisData?.issues.filter` → könnte crash: `.issues` direkt ohne `?`

### 4. api.ts ❌
- Zeile 19: `localStorage.getItem` direkt ohne SSR-Check
- Alle fetch-Aufrufe können bei SSR crashen

### 5. LegalActionWidget.tsx ❌
- Falscher Token-Key `auth_token` → immer null → alle API-Calls schlagen fehl

---

## Fix-Prioritäten

| Priorität | Komponente | Problem | Fix |
|-----------|-----------|---------|-----|
| 🔴 | LegalActionWidget.tsx | auth_token statt access_token | Key korrigieren |
| 🔴 | api.ts | kein SSR-Guard | typeof window check |
| 🟠 | ComplianceIssueGroup.tsx | sub_issues ohne default | `?? []` hinzufügen |
| 🟠 | ThemeContext.tsx | kein SSR-Guard localStorage | typeof window |
| 🟡 | dashboard.ts | `.issues` ohne `?.` | optional chaining |
