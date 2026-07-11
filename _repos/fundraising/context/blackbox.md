# fundraising — blackbox view

**What this file is.** The standalone briefing for a session that manages ONLY the fundraising context repo:
what this repo owns (its published interface), its current contents, and how it connects. Every claim links
to a real source; where the two disagree, the cited source wins. How this repo connects to its neighbors is
in `edges.md` + `../EDGES.md`.

## What this repo owns (its published interface)

The money/market **plan** — kept separate from the deck itself (the sibling `pitch-decks`) and from product
code. Source of the interface: `../../dev-rules-context/contracts/surface-registry.json` (surface
`fundraising`). It exposes:

- **gtm-plan** — the go-to-market plan: beachhead vertical, motion, phased launch.
- **fundraising-strategy** — the fundraising strategy: round shape, targets, timeline, use of funds.
- **investor-outreach** — investor outreach tracking + materials (public-only, no confidential data).
- **market-sizing** — market sizing (TAM / SAM / SOM) for the consumption context layer.

**Context-only, no product code.** Nothing here is importable; it is *read* for grounding.

## Current contents (`context/`)

- **`baltor-gtm-fundraising-plan.md`** — the Baltor GTM & fundraising plan: positioning, beachhead, buyer,
  pilot offer, fundraising narrative, and seed milestones. Moved losslessly from
  `_repos/shared-backend-components/docs/strategy/baltor-gtm-fundraising-plan.md`.

## Reference note (repointed on move)

Because this plan was previously baltor's GTM grounding doc, several portfolio references were repointed to
its new home here (the `/goal` reading lists in `.claude/commands/goal.md` + `.codex/prompts/goal.md`,
`_repos/baltor/context/blackbox.md`, `_repos/_shared/PRODUCT-MARKET-FIT.md`, and the strategy docs
`yc-master-current-state-business-plan-and-pitch.md`, `portfolio-pmf-solidification-2026-07-01.md`,
`document-cascade-improvement-loop-2026-06-20.md`, `baltor-autonomous-goal.md`). A classifier self-test in
`scripts/plan_context_reorg.py` and a dated review snapshot still name the old path by design (a script and
a frozen artifact). Baltor now reaches this plan as a doc pointer across the org; that is a "see also"
reference, not a code import, so it does not create a runtime dependency edge.

## Connections

See `edges.md` (neighbor view) and `../EDGES.md` (generated contract). This repo may consume
`dev-rules-context` (standards) and `aidoneright` (brand public face); nobody consumes it yet. Its numbers
must stay consistent with the sibling `pitch-decks` (the deck) and `yc-applications` (which cite this plan's
GTM and market sizing).
