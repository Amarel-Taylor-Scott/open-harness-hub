# Architecture and pages: the whole-product context for Claude Design

> Companion to `AIDevObserver-BRIEF.md` (the feature spec) and `DESIGN-BIBLE.md` (the design system). This gives the
> full picture a designer needs to build a complete SaaS product: the architecture, the tech stack, the user flows,
> the standard page schemes, and the FULL page inventory (marketing, auth, account, billing, subscription, team, and
> the product app). serves_truth=false.

## 1. Overarching architecture

- **AI Done Right** is the parent (holding) brand. It owns three product layers plus an open ecosystem, shown as **5
  surfaces** that share one design system:
  - **Teleon** (the runtime), **Baltor** (the governed context product, powered by Teleon), **AIDevObserver** (AI
    coding usage review), **OpenHubForAI** (the open store both products consume), and **AI Done Right** (the parent
    hub / portfolio).
  - Dependency law (do not cross it): **Baltor depends on Teleon depends on OpenHarnessHub**, never the reverse.
- **The surfaces are full React apps** at `web/<brand>/`, served by the showcase (`OH_PRODUCT=<brand> python3 -m
  scripts.showcase`). Every app imports the SAME shared kit and differs only by accent and copy.
- **Backends** are the service-plane (identity, registry, events, Teleon runtime, AIDevObserver review, mailbox),
  reached by same-origin **seams** (`/api/identity/`, `/registry/`, `/api/observer/`, ...). The same frontend code
  runs locally and in cloud; only `OH_SEAM_*_BASE` differs. See `INTEGRATION-BIBLE.md`.
- **Data:** a 147-catalog registry federation (plus pgvector at scale). **Governance:** serves_truth=false on
  candidate output; only Baltor's governed pipeline serves truth; a bring-your-own key is used for one request and
  never stored.

## 2. Tech stack (what you design inside)

- **Frontend:** React 18 with in-browser Babel (no build step), the shared kit (`oh-tokens.css`, `oh-components.css`,
  `oh-site.css`, `oh-site.jsx`, `products.js`, all verbatim in `DESIGN-ASSETS.md`), hash routing
  (`useHashRoute` / `navigate`). Light theme, Inter UI font, one per-brand accent.
- **Backend:** the showcase serves `web/<brand>/` and routes the seams to stdlib HTTP services. A new backend is a
  service-plane service plus a seam, never a hardcoded host.
- **Identity and auth:** a **separate realm per product, NO single sign-on** (this is a hard lock). The
  `/api/identity/` seam backs login, account, and session.
- **Billing and metering:** **usage-metered (consumption), NOT per-seat.** The economic unit is what the product
  meters (for AIDevObserver: sessions reviewed, findings, live checks). The exact prices are owner-set; design the
  structure, not the numbers.
- **Deploy:** one showcase service per `OH_PRODUCT`, `OH_BIND_HOST=0.0.0.0`, the platform injects the port, the seams
  point at cloud backends via `OH_SEAM_*_BASE`.

## 3. Standard design schemes (the page archetypes, all built from the kit)

| Scheme | Built from | Used for |
|---|---|---|
| **A. Marketing page** | `OhTopBar` + `OhHero` + `OhSection`/`OhFeatures` + `OhBand` + `OhFooter` | home, pricing, docs, cases |
| **B. App shell (logged in)** | `OhAppShell` (left sidebar nav + content + a top bar with the account menu) | the product app, account, billing, team, settings |
| **C. Form page** | a kit card with the kit inputs, selects, and buttons | settings, account, payment method, auth |
| **D. Table / list page** | the kit table or list | sessions, findings, invoices, members, usage |
| **E. States** | every data page needs them | empty, loading (skeleton), populated, error |

The marketing pages use the light top-nav chrome; everything behind login uses the `OhAppShell` left-sidebar chrome.
Both share the same tokens, type scale, and accent, so the transition feels like one product.

## 4. User flows (design these journeys)

