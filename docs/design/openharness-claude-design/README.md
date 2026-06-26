# README: Claude Design handoff (AI Done Right, focus on AIDevObserver)

You are the designer ("Claude Design"). **This folder is self-contained. You do not need the rest of the repo.**
Everything you need (the design system, the actual source code, the backend contract, and the build spec with real
data) is in the files below.

## Upload this set (7 files, self-contained)

| File | What it is |
|---|---|
| **`README.md`** (this) | the front door and read order |
| **`AIDevObserver-BRIEF.md`** | the AIDevObserver build spec: screens, states, the real API JSON, the finding card, registry integrations, features, PMF, the deliverable |
| **`OpenHubForAI-BRIEF.md`** | the OpenHubForAI build spec: the record browsers (faceted table, card grid, browse-by-area, record detail), filters, search, over the real 242-record spine and facets |
| **`ARCHITECTURE-AND-PAGES.md`** | the WHOLE-PRODUCT context: architecture, tech stack, user flows, design schemes, and the full page inventory (marketing, auth, account, billing, subscription, team) |
| **`../../DESIGN-BIBLE.md`** | the design system guide: tokens, type, every component, the two layouts (marketing top-nav and the `OhAppShell` left-sidebar logged-in shell), routes, governance, copy rules |
| **`DESIGN-ASSETS.md`** | the ACTUAL source, verbatim: the full shared kit CSS and React components plus one complete app. When a doc says "see `oh-tokens.css`", the code is here |
| **`../../INTEGRATION-BIBLE.md`** | how a frontend talks to a backend (same-origin seams), local and cloud |

(`FAMILY-README.md`, `START-HERE.md`, `HANDOFF.md`, and `MARKETING.md` are extra orientation; the five files above are the package.)

## Read order

1. **This README** (orientation + the deliverable).
2. **`AIDevObserver-BRIEF.md`** (a main build: the AIDevObserver app, with real data).
3. **`OpenHubForAI-BRIEF.md`** (a main build: the OpenHubForAI record browsers, over the real spine and facets).
4. **`ARCHITECTURE-AND-PAGES.md`** (the whole-product context: flows, tech stack, and every page to build, from auth to billing).
5. **`DESIGN-BIBLE.md`** (the design system you build inside).
6. **`DESIGN-ASSETS.md`** (the source you reuse; do not reinvent the kit).
7. **`INTEGRATION-BIBLE.md`** (the API seams the app calls).

## Your deliverable (two things)

1. **The AIDevObserver app**, in the shared kit, accent `#b25fd6`: the `OhAppShell` left-sidebar logged-in shell
   (Review, Sessions, Findings, Settings), the `/demo` page, and the elevated marketing home. Render the REAL
   `/api/observer/review` payload (it is in the brief), not placeholder content.
2. **`INTEGRATION-HANDOFF.md`**: a README that explains how to merge your work into `web/aidevobserver/` without
   breaking the codebase. The constraints (do not fork the shared kit, reach backends only through seams, keep the
   proof gate green, follow the copy rules) are spelled out at the end of `AIDevObserver-BRIEF.md`.

## The three hard rules

1. **One design law:** all 5 surfaces use the SAME shared kit and differ ONLY by accent and copy. You edit a kit file
   once and it applies to all 5. Never style one surface in isolation, and never fork the kit.
2. **Copy rules:** no placeholders ("OpenHubForAI", never "Open*Hubs"); no em or en dashes; no strategy leakage
   ("moat", "wedge", "private bench"); real, confident sales and marketing copy.
3. **Integration safety:** backends are reached only through same-origin seams (`/api/observer/...`); the proof gate
   (`PYTHONPATH=. python3 scripts/run_proofs.py`) must stay green.

## Context in one paragraph

AI Done Right is a family of 5 product surfaces (AI Done Right the parent hub, Teleon, Baltor, AIDevObserver,
OpenHubForAI) that share one design system. **AIDevObserver** reviews how a team uses AI coding agents: it reads a
session, runs the review engine (grounded in a 147-catalog component federation), and returns ranked findings
(reinvention, wasted context, risky commands, missed cheaper paths) that the user triages. The accept-or-dismiss
signal is what makes it improve. It is the missing telemetry source for the `agent_behavior` and `agent_qa`
registries. serves_truth=false: findings are governed candidate suggestions a human reviews; the tool is read only
and stores nothing.
