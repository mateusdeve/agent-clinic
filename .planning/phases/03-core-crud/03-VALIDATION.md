---
phase: 03
slug: core-crud
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 (backend API) / Next.js build check (frontend) |
| **Config file** | `agent-service/pytest.ini` (exists from Phase 02) |
| **Quick run command** | `cd agent-service && python -m pytest tests/ -x -q --tb=short` |
| **Full suite command** | `cd agent-service && python -m pytest tests/ -v --tb=long && cd ../frontend && npm run build` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick command
- **After every plan wave:** Run full suite command
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Wave 0 Requirements

- [ ] `@tanstack/react-table` and `date-fns` installed in frontend/
- [ ] shadcn Table, Dialog, Sheet, Tabs, Input, Select, Calendar components added
- [ ] API test stubs for CRUD endpoints

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Calendar renders day/week/month with correct layout | AGENDA-01 | Visual layout | Open /agenda, toggle between views |
| Color-coded appointment blocks by status | AGENDA-05 | Visual styling | Create appointments with different statuses |
| Slide-over panel animation and positioning | D-06 | Visual interaction | Click "Novo" on any entity list |
| Chat bubble timeline matches WhatsApp style | PAT-05 | Visual design | Open patient profile, check Conversas tab |
| Medico sees only own calendar | AGENDA-07 | Role-based visual | Login as Medico, verify no other doctor data |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
