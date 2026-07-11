# SaaS page inventory — EVERY page, standardized (the complete list)

> Companion to `CONSISTENCY-CONTRACT.md` + `ARCHITECTURE-AND-PAGES.md`. The exhaustive map of every page a real
> SaaS needs — marketing, auth, onboarding, the logged-in app, account, billing/subscription, team, developer, and
> system pages — each with its **route**, its **layout** (one of the three standard logged-in/auth layouts), the
> **kit component** that already exists for it, its **states**, and a build **status**. Build all of these; do not
> invent new layouts for them. serves_truth=false.

## Do we have consistent logged-in / dashboard / login layouts? — YES (in the kit)

There are **three standard logged-in/auth layouts**, and every internal page is one of them. Do not create a fourth.

1. **Auth layout — `OhAuth` (centered card).** A single centered card on a quiet background: logo, the form, one
   primary button, secondary links. ALL of login / sign-up / forgot / reset / verify / MFA / accept-invite use it;
   only the fields + copy change. `OhAuth({ brand, mode })`, mode ∈ `signin | signup | forgot` (extend with
   `reset | verify | mfa | invite` — same card, more modes; do NOT fork it).
2. **App-shell layout — `OhLayout variant="sidebar"` (`OhAppShell`).** Left sidebar (logo top · nav · theme-toggle
   foot) + main content; every page starts with `OhPageHead`. This is the logged-in product AND the account/billing/
   team areas (the account area is the same shell with an account sub-nav). One shell for everything behind login.
3. **Marketing layout — `OhLayout variant="no-sidebar"` (`OhTopBar` + `OhFooter`).** All public pages.

The kit already ships the page components for nearly every row below (`OhDashboard`, `OhBilling`, `OhUsage`,
`OhSettings`, `OhApiKeys`, `OhTeam`, `OhAuditLog`, `OhPricing`, `OhOnboarding`, `OhNotifications`, `OhStatus`,
`OhChangelog`, `OhLegal`, `OhNotFound`, `OhContact`, `OhDocs`). Status legend: **✓** kit component exists · **✚**
extend an existing kit component (add a mode/variant, never fork) · **○** compose from primitives.

## A. Marketing (public) — layout 3 (`OhTopBar` + `OhFooter`)

| Page | route | kit | states |
|---|---|---|---|
| Home | `/` | `OhHero`+`OhSection`+`OhBand` | static |
| How it works | `/how` | `OhSection`/`OhFeatures` | static |
| Features | `/features` | `OhFeatures` | static |
| Pricing | `/pricing` | `OhPricing` ✓ | static |
| Docs | `/docs` | `OhDocs` ✓ | static / search |
| Changelog | `/changelog` | `OhChangelog` ✓ | list |
| About | `/about` | `OhAbout` ✓ | static |
| Customers / Cases | `/cases`, `/cases/:id` | `OhCaseStudies`/`OhCaseStudy` ✓ | list / detail |
| Contact | `/contact` | `OhContact` ✓ | form: idle/sending/sent/error |
| Status | `/status` | `OhStatus` ✓ | live/degraded/down |
| Legal (Terms, Privacy, Security, DPA, Cookies, Subprocessors) | `/legal/:doc` | `OhLegal` ✓ | static |

## B. Auth — layout 1 (`OhAuth` centered card) · per-realm, **NO SSO**, `/api/identity/`

| Page | route | kit | states |
|---|---|---|---|
| Log in | `/signin` | `OhAuth mode="signin"` ✓ | idle / submitting / bad-credentials / locked |
| Sign up | `/signup` | `OhAuth mode="signup"` ✓ | idle / submitting / email-taken / weak-password |
| Forgot password (request) | `/forgot` | `OhAuth mode="forgot"` ✓ | idle / sent ("check your email") / error |
| **Reset password (with token)** | `/reset?token=` | `OhAuth mode="reset"` ✚ | valid-token / submitting / done / expired-or-invalid-token |
| Verify email (sent) | `/verify` | `OhAuth mode="verify"` ✚ | sent / resend |
| Verify email (confirmed landing) | `/verify?token=` | `OhAuth mode="verify"` ✚ | confirmed / invalid-or-expired |
| **MFA / 2FA challenge** | `/mfa` | `OhAuth mode="mfa"` ✚ | enter-code / invalid / use-backup-code |
| Accept invite | `/invite?token=` | `OhAuth mode="invite"` ✚ | set-name+password / invalid-or-used |
| Logged out | `/signed-out` | `OhAuth` ✚ | confirmation + "log back in" |
| Session expired | (modal/redirect) | `OhAuth` ✚ | "your session expired, sign in again" |

## C. Onboarding (first run, post-signup) — layout 2

