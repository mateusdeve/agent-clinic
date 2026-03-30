---
phase: 02-auth-multi-tenancy
plan: 03
subsystem: auth-frontend
tags: [nextauth, nextjs, react-hook-form, zod, rbac, jwt, credentials, proxy, tailwind]

# Dependency graph
requires:
  - phase: 02-auth-multi-tenancy
    plan: 02
    provides: "FastAPI /auth/login endpoint returning access_token, role, tenant_id, user_id"
provides:
  - NextAuth v5 CredentialsProvider calling FastAPI /auth/login
  - proxy.ts route protection — unauthenticated redirect to /login, authenticated /login redirect to /home
  - Split-layout login page with react-hook-form + zod validation
  - Dashboard shell with header, sidebar (role-filtered nav), main content area
  - LogoutButton client component
  - Role-adaptive home page (admin/medico/recepcionista content cards)
  - Type augmentation for session.user.role, session.user.tenant_id, session.access_token
affects:
  - All future dashboard pages (use dashboard layout shell)
  - All protected routes (protected by proxy.ts matcher)
  - Any component that reads session.user.role for RBAC

# Tech tracking
tech-stack:
  added:
    - next-auth@5.0.0-beta.30 (NextAuth v5 beta — CredentialsProvider, JWT session, proxy.ts)
    - react-hook-form@7.56.4 (login form state management, uncontrolled inputs)
    - zod@4.3.6 (schema validation for login form)
    - @hookform/resolvers@5.2.3 (zod resolver bridge for react-hook-form)
  patterns:
    - NextAuth v5 CredentialsProvider with authorize() fetching FastAPI /auth/login
    - JWT session strategy — access_token stored in encrypted NextAuth cookie (D-02)
    - proxy.ts (NOT middleware.ts) for Next.js 16.2.1 route protection
    - ExtendedUser cast pattern for NextAuth v5 beta jwt callback typing limitation
    - /// <reference path> directive to include auth.d.ts type augmentation in auth.ts

key-files:
  created:
    - frontend/src/lib/auth.ts
    - frontend/src/lib/auth.d.ts
    - frontend/src/app/api/auth/[...nextauth]/route.ts
    - frontend/proxy.ts
    - frontend/src/app/(auth)/layout.tsx
    - frontend/src/app/(auth)/login/login-form.tsx
    - frontend/src/app/(dashboard)/layout.tsx
    - frontend/src/app/(dashboard)/logout-button.tsx
  modified:
    - frontend/src/app/(auth)/login/page.tsx
    - frontend/src/app/(dashboard)/home/page.tsx
    - frontend/package.json
    - frontend/tsconfig.json
    - frontend/.env.local

key-decisions:
  - "proxy.ts exports `proxy` function (not middleware.ts/middleware) — Next.js 16.2.1 uses proxy.ts per research Pattern 2"
  - "NextAuth v5 beta jwt callback user typed as User | AdapterUser — type augmentation doesn't propagate; ExtendedUser local cast used in auth.ts callbacks"
  - "auth.d.ts augments @auth/core/types User interface (NOT next-auth) — Session augmentation intentionally omitted since it breaks Session extends DefaultSession inheritance"
  - "tsconfig.json include kept standard; auth.d.ts pulled in via /// <reference path> in auth.ts"

patterns-established:
  - "Auth type pattern: /// <reference path=./auth.d.ts /> in auth.ts + declare module @auth/core/types User augmentation"
  - "Dashboard layout pattern: Server Component calling auth() + redirect if !session + role-conditional nav"
  - "Login form pattern: react-hook-form + zodResolver + signIn credentials redirect:false + router.push on success"

requirements-completed: [AUTH-01, AUTH-02, AUTH-03, AUTH-05, AUTH-06]

# Metrics
duration: 25min
completed: 2026-03-30
---

# Phase 2 Plan 3: NextAuth Frontend Integration + Login Page + Dashboard Shell Summary

**NextAuth v5 CredentialsProvider calling FastAPI JWT, split-layout login page (react-hook-form + zod), proxy.ts route protection, and role-adaptive dashboard shell with logout button**

