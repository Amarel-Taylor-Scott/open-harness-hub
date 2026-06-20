<!-- Transcribed from owner research (2026-05-28). Addendum to corpus-acquisition-grid-spec.md.
     Runnable: scripts/acquisition/gap_screen.py + research_queue.py. -->
# Gap-detection screen — knowing a cell is a gap *before* you collect it

The clean lift test is `pipeline_score − bare_model_score`. But that needs content
you don't have yet — you can't run a full lift benchmark on millions of candidate
cells, let alone uncollected ones. So "only collect what LLMs lack" needs a **cheap
predictor of lack that runs before collection.** That predictor is the whole game,
and it's the piece the collection-grid spec hand-waved as "expected_lift comes from
external signals." Here it is, runnable.

## Two stages

**Stage 1 — SCREEN** (cheap, every candidate cell, no collection). Combine a battery
of gap signals into a `gap_likelihood`. Runs across the whole address space.
→ `scripts/acquisition/gap_screen.py`.

**Stage 2 — CONFIRM** (expensive, only high-likelihood × high-value cells). Collect a
thin sample, build a minimal pipeline, run the REAL lift benchmark
(`scripts/eval/durable_gap_harness.py` + the lift gate). Only if it clears do you
commit deep-collection budget. **Sample → confirm → scale** breaks the
chicken-and-egg.

## The signal battery (Stage 1)

| Signal | Kind | Reads gap when… |
|---|---|---|
| corpus / index density | **model-independent** | indexed/English/crawlable text is sparse, PDF-only, login-walled |
| query-miss logs | **model-independent** | the registry couldn't answer real user questions here (purest signal) |
| source tier | **model-independent** | authoritative source is high-tier (4–5) = low training exposure |
| regulatory velocity | **model-independent** | the cell changes faster than any snapshot |
| confident-hallucination probe | **bridge** | model confidently fabricates a verifiable artifact (a circular number, a date) |
| cross-model disagreement | model-dependent | a panel (incl. the frontier) disagrees / universally hedges |
| hedge / perplexity / self-consistency | model-dependent | high hedging, high perplexity on cell entities, high paraphrase variance |
| recency gap | model-dependent | latest issuance the model knows ≪ the cell's real cadence |

## THE SAFEGUARD (the recursed trap)

If you detect gaps by asking the model where it's weak, **you've let the model draw
the map again.** Model-introspection (hedging, disagreement) only catches *known
unknowns* — places the model knows it's unsure. It is structurally **blind to
confident unknowns**: things it never saw and answers about with total fluency and
zero hedge — often your highest-value gaps (un-crawled tier-4 truth). So the screen
**weights model-independent signals highest**, with the confident-hallucination
probe as the bridge. *The model can tell you where it knows it's weak; only the
external world can tell you where it's confidently blind.* `gap_screen.screen()`
reports `model_independent_share` so you can verify the verdict isn't model-drawn.

## Two disciplines

1. **A spike is model- and time-relative.** Re-run the screen each model generation
   (the `decay_signal` from the durability axis): a cell with no spike today gets one
   when the next frontier model ships — retire collection there, don't keep feeding it.
2. **Probe the frontier, not the cheap model.** Screen against a weak open model and
   everything looks like a gap. The baseline must be what your buyer would otherwise use.

## Worked sort (real, 2026)

- **PH × AML × BSP × 2026** → models hedge/fabricate the Circular 1230 threshold;
  index density low/PDF/ASPX; velocity high → **screen says gap → confirm → collect.**
- **France × corporate-tax basics** → models agree; index density enormous →
  **spike → skip** without spending a cent of collection budget.

`gap_screen` self-test reproduces this (PH confirm@~0.79, France skip@~0.06). The
owner feeds areas via `data/research-queue/areas.jsonl`; `research_queue` runs the
screen, feeds `gap_likelihood` into the value function, and prints the queue.
