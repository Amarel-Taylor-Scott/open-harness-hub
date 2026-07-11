# pitch-decks — blackbox view

**What this file is.** The standalone briefing for a session that manages ONLY the pitch-decks context
repo: what this repo owns (its published interface), its current contents, and pointers to the deck material
that stays code-coupled in `shared-backend-components`. Every claim links to a real source; where the two
disagree, the cited source wins. How this repo connects to its neighbors is in `edges.md` + `../EDGES.md`.

## What this repo owns (its published interface)

The outward-facing fundraising **story**, kept separate from product code and from the internal business
memory. Source of the interface: `../../dev-rules-context/contracts/surface-registry.json` (surface
`pitch-decks`). It exposes:

- **pitch-deck** — the investor pitch deck (slides + speaker narrative) for the AI Done Right portfolio.
- **investor-narrative** — the long-form investment narrative: problem, wedge, moat, why-now.
- **one-pager** — the single-page investor summary.
- **traction-metrics** — traction + metrics evidence supporting the raise (proof-first; every number is
  measured or directly computable, never a vanity figure hand-typed into prose).

**Context-only, no product code.** Nothing here is importable; it is *read* for grounding.

## Current contents (`context/`)

- **`pitch.md`** — the acquihire / acquirer-conversation pitch narrative (the wedge, the moat, why a
  team+tech buy). Moved losslessly from `_repos/shared-backend-components/docs/internal/acquihire/pitch.md`.
  It carries wiki-style links to `[[acquihire-roadmap]]` (the execution plan) that travel with the file.
- **`traction-and-metrics.md`** — the traction & metrics evidence: what is measured, what is staged, what
  is aspirational, each with the exact command to recompute it so nothing drifts. Moved losslessly from
  `_repos/shared-backend-components/docs/internal/acquihire/traction-and-metrics.md`.

## Pointers — deck material that stays in `shared-backend-components` (code-coupled)

Two pitch assets are **read by code** and therefore stay where the code expects them (moving them would
break a green check; the code was not edited). Read them in place:

- **The rendered pitch-deck data:** `_repos/shared-backend-components/architecture/teleon_pitch_deck.json`
  — the deck source (slides + demo) with **every number computed live**. It is read/rendered by several
  scripts (`scripts/build_pitch_deck.py`, `scripts/build_yc_demo.py`, `scripts/yc_readiness.py`,
  `scripts/flywheel_proof_modules.py`, `scripts/multi_model_improvement_loop.py`), so it stays as code-read
  config. Do not hand-edit the numbers.
- **The consolidated master pitch:**
  `_repos/shared-backend-components/docs/strategy/yc-master-current-state-business-plan-and-pitch.md`
  — the current-state + business-plan + pitch master. It stays because
  `scripts/check_parallel_dev_lanes.py` (with `architecture/parallel_dev_lanes.json`) hardcodes its path as
  a shared-serialized dev-lane file; moving it would fail that check.

## Connections

See `edges.md` (neighbor view) and `../EDGES.md` (generated contract). This repo may consume
`dev-rules-context` (standards) and `aidoneright` (brand public face); nobody consumes it yet. Its numbers
should stay consistent with the sibling `fundraising` repo's plan.
