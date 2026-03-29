# Phase 2: Auth + Multi-Tenancy — Research

**Researched:** 2026-03-29
**Domain:** Authentication (NextAuth v5 + FastAPI JWT), PostgreSQL RLS, Alembic migrations, Next.js 16 proxy.ts
**Confidence:** HIGH (primary sources: official docs, verified against current versions)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** NextAuth.js handles login UI/session on frontend, FastAPI issues its own JWT with tenant_id + role for API calls. Two token layers: NextAuth session cookie + FastAPI access token.
- **D-02:** FastAPI JWT stored in httpOnly secure cookie. Requires CSRF protection on state-changing endpoints.
- **D-03:** Invite-only registration — Admin creates user accounts. No public signup page.
- **D-04:** No password recovery in v1 — Admin resets passwords manually. Avoids email sending infrastructure.
- **D-05:** Split layout — left side: illustration with medical/clinic theme on green background. Right side: login form with email + password fields.
- **D-06:** Login page follows MedIA brand identity (green palette, DM fonts) from landing page.
- **D-07:** Role checks on both layers — FastAPI middleware enforces roles on API routes (source of truth), Next.js middleware hides UI elements for UX. Defense in depth.
- **D-08:** Three roles only in v1: Admin, Recepcionista, Medico. No Super Admin — platform management done via database.
- **D-09:** All roles land on Dashboard after login. Dashboard content adapts by role.
- **D-10:** PostgreSQL Row-Level Security (RLS) — add tenant_id column to all data tables, create RLS policies. DB enforces isolation even if application code misses a WHERE clause.
- **D-11:** Migration via ALTER TABLE ADD tenant_id + backfill existing rows to a default "Clinic 1" tenant, then enable RLS. Zero data loss, existing WhatsApp bot keeps working.
- **D-12:** Use Alembic for database migrations (already in requirements.txt). Set up migration chain for tenant_id columns, RLS policies, users table, and roles.
- **D-13:** tenant_id extracted from JWT automatically (per TENANT-03), never passed as URL/query parameter.

### Claude's Discretion

- Login form error states and validation UX
- Exact CSRF protection mechanism
- JWT token expiration times and refresh strategy
- Alembic directory structure and naming conventions
- RLS policy exact syntax and testing approach
- Left-side illustration choice/style for login page

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AUTH-01 | Usuario pode fazer login com email e senha | NextAuth v5 CredentialsProvider + FastAPI POST /auth/login |
| AUTH-02 | Usuario pode fazer logout de qualquer pagina | NextAuth `signOut()` server action in proxy/layout |
| AUTH-03 | Sessao do usuario persiste entre recarregamentos do browser (JWT + refresh token) | NextAuth JWT session strategy + refresh token pattern |
| AUTH-04 | Sistema suporta tres roles: Admin, Recepcionista, Medico | JWT claims `role` field, session type augmentation |
| AUTH-05 | Rotas protegidas redirecionam usuario nao autenticado para login | proxy.ts `auth` export with authorized callback |
| AUTH-06 | Funcionalidades sao restritas por role (RBAC) | FastAPI Depends() role check + Next.js conditional rendering |
| TENANT-01 | Cada clinica tem dados completamente isolados (tenant_id em todas as tabelas) | PostgreSQL RLS policies via Alembic migration |
| TENANT-02 | Nenhum endpoint retorna dados de outra clinica | RLS + FastAPI middleware `SET LOCAL app.current_tenant_id` |
| TENANT-03 | tenant_id e extraido do JWT automaticamente, nunca passado como parametro | FastAPI dependency `get_current_tenant` from JWT |
| API-02 | FastAPI implementa autenticacao JWT com refresh token | PyJWT + pwdlib, `/auth/login` + `/auth/refresh` endpoints |
| API-03 | FastAPI implementa middleware de multi-tenancy com filtro automatico por tenant_id | FastAPI middleware + psycopg2 SET LOCAL pattern |
</phase_requirements>

---

## Summary

Phase 2 has two independent but tightly coupled concerns: authentication (NextAuth v5 + FastAPI JWT) and multi-tenancy (PostgreSQL RLS + Alembic migrations). The auth system follows a two-token architecture: NextAuth manages the browser session in an encrypted httpOnly cookie, while FastAPI issues its own JWT containing `user_id`, `tenant_id`, and `role`. The FastAPI JWT is stored inside the NextAuth session and forwarded as a Bearer token on every API call.

The multi-tenancy implementation uses PostgreSQL Row-Level Security as the enforcement layer. Alembic (already in requirements.txt at 1.16.5) needs to be initialized in `agent-service/` and a migration chain written to: (1) create `tenants` and `users` tables, (2) add `tenant_id` UUID columns to all existing tables, (3) backfill with a default tenant UUID, (4) enable RLS and create policies. The WhatsApp bot (Sofia/Carla) continues writing to the DB as-is — it operates on a bypassed DB user (`BYPASSRLS`) or using a service role that skips RLS, ensuring the existing pipeline is not disrupted.

