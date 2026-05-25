# Duplicate / Obsolete File Audit

## Pattern: Versioning clutter — incremental rewrites never cleaned up

---

## Group 1: classify_new_updates — 3 near-identical one-off scripts

| File | Lines | Status |
|------|-------|--------|
| classify_new_updates.py | 88 | Superseded — uses old DB schema (9 columns INSERT) |
| classify_new_updates_v2.py | 113 | Superseded — same SQL query, slightly expanded INSERT (19 columns) |
| classify_new_updates_v3.py | 122 | Likely current — adds `confidence_to_float()` helper, 19-column schema |

**Finding:** v1 and v2 have identical headers and the same `async def classify_new_updates()` entry point. v2 vs v3 differ only by the addition of `confidence_to_float()` and minor INSERT field reordering. None of these are imported by any module — they are standalone one-off CLI scripts. v1 and v2 are obsolete.

---

## Group 2: classify_legal_updates — 2 parallel approaches, neither imported

| File | Lines | Status |
|------|-------|--------|
| classify_legal_updates.py | 170 | AI-based classifier using OpenRouter API |
| classify_legal_updates_simple.py | 228 | Rule-based fallback, no AI dependency |

**Finding:** Both are standalone scripts (not imported anywhere). The "simple" variant is a fallback written when the AI version was unreliable. The AI version (classify_legal_updates.py) is older/original; the simple version is a lateral alternative, not a direct superseding. Both are potentially obsolete — the production path uses `ai_legal_classifier.py` (imported by the v3 classify_new_updates script).

---

## Group 3: erecht24_routes_v2 — full vs stripped-down "simple" variant

| File | Lines | Status |
|------|-------|--------|
| erecht24_routes_v2.py | 1025 | ACTIVE — imported in main_production.py line 137 |
| erecht24_routes_v2_simple.py | 173 | Obsolete — stripped diagnostic stub, not imported anywhere |

**Finding:** `erecht24_routes_v2_simple.py` is a temporary diagnostic stub ("Simplified version... Full features will be gradually enabled once base system is stable"). The full `erecht24_routes_v2.py` is the active production file. The simple variant is safe to delete.

---

## Group 4: update_main.py — abandoned migration helper

| File | Lines | Status |
|------|-------|--------|
| update_main.py | 70 | Obsolete — script that prints a new main.py to stdout, references old path /opt/projects/saas-project-2/ |

**Finding:** This file contains a Python script whose entire body is generating a string (`content = '''...'''`) to be written to a different file. It references an old project path (`/opt/projects/saas-project-2/backend`). Not imported anywhere. Dead migration artifact.

---

## Group 5: ComplyoCookieManager vs ERecht24CookieManager — near-identical TSX components

| File | Lines | Status |
|------|-------|--------|
| ComplyoCookieManager.tsx | 241 | Unknown which is canonical |
| ERecht24CookieManager.tsx | 241 | Unknown which is canonical |

**Finding:** `diff` shows exactly ONE line difference: the exported component name (`ComplyoCookieManager` vs `ERecht24CookieManager`). Both have 241 lines, identical integration code, identical logic, identical JSX structure. One was copy-renamed from the other and the body was never diverged. This is a near-perfect duplicate — one should be removed or they should be merged into a single parameterized component.

---

## Group 6: Accessibility widget versions — versioned JS served conditionally

| File | Lines | Status |
|------|-------|--------|
| accessibility.js | 778 | Fallback (v4.0) — served when version param is unrecognized |
| accessibility-v5.js | 1883 | Active — served when `?version=5` |
| accessibility-v6.js | 2304 | Default active — served when `?version=6` or no param |

**Finding:** These are NOT duplicates — they are intentionally versioned and all three are actively served by `widget_routes.py` (lines 166–180). v6 is the default. v5 and the base file are legacy but still reachable via query param. This is intentional version routing, not clutter — but v4 (accessibility.js) could be reviewed for removal if no customers are on it.

---

## Summary

| Candidate for deletion | Reason |
|------------------------|--------|
| classify_new_updates.py | Superseded by v2/v3, not imported |
| classify_new_updates_v2.py | Superseded by v3, not imported |
| classify_legal_updates.py | One-off script, superseded by ai_legal_classifier.py module |
| classify_legal_updates_simple.py | One-off fallback script, not imported |
| erecht24_routes_v2_simple.py | Diagnostic stub, not imported, replaced by full v2 |
| update_main.py | Dead migration artifact referencing old path |
| ERecht24CookieManager.tsx OR ComplyoCookieManager.tsx | Near-identical duplicate (1 line diff), one is redundant |
