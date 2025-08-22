# AGENTS.md — AgentFlow Frontend Collaboration Guide
**Stack:** Next.js (App Router) · React 18 · TypeScript 5.x · Tailwind CSS  
**Audience:** AI agents & contributors implementing the **frontend only**.  
**Scope:** Everything in `frontend/` for the web UI. **Do not** modify backend, infra, or storage.

---

## 1) Purpose & Success
**Goal:** Ship a production-ready Next.js app that lets users **create, configure, test, and monitor agents** through an intuitive UI in **≤10 minutes** from first interaction.

**Frontend Success Criteria**
- First Meaningful Paint (FMP) ≤ 1.5s (local dev profile), TTI ≤ 2.5s.
- Dashboard renders without layout shift (CLS < 0.1).
- Agent creation wizard completes happy path in ≤ 5 minutes.
- All major flows keyboard- and screen-reader-accessible (WCAG 2.1 AA).
- No untyped APIs; TS strict mode passes with zero errors.
- Test suite (unit+e2e) green in CI.

**Non-Goals (Frontend must not do)**
- No direct DB/storage access.
- No backend framework or infra changes.
- No embedding secrets in client bundles.

---

## 2) Tech & Version Rules (Frontend)
- **React 18**: use `createRoot`, Suspense, streaming SSR; prefer **Server Components by default**.
- **Next.js App Router**: no Pages Router APIs (`getServerSideProps`/`getStaticProps`).
- **TypeScript 5.x**: `strict` on; no `any`; no `@ts-ignore` unless documented with a TODO and a tracking issue.
- **Styling**: Tailwind CSS; prefer utility-first with small, composable components.
- **Lint/Format**: Biome (or ESLint+Prettier if configured); CI must fail on lint errors.
- **Testing**: Jest + React Testing Library (unit), Playwright (e2e), axe-core (a11y).

---

## 3) Project Structure (Authoritative)
```

frontend/
├─ app/                       # App Router (server-first)
│  ├─ layout.tsx              # Root layout: theme, fonts, providers
│  ├─ page.tsx                # Landing/dashboard
│  ├─ (auth)/                 # Auth routes (client)
│  │  ├─ login/page.tsx
│  │  └─ register/page.tsx
│  ├─ (dashboard)/            # Main product area
│  │  ├─ layout.tsx
│  │  ├─ agents/              # Agent list/detail/wizard
│  │  ├─ memory/              # Memory UI
│  │  ├─ knowledge/           # Knowledge UI
│  │  └─ analytics/           # Charts & metrics
│  └─ api/                    # Minimal proxy/edge helpers (if needed)
├─ components/                # Reusable UI (islands)
│  ├─ ui/                     # Buttons, inputs, modals, toasts
│  ├─ agents/                 # Agent builder/wizard/cards/chat
│  ├─ memory/                 # Tables, editors, inspectors
│  ├─ knowledge/              # Uploaders, search, viewers
│  └─ layout/                 # Header, sidebar, breadcrumbs
├─ hooks/                     # Custom hooks (client only)
├─ lib/                       # Typed client, schemas, utils, env
├─ providers/                 # Context providers (client only)
├─ styles/                    # Tailwind + globals
└─ **tests**/                 # Unit & e2e tests

````

---

## 4) App Router Rules of Engagement
- **Server default.** Pages and layouts are Server Components unless interactivity is required.
- **Client boundary.** Add `'use client'` only for components using state, effects, browser APIs, or event handlers.
- **Data fetching.** Prefer server fetching (built-in `fetch`) with caching semantics; pass data to client islands via props.
- **Streaming.** Use streaming SSR + Suspense for slow data; show skeletons/placeholders.
- **Forms.** Use server actions where appropriate, or client forms that POST to API routes/proxies.

---

## 5) TypeScript 5.x Standards
- `strict: true`, `noUncheckedIndexedAccess: true`, `exactOptionalPropertyTypes: true`.
- `moduleResolution: "bundler"` (or the project’s agreed resolver for Next).
- No `any`. If unavoidable, wrap at the boundary with **zod** runtime validation and convert to typed objects.
- Public envs are `NEXT_PUBLIC_*` only. Validate all envs at boot (see §10.3).

**Sample `tsconfig.json` (baseline)**
```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "target": "ES2022",
    "lib": ["DOM", "DOM.Iterable", "ES2022"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "jsx": "preserve",
    "noEmit": true,
    "incremental": true,
    "forceConsistentCasingInFileNames": true,
    "isolatedModules": true,
    "types": ["jest", "node"]
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules"]
}
````

