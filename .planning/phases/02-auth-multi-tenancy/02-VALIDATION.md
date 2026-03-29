---
phase: 02
slug: auth-multi-tenancy
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-29
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 (backend) / Next.js build check (frontend) |
| **Config file** | `agent-service/pytest.ini` (to be created in Wave 0) |
| **Quick run command** | `cd agent-service && python -m pytest tests/ -x -q --tb=short` |
| **Full suite command** | `cd agent-service && python -m pytest tests/ -v --tb=long` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd agent-service && python -m pytest tests/ -x -q --tb=short`
- **After every plan wave:** Run `cd agent-service && python -m pytest tests/ -v --tb=long`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | TENANT-01 | migration | `alembic upgrade head` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 1 | API-02 | unit | `pytest tests/test_auth.py` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 1 | AUTH-04, AUTH-06 | unit | `pytest tests/test_rbac.py` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 2 | AUTH-01, AUTH-02 | build | `npm run build` | ✅ | ⬜ pending |
| 02-03-02 | 03 | 2 | AUTH-05 | build | `npm run build` | ✅ | ⬜ pending |
| 02-04-01 | 04 | 3 | TENANT-02, TENANT-03 | integration | `pytest tests/test_tenant_isolation.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `agent-service/tests/conftest.py` — shared fixtures (test DB, test client)
- [ ] `agent-service/tests/test_auth.py` — stubs for AUTH-01 through AUTH-06
- [ ] `agent-service/tests/test_rbac.py` — stubs for AUTH-04, AUTH-06
- [ ] `agent-service/tests/test_tenant_isolation.py` — stubs for TENANT-01, TENANT-02, TENANT-03
- [ ] `agent-service/pytest.ini` — pytest configuration

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Login page renders split layout with illustration | AUTH-01 | Visual layout verification | Open /login, verify split layout with medical illustration on left |
| Session persists after browser refresh | AUTH-03 | Requires real browser session | Log in, refresh page, verify still authenticated |
| Admin sees admin-only controls | AUTH-06 | Visual role-based UI check | Log in as Admin vs Recepcionista, compare visible controls |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
