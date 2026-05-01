---
phase: 2
slug: accessibility-statement-generator
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-01
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (backend) + manual browser checks (frontend) |
| **Config file** | backend/ (no explicit pytest.ini) |
| **Quick run command** | `cd /home/clawd/saas/legal/backend && python3 -m pytest tests/test_statement_generator.py -v` |
| **Full suite command** | `cd /home/clawd/saas/legal/backend && python3 -m pytest tests/ -v` |
| **Estimated runtime** | ~20 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick statement generator test
- **After every plan wave:** Run full backend test suite + TypeScript check
- **Before `/gsd:verify-work`:** Full suite green + manual browser smoke test
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 2-01-01 | 01 | 1 | AUDIT-05 | unit | `python3 -m pytest tests/test_statement_generator.py -v` | ❌ W0 | ⬜ pending |
| 2-01-02 | 01 | 1 | AUDIT-05 | automated | `grep -q "generate-statement" backend/accessibility_fix_routes.py` | ✅ | ⬜ pending |
| 2-02-01 | 02 | 2 | AUDIT-05 | manual | Dashboard → Accessibility → Statement Generator → Formular ausfüllen → Preview | ❌ W0 | ⬜ pending |
| 2-02-02 | 02 | 2 | AUDIT-05 | automated | `cd dashboard-react && npx tsc --noEmit 2>&1 \| grep -i statement` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_statement_generator.py` — unit tests für generate_accessibility_statement() Funktion

*Frontend (Dashboard UI) ist manuelle Browser-Verifikation. Backend-Template-Generierung hat Unit-Tests.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Dashboard zeigt Generator-UI mit Formular und Preview | AUDIT-05 | Next.js UI, kein E2E-Setup | Dashboard → Accessibility → Statement → Formular füllen → Preview prüfen |
| Download-Button liefert HTML-Datei | AUDIT-05 | Datei-Download, nicht automatisch testbar | Click "HTML herunterladen" → Datei öffnen → BFSG-Felder prüfen |
| PDF-Export via window.print() | AUDIT-05 | Browser-Dialog, nicht automatisch testbar | Click "PDF exportieren" → Druckdialog erscheint |
| Pflichtfelder in generierter Erklärung | AUDIT-05 | Inhalt-Qualität, nicht nur Vorhandensein | Generierte HTML-Datei auf alle 6 BFSG-Pflichtfelder prüfen |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