---

## 6) Data Access & API Patterns (Frontend)

* **Single typed client** in `lib/api.ts`.
* **Server-first fetching** in Server Components; switch to client only for interactive flows.
* **Auth tokens**: prefer httpOnly cookies managed by the backend; if using Bearer in client, store minimally and never in HTML.
* **Error model**: normalize to `{ code?: string; message: string; detail?: unknown }`.
* **Zod at edges**: validate all untyped API responses at boundaries.

**Minimal client**

```ts
// lib/api.ts
export class APIError extends Error {
  constructor(public status: number, public code?: string, public detail?: unknown) {
    super(code ?? `HTTP_${status}`);
  }
}

const BASE = process.env.NEXT_PUBLIC_API_URL!;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    cache: "no-store" // tune per endpoint
  });
  const text = await res.text();
  const json = text ? JSON.parse(text) : null;
  if (!res.ok) throw new APIError(res.status, json?.code, json?.detail ?? json);
  return json as T;
}

export const api = {
  listAgents: () => request<Agent[]>("/agents/"),
  createAgent: (body: CreateAgentRequest) =>
    request<Agent>("/agents/", { method: "POST", body: JSON.stringify(body) }),
  // …add additional endpoints as needed
};
```

---

## 7) UI, Accessibility & Internationalization

* **WCAG 2.1 AA**: all interactive elements reachable via keyboard; visible focus ring; ARIA landmarks where appropriate.
* **Color & contrast**: meet AA contrast; don’t use color alone to convey meaning.
* **Forms**: label every input; associate errors with `aria-describedby`.
* **Motion**: respect `prefers-reduced-motion`.
* **I18n readiness**: no hard-coded dates/numbers; centralize formatters.

**Accessible Button Pattern**

```tsx
// components/ui/button.tsx
import { forwardRef } from "react";
export const Button = forwardRef<HTMLButtonElement, JSX.IntrinsicElements["button"]>(
  ({ children, disabled, ...props }, ref) => (
    <button
      ref={ref}
      className="inline-flex items-center justify-center rounded-md px-4 py-2
                 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2
                 disabled:opacity-50 disabled:pointer-events-none"
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  )
);
Button.displayName = "Button";
```

---

## 8) Performance Budgets & Patterns

* **Budgets**: JS < 200KB gz for initial route; image LCP asset < 120KB; route change TTI < 1s.
* **Split heavy code** with `next/dynamic`; disable SSR for client-only widgets.
* **Use `next/image`** and responsive sizes; avoid layout shift.
* **Cache smartly**: per-route revalidation, `stale-while-revalidate` where safe.
* **State locality**: keep state close to components; avoid global state unless necessary.

**Dynamic import**

```tsx
const WorkflowCanvas = dynamic(() => import("@/components/workflows/workflow-canvas"), {
  ssr: false,
  loading: () => <div className="p-4">Loading editor…</div>
});
```

---

## 9) State, Streaming & Interactivity

* **Server → Client**: pass fetched data as props; avoid fetching in client when not needed.
* **Streaming**: use EventSource or fetch streams for conversation tokens; render incremental UI with Suspense boundaries.
* **Hooks** live in `hooks/` and are client-only. Prefix with `use-` and document state machine if non-trivial.
* **Transitions**: use `useTransition` for non-urgent UI updates.

---

## 10) Configuration & Environment

* **Public env only**: `NEXT_PUBLIC_*` for values required in the browser (e.g., `NEXT_PUBLIC_API_URL`).
* **Type-safe env**: validate at boot.

```ts
// lib/env.ts
import { z } from "zod";
export const env = z.object({
  NEXT_PUBLIC_API_URL: z.string().url(),
  NEXT_PUBLIC_APP_ENV: z.enum(["development","staging","production"]).default("development"),
}).parse({
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  NEXT_PUBLIC_APP_ENV: process.env.NEXT_PUBLIC_APP_ENV
});
```

---

## 11) Authentication (Frontend Responsibilities)

* Render login/register forms; submit to backend auth endpoints.
* Read auth state from cookies/session endpoints via Server Components where possible.
* Protect dashboard routes; redirect unauthenticated users to `/login`.
* Never embed secrets in client; never log tokens.

---

## 12) Testing & Quality Gates