| Page | route | kit | states |
|---|---|---|---|
| Welcome / setup (multi-step) | `/onboarding` | `OhOnboarding` ✓ | per-step progress; skip; done → app |
| Connect the editor / integration | step | `OhOnboarding` step | not-connected / connected |
| Invite your team (optional) | step | `OhOnboarding` step | skip / sent |

## D. The logged-in app — layout 2 (`OhAppShell` sidebar) · the product

| Page | route | kit | states |
|---|---|---|---|
| Dashboard / Home | `/app` | `OhDashboard` ✓ | empty (new account) / populated |
| Product screens (per surface — e.g. AIDevObserver: Review, Sessions, Findings, Agentic) | `/app/...` | `OhPageHead`+`OhTable`+cards | empty / loading / populated / error |
| Notifications | `/app/notifications` | `OhNotifications` ✓ | empty / list / mark-read |
| Search / Command-K | `⌘K` | `OhCommandK` ✓ | empty / results |
| Help / Support | `/app/help` | `OhDocs`/`OhContact` ✓ | static + contact |
| In-app 404 | `/app/*` | `OhNotFound` ✓ | not-found |

## E. Account & profile — layout 2 (sidebar + an **account sub-nav**)

| Page | route | kit | states |
|---|---|---|---|
| Profile | `/account` | `OhSettings` ✓ | view / editing / saved / error |
| Security — password change | `/account/security` | `OhSettings` ✓ | idle / wrong-current / saved |
| Security — MFA / 2FA setup | `/account/security` | `OhSettings`+`OhSwitch` ✚ | off / setup(QR) / on / regenerate-codes |
| Security — active sessions / devices | `/account/sessions` | `OhTable` ○ | list / revoke |
| API keys / BYO key | `/account/keys` | `OhApiKeys` ✓ | empty / list / create(reveal-once) / revoke |
| Notification preferences | `/account/notifications` | `OhSettings`+`OhSwitch` ✓ | toggles / saved |
| Appearance (theme) | `/account/appearance` | `OhSettings`+`OhThemeToggle` ✓ | light/dark/system |
| Connected integrations | `/account/integrations` | `OhTable`/cards ○ | connected / disconnect |
| Data export | `/account/export` | `OhSettings` ○ | request / preparing / download |
| **Danger zone — delete account** | `/account/danger` | `OhSettings` ○ | confirm (type-to-confirm) / deleting |

## F. Billing & subscription — layout 2 (sidebar + a **billing sub-nav**) · **usage-metered, not per-seat**

| Page | route | kit | states |
|---|---|---|---|
| Current plan + usage meter | `/billing` | `OhBilling`+`OhUsage` ✓ | within-limit / near-limit / over |
| Plans (in-app pricing) | `/billing/plans` | `OhPricing` ✓ | current-plan highlighted |
| Upgrade / Downgrade | `/billing/change` | `OhPricing`+confirm ○ | preview-proration / confirm / done |
| Payment method (add / update card) | `/billing/payment` | `OhBilling` form ✓ | none / add / update / invalid-card |
| Invoices / Receipts | `/billing/invoices` | `OhBilling`(invoices)/`OhTable` ✓ | empty / list / download |
| Billing history | `/billing/history` | `OhTable` ○ | list |
| Usage / metering detail | `/billing/usage` | `OhUsage` ✓ | per-metric breakdown |
| **Failed payment / dunning** | `/billing` banner + `/billing/payment` | `OhBilling` ✚ | past-due banner / retry / grace-period |
| Cancel subscription | `/billing/cancel` | confirm ○ | reason / confirm / cancels-at-period-end |
| Reactivate | `/billing` | `OhBilling` ○ | reactivate |
| Tax / VAT / billing details | `/billing/details` | `OhSettings` ○ | company, address, tax id |
| Credits / promo | `/billing` | `OhBilling` ○ | apply code / balance |

## G. Team / organization — layout 2 (sidebar + a **team sub-nav**)

| Page | route | kit | states |
|---|---|---|---|
| Members | `/team` | `OhTeam` ✓ | list / role-change / remove |
| Roles & permissions | `/team/roles` | `OhTable` ○ | matrix |
| Invites (send + pending) | `/team/invites` | `OhTeam` ✓ | none / pending / resend / revoke |
| Org settings | `/team/settings` | `OhSettings` ○ | name, logo, domain |
| Org switcher | (top of sidebar) | `OhAppShell` header ○ | switch active org |
| Team usage + savings | `/team/usage` | `OhUsage` ✓ | aggregate |
| Audit log | `/team/audit` | `OhAuditLog` ✓ | empty / list / filter |

## H. Developer · API · docs · MCP · integrations — layout 2 (sidebar + a **developer sub-nav**)

This surface is FIRST-CLASS for this family, not an afterthought: **AIDevObserver** ships an MCP server + a VS Code/
Cursor extension + a CLI + a PreToolUse hook, and **OpenHubForAI** literally IS a directory of MCP servers / tools /
skills (the registry browser). Three sub-areas.

