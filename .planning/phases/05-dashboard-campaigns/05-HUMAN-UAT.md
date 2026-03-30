---
status: partial
phase: 05-dashboard-campaigns
source: [05-VERIFICATION.md]
started: 2026-03-30T00:00:00Z
updated: 2026-03-30T00:00:00Z
---

## Current Test

[user approved visual walkthrough during checkpoint]

## Tests

### 1. Dashboard visual rendering (5 KPI cards + charts)
expected: Admin sees 5 KPI cards and 2 charts on /home
result: approved (checkpoint)

### 2. Role-based visibility
expected: Recepcionista sees no charts, medico redirected to /agenda
result: pending

### 3. Sidebar admin-only links
expected: Templates and Campanhas links visible to admin only
result: pending

### 4. Template live preview
expected: Typing {{nome}} shows sample data substituted in real-time
result: pending

### 5. Campaign wizard segment count
expected: Segment filter shows live patient count with debounce
result: pending

### 6. QuickSend in inbox
expected: Template button visible, modal opens with preview
result: pending

### 7. Overall visual correctness
expected: Layout, colors, Recharts rendering match design
result: pending

## Summary

total: 7
passed: 1
issues: 0
pending: 6
skipped: 0
blocked: 0

## Gaps
