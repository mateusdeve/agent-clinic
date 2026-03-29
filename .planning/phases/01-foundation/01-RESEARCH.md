# Phase 1: Foundation - Research

**Researched:** 2026-03-29
**Domain:** Next.js 15 App Router + Tailwind CSS 4 + shadcn/ui — project scaffolding and landing page
**Confidence:** HIGH

---

## Summary

Phase 1 scaffolds a brand-new Next.js 15 frontend inside `/Users/mateuspires/Dev/agent-clinic/frontend/`, replacing the current static `site.html` with a full React application. The landing page must replicate the visual design of `site.html` (green palette, DM Serif Display headings, DM Sans body) and satisfy four requirements: a hero section with a WhatsApp CTA (LAND-01), feature/how-it-works/testimonial sections (LAND-02), mobile responsiveness at 375 px (LAND-03), and the full visual identity (LAND-04).

Tailwind CSS 4 is a breaking change from v3. The `tailwind.config.ts` file is gone — all design tokens are declared with the `@theme` directive directly in `globals.css`. shadcn/ui has been updated to work with this CSS-first approach. Route groups use the `(folder)` naming convention and do not appear in URLs; they allow separate layouts for `(landing)`, `(auth)`, and `(dashboard)` segments.

The WhatsApp CTA link is a standard `https://wa.me/<E.164_number>?text=<encoded>` URL. No backend interaction is needed for Phase 1 — this is a purely static rendering phase. Next.js 15 ships with Turbopack as the default dev bundler, which is production-ready for this use case.

**Primary recommendation:** Scaffold with `npx create-next-app@latest` (TypeScript + Tailwind + App Router), then `npx shadcn@latest init`, configure the green design tokens in `globals.css` using `@theme`, and implement each site.html section as a dedicated React component.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| LAND-01 | Visitante ve hero section com proposta de valor e CTA que redireciona para WhatsApp | Hero component with `<a href="https://wa.me/...">` anchor. No backend required. |
| LAND-02 | Visitante ve secoes de features, como funciona e depoimento (baseado no site.html) | Three dedicated section components mirroring site.html structure — FeaturesSection, HowItWorksSection, TestimonialSection. |
| LAND-03 | Landing page e responsiva e funcional em dispositivos moveis (375px width) | Tailwind responsive prefixes (`md:`, `lg:`), overflow-x-hidden on body, tested at 375 px. Matches site.html breakpoint at 900 px. |
| LAND-04 | Landing page segue identidade visual do site.html (paleta verde, DM Serif/DM Sans) | `@theme` block in globals.css with green color tokens; Google Fonts loaded via `next/font/google`; custom font variables mapped to Tailwind utilities. |
</phase_requirements>

---

## Project Constraints (from CLAUDE.md)

The following directives come from `CLAUDE.md` at the project root. The planner MUST honor all of them.

- **Frontend stack:** Next.js + Tailwind CSS — user decision, non-negotiable
- **Backend stack:** Python/FastAPI — already exists, do not touch in Phase 1
- **WhatsApp:** Evolution API — already integrated, Phase 1 does not interact with it
- **Interface language:** Portuguese Brazilian (pt-BR) — all user-facing text in pt-BR
- **Design source of truth:** `frontend/site.html` — green palette, DM Serif Display + DM Sans typography
- **GSD workflow:** All edits must go through a GSD command entry point; no direct repo edits outside GSD
- **Multi-tenancy:** Not relevant to Phase 1 (landing page is public, no tenant context)

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| next | 16.2.1 (latest) | App framework, routing, SSG/SSR | Locked decision; App Router for route groups |
| react | 19.2.4 (latest) | UI runtime | Ships with Next.js 15/16 |
| react-dom | 19.2.4 | DOM rendering | Paired with react |
| typescript | 6.0.2 (latest) | Type safety | Locked in create-next-app defaults |
| tailwindcss | 4.2.2 (latest) | Styling | Locked decision; v4 CSS-first config |
| @tailwindcss/postcss | 4.2.2 | PostCSS integration for Tailwind 4 | Required by Tailwind 4 for Next.js |

