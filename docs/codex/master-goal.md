# Master Goal — The Long-Horizon Program

> **This is the single canonical goal.** An agent (Claude Code / Codex) reads
> this at session start and can run for hours or days, across every phase of
> the project, without re-deriving strategy. It reconciles and supersedes the
> fragmented goal docs — see *Reconciliation map* at the bottom. When this doc
> and any other goal/runbook doc disagree, **this doc wins**; fix the other.

## Mission (one sentence)

Build a portable, database-backed registry **and** an easy conversational
builder of reusable AI-pipeline components whose **only** admission criterion
is **capability lift over a bare LLM** — and make the headline interaction land:
*paste a task description, get back a working, costed, deployable flow built
from existing components.*

## The usefulness bar — the front gate (read this before generating anything)

A component is useful **if and only if** it lets a model do something it
**cannot do reliably alone.** Everything in the registry must clear this bar.

- **Operational test:** a benchmark delta — `pipeline_score − bare_model_score`
  on a real task — that is meaningfully **> 0**. If a current frontier model
  already does the task zero-shot, the component does not belong here.
- **Dominant axis:** `not_solved_by_out_of_box_llms` / capability-lift. In the
  priority formula it is no longer just one weighted term among many; it is a
  **hard floor** — a row below the lift floor is dropped, not down-weighted.
- **Where the lift is largest (the Kaggle/hackathon evidence):** esoteric,
  specialized arenas where the base model lacks knowledge or reliability, but a
  grounded, structured pipeline fixes it — domain-specific rules, citeable
  facts, deterministic checks, retrieval over private/long-tail corpora,
  multi-step verification, tool use, and review gates. Spend the budget there.
- **The anti-examples (do not generate / do not catalog):** combinatorial
  template clones (`scale-*-arm-NNN`), restyled prompts a model writes fine on
  its own, general dev resources (web frameworks, learn-to-code lists), and any
  "component" with no measurable lift. These dilute search and inflate counts.

## Non-goals — admission filters, not disclaimers

From `docs/about/project.md`, promoted to hard gates:

- **Not** a hosted inference provider.
- **Not** a fork of any eval framework.
- **Not** tied to any single industry.
- **Not** a re-implementation of capability the model already has. *(new — the
  capability-lift bar, stated as a non-goal so it gates intake, repos, and
  corpora alike.)*

## The six supervisors (gates)

A staged batch is run through all six. **A batch that fails any gate is not
promoted and is not counted toward yield.** Most of these already exist as
scripts; the table says what is real vs. what needs work.

| # | Gate | Enforces | Today |
|---|------|----------|-------|
| 1 | **Green build** | `scripts/validate.py` exits 0 on changed paths | ✅ green (kept honest per cycle) |
| 2 | **Stats fresh** | `scripts/build_readme_stats.py --check` passes (no hand-typed counts) | ✅ passing |
| 3 | **Novelty / dedupe** | reject near-duplicates; SimHash/LSH blocking so a batch > ~1–2k does not hang | ⚠️ O(n²) bottleneck — `duplicate_collapse_report.py` exists; needs LSH |
| 4 | **Capability-lift** | priority score above floor **with `not_solved_by_out_of_box_llms` as a hard floor**, benchmark delta where available | ⚠️ `candidate_promotion_scorer.py` scores it (weight 1.2) but does not *gate* on it |
| 5 | **Provenance** | every row carries `source_url` + `license` + `author`; uncertain → review ticket | ✅ fields exist; enforce in the gate |
| 6 | **Vectorization** | no promotion without a **real** embedding (declared model + dim from `scripts/_config.py`); hash/zero vectors are staging-only | ❌ 0 embeddings today — P1 unblocks this |

## The in-session loop (runs for hours)

Per `autonomous-session-runbook.md`, ~20–45 min per cycle, never stop on a block:

```
ORIENT  → read the session ledger; pick the highest-value unblocked item
PLAN    → state the one batch this cycle produces (one path)
BUILD   → durable change: full row families; real embeddings for promotable rows
VALIDATE→ fast path on changed paths only (gates 1–2 inline)
RECORD  → append a ledger line: counts (generated/staged/committed/vectorized),
          yield (useful-promoted), validation result
BRANCH  → blocked? switch paths, note roadblock + fallback; do NOT end
REPEAT
```

Counts are produced by `scripts/factory/daily_stage_ledger.py` and
`run_report.py` — never hand-typed (no-magic-values).

## The phases (the days-long arc)

Advance a phase only when its **exit criteria** are green. Phases overlap at the
edges, but do not scale (P5) before the foundation (P1) and integration (P3)
hold.

### P0 — Reconcile & hygiene *(make the project internally consistent)*
- **Entry:** now.
- **Do:** keep the validator green and stats fresh (done this cycle); finish the
  `manifest`/`primitive`/`artifact` → `component` rename in prose **and** in the
  derived DB (`dist/catalog.sqlite` still has an `artifacts` table); collapse the
  overlapping goal docs under this one (Reconciliation map); expand
  `docs/strategy/product-market-monetization-brief.md` (named competition,
  pricing tiers, a single beachhead wedge, the capability-lift moat, an
  OSS-ecosystem ingestion line); **cull the `scale-*` filler** the novelty + lift
  gates reject.