## Performance

- **Duration:** 25 min
- **Started:** 2026-03-30T00:00:00Z
- **Completed:** 2026-03-30T00:25:00Z
- **Tasks:** 3 of 4 (Task 4 is checkpoint:human-verify, pending user verification)
- **Files created:** 8, files modified: 5

## Accomplishments

- Created `frontend/src/lib/auth.ts` — NextAuth v5 CredentialsProvider that fetches FastAPI `POST /auth/login`, jwt callback copies role/tenant_id/access_token to JWT token, session callback exposes them on session object; pages config sets signIn: "/login"
- Created `frontend/src/lib/auth.d.ts` — type augmentation for `@auth/core/types User` interface adding role, tenant_id, access_token; plus `next-auth/jwt JWT` augmentation; Session augmentation intentionally omitted (see Decisions)
- Created `frontend/src/app/api/auth/[...nextauth]/route.ts` — NextAuth API route exporting GET and POST from handlers
- Created `frontend/proxy.ts` — route protection using NextAuth's auth function; redirects unauthenticated users from protected paths to /login; redirects authenticated users from /login to /home
- Created split-layout login page: `(auth)/layout.tsx` (minimal full-height flex), `login/page.tsx` (green illustration left, form right), `login/login-form.tsx` (react-hook-form + zod + signIn credentials)
- Created dashboard shell: `(dashboard)/layout.tsx` (header with brand/user/logout, role-filtered sidebar nav, main content), `logout-button.tsx` (client component calling signOut), `home/page.tsx` (role-adaptive content cards per AUTH-06)
- Installed dependencies: next-auth@beta, react-hook-form, zod, @hookform/resolvers
- `next build` completes with zero TypeScript errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Install frontend auth dependencies and configure NextAuth v5** - `78ccc67` (feat)
2. **Task 2: Build login page with split layout and form** - `f2c6baf` (feat)
3. **Task 3: Create dashboard layout with logout and role-based visibility** - `af2c9cb` (feat)

**Task 4 (checkpoint:human-verify):** Pending user verification of full auth flow.

## Files Created/Modified