### Supporting (Phase 1 only)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| lucide-react | 1.7.0 | Icon set | Used by shadcn/ui; needed for any icon in landing page |
| next/font/google | — (built-in) | Load DM Serif Display + DM Sans | Zero layout shift, self-hosted from Google Fonts |
| class-variance-authority | latest | shadcn component variants | Installed automatically by shadcn init |
| clsx | latest | Conditional class merging | Installed automatically by shadcn init |
| tailwind-merge | latest | Deduplicate Tailwind classes | Installed automatically by shadcn init |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| next/font/google | Manual `<link>` tag to Google Fonts | next/font self-hosts and eliminates layout shift; always prefer it |
| Tailwind 4 @theme directive | Tailwind 3 tailwind.config.ts | v4 is already in package; config file approach is deprecated in v4 |
| CSS animations (keyframes) | Framer Motion | STACK.md marks Framer Motion as LOW confidence / optional; CSS keyframes already in site.html and sufficient for Phase 1 |

**Installation:**

```bash
# Step 1 — scaffold (run from /Users/mateuspires/Dev/agent-clinic/frontend)
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --yes

# Step 2 — shadcn/ui init
npx shadcn@latest init

# Step 3 — add any needed shadcn components (button is sufficient for Phase 1)
npx shadcn@latest add button
```

**Version verification (confirmed 2026-03-29):**

| Package | Verified Version | Source |
|---------|-----------------|--------|
| next | 16.2.1 | `npm view next dist-tags.latest` |
| react | 19.2.4 | `npm view react dist-tags.latest` |
| tailwindcss | 4.2.2 | `npm view tailwindcss dist-tags.latest` |
| lucide-react | 1.7.0 | `npm view lucide-react dist-tags.latest` |
| typescript | 6.0.2 | `npm view typescript dist-tags.latest` |

---

## Architecture Patterns

### Recommended Project Structure

```
src/
├── app/
│   ├── (landing)/              # Route group — public landing page
│   │   ├── layout.tsx          # Landing-specific layout (no sidebar/nav chrome)
│   │   └── page.tsx            # Assembles landing sections
│   ├── (auth)/                 # Route group — future Phase 2
│   │   └── login/
│   │       └── page.tsx
│   ├── (dashboard)/            # Route group — future Phase 3+
│   │   └── page.tsx
│   ├── layout.tsx              # Root layout (html, body, font vars)
│   └── globals.css             # Tailwind @import + @theme design tokens
├── components/
│   ├── landing/                # Landing-page-specific sections
│   │   ├── NavBar.tsx
│   │   ├── HeroSection.tsx
│   │   ├── StatsSection.tsx
│   │   ├── FeaturesSection.tsx
│   │   ├── HowItWorksSection.tsx
│   │   ├── TestimonialSection.tsx
│   │   ├── FinalCtaSection.tsx
│   │   └── Footer.tsx
│   └── ui/                     # shadcn/ui primitives (auto-generated)
│       └── button.tsx
├── lib/
│   └── utils.ts                # cn() utility from shadcn init
└── types/                      # Shared TypeScript types (empty in Phase 1)
```

Route groups `(landing)`, `(auth)`, `(dashboard)` are folder names wrapped in parentheses. They do NOT appear in URLs. Each can have its own `layout.tsx`, enabling the landing page to have a completely different shell from the authenticated dashboard.

### Pattern 1: CSS-First Design Tokens (Tailwind 4)

**What:** All custom colors and fonts declared with `@theme` in `globals.css`, not in a JS config file.

**When to use:** Always in Tailwind 4. No `tailwind.config.ts` should exist.

**Example:**