**Primary recommendation:** Implement the DB layer first (Alembic init → migrations → RLS), then the FastAPI auth endpoints, then the NextAuth frontend integration. The DB layer is the riskiest because it modifies existing production tables — get that right before touching the auth UI.

---

## Standard Stack

### Core — Frontend (NextAuth)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| next-auth | 5.0.0-beta.30 | Session management, CredentialsProvider, proxy.ts integration | Official Auth.js for Next.js App Router |
| react-hook-form | 7.72.0 | Login form state, validation, submission | Performant, uncontrolled, minimal re-renders |
| zod | 4.3.6 | Schema validation for login form | TypeScript-first, integrates with RHF resolver |
| @hookform/resolvers | 5.2.2 | Bridge between zod and react-hook-form | Standard bridge package |

### Core — Backend (FastAPI JWT)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyJWT | 2.12.1 | JWT encode/decode (FastAPI official docs recommendation) | Official FastAPI docs use PyJWT over python-jose |
| pwdlib[argon2] | 0.2.1 | Password hashing (Argon2 algorithm) | FastAPI official docs recommendation as of 2025 |
| alembic | 1.16.5 | Database migrations (already in requirements.txt) | Already decided (D-12) |

> **Note on python-jose vs PyJWT:** The FastAPI official tutorial (as of 2026) switched from `python-jose` to `PyJWT` (`pyjwt`). `python-jose` is still at 3.5.0 with limited recent updates. Use `PyJWT==2.12.1` as the primary JWT library.

> **Note on passlib vs pwdlib:** `passlib` (1.7.4, 2019 release, unmaintained) is the legacy option. FastAPI docs now recommend `pwdlib[argon2]` (0.2.1). Argon2 is the strongest hash algorithm. Both are viable — `pwdlib` is the forward-looking choice.

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-multipart | latest | Required for OAuth2PasswordRequestForm in FastAPI | FastAPI form parsing |
| fastapi-csrf-protect | latest | Double-submit CSRF tokens for state-changing endpoints | D-02 requires CSRF protection |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PyJWT | python-jose | python-jose has broader JOSE support but is less maintained and not in FastAPI official docs |
| pwdlib[argon2] | passlib[bcrypt] | passlib is unmaintained since 2020 but has more docs/examples online; either works |
| next-auth@beta | better-auth | better-auth is newer, stable, has more features — but less documentation/community |

**Installation (Frontend):**
```bash
cd frontend
npm install next-auth@beta react-hook-form zod @hookform/resolvers
```

**Installation (Backend):**
```bash
cd agent-service
pip install pyjwt "pwdlib[argon2]" python-multipart fastapi-csrf-protect
# Then add to requirements.txt
```

**Version verification (confirmed 2026-03-29):**
- `next-auth` beta: 5.0.0-beta.30
- `react-hook-form`: 7.72.0
- `zod`: 4.3.6
- `@hookform/resolvers`: 5.2.2
- `PyJWT` (pyjwt): 2.12.1
- `pwdlib`: 0.2.1
- `alembic`: 1.16.5 (already in requirements.txt)

---

## Architecture Patterns

### Recommended Project Structure — Frontend Auth

```
frontend/src/
├── app/
│   ├── (auth)/
│   │   ├── layout.tsx         # Minimal layout, no sidebar
│   │   └── login/
│   │       └── page.tsx       # Split-screen login page (replaces stub)
│   ├── (dashboard)/
│   │   ├── layout.tsx         # Sidebar + header, requires auth
│   │   └── home/page.tsx      # Role-adaptive dashboard stub
│   └── api/
│       └── auth/
│           └── [...nextauth]/
│               └── route.ts   # NextAuth handler: export { handlers as GET, POST }
├── lib/
│   ├── auth.ts                # NextAuth config: CredentialsProvider + callbacks
│   └── auth.d.ts              # Type augmentation for session (role, tenant_id, access_token)
└── proxy.ts                   # Route protection (NOT middleware.ts — Next.js 16)
```

### Recommended Project Structure — Backend Auth

```
agent-service/
├── alembic/                   # Created by: alembic init alembic
│   ├── versions/
│   │   ├── 001_create_tenants_users.py
│   │   ├── 002_add_tenant_id_columns.py
│   │   └── 003_enable_rls_policies.py
│   ├── env.py                 # Configure target_metadata = None (raw SQL migrations)
│   └── script.py.mako
├── alembic.ini                # sqlalchemy.url = %(DATABASE_URL)s
└── src/
    └── api/
        ├── auth.py            # NEW: /auth/login, /auth/refresh, /auth/me endpoints
        ├── deps.py            # NEW: get_current_user, require_role, get_current_tenant
        └── webhook.py         # EXISTING: mount new auth router here
```

---

### Pattern 1: NextAuth v5 Configuration with External Backend

**What:** `auth.ts` uses CredentialsProvider to call FastAPI `/auth/login`. The FastAPI JWT is stored in the NextAuth token and forwarded on API calls.

