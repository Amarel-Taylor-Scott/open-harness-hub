# BUILD-PROMPT — paste this whole block into Claude Design

> The single, aggressive prompt to paste when Claude Design leaves things unwired / missing / broken. Everything it
> needs is in this folder (START-HERE → DESIGN-BIBLE → DESIGN-ASSETS → SAAS-PAGE-INVENTORY → CONSISTENCY-CONTRACT →
> the briefs → AIDevObserver-app-STARTER.html). Copy from the line below to the end.

---

STOP. Read this entire instruction before you build, and follow it literally.

Build the **COMPLETE, FULLY-WIRED AIDevObserver web app** — not a design comp, not a mockup, not a subset, not "a
representative screen." The entire working product: every page, every button wired, every route rendering, output in
full. If your output is long, output all of it anyway. Partial output is a failure.

## OUTPUT (non-negotiable)
- **ONE self-contained `.html` artifact** that renders **EVERY** screen and page listed below, hash-routed, all
  working, when opened in a browser.
- **Emit every line.** You are FORBIDDEN to write `// …`, `/* rest is the same */`, `(other screens here)`,
  "the remaining pages follow the same pattern", or to truncate ANYTHING. If a section is repetitive, write it out
  in full anyway. Never stop early. Never summarize code instead of writing it.

## BUILD IN COMPLETE BATCHES — never thin everything to fit (this is how you avoid leaving pages out)
The full app is too big for one message. Do NOT respond by building a thin version of everything and stubbing the
rest — that is the exact failure I am rejecting. Instead, build into **one growing artifact**, one complete batch
at a time, and **keep going across messages on your own** (do not wait to be asked "continue") until **every** page
in the inventory exists and is wired. Each batch must be FULLY built and self-audited before you move to the next:

1. **App shell + all App pages** (Dashboard, Review, Sessions, Findings, Agentic, Notifications, ⌘K, Help, in-app 404)
2. **Auth + Onboarding** (login, signup, forgot, reset-token, verify, MFA, accept-invite, logged-out, expired, welcome)
3. **Account + Billing** (profile, security, keys, prefs, appearance, integrations, export, danger-zone; plan, plans,
   payment method, invoices, usage, dunning, cancel, reactivate, tax, credits)
4. **Team + Developer** (members, roles, invites, org settings, switcher, team usage, audit log; webhooks, API docs,
   rate limits, the integrations card)
5. **Marketing + System** (home, how-it-works, features, pricing, docs, changelog, about, cases, contact, status,
   legal; 404, 500, maintenance)

After each batch say which pages you just added and which remain, then immediately build the next batch. Go DEEP per
batch (every page in it fully wired) rather than SHALLOW across all (every page stubbed). Stop only when the inventory
is 100% built.

## The kit is a FIXED dependency — spend your output budget on SCREENS, not on re-deriving the kit
The shared kit (in `DESIGN-ASSETS.md`, already in `AIDevObserver-app-STARTER.html`) is DONE. Include it once,
unchanged, and spend the rest of your output building **pages**. Do not rewrite, restyle, or "improve" the kit, and
do not waste budget regenerating it each batch — reuse the components as-is so every token goes toward new wired pages.

## START from the working app, do not regress it
`AIDevObserver-app-STARTER.html` in this folder is the complete 5-screen app **already wired and working** (shared
kit + Review/Sessions/Findings/Agentic/Settings + a demo-data fetch shim so screens populate with no backend).
EXTEND it to the full page set below. Keep the shim and keep every screen populated. Do not break what works.

## BUILD EVERY PAGE (from `SAAS-PAGE-INVENTORY.md` — build EVERY row, each to its kit component + layout)
- **App (sidebar shell):** Dashboard, Review, Sessions, Findings, Agentic runs, Notifications, Search/⌘K, Help, in-app 404
- **Auth (centered `OhAuth` card):** Login, Sign up, Forgot password, **Reset password (token)**, Verify email,
  **MFA/2FA**, Accept invite, Logged out, Session expired
- **Onboarding:** multi-step welcome (connect editor, invite team)
- **Account:** Profile, Security (password + **MFA** + **active sessions/devices**), API/BYO keys, Notification
  preferences, Appearance, Connected integrations, Data export, **Danger-zone delete**
