---
phase: 01-foundation
plan: 01
subsystem: ui
tags: [nextjs, tailwind, shadcn, react, typescript, next-font, route-groups]

# Dependency graph
requires: []
provides:
  - Next.js 16.2.1 project scaffolded inside frontend/ with TypeScript and App Router
  - Tailwind 4 CSS-first design tokens (@theme) with green palette matching site.html
  - DM Serif Display + DM Sans fonts via next/font/google with CSS variables
  - shadcn/ui initialized (components.json) with Button component at src/components/ui/button.tsx
  - Route groups (landing), (auth), (dashboard) created with non-conflicting paths
  - cn() utility at src/lib/utils.ts
  - .env.local with NEXT_PUBLIC_WHATSAPP_NUMBER placeholder
affects: [01-02, 01-03, phase-2-auth, phase-3-dashboard]

# Tech tracking
tech-stack:
  added:
    - next@16.2.1
    - react@19.2.4
    - tailwindcss@4.2.2
    - "@tailwindcss/postcss@4.2.2"
    - typescript@6.0.2
    - "@radix-ui/react-slot"
    - class-variance-authority
    - clsx
    - tailwind-merge
    - lucide-react
  patterns:
    - "Tailwind 4 CSS-first: all design tokens declared via @theme in globals.css, no tailwind.config.ts"
    - "next/font/google for DM fonts: CSS variables injected via .variable on <html>, mapped to @theme --font-serif / --font-sans"
    - "Route groups (landing)/(auth)/(dashboard): stub pages at sub-paths (login/, home/) to avoid root / conflicts"
    - "shadcn components at src/components/ui/, utils at src/lib/utils.ts"

key-files:
  created:
    - frontend/src/app/globals.css
    - frontend/src/app/layout.tsx
    - frontend/src/app/(landing)/layout.tsx
    - frontend/src/app/(landing)/page.tsx
    - frontend/src/app/(auth)/login/page.tsx
    - frontend/src/app/(dashboard)/home/page.tsx
    - frontend/src/components/ui/button.tsx
    - frontend/src/lib/utils.ts
    - frontend/components.json
    - frontend/.env.local
    - frontend/package.json
    - frontend/postcss.config.mjs
    - frontend/tsconfig.json
  modified: []

key-decisions:
  - "shadcn init ran interactively — initialized manually (components.json + packages + button.tsx) to avoid interactive prompt in CI/agent context"
  - "Auth and dashboard stub pages placed at /login and /home sub-paths (not /) to avoid route conflict with (landing)/page.tsx which owns /"
  - "tailwind.config.ts not created — Tailwind 4 is CSS-first, all tokens live in globals.css @theme block"

patterns-established:
  - "Pattern: CSS tokens in @theme, not JS config. Add new design tokens to frontend/src/app/globals.css under @theme."
  - "Pattern: Fonts loaded via next/font/google. Add new fonts to frontend/src/app/layout.tsx."
  - "Pattern: Route groups for layout isolation — (landing), (auth), (dashboard) each get their own layout.tsx."

requirements-completed: [LAND-04]

# Metrics
duration: 5min
completed: 2026-03-29
---

# Phase 01 Plan 01: Next.js Scaffold and Design System Summary

**Next.js 16.2.1 scaffolded with Tailwind 4 @theme design tokens (green palette from site.html), DM Serif Display + DM Sans fonts via next/font, shadcn/ui Button, and route groups for landing/auth/dashboard**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-29T22:43:40Z
- **Completed:** 2026-03-29T22:48:11Z
- **Tasks:** 1 of 1
- **Files modified:** 24

## Accomplishments