```css
/* Source: https://tailwindcss.com/docs/theme */
@import "tailwindcss";

@theme {
  /* Green palette from site.html */
  --color-green-50: #edf7f0;
  --color-green-100: #d0edd8;
  --color-green-400: #4caf7d;
  --color-green-500: #2e9e60;
  --color-green-600: #1e7d48;
  --color-green-900: #0d2e1a;

  /* Gray tokens */
  --color-off-white: #f5f7f5;
  --color-gray-200: #e8ece9;
  --color-gray-400: #9aaa9e;
  --color-gray-600: #5a6b5f;
  --color-gray-800: #2a352d;

  /* Fonts — mapped after next/font injects CSS variables */
  --font-serif: var(--font-dm-serif), "DM Serif Display", serif;
  --font-sans: var(--font-dm-sans), "DM Sans", sans-serif;
}
```

These tokens generate utility classes: `bg-green-500`, `text-green-900`, `font-serif`, etc.

### Pattern 2: next/font/google for DM Fonts

**What:** Load DM Serif Display and DM Sans via Next.js font optimization.

**When to use:** Always — eliminates layout shift and self-hosts fonts.

```tsx
// Source: https://nextjs.org/docs/app/building-your-application/optimizing/fonts
// src/app/layout.tsx
import { DM_Serif_Display, DM_Sans } from "next/font/google";

const dmSerif = DM_Serif_Display({
  weight: ["400"],
  style: ["normal", "italic"],
  subsets: ["latin"],
  variable: "--font-dm-serif",
});

const dmSans = DM_Sans({
  weight: ["300", "400", "500", "600"],
  subsets: ["latin"],
  variable: "--font-dm-sans",
});

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" className={`${dmSerif.variable} ${dmSans.variable}`}>
      <body className="font-sans">{children}</body>
    </html>
  );
}
```

### Pattern 3: WhatsApp CTA Link

**What:** A standard anchor tag pointing to `wa.me` — no React state, no backend.

**When to use:** For LAND-01 hero CTA and final CTA section.

```tsx
// Source: https://faq.whatsapp.com/425247423114725 (WhatsApp Click-to-Chat)
const WA_NUMBER = "5511999999999"; // E.164 without + sign
const WA_MESSAGE = encodeURIComponent("Olá! Quero saber mais sobre o MedIA.");

<a
  href={`https://wa.me/${WA_NUMBER}?text=${WA_MESSAGE}`}
  target="_blank"
  rel="noopener noreferrer"
  className="btn-primary"
>
  Falar com especialista →
</a>
```

The phone number must be stored in an environment variable (`NEXT_PUBLIC_WHATSAPP_NUMBER`) so it can be changed without a code edit.

### Pattern 4: Route Groups with Separate Layouts

**What:** Three top-level route groups share zero layout code between them.

**When to use:** Phase 1 creates `(landing)` only; `(auth)` and `(dashboard)` are empty stubs.

```
app/
├── layout.tsx          ← Root layout (fonts, metadata, global CSS)
├── (landing)/
│   ├── layout.tsx      ← Landing-only layout (transparent nav, no sidebar)
│   └── page.tsx        ← / (root URL maps here)
├── (auth)/             ← Empty in Phase 1, stub for Phase 2
└── (dashboard)/        ← Empty in Phase 1, stub for Phase 3
```

**Caveat:** When multiple root layouts exist, navigating between them triggers a full page reload. In Phase 1 there is only one active group, so this is a future concern, not a present one.

### Anti-Patterns to Avoid

- **Do NOT create `tailwind.config.ts`:** Tailwind 4 is CSS-first. A JS config file is not used and will cause confusion.
- **Do NOT use `@apply` for site.html CSS class names:** Rewrite in Tailwind utility classes directly in JSX `className`; `@apply` is discouraged in Tailwind 4.
- **Do NOT inline Google Fonts via `<link>` in `<head>`:** Use `next/font/google` exclusively — the HTML link approach causes layout shift and missing font warnings.
- **Do NOT put `(landing)` page content in the root `app/page.tsx`:** Always place it inside `app/(landing)/page.tsx` so route group isolation is maintained from the start.
- **Do NOT hardcode the WhatsApp phone number:** Use `NEXT_PUBLIC_WHATSAPP_NUMBER` env var.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Class merging / deduplication | Custom merge utility | `clsx` + `tailwind-merge` via shadcn's `cn()` | Handles Tailwind specificity edge cases |
| Button variants | Custom variant system | shadcn/ui Button component | Accessible, keyboard-navigable, variant-ready |
| Font loading with zero layout shift | Manual `<link>` tag | `next/font/google` | Next.js handles preloading, self-hosting, variable injection |
| Responsive image optimization | Raw `<img>` tags | `next/image` | Automatic WebP/AVIF, lazy loading, CLS prevention |
| WhatsApp link construction | Custom URL builder | Plain anchor with `wa.me` template string | Standard Click-to-Chat API, no library needed |

**Key insight:** Phase 1 is intentionally simple. The risk is over-engineering — resist adding animation libraries or state managers that will go unused on a static landing page.

---

## Common Pitfalls

### Pitfall 1: Tailwind 4 Config Confusion

**What goes wrong:** Developer runs `npx create-next-app` and gets a `tailwind.config.ts` from an older scaffold template, then tries to add custom colors there — they don't show up.

**Why it happens:** Some create-next-app versions still generate the old config file. Tailwind 4's CSS-first system ignores the JS config for color definitions.

**How to avoid:** After scaffolding, delete `tailwind.config.ts` if it exists. Define all design tokens only in `globals.css` under `@theme`. Verify by running `npm run dev` and checking that `bg-green-500` resolves to `#2e9e60`.

