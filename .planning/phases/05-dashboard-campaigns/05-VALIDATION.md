---
phase: 05
slug: dashboard-campaigns
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 |
| **Config file** | `agent-service/pytest.ini` |
| **Quick run command** | `cd agent-service && pytest tests/test_dashboard.py tests/test_templates.py tests/test_campaigns.py -x` |
| **Full suite command** | `cd agent-service && pytest tests/ -x` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd agent-service && pytest tests/test_dashboard.py tests/test_templates.py tests/test_campaigns.py -x`
- **After every plan wave:** Run `cd agent-service && pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| T1 | 05-01 | 0 | DASH-01 | unit | `pytest tests/test_dashboard.py::test_stats_kpis -x` | No | pending |
| T2 | 05-01 | 0 | DASH-02 | unit | `pytest tests/test_dashboard.py::test_proximas_consultas -x` | No | pending |
| T3 | 05-01 | 0 | DASH-03 | unit | `pytest tests/test_dashboard.py::test_conversas_ativas -x` | No | pending |
| T4 | 05-01 | 0 | DASH-04 | unit | `pytest tests/test_dashboard.py::test_charts_data -x` | No | pending |
| T5 | 05-01 | 0 | WPP-12 | unit | `pytest tests/test_templates.py -x` | No | pending |
| T6 | 05-01 | 0 | WPP-13 | unit | `pytest tests/test_campaigns.py::test_quick_send -x` | No | pending |
| T7 | 05-01 | 0 | WPP-14 | unit | `pytest tests/test_campaigns.py::test_create_campaign -x` | No | pending |
| T8 | 05-01 | 0 | WPP-15 | unit | `pytest tests/test_campaigns.py::test_dispatch_rate_limit -x` | No | pending |
| T9 | 05-01 | 0 | WPP-16 | unit | `pytest tests/test_campaigns.py::test_campaign_status -x` | No | pending |

---

## Wave 0 Gaps

- [ ] `agent-service/tests/test_dashboard.py` — covers DASH-01 through DASH-04
- [ ] `agent-service/tests/test_templates.py` — covers WPP-12
- [ ] `agent-service/tests/test_campaigns.py` — covers WPP-13 through WPP-16
- [ ] `npm install recharts` in `frontend/` directory
