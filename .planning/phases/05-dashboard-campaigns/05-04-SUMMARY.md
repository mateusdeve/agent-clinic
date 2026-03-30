---
phase: 05-dashboard-campaigns
plan: "04"
subsystem: ui
tags: [react, next.js, tailwind, campaigns, whatsapp, templates, tanstack-table]

requires:
  - phase: 05-01
    provides: Campaign and template types in types.ts, backend campaign API endpoints
  - phase: 05-02
    provides: DataTable, SlideOver, StatusBadge patterns; apiFetch utility

provides:
  - /campanhas list page with DataTable, polling, and Nova Campanha button
  - CampaignWizard 4-step wizard (template, segmento, preview, confirmar) with live segment count
  - CampaignStatusBadge and RecipientStatusBadge components
  - CampaignTable with buildCampaignColumns factory
  - /campanhas/[id] detail page with stats bar and per-recipient table with polling
  - RecipientTable with buildRecipientColumns factory
  - QuickSendModal for template dispatch from WhatsApp inbox
  - QuickSend wired into InboxPanel with Template button

affects: [phase-05-campaigns, whatsapp-panel, templates]

tech-stack:
  added: []
  patterns:
    - "Campaign wizard uses step-based state machine (WizardStep type) inside SlideOver"
    - "Live segment preview uses 500ms debounce on filter state changes"
    - "Campaign detail polls every 10s while status===enviando; list polls every 30s"
    - "QuickSendModal uses absolute positioned backdrop div (not dialog element) for simplicity"
    - "Template button overlays TakeoverBar using absolute right positioning"

key-files:
  created:
    - frontend/src/components/dashboard/CampaignStatusBadge.tsx
    - frontend/src/components/dashboard/CampaignTable.tsx
    - frontend/src/components/dashboard/CampaignWizard.tsx
    - frontend/src/app/(dashboard)/campanhas/page.tsx
    - frontend/src/components/dashboard/RecipientTable.tsx
    - frontend/src/app/(dashboard)/campanhas/[id]/page.tsx
    - frontend/src/components/dashboard/QuickSendModal.tsx
  modified:
    - frontend/src/app/(dashboard)/whatsapp/_components/InboxPanel.tsx

key-decisions:
  - "CampaignWizard step confirmar shows submit button in nav footer — no separate trigger needed"
  - "Template button in InboxPanel uses absolute positioning to overlay TakeoverBar right side without restructuring existing layout"
  - "StepConfirmar is split into dedicated sub-component with success/error state for clean render flow"

patterns-established:
  - "buildXxxColumns factory pattern (no props): CampaignTable, RecipientTable follow buildPatientColumns precedent from Phase 3"
  - "Polling pattern: useEffect returning clearInterval cleanup, triggered only when status condition met"
  - "WizardStep type alias for string union with step-based titles Record"

requirements-completed: [WPP-13, WPP-14, WPP-15, WPP-16]

duration: 12min
completed: 2026-03-30
---

# Phase 05 Plan 04: Campaign Management Pages Summary

**Campaign list/detail pages with 4-step creation wizard (template > segment > preview > confirm) and QuickSendModal in WhatsApp inbox for per-patient template dispatch**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-03-30T14:11:00Z
- **Completed:** 2026-03-30T14:23:33Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- /campanhas page lists all campaigns with status badges, delivery stats, and 30s polling for active sends
- CampaignWizard 4-step flow: template picker with selectable cards, segment filter with live count via preview-segment endpoint (500ms debounce), preview summary, and POST /api/campaigns confirm
- /campanhas/[id] detail shows 4-stat bar (enviado/entregue/lido/falha) + recipient table with polling every 10s while enviando
- QuickSendModal lets receptionists select a template and send to individual patient with live preview of variable substitution
- QuickSend wired into InboxPanel with a Template button overlaid on TakeoverBar

## Task Commits

1. **Task 1: CampaignStatusBadge + CampaignTable + CampaignWizard + campaigns list page** - `01c66a4` (feat)
2. **Task 2: Campaign detail page + RecipientTable + QuickSendModal in inbox** - `5ac8c5e` (feat)

## Files Created/Modified

- `frontend/src/components/dashboard/CampaignStatusBadge.tsx` - CampaignStatusBadge and RecipientStatusBadge components
- `frontend/src/components/dashboard/CampaignTable.tsx` - buildCampaignColumns factory with 6 columns
- `frontend/src/components/dashboard/CampaignWizard.tsx` - 4-step wizard in SlideOver with live segment preview
- `frontend/src/app/(dashboard)/campanhas/page.tsx` - Campaign list page with DataTable and polling
- `frontend/src/components/dashboard/RecipientTable.tsx` - buildRecipientColumns factory with 5 columns
- `frontend/src/app/(dashboard)/campanhas/[id]/page.tsx` - Campaign detail with stats bar and recipient table
- `frontend/src/components/dashboard/QuickSendModal.tsx` - Template quick-send modal with variable preview
- `frontend/src/app/(dashboard)/whatsapp/_components/InboxPanel.tsx` - Added QuickSendModal + Template button

## Decisions Made

- Template button in InboxPanel uses `absolute` right positioning over TakeoverBar's existing layout — avoids restructuring the 3-column InboxPanel
- CampaignWizard uses SlideOver wrapper consistent with other wizard patterns in the codebase
- Segment filter hardcodes common specialties matching the bot's domain knowledge (Cardiologia, Dermatologia, etc.)

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

TakeoverBar renders its own `border-b div` container. Initial edit wrapped it in another bordered div causing double border. Fixed by using `relative` wrapper on the outer div and `absolute right-4 top-1/2 -translate-y-1/2` positioning for the Template button — clean overlay without restructuring.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Campaign management UI fully implemented (create, list, detail, quick-send)
- Requirements WPP-13 through WPP-16 satisfied
- Next: Phase 05-05 (final plan) — integration verification, build check, and dashboard metrics
- No blockers

---
*Phase: 05-dashboard-campaigns*
*Completed: 2026-03-30*