**Warning signs:** Utility classes for custom colors produce `bg-[#2e9e60]` workarounds; `tailwind.config.ts` still present in project root.

### Pitfall 2: Route Group Root Page Conflict

**What goes wrong:** `app/page.tsx` and `app/(landing)/page.tsx` both exist, causing a build error because they both resolve to `/`.

**Why it happens:** create-next-app generates `app/page.tsx` by default; developer adds the route group without removing the root page.

**How to avoid:** After scaffolding, delete `app/page.tsx` and create `app/(landing)/page.tsx` as the home route. Confirm no conflicting paths exist before running `next build`.

**Warning signs:** Next.js build error: "Two pages resolve to the same route."

### Pitfall 3: Google Fonts FOUC / Layout Shift

**What goes wrong:** The DM Serif Display font loads visibly after the page renders, causing a flash of unstyled text.

**Why it happens:** Developer used a `<link>` tag in the HTML head instead of `next/font/google`. Or forgot to attach `.variable` to the `<html>` element.

**How to avoid:** Use `next/font/google` exclusively. Apply font variables (`dmSerif.variable`, `dmSans.variable`) as CSS classes on `<html>`. Add the Tailwind `@theme` font mappings to pick up these variables.

**Warning signs:** Chrome DevTools shows font loading in waterfall after LCP; `font-family: 'DM Serif Display'` resolves to fallback serif initially.

### Pitfall 4: Horizontal Overflow on Mobile

**What goes wrong:** Landing page has horizontal scroll on 375 px devices, violating LAND-03.

**Why it happens:** Fixed pixel widths, `hero::before` radial gradient absolutely positioned beyond viewport, or `grid-template-columns: 1fr 1fr` without a mobile override.

**How to avoid:** Set `overflow-x: hidden` on `<html>` and `<body>`. Use `grid-cols-1` at mobile, `md:grid-cols-2` at tablet+. Test explicitly with Chrome DevTools at 375 px width before completing the phase.

**Warning signs:** Scrollbar appears at 375 px; `document.body.scrollWidth > window.innerWidth` evaluates to `true`.

### Pitfall 5: `"use client"` Overuse

**What goes wrong:** Developer adds `"use client"` to every component because they're used to it, eliminating SSG benefits.

**Why it happens:** Familiarity with older React patterns; uncertainty about when client state is needed.

**How to avoid:** Landing page sections are fully static. Add `"use client"` only if the component needs `useState`, `useEffect`, or browser event handlers. A WhatsApp anchor link does not need client-side JS.

**Warning signs:** Large JavaScript bundle for a static page; components marked `"use client"` with no interactivity.

---

## Code Examples

### globals.css — Full Design Token Configuration