- Scaffolded complete Next.js 16.2.1 project with TypeScript, App Router, src/ directory structure
- Configured Tailwind 4 CSS-first design tokens with the exact green palette (#2e9e60, #1e7d48, #0d2e1a, #edf7f0, etc.) and neutral grays from site.html
- Set up DM Serif Display and DM Sans fonts via next/font/google with CSS variable injection, lang="pt-BR"
- Initialized shadcn/ui manually (components.json + dependencies + Button component) and created cn() utility
- Created route groups (landing)/(auth)/(dashboard) with correct isolation, build passes with zero errors

## Task Commits

1. **Task 1: Scaffold Next.js project and configure design system** - `ac72fcd` (feat)

**Plan metadata:** (to be added by final commit)

## Files Created/Modified

- `frontend/src/app/globals.css` — Tailwind 4 @theme with full green palette and DM font variables
- `frontend/src/app/layout.tsx` — Root layout with DM_Serif_Display + DM_Sans, lang=pt-BR
- `frontend/src/app/(landing)/layout.tsx` — Landing route group layout shell
- `frontend/src/app/(landing)/page.tsx` — Placeholder landing page (Phase 01-02 builds the full landing page)
- `frontend/src/app/(auth)/login/page.tsx` — Auth stub for Phase 2
- `frontend/src/app/(dashboard)/home/page.tsx` — Dashboard stub for Phase 3
- `frontend/src/components/ui/button.tsx` — shadcn Button with CVA variants
- `frontend/src/lib/utils.ts` — cn() merge utility
- `frontend/components.json` — shadcn configuration pointing to globals.css
- `frontend/.env.local` — NEXT_PUBLIC_WHATSAPP_NUMBER placeholder
- `frontend/package.json` — All Next.js + Tailwind 4 + shadcn dependencies
- `frontend/postcss.config.mjs` — @tailwindcss/postcss plugin (Tailwind 4 required)
- `frontend/tsconfig.json` — TypeScript config with @/* alias

## Decisions Made

- **shadcn manual init:** `npx shadcn@latest init -y` launched an interactive library/preset selector that could not be bypassed with `-y`. Initialized manually by creating components.json, installing packages individually, and writing the Button component directly. Outcome matches what shadcn init would have produced.
- **Route group stub paths:** Auth and dashboard stubs placed at `/login` and `/home` sub-paths (not root `/`). Multiple route groups with `page.tsx` at `/` all resolve to the same path and cause a build error. The (landing)/page.tsx owns `/`.
- **No tailwind.config.ts:** Tailwind 4 is CSS-first. The scaffolder did not generate this file; design tokens live exclusively in globals.css @theme block.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed route conflict caused by multiple route-group root pages**
- **Found during:** Task 1 (build verification)
- **Issue:** Plan instructed creating `(auth)/page.tsx` and `(dashboard)/page.tsx` as stubs, but both resolve to `/` and conflict with `(landing)/page.tsx` — Next.js 16 throws "Two pages resolve to the same route"
- **Fix:** Moved auth stub to `(auth)/login/page.tsx` and dashboard stub to `(dashboard)/home/page.tsx` so they resolve to `/login` and `/home` respectively
- **Files modified:** Removed `(auth)/page.tsx`, `(dashboard)/page.tsx`; created `(auth)/login/page.tsx`, `(dashboard)/home/page.tsx`
- **Verification:** `npm run build` exits 0 with no errors
- **Committed in:** ac72fcd (Task 1 commit)

**2. [Rule 3 - Blocking] Manually initialized shadcn/ui (bypassed interactive prompt)**
- **Found during:** Task 1 (shadcn init step)
- **Issue:** `npx shadcn@latest init -y` launched an interactive terminal UI (library selector, preset selector) that cannot be bypassed with `-y` in agent context
- **Fix:** Installed shadcn dependencies manually (`class-variance-authority`, `clsx`, `tailwind-merge`, `lucide-react`, `@radix-ui/react-slot`), created `components.json` from RESEARCH.md spec, wrote `button.tsx` following shadcn source pattern
- **Files modified:** components.json, src/components/ui/button.tsx, src/lib/utils.ts
- **Verification:** Button component imports without error, `npm run build` passes
- **Committed in:** ac72fcd (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 bug fix, 1 blocking issue)
**Impact on plan:** Both fixes were necessary for build correctness. No scope creep.

## Issues Encountered

- `.env.local` was covered by `frontend/.gitignore` (`.env*` pattern). Force-added with `git add -f` since the file contains only a placeholder value with no secrets.

## Known Stubs

- `frontend/src/app/(landing)/page.tsx` — Placeholder page ("MedIA — Landing Page") with no real content. Plan 01-02 builds the full landing page with all sections.
- `frontend/src/app/(auth)/login/page.tsx` — Stub ("Auth — Phase 2"). Phase 2 builds real auth.
- `frontend/src/app/(dashboard)/home/page.tsx` — Stub ("Dashboard — Phase 3"). Phase 3 builds real dashboard.

These stubs are intentional scaffolding — they exist to establish route group isolation. Plan 01-02 will replace the landing stub with real content.

## User Setup Required

None — no external service configuration required. The `.env.local` file contains a placeholder WhatsApp number that will need to be updated before production use.

## Next Phase Readiness

- Ready for Plan 01-02: landing page component implementation (HeroSection, StatsSection, FeaturesSection, etc.)
- Design tokens, fonts, and route group structure are all in place
- Button component and cn() utility available for use in landing page components
- No blockers for next plan

---
*Phase: 01-foundation*
*Completed: 2026-03-29*
