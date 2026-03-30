---
status: partial
phase: 03-core-crud
source: [03-VERIFICATION.md]
started: 2026-03-30T04:00:00Z
updated: 2026-03-30T04:00:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Calendar visual rendering
expected: Time grid positioning correct, appointment blocks show correct colors (blue/green/gray/red) in Day/Week/Month views
result: [pending]

### 2. Appointment CRUD flow
expected: Create shows Agendado blue block, edit updates status, cancel shows motivo prompt and red strikethrough
result: [pending]

### 3. Patient search debounce
expected: 300ms delay before search fires, minimum 2 characters required
result: [pending]

### 4. WhatsApp chat timeline visual
expected: Bot messages white/left, patient messages green/right, bubble alignment correct
result: [pending]

### 5. Doctor schedule grid save
expected: Cell toggle state persists after PUT round-trip, saved schedules reload correctly
result: [pending]

### 6. User status toggle self-protection
expected: Current user's toggle is disabled, cannot deactivate self
result: [pending]

### 7. Medico role isolation
expected: Doctor filter hidden on /agenda, only own appointments visible, /medicos and /usuarios not accessible
result: [pending]

## Summary

total: 7
passed: 0
issues: 0
pending: 7
skipped: 0
blocked: 0

## Gaps
