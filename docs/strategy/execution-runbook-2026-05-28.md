<!-- Companion to north-stars.md, external-research-brief-2026-05-28.md, corpus-acquisition-grid-spec.md,
     gap-detection-screen-spec.md. A runbook, not a strategy doc: ship the DoD, don't gold-plate.
     Status tags reflect repo state on 2026-05-28. -->
# OHH Execution Runbook — low-hanging fruit + parallel agent fleet

## North Star (the only goal this sprint serves)

> **One benchmarked sanctions-screening workflow that visibly beats the frontier
> model (Claude Opus 4.7 / GPT-5.5) with a signed, dated provenance trail — in
> front of one design partner.** De-risks CEO/CFO/CRO/CCSO at once. Every lane is
> justified only by how it serves this; otherwise it's parked.

## Operating rules (so parallel ≠ sprawl)

1. **Lock the spine before fan-out.** All lanes commit against one contract — here
   the single-source modules `scripts/eval/reason_codes.py` (lift_reason →
   durability_class, mechanisms, tiers, decay_signal) and `scripts/acquisition/`
   (cell schema + value function + gap screen). No lane reinvents them.
2. **Frontier baseline, always.** Lift is measured vs the model a buyer would
   otherwise use (Claude Opus 4.7 / GPT-5.5), never a cheap OSS model.
3. **DoD or it's not done.** Each lane ships a thin demonstrable slice in ≤2 weeks.
4. **No new families without clearing the two-axis gate** (lift AND durable reason).
5. **Weekly integration checkpoint** vs `docs/codex/master-goal.md`; off-North-Star → park.
6. **Model-independence rule for gap-finding:** weight external signals (index
   density, tier, regulatory velocity, query-miss logs) over model self-report.

## P0 — serial, do first (unblocks everyone)

- **P0.1 Lock the shared spine.** Durability axis + provenance + cell coordinates +
  value-function contract. **Status: SUBSTANTIALLY DONE in code** (the single-source
  modules above). **Remaining:** add `lift_reason / durability_class / decay_signal /
  last_lift_eval` as OPTIONAL fields on the component schema (`schemas/*.json`) so
  YAML components can carry them; keep the validator green (optional → existing
  components still pass). ← next serial task.
- **P0.2 Close the security hole.** Token-gate `/api/build` + `/api/export`.
  **Status: DONE** (`OH_SHOWCASE_TOKEN`; verified 401/200). CI running self-tests +
  validator on push: **TODO**.

## P1 — parallel fleet (each ≤2-week thin slice)

### Lane A — Wedge vertical ★ CRITICAL PATH = the North Star
OFAC SLS connector (delta + CDC) → screening pipeline (fuzzy match + 50%-rule
aggregation = the lift) → frontier-baseline benchmark recording `lift_delta` →
surface provenance + a revocation event. **DoD:** a shareable run that beats the
frontier AND shows the signed source/date + a "superseded" event.
**Status: SCAFFOLD IN PROGRESS** (background agent: `scripts/wedge/` deterministic
screen + benchmark harness over synthetic fixtures; the live OFAC connector + real
frontier baseline are the follow-ups).

### Lane B — Gap-detection screen
**Status: BUILT** (`scripts/acquisition/gap_screen.py` + `research_queue.py`; sanity
check passes — PH×AML×BSP→gap, France×corporate-tax→spike). **Remaining:** wire the
real cross-model probes + live query-miss logging (today the model-dependent signals
are inputs, not yet auto-probed).

### Lane C — Kaggle harness ingestion (low-hanging fruit)
Kaggle API pull → boilerplate-vs-pipeline extractor (reject Unsloth/LoRA/4-bit
plumbing) → frontier-baseline re-test → auto-classify **cost-lift** (transient, tag)
vs **capability-lift** (admit) → license gate (Apache-2.0 pass; Gemma ToU flag;
unlabeled → review). **DoD:** N admitted + N tagged, license-cleared. **Status: TODO**
(needs network; do not admit a harness until Lane A's frontier classifier exists).

### Lane D — Governance made visible (the moat, surfaced)
C2PA-style signed manifests (X.509 + content hash + appended chain) → show
source/freshness/signer per component in the UI → CDC fixtures (CSDDD pre/post-Omnibus,
BSP Circular 1230). **DoD:** a component shows signer/source/effective-date + a
working "superseded → successor" state. **Status: TODO**.

### Lane E — Foundation at scale (unblocks scale, NOT the demo)
Postgres/pgvector + partitioned load + committed-count audit; port SimHash/LSH dedup
into the factory; gap scout on cron. **DoD:** live rows + honest staged-vs-committed-
vs-vectorized accounting. **Status: TODO** (Lane A demos on a thin local slice meanwhile).

### Lane F — Strategy / review (non-engineering, continuous)
Lock wedge (sanctions primary, EU-AI-Act docs second, CSDDD → showcase); recruit ONE
design partner + ONE verified publisher; monthly competitive watch; 8-lens rubric per
release. **DoD:** a signed LOI partner + a tested price + a recruited publisher.

### Lane G — Negative-space corpus cells (the owner's live feed) — NEW
Owner feeds cells to `data/research-queue/areas.jsonl`; the screen ranks them.
Confirmed-gap cells now include **developing-country building / safety / medical
regulations** (PH/ID/NG building codes, PH FDA, OSH) — all screen as `confirm`,
motivated by the Angeles City building collapse. **DoD per cell:** source registry
(spec §4) + a defensive detection component (If Statement + Knowledge Corpus +
routing Action with citations). **Status: IN PROGRESS** (background agent building the
PH building-safety registry + worked example). **Safety:** detection + routing +
citations only; never evasion; no PII; bias review.

## Harvester backends (the "openclaw / hermes / similar" ask)

Keep the Harvester role (spec §3/§6) **tool-agnostic**: a thin per-source adapter
interface so browser/agent backends (openclaw, hermes, Playwright, etc.) plug in
behind one contract. Tier-1 = direct API; Tier-2/3 = browser-agent backend; Tier-4 =
human-router (no backend closes it). Don't hard-wire one tool; the value is the
registry + screen + governance, not the crawler.

## Dependency map

```
spine (reason_codes + acquisition) ──► all lanes      P0.2 security ──► any public demo [DONE]
Lane A (wedge) = the demo  ◄── Lane D wraps A in visible provenance
Lane B (screen) ──► ranks cells ──► tells C/A/G what to collect next
Lane C (Kaggle) ──► catalog, uses A's benchmark rig    Lane E ──► scale, not the first demo
Lane G (cells) ──► feeds B/the queue (owner-driven)    Lane F ──► consumes A's demo
```
Hard serial edges only: **P0 → all** and **A → demo → F's pitch.** Else concurrent.

## Kill / park list (anti-sprawl)

✗ boil-the-ocean corpus (head of distribution, ~zero lift) · ✗ commodity
fine-tuning-mechanics components · ✗ a second vertical before sanctions proves ·
✗ billion-tier infra before the wedge pays · ✗ LLM-proposed collection targets.

## First-week checklist

1. [P0.1] add the durability fields to `schemas/*.json` (optional), validator green.
2. [P0.2] CI on push (self-tests + validator). 
3. [A] OFAC SLS connector (SDN + delta) — promote the scaffold to a live pull.
4. [A] real frontier baseline replacing the benchmark stub.
5. [G] commit the building-safety registry + worked example (agent output).
6. [B] wire query-miss logging from the showcase into the queue.
7. [D] render source/date/signer on one component in the UI.
8. [F] draft sanctions design-partner outreach; shortlist 3 + 1 verified publisher.
