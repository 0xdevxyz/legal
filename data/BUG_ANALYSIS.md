# Bug Analysis: issue_groups missing + /api/v2/analyze 500

## Bug 1 — "Keine issue_groups in analysisData! null"

### Root cause

The frontend loads last-scan data via `useLatestScan` (hook), which calls `/api/scans/latest`.
The backend at `/api/scans/latest` (main_production.py line 1269–1342) correctly extracts
`issue_groups` from `scan_data` and returns them. BUT that endpoint queries with
`int(current_user["id"])` (line 1296):

```python
int(current_user["id"])   # main_production.py:1296
```

The JWT payload (auth_service.py lines 166–167) stores `id` as a **string** (`str(user_id)`).
If `user_id` in the DB is a UUID, `int(...)` throws a `ValueError → 500`, and the endpoint
never returns data. If user_id is a plain integer stored as string, this technically works —
but the inconsistency is still the first suspect.

The **real structural cause** is at frontend level:

**File:** `/home/clawd/saas/legal/dashboard-react/src/hooks/useCompliance.ts`  
**Lines 108–128 — `useLatestScan`:**

```ts
const response = await apiClient.get('/api/scans/latest');
return response.data?.data || null;   // line 114
```

The backend returns `{ success: true, data: { ..., issue_groups: [...] } }`.
So `response.data.data` contains `issue_groups`. That part is fine.

**File:** `/home/clawd/saas/legal/dashboard-react/src/components/dashboard/WebsiteAnalysis.tsx`  
**Line 61:**

```ts
const analysisData = storedAnalysisData || fetchedAnalysisData || latestScanData;
```

- `storedAnalysisData` comes from the Zustand store (`complyo_last_analysis` in localStorage).
- `fetchedAnalysisData` comes from `useComplianceAnalysis` which is **disabled** by default
  (`enabled: false`, useCompliance.ts line 27). It only runs when `refetch()` is called manually.
- `latestScanData` is only populated if `/api/scans/latest` returns successfully.

**The store's `setAnalysisData` (dashboard.ts lines 68–80) persists to localStorage**, but the
`normalizeAnalysisResponse` function in `api.ts` (lines 823–843) — which strips unknown fields
— is **not** called in the `analyzeWebsite` flow that populates the store. However, if old data
was stored in localStorage from before `issue_groups` was added to the response, it will be read
back without `issue_groups`. The store hydration (`complyo_last_analysis`) never re-fetches, so
stale data without `issue_groups` is served directly.

**Confirmed missing field path:**

1. `/api/v2/analyze` response (main_production.py lines 1152–1155) wraps the result as:
   ```python
   return { "success": True, "data": {**scan_result, "scan_id": new_scan['scan_id']} }
   ```
2. But `analyzeWebsite` in `api.ts` (line 190–198) does:
   ```ts
   const response = await apiClient.post('/api/v2/analyze', payload);
   if (!response.data || !response.data.success) { throw ... }
   return response.data;   // returns the full wrapper {success, data:{...}}
   ```
   It returns `response.data` (the wrapper), **not** `response.data.data` (the actual scan).
   So `issue_groups` is nested one level too deep: `analysisData.data.issue_groups` instead of
   `analysisData.issue_groups`.

---

## Bug 2 — `/api/v2/analyze` returns 500 Internal Server Error

**File:** `/home/clawd/saas/legal/backend/main_production.py`  
**Lines 1090–1164**

### Root cause A — `scan_duration_ms` type mismatch

The scanner (`compliance_engine/scanner.py` lines 196–211) returns `scan_result` containing
`scan_duration_ms`. If this is a `float` (milliseconds as float), asyncpg will reject it for an
`integer` column, raising an exception that cascades to a 500.

### Root cause B — `current_user["id"]` is a string, DB column is likely UUID/int

`get_current_user` in `dependencies.py` (lines 144–186) returns the raw JWT payload.
The JWT stores `"id": str(user_id)` (auth_service.py line 166), so `current_user["id"]` is
always a **string**. At line 1112:

```python
current_user["id"],   # main_production.py:1112 — passed as $2 to user_id UUID/int column
```

If the DB `user_id` column in `scan_history` is `INTEGER` or `UUID`, asyncpg may raise a type
mismatch error when inserting a plain string, causing a 500.

### Root cause C — response structure mismatch (structural, causes silent data loss)

Line 1154:
```python
return {
    "success": True,
    "data": {**scan_result, "scan_id": new_scan['scan_id']}
}
```

Frontend `analyzeWebsite` (api.ts line 198) returns `response.data` (the entire JSON body),
so the frontend receives `{ success: True, data: { ... } }`. Then `WebsiteAnalysis.tsx`
line 61 puts this wrapper object into `analysisData`. Accessing `analysisData.issue_groups`
finds nothing (it's at `analysisData.data.issue_groups`). This is the **direct** cause of
"Keine issue_groups in analysisData!".

---

## Exact file locations summary

| # | File | Line(s) | Problem |
|---|------|---------|---------|
| 1 | `backend/main_production.py` | 1152–1155 | Response wrapped in `{success, data:{...}}` — one level too deep |
| 2 | `dashboard-react/src/lib/api.ts` | 197–198 | `return response.data` returns the wrapper, not `response.data.data` |
| 3 | `backend/main_production.py` | 1112 | `current_user["id"]` is a string, inserted into integer/UUID DB column |
| 4 | `backend/main_production.py` | 1296 | `int(current_user["id"])` will crash if id is a UUID string |
| 5 | `dashboard-react/src/hooks/useCompliance.ts` | 114 | `response.data?.data` — correctly unwraps latest-scan, but scan_data from v2/analyze is never unwrapped |
| 6 | `dashboard-react/src/stores/dashboard.ts` | 68–80 | `setAnalysisData` persists to localStorage without `issue_groups` if old data was stored before the field existed |

---

## Quick verification commands

```bash
# Check scan_history schema
psql $DATABASE_URL -c "\d scan_history"

# Check what user_id type is stored
psql $DATABASE_URL -c "SELECT pg_typeof(user_id) FROM scan_history LIMIT 1"
```