- **Exit:** validator green; `--check` fresh; one canonical goal doc; vocabulary
  consistent code→DB→prose; brief has competitors + pricing + wedge; filler
  removed from the candidate set.

### P1 — Foundation *(turn the design into a running substrate)*
- **Do:** stand up real embeddings — install `sentence-transformers` **or** wire
  a hosted embedding route through the model registry in `scripts/_config.py`;
  embed the 530 committed components with a declared model+dim; load
  `object_embedding` and run `vector_readiness_audit.py`. Turn the two ⚠️ gates
  real: add SimHash/LSH blocking to dedupe; make `candidate_promotion_scorer.py`
  **gate** (hard lift floor), not just score.
- **Exit:** hybrid search (keyword + vector + graph + facet) returns the 530 real
  components; promotion is blocked without a real vector; a batch of 1k passes
  all six gates end to end.

### P2 — Component MVPs *(build the capability-lift families that compound)*
- **Do:** prioritize families with the highest, most measurable lift, each
  shipped with its own benchmark (so the lift is provable): token-efficiency /
  input compression; output-format / strict-envelope control; grounded
  domain-fact + rule packs in esoteric arenas (the verticals pattern: ESG,
  GxP, customs, nuclear, etc.); retrieval/verification/citation packs;
  deterministic pre-LLM checks. Each family = component + rubric + benchmark +
  a showcase pipeline that uses it.
- **Exit:** ≥ N families where the benchmark shows a positive bare-vs-pipeline
  delta; every promoted component is vectorized and benchmarked.

### P3 — Integration *(the paste-to-flow builder)*
- **Do:** build the conversational builder over the vectorized registry —
  understand → hybrid-retrieve → assemble (honoring the hard wiring rules) →
  estimate cost/model-swap → emit deployment blueprint → refine. Maintain the
  **builder benchmark** (`pasted challenge → expected component flow`) fed by the
  Kaggle corpus, so retrieval/assembly quality has a score that can regress.
- **Exit:** paste a real (held-out) Kaggle/use-case task → builder returns a
  validated, costed flow whose composed score beats the bare model on that
  task's own metric; builder benchmark passing.

### P4 — Full MVP *(the sellable product from the brief)*
- **Do:** wrap P1–P3 in the MVP from the monetization brief — searchable private
  registry, task-to-pipeline recommendation, cheap/balanced/quality-first costed
  blueprints, Postgres/pgvector, CPU workers, object storage, exportable
  runtime/Terraform/MCP bundle, eval + review scaffolding, auth + metering.
- **Exit:** one external user can describe a task, get a costed flow, deploy the
  bundle in their environment, and the eval/review trail is real. First paying
  workflow validated against actual run costs.

### P5 — Scaling *(10k useful/day → billion tier)*
- **Do:** run the gated daily loop at volume — partitioned generation (10×1k,
  not a monolithic run; the ledger proved 1k ≈ 31s, 10k monolithic hangs),
  source-surface matrix automation (incl. governed GitHub-repo intake as a
  *source surface*, not a new type), CDC + partitioned loads, cost ceiling held.
- **Exit:** the **yield metric** — *useful, promoted, vectorized, novel
  components/day* — sustains the target; tiers T1 (1M) → T2 (100M) → T3 (1B+)
  each fully vectorized and hybrid-searchable before the next is scaled.

## Daily contract — the metric that kills filler

Report **useful-promoted/day**, not generated/day. A day that generates 10,000
candidates and promotes 200 that each clear the capability-lift bar scored 200,
not 10,000. Always separate and report: generated candidates · unique staged ·
candidate-load-ready · promotion-ready · committed Postgres · **vector-search
ready**.

## Non-negotiables (carry over, enforced harder)

- Capability-lift bar + non-goals gate **all** intake (components, corpora, repos).
- No real PII/secrets/proprietary dumps — synthetic or public metadata only.
- Do not republish `_reference/`.
- No new insurance work; do not expand legacy insurance examples.
- Promotion boundary: no tenant-visible row with open/high-risk review,
  placeholder embeddings, unresolved provenance, or volatile facts without
  CDC/revocation.
- No magic values — counts/dims/model-IDs/paths/thresholds/versions have one
  source (`no-magic-values.md`).
- ID & hash discipline (`CLAUDE.md`): stable hash suffixes; formatting changes
  never mint false versions.

## Reconciliation map (what this supersedes)

This doc is the canonical goal. The following remain as **detail appendices**
for the section noted; they must not restate strategy that conflicts here:

- `billion-component-goal.md` → tiering detail + vectorization mandate (P5/P1).
- `million-object-goal.md` → *superseded*; keep only as history.
- `daily-production-targets.md` → daily mix detail (P5).
- `multi-day-goal-runbook.md` → multi-day state mechanics (the loop).
- `autonomous-session-runbook.md` → the in-session engine (the loop).
- `speed-guardrails.md` / `quality-gates.md` → gate detail (supervisors 1–6).
- `object-factory-workflow.md` → the factory spine (P1/P5).

If any appendix contradicts this page, this page is correct — update the appendix.