### H1. Documentation & reference (`OhDocs` / `OhChangelog` — public docs use layout 3, in-app reference uses layout 2)

| Page | route | kit | notes |
|---|---|---|---|
| Docs home / getting started | `/docs` | `OhDocs` ✓ | the doc landing + search |
| Quickstart | `/docs/quickstart` | `OhDocs` ✓ | the 5-minute path |
| Guides / tutorials | `/docs/guides/:id` | `OhDocs` ✓ | how-to articles |
| **API reference** | `/docs/api` | `OhDocs` ✓ | endpoints + request/response schemas (generated from the seams) |
| SDKs (Python / JS) | `/docs/sdk/:lang` | `OhDocs` ✓ | install + usage |
| **CLI reference** | `/docs/cli` | `OhDocs` ✓ | commands (e.g. `python3 -m src.teleon.observer.cli`) |
| Examples / recipes | `/docs/examples` | `OhDocs` ✓ | copy-paste snippets |
| API changelog / versioning | `/docs/changelog` | `OhChangelog` ✓ | versioned API notes |

### H2. API access & keys (`OhApiKeys` / `OhUsage`)

| Page | route | kit | states |
|---|---|---|---|
| **API keys** (create / list / revoke) | `/dev/keys` | `OhApiKeys` ✓ | empty / create(**reveal once**) / revoke |
| Key scopes & permissions | `/dev/keys/:id` | `OhApiKeys` ✚ | scope toggles |
| Per-key usage | `/dev/keys/:id` | `OhUsage` ✓ | calls this period |
| **BYO inference key** | `/account/keys` | `OhSettings` ✓ | governed: used per request, NEVER stored or logged |
| **Service accounts / OAuth apps** (service-to-service) | `/dev/apps` | `OhApiKeys`/`OhTable` ○ | client id/secret, rotate, scopes, delegated calls |
| Rate limits / quotas | `/dev/limits` | `OhUsage` ○ | usage vs limit |
| Request logs | `/dev/logs` | `OhAuditLog`/`OhTable` ○ | recent calls: status, latency, key |

### H3. MCP · extensions · webhooks (the install / connect surface)

| Page | route | kit | notes |
|---|---|---|---|
| **Install / connect** (the integrations card) | each surface's Settings + its marketing "Where it runs" | the install-line list ○ | VS Code · Cursor · **MCP server** (`claude mcp add aidevobserver -- …`) · CLI · the PreToolUse hook — the SAME card on every surface |
| **MCP server / tool / skill directory** | `/registries` (OpenHubForAI) | the registry browser (`OhTable` + facet rail) ✓ | browse + filter + search — this IS OpenHubForAI's core surface |
| **MCP server / record detail** | `/registries/:id` | record-detail + records `OhTable` ✓ | what it provides + how to install; status shown honestly (live/partial/gap — discovery ≠ trust) |
| "Use via MCP" instructions | per server | a card with the copy-paste connect line ○ | how to add it to a client |
| Webhooks (config + delivery log) | `/dev/webhooks` | `OhTable` + form ○ | add / test / delivery history |
| Editor extensions (VS Code / Cursor) | marketing "Where it runs" + Settings | feature cards ○ | install links |

> AIDevObserver is itself an MCP SERVER a user adds to Claude Code; OpenHubForAI is a DIRECTORY of MCP servers /
> tools / skills (the registry browser). The "integrations card" (the install lines) is identical on every surface.

## I. System / utility (any layout / standalone)

| Page | route | kit | states |
|---|---|---|---|
| 404 Not found | `*` | `OhNotFound` ✓ | — |
| 500 / error boundary | — | `OhNotFound` variant ○ | error + retry/home |
| Maintenance | — | `OhNotFound` variant ○ | scheduled / back-soon |
| Status | `/status` | `OhStatus` ✓ | live / incident |

## The logged-in entry flow (wire this on every surface)

`marketing (/) → Login (OhAuth signin) → [first time: Onboarding] → App dashboard (OhAppShell)`. Today the "Sign in"
/ "Start free" CTAs jump straight into `/app`; the standard is to route them through `OhAuth` first, then the app.
The account/billing/team/developer areas are the SAME `OhAppShell`, switched by a secondary (sub-)nav, not a new layout.

## Rules (so the whole set stays consistent)

- Every internal page is one of the **three layouts** above; never a fourth.
- Reuse the kit component named in each row; **✚ = add a mode/variant to that component in the kit** (it propagates
  to all five surfaces), never a forked copy.
- **NO SSO** — a separate auth realm per product (hard lock); auth is `/api/identity/`.
- **Usage-metered, not per-seat** — billing/subscription pages reflect consumption.
- Every data page has **empty / loading / populated / error**; secrets (API/BYO keys) reveal once and are never
  stored; danger actions use type-to-confirm.
- One accent + copy per surface; backends only through seams; the proof gate stays green.