```css
/* Source: https://tailwindcss.com/docs/theme — Tailwind 4 @theme directive */
@import "tailwindcss";

@theme {
  /* Green palette (from site.html :root) */
  --color-green-50: #edf7f0;
  --color-green-100: #d0edd8;
  --color-green-400: #4caf7d;
  --color-green-500: #2e9e60;
  --color-green-600: #1e7d48;
  --color-green-900: #0d2e1a;

  /* Gray palette (from site.html :root) */
  --color-off-white: #f5f7f5;
  --color-gray-200: #e8ece9;
  --color-gray-400: #9aaa9e;
  --color-gray-600: #5a6b5f;
  --color-gray-800: #2a352d;

  /* Typography — CSS variables injected by next/font */
  --font-serif: var(--font-dm-serif), "DM Serif Display", serif;
  --font-sans: var(--font-dm-sans), "DM Sans", sans-serif;
}

/* Prevent horizontal overflow on all viewports */
html, body {
  overflow-x: hidden;
}
```

### HeroSection.tsx — Static Server Component

```tsx
// Source: site.html hero section structure
// No "use client" needed — pure static markup

const WA_NUMBER = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER ?? "5511999999999";
const WA_MESSAGE = encodeURIComponent(
  "Olá! Quero saber mais sobre o MedIA para minha clínica."
);

export default function HeroSection() {
  return (
    <section className="min-h-screen grid grid-cols-1 md:grid-cols-2 items-center pt-24 pb-16 px-6 md:px-12 gap-12 relative overflow-hidden">
      {/* Radial gradient background blob */}
      <div className="absolute -top-48 -right-48 w-[700px] h-[700px] rounded-full bg-radial-gradient from-green-50 to-transparent pointer-events-none" />

      <div className="relative z-10">
        {/* Badge */}
        <span className="inline-flex items-center gap-1.5 bg-green-50 border border-green-100 text-green-600 px-3.5 py-1.5 rounded-full text-sm font-medium mb-7">
          Lançamento em breve
        </span>

        <h1 className="font-serif text-[clamp(2.4rem,4vw,3.6rem)] leading-tight text-green-900 mb-6">
          O atendente que <em className="italic text-green-500">nunca</em> tira folga da sua clínica
        </h1>

        <p className="text-gray-600 font-light leading-relaxed max-w-lg mb-10">
          Agendamentos, confirmações, lembretes e dúvidas — tudo resolvido por IA, 24 horas por dia.
        </p>

        <a
          href={`https://wa.me/${WA_NUMBER}?text=${WA_MESSAGE}`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block bg-green-500 hover:bg-green-600 text-white font-semibold px-7 py-3.5 rounded-xl transition-all hover:-translate-y-0.5 hover:shadow-lg"
        >
          Falar com especialista →
        </a>
      </div>
    </section>
  );
}
```

### shadcn/ui components.json (generated by init)

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "",
    "css": "src/app/globals.css",
    "baseColor": "neutral",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  }
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `tailwind.config.ts` for design tokens | `@theme` directive in `globals.css` | Tailwind CSS 4.0 (Jan 2025) | No JS config file; all tokens are CSS variables by default |
| `tailwind.config.ts` with `content: []` | Auto content detection | Tailwind CSS 4.0 | No need to specify file globs |
| `next/font` via `@next/font` package | Built-in `next/font/google` | Next.js 13+ | Direct import, no separate package |
| Pages Router (`pages/`) | App Router (`app/`) | Next.js 13 (stable 14+) | Server Components, nested layouts, route groups |
| `npx create-next-app` with webpack | Turbopack as default bundler | Next.js 15 | Faster dev server; no config change needed |
| shadcn-ui CLI (`npx shadcn-ui@latest`) | shadcn CLI (`npx shadcn@latest`) | 2024 | Package renamed; old command still works but deprecated |

**Deprecated/outdated:**
- `tailwind.config.ts`: Not used in Tailwind 4; delete if scaffolder generates one
- `npx shadcn-ui@latest`: Use `npx shadcn@latest` instead
- `postcss.config.js` with `tailwindcss: {}`: Tailwind 4 requires `@tailwindcss/postcss` as the plugin

---

## Open Questions

1. **WhatsApp phone number for the CTA**
   - What we know: The link format is `https://wa.me/<E164>?text=<encoded>`
   - What's unclear: What is the actual clinic's WhatsApp number for the demo/production link?
   - Recommendation: Use `NEXT_PUBLIC_WHATSAPP_NUMBER` env var with a placeholder; the planner should note this as a configuration step

