---
phase: 1
slug: critical-compliance-fixes
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-30
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (backend) + manual browser checks (frontend) |
| **Config file** | backend/pytest.ini or backend/ (no explicit config seen) |
| **Quick run command** | `cd /home/clawd/saas/legal/backend && python -m pytest tests/test_ua_truncation.py -v` |
| **Full suite command** | `cd /home/clawd/saas/legal/backend && python -m pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick UA-truncation test
- **After every plan wave:** Run full backend test suite
- **Before `/gsd:verify-work`:** Full suite must be green + manual browser checks passed
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | AUDIT-01 | manual | Check landing page in browser for BFSG disclaimer | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | AUDIT-02 | manual | Check dashboard Cookie-Compliance → Advanced Settings for "Coming Soon" badge | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 2 | AUDIT-03 | unit | `python -m pytest tests/test_ua_truncation.py -v` | ❌ W0 | ⬜ pending |
| 1-02-02 | 02 | 2 | AUDIT-04 | automated | `curl -I https://api.complyo.de \| grep -i strict-transport` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_ua_truncation.py` — unit tests für UA-Truncation Funktion (AUDIT-03)

*Frontend (BFSG disclaimer, TCF badge) und nginx (STS header) sind Browser/curl-Verifikation — kein automatisiertes Test-Setup nötig.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| BFSG Disclaimer sichtbar auf Landing Page | AUDIT-01 | React/Next.js UI, kein E2E-Test-Setup in Phase 1 | Browser öffnen: complyo.de → Suche nach "28.06.2025" oder "Forward-Looking" Text |
| TCF 2.2 "Coming Soon" Badge im Dashboard | AUDIT-02 | Dashboard-UI, kein automatisierter Test | Dashboard → Cookie-Compliance → Einstellungen → Advanced → TCF 2.2 Abschnitt |
| STS-Header aktiv auf api.complyo.de | AUDIT-04 | nginx live-config, kein unittest möglich | `curl -I https://api.complyo.de` → Header `Strict-Transport-Security` muss vorhanden sein |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
