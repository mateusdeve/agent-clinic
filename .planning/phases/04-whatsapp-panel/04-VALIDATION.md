---
phase: 04
slug: whatsapp-panel
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 04 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 (backend) / Next.js build check (frontend) |
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

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real-time message arrival without refresh | WPP-04 | Requires 2 browser tabs + WhatsApp message | Send WhatsApp message, verify it appears in inbox panel |
| Takeover stops AI immediately | WPP-10 | Requires real Evolution API + Sofia pipeline | Click Assumir, send patient message, verify no AI response |
| All users see takeover indicator | WPP-11 | Requires multiple browser sessions | Open 2 tabs, takeover in one, verify indicator in both |
| Human message delivered via WhatsApp | WPP-08 | Requires real Evolution API | Send from panel, verify delivery on phone |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity
- [ ] Wave 0 covers all MISSING references
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