**When to use:** Always — this is the single source of truth for the frontend session.

```typescript
// Source: authjs.dev + codevoweb.com verified
// frontend/src/lib/auth.ts
import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";

export const { handlers, auth, signIn, signOut } = NextAuth({
  session: { strategy: "jwt" },
  providers: [
    Credentials({
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        const res = await fetch(`${process.env.FASTAPI_URL}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: credentials.email,
            password: credentials.password,
          }),
        });
        if (!res.ok) return null;
        const data = await res.json();
        return {
          id: data.user_id,
          email: data.email,
          name: data.name,
          role: data.role,
          tenant_id: data.tenant_id,
          access_token: data.access_token,
        };
      },
    }),
  ],
  callbacks: {
    jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.role = user.role;
        token.tenant_id = user.tenant_id;
        token.access_token = user.access_token;
      }
      return token;
    },
    session({ session, token }) {
      session.user.id = token.id as string;
      session.user.role = token.role as string;
      session.user.tenant_id = token.tenant_id as string;
      session.access_token = token.access_token as string;
      return session;
    },
  },
  pages: {
    signIn: "/login",
  },
});
```

```typescript
// frontend/src/lib/auth.d.ts — TypeScript type augmentation
import "next-auth";

declare module "next-auth" {
  interface User {
    role: string;
    tenant_id: string;
    access_token: string;
  }
  interface Session {
    user: User;
    access_token: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    id: string;
    role: string;
    tenant_id: string;
    access_token: string;
  }
}
```

---

### Pattern 2: Next.js 16 proxy.ts (NOT middleware.ts)

**What:** Next.js 16 renamed `middleware.ts` to `proxy.ts`. The exported function is `proxy`, not `middleware`. Auth.js exports `auth as proxy` directly.

**Critical:** This is a breaking change from Next.js 15. The project uses Next.js 16.2.1. Use `proxy.ts`.

```typescript
// Source: nextjs.org/docs/app/api-reference/file-conventions/proxy (verified 2026-03-25)
// frontend/proxy.ts (project root, same level as package.json)
export { auth as proxy } from "@/lib/auth";

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
```

For role-based redirect logic:
```typescript
// frontend/proxy.ts — more explicit version
import { auth } from "@/lib/auth";

export const proxy = auth((req) => {
  const { pathname } = req.nextUrl;
  const isProtected = pathname.startsWith("/(dashboard)") || pathname.startsWith("/home");

  if (!req.auth && isProtected) {
    return Response.redirect(new URL("/login", req.nextUrl.origin));
  }

  if (req.auth && pathname === "/login") {
    return Response.redirect(new URL("/home", req.nextUrl.origin));
  }
});

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
```

---

### Pattern 3: NextAuth Route Handler

**What:** The API route for NextAuth must export both GET and POST from the handlers object.

```typescript
// Source: authjs.dev/reference/nextjs (verified)
// frontend/src/app/api/auth/[...nextauth]/route.ts
import { handlers } from "@/lib/auth";
export const { GET, POST } = handlers;
```

---

### Pattern 4: FastAPI Auth Endpoints (PyJWT + pwdlib)

**What:** FastAPI issues its own JWT on login. This JWT contains `user_id`, `tenant_id`, `role`. It is returned in the JSON response body (not as a cookie set by FastAPI — the httpOnly cookie requirement from D-02 is fulfilled by NextAuth's encrypted session cookie wrapping it).

```python
# Source: fastapi.tiangolo.com/tutorial/security/oauth2-jwt/ (verified 2026-03-29)
# agent-service/src/api/auth.py
import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pydantic import BaseModel

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user_id: str
    email: str
    name: str
    role: str
    tenant_id: str


