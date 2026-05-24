---
phase: 10-agentur-kanal-stufe-1
plan: "02"
subsystem: backend/pdf
tags: [agency, pdf, reportlab, tdd, AGENCY-03]
dependency_graph:
  requires: []
  provides: [AgencyReportGenerator.generate]
  affects: [10-03-agency-download-endpoint]
tech_stack:
  added: [reportlab==4.0.7, Pillow (RGBA normalization)]
  patterns: [TDD RED-GREEN, SimpleDocTemplate, BytesIO, LOAD_TRUNCATED_IMAGES]
key_files:
  created:
    - backend/agency_report_generator.py (185 lines)
    - backend/tests/test_agency_pdf.py (63 lines)
  modified: []
decisions:
  - pageCompression=0 passed to SimpleDocTemplate enables text-searchable PDFs (required for byte-search assertions in tests)
  - _normalize_logo() uses PIL.ImageFile.LOAD_TRUNCATED_IMAGES=True + convert('RGB') to handle minimal/RGBA PNGs that ReportLab's ImageReader.getRGBData() cannot split
  - TOP_ISSUES_LIMIT = 3 class constant enforces AGENCY-03 per-site truncation (not a magic number)
metrics:
  duration: "~6min"
  completed: "2026-05-24T13:49:45Z"
  tasks_completed: 2
  files_created: 2
---

# Phase 10 Plan 02: AgencyReportGenerator PDF Class Summary

**One-liner:** Branded PDF generator with agency logo, client name, and per-site compliance rows (URL + score + top-3 issues) via ReportLab 4.0.7, 7/7 tests green.

## What Was Built

`backend/agency_report_generator.py` — standalone Python class (no FastAPI/DB imports) that produces PDF compliance reports for agency clients.

**Class signature:**
```python
class AgencyReportGenerator:
    TOP_ISSUES_LIMIT = 3  # AGENCY-03: top 3 issues per site

    def generate(
        self,
        client_name: str,
        sites: List[Dict[str, Any]],
        agency_logo_bytes: Optional[bytes] = None,
        generated_at: str = "",
    ) -> bytes: ...

    def _normalize_logo(self, logo_bytes: bytes) -> io.BytesIO: ...
```

**Key constants:** `TOP_ISSUES_LIMIT = 3`

**PDF sizes (measured):**
- Empty sites case: 2,293 bytes
- 2-site case: 3,453 bytes

## Test Coverage

`backend/tests/test_agency_pdf.py` — 7 pytest cases, all GREEN:

1. `test_pdf_generation_returns_bytes` — returns bytes, len > 1000
2. `test_pdf_starts_with_pdf_header` — first 5 bytes == `b"%PDF-"`
3. `test_pdf_generation_empty_sites` — empty sites → valid PDF
4. `test_pdf_with_logo_embeds_without_error` — 1x1 RGBA PNG embedded successfully
5. `test_pdf_contains_client_name` — client name searchable in PDF bytes
6. `test_pdf_handles_missing_compliance_score` — `compliance_score=None` → no exception
7. `test_pdf_handles_top_issues_list_truncated` — 5 issues → only Issue 1-3 in PDF, Issue 4-5 absent

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] pageCompression=0 required for text searchability**
- **Found during:** Task 2 (GREEN)
- **Issue:** ReportLab 4.0.7 default uses ASCII85+FlateDecode compression even with `compress=0` keyword. Text assertions `assert b"Issue 1" in result` failed because content stream was compressed.
- **Fix:** Added `pageCompression=0` to `SimpleDocTemplate(...)` constructor. This is the correct rl_config-level knob; `compress=0` only affects a different layer.
- **Files modified:** `backend/agency_report_generator.py`
- **Commit:** 722cfb1

**2. [Rule 1 - Bug] RGBA PNG logo caused OSError in ReportLab ImageReader.getRGBData()**
- **Found during:** Task 2 (GREEN) — logo test
- **Issue:** The plan-specified TINY_PNG is a 1x1 RGBA PNG. ReportLab's `ImageReader.getRGBData()` calls `im.split()[-1]` to extract the alpha channel, which triggers actual pixel loading. Pillow 12.2.0 raises `OSError: broken data stream` for this truncated IDAT block during forced load.
- **Fix:** Added `_normalize_logo()` method that: (a) sets `PIL.ImageFile.LOAD_TRUNCATED_IMAGES = True`, (b) opens the PNG, (c) converts to RGB via `img.convert('RGB')`, (d) saves as RGB PNG to a fresh BytesIO. ReportLab then handles RGB cleanly without calling split().
- **Files modified:** `backend/agency_report_generator.py`
- **Commit:** 722cfb1

## Known Stubs

None. The generator is fully functional and independently testable.

## Pre-existing Test Failures (not caused by this plan)

- `tests/test_barrierefreiheit.py::TestContrastAnalyzer::test_normal_text_higher_requirement` — pre-existing failure
- `tests/test_tcf_compliance.py::TestTCStringValidation::test_invalid_tc_string_short` — pre-existing failure
- `tests/test_tcf_compliance.py::TestTCFIssues::test_missing_tcf_generates_info_issue` — pre-existing failure

## Self-Check: PASSED
