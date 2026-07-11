# UX Ideation Backlog — AI Done Right

Prioritized, concrete UX opportunities for the family. These are **net-new product ideas**,
distinct from the consistency work tracked by `Design Acceptance Scorecard.html` and the
migration work in `HANDOFF.md §8`. Each item: the gap, the move, which sites, and rough
effort. Build any of these as a tweakable prototype (variations side-by-side) before
committing it across sites.

Ordering ≈ value ÷ effort. Don't build all of it — pull the top item, prototype, validate.

---

## P1 — High value, do next

### 1. Cross-site portfolio switcher  ✅ SHIPPED
**Status.** Done. `OhPortfolioMenu` lives in the kit (`oh-site.jsx`), rendered inside `OhTopBar`
(so it appears on Teleon, the 3 hubs, and OpenHubForAI marketing automatically) and wired into Baltor's
`MarketingTop`. It reads `window.PORTFOLIO`, groups by `LAYERS` (Products / Open resources),
shows each entity in its accent, and **auto-detects the current site from the URL** (marks it
“HERE”). No-ops if `PORTFOLIO` isn't loaded. The parent is excluded by design — it *is* the map.
**Original gap.** Seven sites, one company, but no consistent way to move between them.

### 2. First-run onboarding (empty → first value)
**Gap.** Dashboards assume a populated workspace. A brand-new user lands on someone else's data.
`OhOnboarding` exists in the kit but isn't wired into the first-run path.
**Move.** A 3-step checklist surface on first sign-in (Connect a source → Verify → Serve for
Baltor; Describe → Build → Promote for Teleon), dismissible, resumable, stored in localStorage.
Reuse the kit's progress pattern from Baltor `IngestPage` / Teleon `Runs`.
**Sites.** Baltor, Teleon. **Effort.** M.

### 3. Empty / loading / error states
**Gap.** Every list (corpora, conflicts, capabilities, registry browse) renders populated only.
No zero-state, skeleton, or failed-fetch state — the states a real build hits constantly.
**Move.** Three shared kit primitives: `OhEmpty` (icon + line + primary action), `OhSkeleton`
(shimmer rows for cards/tables), `OhError` (retry). Then apply per list.
**Sites.** All. **Effort.** S for primitives, M to apply. **Note.** Raises the Accessibility/
polish floor and is the most reused thing on this list.

---

## P2 — Worthwhile, after P1

### 4. Unify pricing on `OhPricing`
**Gap.** Baltor has a bespoke `PricingPage`; the kit has `OhPricing` (used by Teleon). Two
pricing layouts in one house. (Flagged in `HANDOFF.md` as an open item.)
**Move.** Move Baltor's three tiers into `OhPricing` data; keep its open-core note as a `slot`.
**Sites.** Baltor (Teleon already on it). **Effort.** S. Also nudges Scorecard C5/C6 up.

### 5. Command palette (⌘K)
**Gap.** Power navigation is all sidebar clicks. Dense apps (Baltor 11 nav items, OpenHubForAI ~43
routes) reward a fuzzy jump-to.
**Move.** Shared `OhCommandK` — routes + primary actions from each site's nav config, fuzzy
filter, keyboard-first. Config = the existing nav arrays.
**Sites.** Baltor, OpenHubForAI, Teleon. **Effort.** M.

### 6. Notifications / inbox depth
**Gap.** Teleon has `/notifications` (`OhNotifications`); Baltor's escalations (conflict review,
integrity quarantine) have no inbox — they only live on the Verify page.
**Move.** Route Baltor's escalations through `OhNotifications` (unread count in the top bar,
links to the reconciliation queue). **Sites.** Baltor. **Effort.** S–M.

### 7. Responsive / mobile pass on the app shells
**Gap.** Sidebars collapse to a wrapped row < 720px (functional, not designed). Marketing pages
are responsive; the consoles are desktop-first.
**Move.** A proper drawer/hamburger for `OhAppShell` + Baltor `AppShell` at small widths.
**Sites.** All app shells. **Effort.** M.

---

## P3 — Exploratory / lower urgency

- **8. Motion language.** One shared set of entrance/transition tokens (durations, easings) so
  page/route changes feel consistent. Today each site animates ad-hoc. Effort S, polish payoff.
- **9. Search across a corpus/registry.** Baltor corpus detail + the hubs' browse graphs would
  benefit from in-surface filter/search beyond the domain chips. Effort M.
- **10. Account/role depth.** `OhTeam` exists but roles are cosmetic. A permissions matrix
  (who can serve / publish / resolve conflicts) would make the governance story real. Effort M.
- **11. Density toggle.** A comfortable/compact setting for table-heavy consoles (audit, usage,
  corpora). Stored per user. Effort S.

---

## How to pick up
1. Choose ONE item (default: P1 #1 or #3 — both are shared kit additions that lift every site).
2. Prototype it as **tweakable variations** in a single file (not N loose files) so directions
   sit side by side.
3. Validate against `Design Acceptance Scorecard.html` before promoting it house-wide.
4. New shared components follow the kit's additive pattern (optional props, `Object.assign`
   export) — the same way `OhDashboard.feature` was added this session.