def create_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    # Load user from DB here
    return payload  # {sub, tenant_id, role, exp}


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    # 1. Fetch user from DB by email
    # 2. Verify password: password_hash.verify(request.password, user.hashed_password)
    # 3. Create tokens with tenant_id and role in claims
    access_token = create_token(
        {"sub": user.id, "tenant_id": str(user.tenant_id), "role": user.role},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_token(
        {"sub": user.id, "type": "refresh"},
        timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user_id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
        tenant_id=str(user.tenant_id),
    )
```

---

### Pattern 5: FastAPI Tenant Isolation Dependency

**What:** Extract `tenant_id` from the JWT in every protected endpoint. Never accept it as a URL/query param.

```python
# agent-service/src/api/deps.py
from typing import Annotated
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_tenant(token: Annotated[str, Depends(oauth2_scheme)]) -> str:
    """Extract tenant_id from JWT. Used as dependency on all protected endpoints."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        tenant_id = payload.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=401, detail="Token sem tenant_id")
        return tenant_id
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


def require_role(*roles: str):
    """Dependency factory for role-based access control."""
    async def _check(token: Annotated[str, Depends(oauth2_scheme)]):
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_role = payload.get("role")
        if user_role not in roles:
            raise HTTPException(status_code=403, detail="Permissão insuficiente")
        return payload
    return _check


# Usage in endpoints:
# @router.get("/patients")
# async def list_patients(tenant_id: str = Depends(get_current_tenant)):
#     # tenant_id is always from JWT, never from request
```

---

### Pattern 6: PostgreSQL RLS Setup

**What:** Enable RLS on all data tables with a single tenant isolation policy using session variables. Use `SET LOCAL` (transaction-scoped) not `SET` (session-scoped) for correctness with connection pooling.

```sql
-- Migration 003: Enable RLS on data tables
-- Source: postgresql.org/docs/current/ddl-rowsecurity.html + crunchydata.com/blog (verified)

-- Helper function to read tenant context
CREATE OR REPLACE FUNCTION current_tenant_id()
RETURNS UUID AS $$
BEGIN
    RETURN NULLIF(current_setting('app.tenant_id', TRUE), '')::UUID;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- Enable RLS on all data tables
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE doctors ENABLE ROW LEVEL SECURITY;
ALTER TABLE doctor_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE follow_ups ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_chunks ENABLE ROW LEVEL SECURITY;

-- Create isolation policy (one per table, covers ALL operations)
CREATE POLICY tenant_isolation ON patients
    USING (tenant_id = current_tenant_id())
    WITH CHECK (tenant_id = current_tenant_id());
-- (repeat for each table)

-- The app_user must have RLS enforced (default behavior)
-- The WhatsApp bot service user needs BYPASSRLS or explicit tenant setting
```

**FastAPI middleware to set tenant context per request:**
```python
# agent-service/src/api/webhook.py (or new middleware file)
# SET LOCAL is transaction-scoped — correct for connection pools
from contextlib import contextmanager

@contextmanager
def _get_db_for_tenant(tenant_id: str):
    """Get DB connection with tenant context set for RLS."""
    import psycopg2
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    try:
        with conn.cursor() as cur:
            # SET LOCAL: only affects current transaction
            cur.execute("SET LOCAL app.tenant_id = %s", (str(tenant_id),))
        yield conn
    finally:
        conn.close()
```

---

### Pattern 7: Alembic Initialization and Migration Chain

**What:** Initialize Alembic in `agent-service/`, configure it to use raw SQL (not autogenerate — the project uses raw psycopg2, not SQLAlchemy models for migrations), and create 3 migrations.

```bash
# Run in agent-service/ directory
alembic init alembic
```

```ini
# alembic.ini — key change
sqlalchemy.url =
# Leave blank — use env.py to read from environment
```

```python
# alembic/env.py — raw SQL migration mode
import os
from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config

def run_migrations_online():
    url = os.getenv("DATABASE_URL")
    connectable = create_engine(url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()
```

Migration chain:
1. `001_create_tenants_users` — `tenants` table, `users` table (with hashed_password, role, tenant_id FK)
2. `002_add_tenant_id_columns` — ALTER TABLE for patients, appointments, doctors, doctor_schedules, follow_ups, conversations, conversation_summaries, knowledge_chunks + backfill with default tenant UUID
3. `003_enable_rls_policies` — CREATE FUNCTION current_tenant_id(), ENABLE RLS, CREATE POLICY on all tables

---

### Pattern 8: Login Page (Split Layout)

**What:** Split-screen layout matching D-05 and D-06. Server Component for the illustration side, Client Component for the form (required for react-hook-form).

```
(auth)/login/page.tsx  →  Server Component
├── Left: <div class="hidden lg:flex bg-green-600"> illustration </div>
└── Right: <LoginForm /> → 'use client' component with react-hook-form + zod
```

---

### Anti-Patterns to Avoid

- **Using `middleware.ts` instead of `proxy.ts`:** Next.js 16 deprecated middleware.ts. The file must be `proxy.ts` with exported `proxy` function (not `middleware`).
- **Storing FastAPI JWT in localStorage:** Vulnerable to XSS. The token lives inside NextAuth's encrypted session cookie (httpOnly). Next.js Server Actions forward it to FastAPI.
- **`SET` instead of `SET LOCAL` for tenant context:** `SET` persists for the connection session. In a pool, the next user gets the previous user's tenant. Use `SET LOCAL` (transaction-scoped).
- **Enabling RLS without BYPASSRLS for the bot:** The WhatsApp bot (Sofia/Carla) writes to DB with no tenant context. After RLS is enabled, all inserts will fail unless the bot's DB connection either (a) sets the tenant_id before writes or (b) uses a role with BYPASSRLS. The bot needs to set `app.tenant_id` before any DB write.
- **Autogenerate Alembic with SQLAlchemy models:** The project uses raw psycopg2, not SQLAlchemy ORM models. Autogenerate won't work. Use `op.execute()` with raw SQL in migration scripts.
- **Running `alembic upgrade head` before backfilling:** If you enable RLS before backfilling existing rows with a tenant_id, the bot's existing data becomes invisible. Order: (1) add columns + default, (2) backfill, (3) enable RLS.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Session management | Custom JWT cookie handling | NextAuth v5 | Cookie rotation, CSRF, secure flags, token encryption handled |
| Password hashing | Custom hash function | pwdlib[argon2] | Argon2 timing attack resistance, salt handling |
| JWT encode/decode | Custom base64 | PyJWT | Expiry validation, algorithm selection, InvalidTokenError |
| Route protection | Custom auth check per page | proxy.ts + `auth()` | Runs before rendering, no server component boilerplate |
| Form validation | Custom regex validation | zod + react-hook-form | Type inference, nested errors, async validation |
| DB migrations | Hand-written ALTER TABLE scripts | Alembic | Migration history, rollback support, version control |

**Key insight:** The auth surface area is large — each shortcut creates a vulnerability. Use libraries for all security-sensitive operations.

---

## Runtime State Inventory

This phase modifies the production database schema of a live WhatsApp bot. Every category must be answered explicitly.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `patients`, `appointments`, `doctors`, `doctor_schedules`, `follow_ups`, `conversations`, `conversation_summaries`, `knowledge_chunks` — none have `tenant_id` column yet | Alembic migration: ALTER TABLE ADD COLUMN + backfill + RLS enable |
| Live service config | WhatsApp bot (Sofia/Carla) is active and writes to DB without tenant context | Bot's `_get_db()` calls must SET LOCAL app.tenant_id before writes, OR the bot DB user needs BYPASSRLS privilege |
| OS-registered state | APScheduler runs follow-up dispatcher inside the FastAPI process (not Task Scheduler/cron) | None — APScheduler is in-process; existing follow-ups backfilled to default tenant |
| Secrets/env vars | `DATABASE_URL` in `.env` — unchanged. New: `JWT_SECRET_KEY` needed for PyJWT signing | Add `JWT_SECRET_KEY` to `.env` and `.env.example` |
| Build artifacts | No compiled artifacts. `alembic/` directory is new — must be git-committed | Run `alembic init alembic` and commit generated files |

**Critical:** The WhatsApp bot writes to `patients`, `appointments`, `follow_ups`, and `conversations` tables. After RLS is enabled, every write needs `tenant_id` set. Two strategies:
1. **Preferred (D-11 compatible):** All existing bot writes get a hardcoded default `tenant_id = <clinic1_uuid>` via the backfill. The bot's `_get_db()` continues to work if the DB connection user has `BYPASSRLS` privilege — no code change to the bot.
2. **Alternative:** Update each `_get_db()` call in the bot to set `SET LOCAL app.tenant_id = <clinic1_uuid>` before queries. More surgical but requires touching bot code.

The plan should choose Strategy 1 (BYPASSRLS for the bot's DB user) to satisfy D-11 (zero data loss, existing bot keeps working without code changes).

---

## Common Pitfalls

### Pitfall 1: proxy.ts vs middleware.ts Confusion

**What goes wrong:** Developer creates `middleware.ts` (as in all Next.js 15 tutorials), exports `middleware` function. Next.js 16 ignores it silently. All routes are unprotected.

**Why it happens:** All existing tutorials and most LLM training data references `middleware.ts`. Next.js 16 deprecated it.

**How to avoid:** File must be `proxy.ts` at project root (same level as `package.json`). Export named `proxy` function (or use `export { auth as proxy }`). Run codemod: `npx @next/codemod@canary middleware-to-proxy .`

**Warning signs:** Routes are not redirecting even though proxy.ts has redirect logic; no 401s for unauthenticated requests.

---

### Pitfall 2: RLS Breaks the WhatsApp Bot

**What goes wrong:** Migrations enable RLS on `patients` table. Bot tries to INSERT a new patient but `current_tenant_id()` returns NULL (no SET LOCAL called). PostgreSQL rejects the insert. Patients can no longer be registered by the bot.

**Why it happens:** The bot's `_get_db()` context manager creates a plain psycopg2 connection with no tenant context set. After RLS is enabled, all rows fail the policy check.

**How to avoid:** Grant `BYPASSRLS` to the application DB user used by the bot OR ensure migration 003 (RLS enable) creates a separate `app_service` role with BYPASSRLS for the bot, and a restricted `app_web` role for the web API.

**Warning signs:** Bot stops creating patient records; `salvar_paciente()` logs `[patients] salvar_paciente error:` with a permission error.

---

### Pitfall 3: SET vs SET LOCAL in Connection Pool

**What goes wrong:** Tenant A's request sets `SET app.tenant_id = 'A'` on a pooled connection. Request finishes, connection returned to pool. Tenant B's request gets that connection — `app.tenant_id` is still `'A'`. Tenant B reads Tenant A's data.

**Why it happens:** PostgreSQL `SET` is session-scoped. Connection pools reuse sessions.

**How to avoid:** Always use `SET LOCAL app.tenant_id = %s` — this only affects the current transaction and resets automatically when the transaction ends.

**Warning signs:** Data from one clinic appearing in another clinic's views; intermittent cross-tenant data leaks that are hard to reproduce.

---

### Pitfall 4: next-auth@beta Version Pinning

**What goes wrong:** Developer runs `npm install next-auth@beta` without pinning — gets a future breaking beta. Auth callbacks no longer work.

**Why it happens:** `@beta` tag floats to latest beta. Next-auth v5 remains in beta as of 2026-03-29.

**How to avoid:** Pin to exact beta version in `package.json`: `"next-auth": "5.0.0-beta.30"`. Update deliberately.

**Warning signs:** TypeScript errors in `auth.ts` after an `npm update`; `signIn`/`signOut` imports break.

---

### Pitfall 5: Alembic Migration Order Violation

**What goes wrong:** Developer runs migration 003 (enable RLS) before migration 002 (backfill tenant_id). Existing rows have NULL tenant_id. All existing data becomes invisible to every tenant.

**Why it happens:** Running migrations out of order, or running `alembic upgrade head` on a partially-initialized database.

**How to avoid:** Alembic enforces order via the revision chain (`down_revision`). Always run `alembic upgrade head` — never skip versions. Verify with `alembic current` before upgrading.

**Warning signs:** All tables appear empty after migration; no data in the application.

---

### Pitfall 6: NextAuth Session Does Not Include FastAPI Token

**What goes wrong:** Login succeeds, user is authenticated in NextAuth, but API calls to FastAPI return 401. The `access_token` from FastAPI was not persisted in the session.

**Why it happens:** The `jwt` callback was not implemented to copy `user.access_token` to `token`. Or the `session` callback was not implemented to copy `token.access_token` to `session`.

**How to avoid:** Both `jwt` and `session` callbacks must be implemented. The `jwt` callback runs first and persists to the encrypted cookie. The `session` callback runs on `auth()` calls and exposes the token to the client. (See Pattern 1 above.)

**Warning signs:** `session.access_token` is undefined in server components; Authorization header on API calls is `Bearer undefined`.

---

## Code Examples

### Login Form with React Hook Form + Zod (Client Component)

```typescript
// Source: react-hook-form.com + zod.dev (standard pattern)
"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";

const loginSchema = z.object({
  email: z.string().email("Email inválido"),
  password: z.string().min(8, "Senha deve ter ao menos 8 caracteres"),
});

type LoginForm = z.infer<typeof loginSchema>;

export function LoginForm() {
  const router = useRouter();
  const { register, handleSubmit, formState: { errors, isSubmitting }, setError } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  async function onSubmit(data: LoginForm) {
    const result = await signIn("credentials", {
      email: data.email,
      password: data.password,
      redirect: false,
    });
    if (result?.error) {
      setError("root", { message: "Email ou senha incorretos" });
    } else {
      router.push("/home");
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {/* fields + error display */}
    </form>
  );
}
```

### FastAPI Protected Endpoint with Tenant Isolation

```python
# Source: fastapi.tiangolo.com/tutorial/security/dependencies (verified pattern)
from fastapi import APIRouter, Depends
from src.api.deps import get_current_tenant, require_role

router = APIRouter()

@router.get("/patients")
async def list_patients(tenant_id: str = Depends(get_current_tenant)):
    with _get_db_for_tenant(tenant_id) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT phone, nome FROM patients")
            rows = cur.fetchall()
    return [{"phone": r[0], "nome": r[1]} for r in rows]


@router.post("/users")
async def create_user(
    user_data: CreateUserRequest,
    _: dict = Depends(require_role("Admin")),
    tenant_id: str = Depends(get_current_tenant),
):
    # Admin-only endpoint
    ...
```

### Alembic Raw SQL Migration

```python
# Source: alembic official docs (standard pattern for raw SQL)
# alembic/versions/002_add_tenant_id_columns.py
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    # Add tenant_id column to all data tables
    tables = [
        "patients", "appointments", "doctors", "doctor_schedules",
        "follow_ups", "conversations", "conversation_summaries", "knowledge_chunks"
    ]
    for table in tables:
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS tenant_id UUID")

    # Backfill existing rows with default tenant UUID
    # The UUID comes from the tenants table created in migration 001
    op.execute("""
        UPDATE patients SET tenant_id = (SELECT id FROM tenants WHERE nome = 'Clínica Padrão' LIMIT 1)
        WHERE tenant_id IS NULL
    """)
    # ... repeat for each table ...

    # Add NOT NULL constraint after backfill
    for table in tables:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN tenant_id SET NOT NULL")


def downgrade():
    for table in ["patients", "appointments", "doctors", "doctor_schedules",
                  "follow_ups", "conversations", "conversation_summaries", "knowledge_chunks"]:
        op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS tenant_id")
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `middleware.ts` | `proxy.ts` | Next.js 16.0.0 (2026) | File rename required; middleware.ts is deprecated |
| `python-jose` | `PyJWT` | FastAPI docs updated 2024-2025 | python-jose less maintained; PyJWT is the official recommendation |
| `passlib[bcrypt]` | `pwdlib[argon2]` | FastAPI docs updated 2024-2025 | passlib unmaintained since 2020; pwdlib is the new standard |
| `getServerSession()` + `getToken()` | unified `auth()` | NextAuth v5 | One function for all contexts (server components, API routes, middleware) |
| `export default function middleware()` | `export function proxy()` or `export { auth as proxy }` | Next.js 16.0.0 | Named export rename |

**Deprecated/outdated:**
- `next-auth/middleware` import: Replaced by `export { auth as proxy }` from your own auth.ts
- `pages/api/auth/[...nextauth].ts` file location: Replaced by `src/app/api/auth/[...nextauth]/route.ts`
- `getServerSession(authOptions)` call pattern: Replaced by `await auth()` with no arguments

---

## Open Questions

1. **CSRF protection mechanism**
   - What we know: D-02 requires CSRF protection on state-changing endpoints. FastAPI returns JWT in JSON body (not as a cookie). NextAuth wraps it in an httpOnly encrypted cookie.
   - What's unclear: Since the FastAPI JWT is inside NextAuth's session cookie (SameSite=Lax by default), and API calls are made server-side from Next.js server actions (not directly from the browser), CSRF risk is significantly reduced. The double-submit cookie pattern may be overkill.
   - Recommendation: For Phase 2, rely on NextAuth's built-in CSRF protection (SameSite=Lax + CSRF token for signIn/signOut). Implement `fastapi-csrf-protect` only if the frontend makes direct cross-origin browser requests to FastAPI (which it shouldn't in this architecture).

2. **Token refresh strategy**
   - What we know: Access token expires in 15-30 min. Refresh token in 7 days. NextAuth `jwt` callback can check expiry and refresh.
   - What's unclear: Exact refresh endpoint implementation in FastAPI; whether NextAuth session update on token refresh needs a dedicated `/auth/refresh` endpoint.
   - Recommendation: Implement `/auth/refresh` in FastAPI. In the NextAuth `jwt` callback, check `token.exp` and call `/auth/refresh` when within 5 minutes of expiry. Return new tokens to update the session.

3. **WhatsApp bot DB user and RLS**
   - What we know: The bot uses `DATABASE_URL` which connects as the main app user. After RLS is enabled, all queries without tenant context fail.
   - What's unclear: Whether the existing PostgreSQL user has `BYPASSRLS` privilege or if a new database user must be created.
   - Recommendation: Migration 003 should include `ALTER ROLE <app_user> BYPASSRLS` as a short-term solution for the bot. Long-term, the bot's writes should be scoped to the correct tenant. The plan should document this explicitly.

---

## Project Constraints (from CLAUDE.md)

| Directive | Impact on Phase 2 |
|-----------|-------------------|
| Tech stack frontend: Next.js + Tailwind CSS | Use NextAuth v5, not Clerk/Auth0. Login page uses existing Tailwind 4 design tokens. |
| Tech stack backend: Python/FastAPI — manter | Auth endpoints are Python FastAPI, not Node.js. No Prisma, no tRPC. |
| Idioma: Interface em pt-BR | All UI text, error messages, form labels in Portuguese. |
| Design: Seguir identidade visual do site.html (paleta verde, DM) | Login page uses `--color-green-500` (#2e9e60), `--font-sans` (DM Sans), `--font-serif` (DM Serif Display). |
| Backend uses raw psycopg2 with `_get_db()` context manager | All new DB code follows same pattern. No SQLAlchemy ORM queries. Alembic migrations use `op.execute()` with raw SQL. |
| Module-scoped loggers with `[module]` prefix | New modules: `logger = logging.getLogger("agent-clinic.auth")`, log as `[auth] user logged in: {email}` |
| Error handling: broad except + log + return safe default | Auth modules follow same pattern: `except Exception as e: logger.error(f"[auth] login error: {e}"); raise HTTPException(500)` |
| snake_case for Python, PascalCase for classes | `get_current_user()`, `require_role()`, `create_access_token()`. Classes: `TokenResponse`, `LoginRequest`. |
| GSD Workflow Enforcement: start through GSD commands | Phase is already going through GSD — compliant. |

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js (npm) | next-auth, react-hook-form, zod | Yes | npm 16.2.1 runtime | — |
| Python 3 (pip) | PyJWT, pwdlib, alembic | Yes | Python 3.9.6 | — |
| PostgreSQL | RLS migrations | Unknown — not directly verifiable | — | Must be running before `alembic upgrade head` |
| alembic CLI | DB migrations | Not in system PATH (in venv) | 1.16.5 in requirements.txt | Use `.venv/bin/alembic` or `python -m alembic` |
| next-auth@5.0.0-beta.30 | Auth frontend | Not yet installed | — | Install: `npm install next-auth@beta` |
| PyJWT 2.12.1 | Auth backend | Not yet installed | — | Install: `pip install pyjwt` |
| pwdlib[argon2] 0.2.1 | Password hashing | Not yet installed | — | Install: `pip install "pwdlib[argon2]"` |

**Missing dependencies with no fallback:**
- PostgreSQL must be accessible via `DATABASE_URL` before running Alembic migrations

**Missing dependencies with fallback:**
- alembic CLI: use `python -m alembic` from activated venv instead of system `alembic`

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 (already in requirements.txt) |
| Config file | None detected — Wave 0 creates pytest.ini |
| Quick run command | `python -m pytest tests/ -x -q` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AUTH-01 | POST /auth/login with valid credentials returns access_token + tenant_id + role | integration | `pytest tests/test_auth.py::test_login_success -x` | Wave 0 |
| AUTH-01 | POST /auth/login with wrong password returns 401 | integration | `pytest tests/test_auth.py::test_login_wrong_password -x` | Wave 0 |
| AUTH-02 | signOut clears session | manual | — | Manual only — requires browser |
| AUTH-03 | JWT stored in NextAuth session persists across requests | manual | — | Manual only — requires browser |
| AUTH-04 | JWT payload contains role field with value Admin/Recepcionista/Medico | unit | `pytest tests/test_auth.py::test_token_contains_role -x` | Wave 0 |
| AUTH-05 | Unauthenticated request to /home redirects to /login | manual | — | Manual only — requires browser |
| AUTH-06 | Admin-only endpoint returns 403 for Recepcionista role | integration | `pytest tests/test_auth.py::test_rbac_medico_forbidden -x` | Wave 0 |
| TENANT-01 | Patient inserted by Tenant A is not visible to Tenant B | integration | `pytest tests/test_tenant_isolation.py::test_rls_isolation -x` | Wave 0 |
| TENANT-02 | GET /patients only returns records for current tenant | integration | `pytest tests/test_tenant_isolation.py::test_patients_scoped -x` | Wave 0 |
| TENANT-03 | Endpoint extracts tenant_id from JWT not from query param | unit | `pytest tests/test_auth.py::test_tenant_from_jwt_only -x` | Wave 0 |
| API-02 | /auth/refresh returns new access token from valid refresh token | integration | `pytest tests/test_auth.py::test_refresh_token -x` | Wave 0 |
| API-03 | DB query with no SET LOCAL returns no rows (RLS blocks it) | integration | `pytest tests/test_tenant_isolation.py::test_rls_blocks_without_context -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/test_auth.py -x -q`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `agent-service/tests/test_auth.py` — covers AUTH-01, AUTH-04, AUTH-06, TENANT-03, API-02
- [ ] `agent-service/tests/test_tenant_isolation.py` — covers TENANT-01, TENANT-02, API-03
- [ ] `agent-service/tests/conftest.py` — shared fixtures: test DB, test user creation, test tenant creation
- [ ] `agent-service/pytest.ini` or `agent-service/pyproject.toml [tool.pytest.ini_options]` — test root config

*(Frontend auth tests are manual-only — AUTH-02, AUTH-03, AUTH-05 require a live browser session)*

---

## Sources

### Primary (HIGH confidence)

- `nextjs.org/docs/app/api-reference/file-conventions/proxy` — proxy.ts API reference (version 16.2.1, verified 2026-03-25)
- `authjs.dev/reference/nextjs` — NextAuth v5 configuration reference
- `authjs.dev/getting-started/migrating-to-v5` — v4 → v5 changes
- `authjs.dev/getting-started/session-management/protecting` — proxy.ts route protection pattern
- `fastapi.tiangolo.com/tutorial/security/oauth2-jwt/` — Official FastAPI JWT tutorial (PyJWT + pwdlib)
- `postgresql.org/docs/current/ddl-rowsecurity.html` — PostgreSQL RLS documentation

### Secondary (MEDIUM confidence)

- `crunchydata.com/blog/row-level-security-for-tenants-in-postgres` — RLS SET variable pattern for single app user
- `oneuptime.com/blog/post/2026-01-25-row-level-security-postgresql/view` — CREATE POLICY syntax, SET LOCAL pattern
- `codevoweb.com/how-to-set-up-next-js-15-with-nextauth-v5/` — CredentialsProvider + callbacks with external backend
- `dev.to/huangyongshan46a11y/authjs-v5-with-nextjs-16-the-complete-authentication-guide-2026-2lg` — Auth.js v5 + Next.js 16 patterns

### Tertiary (LOW confidence)

- `github.com/nextauthjs/next-auth/discussions/13382` — next-auth v5 beta production safety discussion

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions verified via npm view / pip index
- Architecture: HIGH — patterns verified against official docs (NextAuth, FastAPI, PostgreSQL)
- proxy.ts rename: HIGH — verified directly from official Next.js 16 docs
- Pitfalls: HIGH — derived from official documentation + architectural analysis
- RLS patterns: MEDIUM-HIGH — core SQL verified from official PostgreSQL docs; psycopg2-specific pattern derived from principle

**Research date:** 2026-03-29
**Valid until:** 2026-04-30 (next-auth beta may have breaking changes; re-verify before starting)
