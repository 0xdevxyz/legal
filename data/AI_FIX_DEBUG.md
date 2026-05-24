# AI Fix "Datenbankfehler" — Debug Findings

## 1. Frontend Button

**File:** `dashboard-react/src/components/ai/AIFixPreview.tsx` (line 71–78)

Button label: `Detaillierten KI-Fix generieren`
onClick handler: `onGenerateFull` prop — wired up in `ComplianceIssueCard.tsx`.

**File:** `dashboard-react/src/components/dashboard/ComplianceIssueCard.tsx` (line 311)
```ts
const result = await generateFix(issue.id, mappedCategory);
```

## 2. API Call

**File:** `dashboard-react/src/lib/api.ts` (lines 511–585)

```ts
export const generateFix = async (issueId: string, issueCategory: string): Promise<FixResult> => {
  const response = await apiClient.post('/api/v2/fixes/generate', {
    issue_id: issueId,
    issue_category: issueCategory
  });
  ...
}
```
- **URL:** `POST /api/v2/fixes/generate`
- HTTP 500 with structured `detail` object falls through to `(errorObj.message || 'Interner Serverfehler')`.

## 3. Backend Route Handler

**File:** `backend/fix_routes.py`
- Router prefix: `/api/v2/fixes` (line 23)
- Handler: `async def generate_fix(...)` at line 62

## 4. Database Queries That Could Be Failing

### Query 1 — SELECT user_limits (line 127–138)
```sql
SELECT fix_started, money_back_eligible, fixes_used, fixes_limit, plan_type
FROM user_limits
WHERE user_id = $1
```
- `user_limits` schema in `init_user_limits.sql` does NOT have `fixes_used` or `fixes_limit` columns.
- Those columns are only in `migration_freemium_model.sql` / `migration_user_limits_uuid.sql`.
- If the migration was never applied, this SELECT raises a PostgresError -> caught by the `asyncpg.PostgresError` handler at line 263 -> returns `"Datenbankfehler. Bitte versuchen Sie es später erneut."`.

### Query 2 — INSERT user_limits fallback (lines 143–148)
```sql
INSERT INTO user_limits (user_id, plan_type, fixes_used, fixes_limit)
VALUES ($1, $2, 0, 1)
```
- Same issue: `fixes_used` and `fixes_limit` columns may not exist.

### Query 3 — UPDATE user_limits (lines 186–194)
```sql
UPDATE user_limits
SET fixes_used = COALESCE(fixes_used, 0) + 1, fix_started = TRUE
WHERE user_id = $1
```

### Query 4 — INSERT generated_fixes (lines 198–203)
```sql
INSERT INTO generated_fixes (user_id, issue_id, issue_category, fix_type, plan_type)
VALUES ($1, $2, $3, $4, $5)
```
- Schema in `complete_migration.sql` (UUID-based) has NO `issue_category`, `fix_type`, or `plan_type` columns.
- Schema in `init_user_limits.sql` (INTEGER-based) has them, but `user_id` is INTEGER while JWT `user_id` may be UUID.
- Type mismatch between user_id (UUID vs INTEGER) is a common cause of PostgresError here.

## 5. Error Handler

**File:** `backend/fix_routes.py` (lines 263–270)
```python
except asyncpg.PostgresError as db_error:
    logger.error(f"❌ Database error in generate_fix: {db_error}", exc_info=True)
    raise HTTPException(
        status_code=500,
        detail={
            'error': 'database_error',
            'message': 'Datenbankfehler. Bitte versuchen Sie es später erneut.'
        }
    )
```
This is the exact source of the error message shown in the UI.

## Root Cause Summary

The `asyncpg.PostgresError` at line 263 is triggered by one of:
1. Missing columns `fixes_used` / `fixes_limit` on the `user_limits` table (migration not applied).
2. Schema mismatch on `generated_fixes` — columns `issue_category`, `fix_type`, `plan_type` missing in the UUID-based migration version.
3. Type mismatch: `user_id` from JWT is UUID, but `user_limits.user_id` is `INTEGER PRIMARY KEY` in `init_user_limits.sql`.

Check the backend logs for the exact `db_error` line from the `logger.error` at line 264 to confirm which query fails.
