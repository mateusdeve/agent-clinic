---
phase: 06
slug: polish-hardening
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 06 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 (backend), Next.js build (frontend) |
| **Config file** | agent-service/pytest.ini (if exists), frontend/next.config.ts |
| **Quick run command** | `cd frontend && npx next build 2>&1 | tail -5` |
| **Full suite command** | `cd agent-service && python3 -m pytest tests/ -q --tb=short` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npx next build 2>&1 | tail -5`
- **After every plan wave:** Run full suite
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | SC-1 (responsive) | visual + build | `npx next build` | ✅ | ⬜ pending |
| 06-01-02 | 01 | 1 | SC-1 (responsive) | visual + build | `npx next build` | ✅ | ⬜ pending |
| 06-02-01 | 02 | 1 | SC-2 (error boundaries) | build | `npx next build` | ❌ W0 | ⬜ pending |
| 06-02-02 | 02 | 1 | SC-4 (loading states) | build | `npx next build` | ❌ W0 | ⬜ pending |
| 06-03-01 | 03 | 2 | SC-3 (tenant isolation) | integration | `pytest tests/test_auth.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- Existing infrastructure covers all phase requirements.
- pytest already configured with xfail stubs from Phase 2
- Next.js build already validates TypeScript and route integrity

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Responsive layout at 375px | SC-1 | Visual rendering | Open Chrome DevTools, toggle mobile view, check each page |
| Responsive layout at 768px | SC-1 | Visual rendering | Same with tablet dimensions |
| Error toast/fallback UI | SC-2 | Network simulation | Use Chrome DevTools to block API requests, verify error states |
| Loading skeleton appearance | SC-4 | Visual rendering | Throttle network, verify loading indicators appear |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