2. **Deployment target**
   - What we know: No deployment requirement is specified for Phase 1
   - What's unclear: Is Phase 1 verified locally or deployed to Vercel?
   - Recommendation: Plan for local verification (`npm run dev`); Vercel deployment is out of scope for this phase

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Next.js runtime | Yes | v24.14.0 | — |
| npm | Package installation | Yes | 11.9.0 | — |
| Git | Version control | Yes | — | — |

**Missing dependencies with no fallback:** None.

All required tools are present. The Next.js project does not yet exist inside `frontend/` — scaffolding is the Wave 0 task.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | None yet — Wave 0 must add Playwright or skip automated UI tests |
| Config file | None — see Wave 0 |
| Quick run command | `npm run dev` (visual/manual verification) |
| Full suite command | N/A until test framework is added |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LAND-01 | Root URL shows hero + WhatsApp CTA anchor | Manual/smoke | Open `http://localhost:3000`, click CTA | No — manual only |
| LAND-02 | Features, how-it-works, testimonial sections visible | Manual/smoke | Visual inspection at `http://localhost:3000` | No — manual only |
| LAND-03 | No horizontal overflow at 375 px | Manual | Chrome DevTools responsive mode | No — manual only |
| LAND-04 | Green palette + DM Serif Display + DM Sans rendered | Manual | Visual comparison vs site.html | No — manual only |

**Note:** All Phase 1 requirements are visual/layout requirements. Automated unit tests provide minimal value here. The verification gate is visual inspection via `npm run dev` at 375 px and 1280 px.

### Sampling Rate

- **Per task commit:** `npm run build` (catches TypeScript and JSX errors)
- **Per wave merge:** `npm run build && npm run lint`
- **Phase gate:** `npm run build` passes with zero errors + manual visual check at 375 px and 1280 px widths

### Wave 0 Gaps

- [ ] Next.js project does not exist yet — must be scaffolded as the first task
- [ ] `components.json` (shadcn) does not exist yet — created during `npx shadcn@latest init`
- [ ] `.env.local` with `NEXT_PUBLIC_WHATSAPP_NUMBER` placeholder must be created

*(No existing test infrastructure — all testing for Phase 1 is manual visual verification.)*

---

## Sources

### Primary (HIGH confidence)

- Next.js official docs — `https://nextjs.org/docs/app/getting-started/installation` — scaffolding, App Router, route groups, next/font
- Tailwind CSS official docs — `https://tailwindcss.com/docs/theme` — @theme directive, custom colors and fonts in v4
- shadcn/ui official docs — `https://ui.shadcn.com/docs/installation/next` — init process, Tailwind 4 compatibility
- `npm view` registry queries (2026-03-29) — verified package versions

### Secondary (MEDIUM confidence)

- DEV.to guide (2025): "Setting Up Next.js 15 with shadcn & Tailwind CSS v4" — confirmed no-config-file approach
- WhatsApp Click-to-Chat official format (Meta) — `https://wa.me/<number>?text=<message>` pattern

### Tertiary (LOW confidence)

- None for this phase

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all package versions verified against npm registry on 2026-03-29
- Architecture: HIGH — route groups and file conventions from official Next.js docs
- Tailwind 4 setup: HIGH — verified from official tailwindcss.com/docs/theme
- Pitfalls: MEDIUM-HIGH — some from official docs, some from community guides cross-referenced with official sources

**Research date:** 2026-03-29
**Valid until:** 2026-04-29 (stable stack; Tailwind 4 minor versions update frequently but @theme API is stable)
