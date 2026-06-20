# Autonomous Session Runbook — Work For Hours Without Stalling

> A robust, self-sustaining work loop for a single multi-hour agent session
> (Codex or Claude Code). The goal is `docs/codex/billion-component-goal.md`;
> this page is *how to keep making validated progress toward it for hours*
> without waiting for permission between steps and without stopping when one
> path is blocked.
>
> **2026-05-31 update:** active `/goal` runs should now start from
> `docs/codex/baltor-clean-context.md` and
> `docs/codex/baltor-autonomous-goal.md`. The loop mechanics below still apply.
>
> Pace and daily mix come from `daily-production-targets.md`; multi-day state
> comes from `multi-day-goal-runbook.md`; speed rules from
> `speed-guardrails.md`. This page is the in-session engine that ties them
> together.

## Session contract

- **Default to the fast path.** Never full-rebuild the catalog or run global
  validation as the inner loop — those are release gates (`CLAUDE.md`,
  `speed-guardrails.md`). Validate only changed paths each cycle.
- **Small, coherent, validated batches.** Every cycle ends green or is rolled
  back. Never leave the tree invalid between cycles.
- **Never stop on a block — switch paths.** The work-path menu always has a
  path that needs no network and no external provider.
- **Keep a session ledger** so a fresh context (after compaction or restart)
  can resume without re-deriving state.
- **Honor every non-negotiable** in the billion goal: no real PII, no
  republishing `_reference/`, no new insurance work, promotion boundary,
  ID/hash discipline, and **no magic values**
  ([`no-magic-values.md`](no-magic-values.md)).

## The loop (repeat ~20–45 min per cycle)

```
1. ORIENT   read the session ledger; pick the highest-value unblocked item.
2. PLAN     state the one batch this cycle will produce (1 path from the menu).
3. BUILD    make the durable change — small, coherent, with full row families
            and real embeddings for any promotable rows.
4. VALIDATE fast path on changed paths only:
              python3 scripts/validate.py <changed catalog paths>
              python3 scripts/build_component_id_index.py --update <changed paths>
              python3 scripts/build_catalog_pages.py --paths <changed paths> --update-index
              python3 scripts/validate.py --global-ref-check <changed pipeline paths>
              python3 scripts/build_component_id_index.py --check-fresh
5. RECORD   append a ledger line: cycle, path, what changed, files that matter,
            generated/staged/committed/vectorized counts, validation result.
6. BRANCH   if BUILD or VALIDATE was blocked, switch to another menu path and
            note the roadblock + fallback. Do NOT end the session.
7. REPEAT   back to step 1.
```

Run `scripts/factory/daily_stage_ledger.py` (and `run_report.py`) to keep the
counts honest; do not hand-type them (that would violate
[`no-magic-values.md`](no-magic-values.md)).

## Work-path menu (priority-ordered)

Always pick the highest item that is unblocked. Higher paths buy more trust;
lower paths are the always-available fallbacks that keep the session moving.

**P0 — Truth and hygiene (do these first, once each; they are cheap and
high-leverage; sourced from the 2026-05-26 repo review):**

- Add a `.gitignore` so 2.8G of `dist/` generated output and 2.4G of
  `_reference/` clones cannot be staged by accident (and exclude `.DS_Store`).
- Replace the README's hand-typed `172 components / v0.3.0` with a generated,
  diff-checked stats block (driven by `oh_hub stats` /
  `build_catalog_index.py`) per [`no-magic-values.md`](no-magic-values.md).
- Add `scripts/_config.py` and dedupe the seven-plus `384` embedding-dimension
  literals and scattered model-ID strings into one definition + a model
  registry; build every `vector(...)` string from the constant.
- Finish the `manifest`/`primitive` → `component`/`subcomponent` vocabulary
  rename in user-facing prose (`CLAUDE.md` mandates this).

**P1 — Vectorize the dark rows.** Turn placeholder/hash-fallback embeddings
into real embeddings (declared model + dimension from config), emit index
records, and re-run `scripts.db.daily_promotion_readiness_plan`. No promoted
row stays unvectorized.

**P2 — Kaggle competition corpus.** Mine more competitions
(`mine_kaggle_harnesses.py`, `mine_meta_kaggle.py`) across LLM usage, tuning,
RAG, eval, multimodal, tabular. Each competition → one use-case + one builder
benchmark case (`pasted challenge → expected component flow`). Permissive
licenses only; carry author + URL + license; uncertain → review ticket.

**P3 — Conversational builder.** Improve the paste-a-challenge → working-flow
path and its eval harness (understand → retrieve → assemble → estimate → emit
→ refine). Score against the Kaggle benchmark set.

**P4 — Daily factory batch.** Generate 1,000–5,000 database-backed candidates
with full row families (`source_record` … `index_record`, `review_ticket`
where risk warrants), staged as JSONL, vectorized, with load/promotion audits.

**P5 — Showcase pipelines.** Add or refresh 5–25 preconfigured showcase
pipelines/day that exercise the builder end to end across domains.

**P6 — Always-available fallback (no network needed).** When every source,
scraper, provider, or full rebuild is slow or blocked: generate pipeline
templates, rubrics, benchmark rows, repair planners for missing row families,
and docs/runbooks that prevent repeated slow or incorrect paths.

## Unblock rules (why the loop never stops)

- A blocked scraper/API/provider → drop to **P6** (pure-local generation) and
  log the block.
- A slow full rebuild → stop repeating it; switch to fast-path validation on
  changed paths and capture the bottleneck as a P0/P6 improvement.
- An uncertain or sensitive source → route to a **review ticket**, do not
  publish, keep moving.
- A validation failure → fix or revert *this cycle's* change; never carry an
  invalid tree into the next cycle.
- Missing row families in a batch → run the repair planner rather than
  promoting incomplete rows.

## Guardrails and stop conditions

Keep going across these — they shape work, they don't end the session:

- **Safety:** no real PII/secrets/confidential/proprietary data; synthetic or
  public metadata only; no `_reference/` republish; no new insurance work.
- **Promotion boundary:** candidate load-readiness ≠ publication. Open/high-
  risk review tickets, placeholder embeddings, or unresolved
  source/signature/CDC questions block promotion.
- **Accounting honesty:** never count raw generated lines as committed rows;
  separate generated · staged · load-ready · promotion-ready · committed ·
  vector-search-ready.
- **No magic values:** every value used twice has one definition; counts and
  versions are computed, not typed.

**Actually stop only when:** the user-set cost/time budget is reached; a
safety or licensing question needs a human; or repeated cycles produce no
validated progress (record why and surface it).

## Resumability

Persist enough state to resume cold:

- a session-ledger file (one line per cycle: timestamp, path, change, files,
  counts, validation result) under `.research-notes/` or `dist/factory-runs/`;
- the current P0 checklist state (which one-time items are done);
- the next intended path.

On resume: read the ledger, confirm the tree is valid
(`validate.py` on recently changed paths), and re-enter the loop at step 1.

## Per-cycle and end-of-session closeout

Each cycle records what changed, which files matter, the path used (fast vs
release gate), counts, and validation result. The end-of-session report sums
the cycles: total validated batches, generated/staged/committed/vectorized
deltas, P0 items completed, roadblocks hit with the fallback used, and the
next logical factory area.
