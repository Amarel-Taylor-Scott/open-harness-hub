# yc-applications — blackbox view

**What this file is.** The standalone briefing for a session that manages ONLY the yc-applications context
repo: what this repo owns (its published interface), its current contents, and pointers to the readiness /
storyboard / loop material that stays code-coupled in `shared-backend-components`. Every claim links to a
real source; where the two disagree, the cited source wins. How this repo connects to its neighbors is in
`edges.md` + `../EDGES.md`.

## What this repo owns (its published interface)

The Y Combinator (and other accelerator) **application artifacts**, kept separate from product code. Source
of the interface: `../../dev-rules-context/contracts/surface-registry.json` (surface `yc-applications`). It
exposes:

- **yc-application** — the accelerator application draft: answers, founder story, video script.
- **yc-readiness** — YC-readiness scoring across the dimensions gate. **Computed** by
  `scripts/yc_readiness.py` (never asserted here).
- **demo-storyboard** — the YC / demo-day storyboard: the live capability demo sequence.
- **founder-answers** — reusable answers to common YC / investor founder questions.

**Context-only, no product code.** Nothing here is importable; it is *read* for grounding.

## Current contents (`context/`)

- **`yc-application-2026.md`** — the working YC application draft (the single application surface: answers,
  founder story, one-minute-video script; owner-decision items flagged, not invented). Moved losslessly
  from `_repos/_shared/strategy/yc-application-2026.md`. A farm-symlink mirror of it at
  `_repos/shared-backend-components/docs/strategy/yc-application-2026.md` became dangling on the move and was
  removed; `scripts/multi_model_improvement_loop.py` globs `docs/strategy/yc-application*.md` behind a
  graceful `.exists()` guard, so nothing breaks.

## Pointers — readiness / storyboard / loop material that stays (code-coupled)

Three inputs are **read by code** and stay where the code expects them (moving them would break a green
check; the code was not edited). Read them in place:

- **`yc-readiness` is computed, not stored.** `scripts/yc_readiness.py` reads its target doc
  `_repos/shared-backend-components/docs/strategy/yc-readiness-and-prep-2026.md` via
  `_exists(YC_PREP_DOC)` (line ~75) as part of the readiness score. That doc stays in place — moving it
  regresses the computed score. Never restate a readiness number in prose; read the scorer's output.
- **The demo storyboard data:** `_repos/shared-backend-components/architecture/yc_demo_storyboard.json` —
  the demo-day storyboard sequence, read by `scripts/check_yc_demo_recording.py` (its `STORYBOARD`
  constant). Stays as code-read config.
- **The YC-readiness dev-loop `/goal` entrypoint:**
  `_repos/shared-backend-components/docs/goals/yc-readiness-loop.md` — the long goal the shared improvement
  loop steers toward (tied to `scripts/yc_readiness.py`; its path is also cited by
  `scripts/check_live_ofac_receipt.py`). It is dev-process infrastructure, so it stays with the loop it
  drives.

## Historical note

The earlier "Teleon YC application kit" (00-strategy-and-spine, 01-application-answers, 02-one-minute-video,
03-deck, …) index was **archived** (not deleted) to
`_repos/_shared/archive/legacy/_shared/yc/README.md`. Archived material is off-limits to moves; restore is a
`git mv` if the owner wants it here.

## Connections

See `edges.md` (neighbor view) and `../EDGES.md` (generated contract). This repo may consume
`dev-rules-context` (standards) and `aidoneright` (brand public face); nobody consumes it yet. Its demo /
deck references should stay consistent with the sibling `pitch-decks` and `fundraising` repos.
