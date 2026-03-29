---
phase: 1
slug: foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-29
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None needed — Phase 1 is static landing page |
| **Config file** | none — Wave 0 installs Next.js |
| **Quick run command** | `npm run build` |
| **Full suite command** | `npm run build && npm run start` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `npm run build`
- **After every plan wave:** Run `npm run build && npm run start`
- **Before `/gsd:verify-work`:** Build must succeed with zero errors
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | LAND-01..04 | build | `npm run build` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `package.json` — Next.js project initialized via `npx create-next-app@latest`
- [ ] `tailwind.config` — Tailwind CSS 4 configured with design tokens
- [ ] `components.json` — shadcn/ui initialized via `npx shadcn@latest init`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Hero CTA opens WhatsApp | LAND-01 | WhatsApp deep link requires mobile/browser | Click CTA button, verify wa.me URL opens |
| Visual identity matches site.html | LAND-04 | Visual comparison not automatable | Compare side-by-side at 1280px and 375px |
| Mobile layout no horizontal overflow | LAND-03 | Layout check at 375px | Open DevTools, set viewport 375px, verify no horizontal scroll |
| All sections present and ordered | LAND-02 | Content structure visual check | Scroll page, verify: hero, stats, features, how-it-works, testimonial, CTA, footer |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