**Unit:** Jest + React Testing Library (components, hooks)
**E2E:** Playwright (auth, agent creation, chat, uploads)
**A11y:** `@axe-core/playwright` smoke on key routes
**CI must fail** on: type errors, lint errors, test failures, a11y violations > 0 (critical), and bundle budget regressions.

**Example test**

```tsx
// __tests__/components/agent-card.test.tsx
import { render, screen } from "@testing-library/react";
import { AgentCard } from "@/components/agents/agent-card";
test("shows agent name and status", () => {
  render(<AgentCard agent={{ id:"a1", name:"Helper", description:"", is_active:true }} />);
  expect(screen.getByText("Helper")).toBeInTheDocument();
  expect(screen.getByText(/active/i)).toBeInTheDocument();
});
```

---

## 13) Developer Experience

**Scripts**

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "biome check .",
    "lint:fix": "biome check . --apply",
    "type-check": "tsc --noEmit",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:e2e": "playwright test",
    "a11y:smoke": "playwright test --grep @a11y"
  }
}
```

**PR Checklist (must pass)**

* [ ] TypeScript strict clean
* [ ] Lint & format clean
* [ ] Unit tests added/updated
* [ ] E2E added/updated (if UX changes)
* [ ] A11y checked (critical pages)
* [ ] No hard-coded URLs or secrets
* [ ] Meets performance budgets (bundle/analyze if heavy)

---

## 14) Page Blueprints (MVP)

* **Dashboard**: resource counts, quick links, recent runs; server-rendered data; skeletons.
* **Agents List**: searchable table/grid; “Create Agent” CTA.
* **Agent Create Wizard**: multi-step (Basics → Prompt → Tools → Review); zod-validated forms.
* **Agent Detail**: tabs (Settings, Test, Deploy); chat panel with streaming; run trace viewer.
* **Memory**: search, paginate, edit modal; optimistic updates with error toast fallback.
* **Knowledge**: drag-and-drop upload with progress; searchable list; doc preview.
* **Analytics**: charts with Suspense; lazy-load chart lib.

---

## 15) Anti-Patterns (Fail CI/Review)

* Using Pages Router APIs in App Router.
* Fetching data in client when a Server Component can do it.
* Introducing `any`, `@ts-ignore`, or unresolved TODOs without issues.
* Storing or exposing secrets/tokens in client code.
* Non-keyboard-accessible interactive elements.
* Large, monolithic components (>250 lines) without refactor.
* Blocking main thread with heavy sync work (move to worker or server).

---

## 16) Snippets & Templates

**Server Component page with server fetch**

```tsx
// app/(dashboard)/agents/page.tsx
import { api } from "@/lib/api";
export default async function AgentsPage() {
  const agents = await api.listAgents(); // server-side fetch
  return <AgentsTable agents={agents} />;
}
```

**Client island with search/filter**

```tsx
// components/agents/agents-table.tsx
"use client";
import { useMemo, useState } from "react";
export function AgentsTable({ agents }: { agents: Agent[] }) {
  const [q, setQ] = useState("");
  const filtered = useMemo(
    () => agents.filter(a => a.name.toLowerCase().includes(q.toLowerCase())),
    [agents, q]
  );
  return (
    <section>
      <label className="sr-only" htmlFor="agent-search">Search agents</label>
      <input id="agent-search" value={q} onChange={e=>setQ(e.target.value)}
             className="w-full border rounded px-3 py-2" placeholder="Search…" />
      <ul className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        {filtered.map(a => <li key={a.id}><AgentCard agent={a} /></li>)}
      </ul>
    </section>
  );
}
```

**Zod form schema (wizard step)**

```ts
import { z } from "zod";
export const AgentBasicsSchema = z.object({
  name: z.string().min(1).max(80),
  description: z.string().max(500).optional(),
  config: z.object({
    system_prompt: z.string().min(1),
    model: z.string().default("gpt-4o-mini"),
    temperature: z.number().min(0).max(2).default(0.7)
  })
});
export type AgentBasics = z.infer<typeof AgentBasicsSchema>;
```

---

## 17) Ownership & Boundaries

* **This document governs only `frontend/`.**
* If a feature requires backend or infra changes, open a design issue with a clear API contract and link to this guide.

---

## 18) Definition of Done (Frontend)

* Meets UX & performance targets in §1 and §8.
* Implements with Server Components by default, client islands where necessary.
* Types are complete; no `any`.
* Accessibility verified on updated pages.
* Tests (unit/e2e) updated; CI green.
* Developer docs updated (README snippets or in-app help if applicable).

---
::contentReference[oaicite:0]{index=0}
```