- **New user (acquire to activate):** marketing home, then **Sign up** (the product's own realm), then **Welcome /
  onboarding** ("connect your editor": install the VS Code or Cursor extension, or add the MCP server, or paste a
  transcript), then the **first review** (the aha moment), then a prompt to upgrade when they reach the free limit.
- **Returning user:** **Login**, then the app (Review by default), then Sessions, Findings, Settings.
- **Convert to paid:** in-app **Pricing**, choose a plan, add a **Payment method**, the subscription goes active and
  the higher-tier features unlock.
- **Manage subscription:** **Account**, then **Billing** (current plan plus usage), then upgrade, downgrade, or
  cancel, then **Invoices / receipts**.
- **Team:** **Account**, then **Team**, invite members, set roles, see shared **usage** and the **savings dashboard**.

## 5. Functionality and features (the whole product)

- **The product (AIDevObserver):** the four app screens (Review, Sessions, Findings, Settings), the finding card, the
  demo, and the deeper integrations (registry deep-links, dollars-saved, the cheaper-path ladder, the savings and team
  analytics, the PR check, live in-editor coaching). Full detail in `AIDevObserver-BRIEF.md`.
- **Account and identity:** profile, security (password, API keys / BYO), notifications.
- **Billing and subscription:** plans, payment method, invoices, a usage / metering dashboard, plan management.
- **Team:** members, roles, invites, shared usage, the savings dashboard.
- **Marketing:** home, how it works, pricing, docs, cases.

## 6. Required pages inventory (design all of these)

> **The COMPLETE, exhaustive inventory** — every auth / account / billing / subscription / reset-password /
> team / developer / system page, each mapped to its kit component + layout + states — is
> `SAAS-PAGE-INVENTORY.md`. The grouping below is the summary.

Each page names its scheme (section 3), its data or seam, and its key states.

### Marketing (public)
- **Home** (`/`), **How it works**, **Pricing**, **Docs**, **Cases**. Scheme A. Static or lightly dynamic.

### Auth (the product's own realm; NO SSO; `/api/identity/`)
- **Login**, **Sign up**, **Forgot password**, **Verify email**, **Welcome / onboarding** (connect the editor).
  Scheme C. States: error (bad credentials), loading, success. The BYO-key field is governed copy ("used only for the
  request, never stored").

### Product app (logged in; `OhAppShell`)
- **Review** (default), **Sessions**, **Findings**, **Settings**. Scheme B plus the finding card. Full spec in the
  brief.

### Account
- **Profile**, **Security** (password, API keys / BYO), **Notifications**. Scheme C.

### Billing (usage-metered; numbers are owner-set, design the structure)
- **Plans / Pricing** (in-app), **Payment method**, **Invoices / Receipts**, **Usage / Metering** (a consumption
  dashboard: what was used this period against the plan). Schemes C and D.

### Subscription
- **Current plan + usage**, **Upgrade / Downgrade**, **Cancel**. Scheme C. Make the metered model legible (the user
  pays for what they use, not per seat).

### Team
- **Members**, **Roles**, **Invites**, **Team usage + savings dashboard**. Scheme D.

## 7. Constraints (do not break any of these)

- **One design law:** the shared kit is the only style source; accent and copy are the only per-surface variables.
- **NO single sign-on:** a separate auth realm per product (a hard lock).
- **Usage-metered, not per-seat:** the billing and subscription pages reflect consumption.
- **Backends only through seams** (`/api/.../`); the proof gate stays green; new endpoint equals a service plus a seam.
- **Copy rules:** no placeholders, no em or en dashes, no strategy leakage, real copy.
- **Governance:** serves_truth=false on candidate output; BYO keys never stored; private bench surfaces are never shown
  as public production.

*This doc is whole-product context. The exact AIDevObserver build (screens, real API data, the deliverable) is in
`AIDevObserver-BRIEF.md`. The design system and the verbatim source are in `DESIGN-BIBLE.md` + `DESIGN-ASSETS.md`.*