- `frontend/src/lib/auth.ts` — NextAuth config with CredentialsProvider, jwt/session callbacks
- `frontend/src/lib/auth.d.ts` — Type augmentation for User and JWT interfaces
- `frontend/src/app/api/auth/[...nextauth]/route.ts` — NextAuth API route handler
- `frontend/proxy.ts` — Route protection (unauthenticated -> /login, authenticated + /login -> /home)
- `frontend/src/app/(auth)/layout.tsx` — Minimal full-height layout for auth pages
- `frontend/src/app/(auth)/login/page.tsx` — Split-layout login page (Server Component)
- `frontend/src/app/(auth)/login/login-form.tsx` — Client Component login form with RHF + zod
- `frontend/src/app/(dashboard)/layout.tsx` — Dashboard shell with header, sidebar, main area
- `frontend/src/app/(dashboard)/logout-button.tsx` — Client Component logout button
- `frontend/src/app/(dashboard)/home/page.tsx` — Role-adaptive home page
- `frontend/package.json` — Added next-auth, react-hook-form, zod, @hookform/resolvers
- `frontend/tsconfig.json` — Added **/*.d.ts to include (for future .d.ts files)
- `frontend/.env.local` — Added AUTH_SECRET (empty, needs generation) and FASTAPI_URL

## Decisions Made

- proxy.ts named `proxy` function (not `middleware`) — Next.js 16.2.1 uses proxy.ts per the project research (RESEARCH.md Pattern 2)
- NextAuth v5 beta typing: jwt callback `user` parameter is typed as `User | AdapterUser` by NextAuth internally; module augmentation of `@auth/core/types User` is applied to consumer code but not to the jwt callback param. Solution: `ExtendedUser` local interface cast with `user as unknown as ExtendedUser` in auth.ts callbacks
- Session augmentation intentionally NOT added to `@auth/core/types Session` — augmenting `Session` there causes the `Session extends DefaultSession` inheritance to break (TypeScript drops `user` from the type). The `user.role/tenant_id` fields come from the `User` augmentation which flows through `DefaultSession.user?: User`
- `/// <reference path="./auth.d.ts" />` in auth.ts is required to pull in the type declarations — tsconfig `**/*.ts` glob does not auto-include `.d.ts` files in the same directory with `moduleResolution: bundler`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] NextAuth v5 beta type augmentation not propagating to jwt callback**
- **Found during:** Task 3 (next build type check)
- **Issue:** `declare module "@auth/core/types" { interface User { role: string } }` in auth.d.ts was not being included by tsconfig `**/*.ts` glob. The .d.ts file was not appearing in `tsc --listFiles`. Additionally, adding `Session { access_token }` augmentation broke `Session extends DefaultSession` inheritance (TypeScript dropped `user` from Session type).
- **Fix:** Added `/// <reference path="./auth.d.ts" />` to auth.ts to force inclusion. Used `ExtendedUser` local cast for jwt callback. Removed `Session` augmentation to preserve `DefaultSession.user` inheritance. Added `session as unknown as { user: ..., access_token }` cast for session callback.
- **Files modified:** `frontend/src/lib/auth.ts`, `frontend/src/lib/auth.d.ts`, `frontend/tsconfig.json`
- **Commit:** af2c9cb

## User Setup Required

Before running the auth flow, the user must:

1. Generate AUTH_SECRET and add to `frontend/.env.local`:
   ```bash
   npx auth secret
   # Add the output to frontend/.env.local: AUTH_SECRET=<generated>
   ```

2. Ensure FastAPI is running with JWT_SECRET_KEY set (from plan 02-02):
   ```bash
   cd agent-service
   # Ensure .env has JWT_SECRET_KEY set
   uvicorn src.api.webhook:app --reload
   ```

3. Create a test admin user via seed endpoint:
   ```bash
   curl -X POST http://localhost:8000/auth/seed \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@clinica.com","password":"admin123","name":"Admin Teste"}'
   ```

## Known Stubs

The dashboard home page contains placeholder content cards:
- `frontend/src/app/(dashboard)/home/page.tsx` lines 14-18: "Painel Administrativo / KPIs e gestao completa — Phase 5"
- `frontend/src/app/(dashboard)/home/page.tsx` lines 22-26: "Sua Agenda / Consultas do dia — Phase 3"
- `frontend/src/app/(dashboard)/home/page.tsx` lines 29-33: "Recepcao / Agendamentos e pacientes — Phase 3"

These are intentional placeholder stubs — the plan explicitly states "This creates placeholder cards that future phases will replace with real content." They do not prevent the plan's core goals (auth flow, role-based visibility, session management) from being achieved.

## Next Phase Readiness

- Complete auth flow is ready for verification (Task 4 checkpoint)
- After human verifies the flow, Phase 2 Plan 4 can proceed with protected API endpoints
- Dashboard shell layout is in place for all future pages to render within
- Role-based sidebar navigation links are pre-built for routes that Phase 3-5 will implement

## Self-Check: PASSED

Files verified on disk:
- frontend/src/lib/auth.ts: FOUND
- frontend/src/lib/auth.d.ts: FOUND
- frontend/src/app/api/auth/[...nextauth]/route.ts: FOUND
- frontend/proxy.ts: FOUND
- frontend/src/app/(auth)/layout.tsx: FOUND
- frontend/src/app/(auth)/login/login-form.tsx: FOUND
- frontend/src/app/(dashboard)/layout.tsx: FOUND
- frontend/src/app/(dashboard)/logout-button.tsx: FOUND
- frontend/src/app/(dashboard)/home/page.tsx: FOUND

Commits verified:
- 78ccc67 (feat Task 1): FOUND
- f2c6baf (feat Task 2): FOUND
- af2c9cb (feat Task 3): FOUND

`next build`: PASS (zero TypeScript errors, zero compilation errors)

---
*Phase: 02-auth-multi-tenancy*
*Completed: 2026-03-30 (Tasks 1-3; Task 4 pending human verification)*