- **Billing:** Plan + usage meter, Plans, Upgrade/Downgrade, **Payment method (add/update card)**, Invoices,
  Billing history, Usage detail, **Failed-payment/dunning**, Cancel, Reactivate, Tax/VAT, Credits
- **Team:** Members, Roles, Invites (pending), Org settings, Org switcher, Team usage, **Audit log**
- **Developer:** API keys, **Webhooks**, API docs, Rate limits, **the integrations card** (MCP `claude mcp add`,
  VS Code, Cursor, CLI, PreToolUse hook, **Manual upload**)
- **Marketing:** Home, How-it-works, Features, Pricing, Docs, Changelog, About, Cases, Contact, Status, Legal
- **System:** 404, 500/error, Maintenance, Status

## EVERY interactive element MUST be wired — these are BANNED and will get the output rejected
- ❌ **Dead buttons.** Every `onClick`/button/link DOES something real: navigates to a route that EXISTS, opens a
  modal/drawer, toggles a state, submits a form (with loading → success/error), copies to clipboard, expands a row.
  A control that does nothing is a bug. There are zero exceptions.
- ❌ **Broken links / nav.** Every sidebar item, header link, footer link, sub-nav tab, and in-content link points to
  a route that EXISTS and renders a real page. No `href="#"` no-ops. No 404 on a nav item. No dangling routes.
- ❌ **Missing pages / placeholders.** Every page above must exist and render real content. NO "Coming soon", NO
  "TODO", NO `FIXME`, NO blank `<div>`, NO lorem-only screen.
- ❌ **Incorrect functionality.** Match the real API contract (`POST /api/observer/review|live|agentic`,
  `GET /api/observer/sessions`) and each screen's spec; the demo shim makes it work standalone — keep every screen
  populated and every fetching button transitioning loading → result.
- ❌ **A new CSS system or forked kit components.** Use the shared kit only (`OhTopBar`, `OhFooter`, `OhLayout`,
  `OhAppShell`, `OhAuth`, `OhDashboard`, `OhBilling`, `OhUsage`, `OhSettings`, `OhApiKeys`, `OhTeam`, `OhAuditLog`,
  `OhPricing`, `OhOnboarding`, `OhStatus`, `OhNotFound`, `OhPageHead`, `OhRollup`, `OhTable`, the finding card).
  Differ ONLY by accent (`#b25fd6`) and copy. One accent across the whole surface.
- ❌ **Console errors or warnings.** Zero.
- ❌ **Missing states.** Every data view designs and wires FOUR states: empty, loading (skeleton), populated, error
  (message + retry).

## Layout law (from `CONSISTENCY-CONTRACT.md`)
Three layouts only — Auth (centered `OhAuth` card), App shell (`OhLayout variant="sidebar"`, reused for account/
billing/team/developer via a sub-nav), Marketing (`OhTopBar` + `OhFooter` with a "Family" column). Never a fourth.
Light theme, Inter, mono for code. A working light/dark toggle in the header/sidebar foot.

## SELF-AUDIT — run this on your own output and FIX every failure before you return. Do not return until ALL pass.
1. Open the HTML. Click **every** sidebar item, **every** header link, **every** footer link, **every** sub-nav tab
   → each renders a real, complete page (no 404, no blank, no placeholder).
2. Click **every** button on **every** page → each does something visible (navigate / modal / toggle / submit / copy).
3. Submit each form → it shows loading, then success or error.
4. Trigger each empty and error state → it renders.
5. Open the browser console → **zero** errors and warnings.
6. Search your own output for: `coming soon`, `TODO`, `FIXME`, `placeholder`, `href="#"`, `// ...`, `rest of`,
   `same pattern` → **zero** matches. Any match means you are NOT done — go build it.
7. Confirm **every** route in the inventory exists and renders. Count them; if any are missing, add them.

Output the complete, self-contained, fully-wired HTML now — every page, every button, every state, every line. No
omissions, no truncation, no placeholders. If you are running low on space, keep going in the next message until the
ENTIRE app is emitted.
