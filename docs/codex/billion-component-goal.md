# Billion Component Goal

> The north-star goal for Open Harness Hub. It mirrors and supersedes
> `docs/codex/million-object-goal.md`: same priority formula, same row
> families, same safety non-negotiables — but the target is **thousands of
> millions of components** (10⁸–10⁹+), every component is **vectorized and
> searchable**, and the front door is an **easy conversational builder** that
> turns a plain-language task into a runnable, costed, deployable pipeline.

The million goal is the proven floor. This is the ceiling we build toward.

## Objective

Scale Open Harness Hub into a validated, signed, versioned, deduped, and
deployable registry of **thousands of millions** of reusable AI pipeline
components and subcomponents — and make all of it reachable two ways:

1. **By vector.** Every component carries a real embedding and is retrievable
   by semantic, keyword, graph, and facet search together (hybrid retrieval).
2. **By conversation.** A user describes a task, role, procedure, policy,
   alert workflow, or domain problem in natural language and gets back a
   composed pipeline — components, RAG packs, tools, rubrics, cost/model/
   hosting estimates, and a deployment blueprint — without learning the
   schema first.

## The three improvements over the million goal

This goal adds three load-bearing pillars on top of everything in
`million-object-goal.md`:

1. **Everything vectorized (no dark rows).** A component is not "done" until
   it has a real embedding from a declared model + dimension and an index
   record. Placeholder/zero vectors may exist in staging but **must not be
   promoted** to tenant-visible search. See *Vectorization mandate* below.
2. **An easy conversational builder.** The registry is a product, not a file
   dump. The builder is the primary surface; the catalog is its substrate.
   See *Conversational builder* below.
3. **Single source of truth / no magic values.** Scaling 1000× multiplies any
   drift 1000×. Counts, dimensions, model IDs, paths, thresholds, and
   versions get one definition and are derived everywhere else. This is a hard
   requirement now, not a cleanup task — see
   [`no-magic-values.md`](no-magic-values.md).

## Component definition (unchanged)

A component is any durable, typed unit that improves a pipeline; subcomponents
are smaller rows that belong to, configure, test, verify, or enrich a
component. Most high-volume atoms live as **database-backed rows with JSONL
staging**, not standalone files. Required row families per the factory
(`CLAUDE.md`): `source_record`, `normalized_object`, `canonical_entity`,
`object_entity_ref`, `dedupe_cluster`, `label_assignment`, `dimension_value`,
`object_embedding`, `index_record`, and `review_ticket` when risk warrants.

## Priority formula (unchanged)

```
priority = usefulness x demand x complexity x time_savings
         x frequency_of_deployment x not_solved_by_out_of_box_llms
         x cost_savings x deployment_management_value x model_swap_value

capability_spike ~= verifiability x training_attention
                  x data_coverage x economic_value
```

Spend the budget where economic value is large, facts/procedures are
verifiable, and out-of-box LLMs are weak without structured tools, RAG, or
workflow logic.

## Target composition (tiered to a billion)

Grow in tiers; each tier must be fully vectorized and searchable before the
next is scaled. Per-tier mix scales the proven million composition ~1000×:

| Tier | Components | Gate to advance |
|---|---|---|
| **T1 — proven floor** | 1,000,000 | million-goal composition, all promoted rows vectorized, hybrid search live |
| **T2 — breadth** | ~100,000,000 | source-surface matrix automated, dedupe collapse < target, conversational builder in beta |
| **T3 — billion+** | 1,000,000,000+ | partitioned load + CDC at scale, cost ceiling held, builder eval passing |

A representative billion-scale mix (≈1000× the T1 table):

- ~250M occupation work atoms (O*NET, ESCO, BLS ORS, SOC, ISCO, curated roles);
- ~200M procedure questions and checklist items (SOPs, audits, standards, forms, training);
- ~150M versioned public facts (gov, regulatory, public health, standards, market);
- ~100M tools, adapters, API patterns, cloud functions, containerized workers;
- ~100M domain RAG chunks with provenance and retrieval policies;
- ~75M rubrics and benchmark cases;
- ~75M deployment blueprints, Terraform/MCP setup patterns, runtime profiles;
- ~50M workflow graph patterns (ComfyUI-like, n8n-like, agent, data, media, enterprise);
- ~25M skill/agent-workflow components from controlled reference intake.

## High-value component families to prioritize

Beyond the composition above, these families score high on the priority
formula — especially `cost_savings`, `not_solved_by_out_of_box_llms`, and
`time_savings` — and repeat across every domain, so they compound:

- **Token-efficiency / input compression.** Shrink what the model must read:
  context pruning, retrieved-chunk dedupe, extractive pre-summarization, prompt
  compression (LLMLingua-style), schema-aware field selection, and token
  budgeters that cap context to a cost ceiling. Each declares tokens-in saved
  and any quality trade-off.
- **Output reduction / terse-output control.** Shrink what the model writes:
  max-token / max-char budgets, answer-only response policies, stop-sequence
  and length-penalty profiles, summarize-then-return wrappers. Pair with a
  rubric so brevity never costs correctness.
- **Output-format / response-shaping.** Force the response into a specific
  shape — strict JSON (schema-constrained or function-call), Markdown, tables,
  CSV, a fixed character/word count, or a typed envelope — with a validator
  that rejects or repairs non-conforming output. The existing `format response`
  pipeline kind and the `refuse-on-redacted` / `critical-tier-output-override`
  patterns are seeds here.

Each is a first-class, **vectorized, benchmarkable** component carrying its own
eval (did it cut tokens / hold the format without losing task quality?), so the
conversational builder can offer "make it cheaper" or "return strict JSON" as a
one-line refinement.

## Vectorization mandate

- Every promotable component row carries an `object_embedding` produced by a
  **declared model + dimension drawn from one config source** (no per-file
  literals — see [`no-magic-values.md`](no-magic-values.md)).
- **Hybrid retrieval is the default**: keyword + vector + graph + facet, fused
  into one ranked result. A component must be reachable by all four.
- Placeholder, zero, or hash-fallback embeddings are allowed in staging only.
  They are a **promotion blocker** — `scripts.db.daily_promotion_readiness_plan`
  must refuse to promote a row whose vector is not real.
- Embeddings are reproducible: the model ID, dimension, normalization, and
  source content hash travel with the vector so re-embeds are detectable and
  index deltas stay deterministic.
- Re-embedding on model change is a planned migration (new index records +
  CDC), never a silent overwrite.

## Conversational builder

The builder is the product surface. The flow:

1. **Understand** — parse the user's natural-language task into intent,
   domain, modality, constraints (cost ceiling, latency, on-prem vs hosted,
   privacy/trust boundary, jurisdiction).
2. **Retrieve** — hybrid search over the vectorized registry for candidate
   pipelines, components, RAG packs, tools, rubrics, and prior showcase
   pipelines.
3. **Assemble** — compose a pipeline DAG of harnesses + rule packs + tools +
   knowledge packs, honoring the hard wiring rules (a pipeline never wires a
   raw rule pack to a model; volatile facts live in tools/knowledge packs;
   every harness declares `model_targets`).
4. **Estimate** — model/runtime cost, hosting shape, and a model-swap matrix
   (local → OpenAI-compatible → managed API → tenant key).
5. **Emit** — a deployment blueprint: runtime profile, MCP/Terraform setup
   where appropriate, eval rubric, and a benchmark to score the result.
6. **Refine** — the user converses ("cheaper", "fully local", "add a review
   queue", "stricter rubric") and the build updates.

The builder must explain *why* each component was chosen (provenance, license,
trust boundary, freshness) and route sensitive domains through review queues,
verified facts, signed publishers, and deterministic gates rather than "just
ask the model."

**The builder is itself evaluated.** Maintain a benchmark of
task-description → expected-component-set so retrieval/assembly quality has a
score that can regress. A good recommendation that cannot be measured does not
count.

### The headline interaction

Open the application, **paste in an LLM challenge or use-case description, and
get back a working flow** — a composed, validated, costed pipeline of existing
components, ready to run or deploy. This single paste-to-flow interaction is
the product. Everything else (the registry, the vectors, the row families)
exists to make it land.

## Use cases and evaluation — the Kaggle competition corpus

Kaggle competitions are the primary supply of **real, diverse, labeled task
descriptions**, so they serve double duty: example use cases *and* the
builder's test set.

- **Scrape broadly and keep going.** Continue mining the full breadth of
  competitions — LLM usage, LLM fine-tuning/tuning, RAG, evaluation/judging,
  classification, extraction, multimodal, time series, tabular — not just the
  LLM-labeled ones. The existing miners are the starting point:
  `scripts/mine_kaggle_harnesses.py` and `scripts/mine_meta_kaggle.py` (prior
  findings live in `data/kaggle-mining-findings-*.json`, and ~24–27 verified
  pipelines are already ported with author + URL + license).
- **Each competition becomes two artifacts.**
  1. a **use-case** — the task statement, constraints, and a showcase pipeline
     the builder produces for it;
  2. a **builder benchmark case** — `pasted challenge text → expected
     component flow`, scored so retrieval/assembly quality can regress.
- **Test the headline interaction with it.** Replay each pasted challenge
  through the builder and grade the composed flow against the expected
  components and the competition's own success metric. This is how "paste a
  challenge, get a working flow" stays honest as the registry grows.
- **Respect provenance and licensing.** Port only permissively-licensed
  material, carry author + URL + license in the component definition, store
  synthetic/public metadata only, and route anything uncertain to a review
  ticket. Never republish `_reference/` or scraped raw dumps.

## Daily production target

- Generate ≥ 1,000 database-backed component candidates/day; stretch to 5,000
  when source surfaces, workers, and validation are healthy.
- **Vectorize the day's promotable candidates** — embedding work rows are part
  of a valid daily batch, not a later phase.
- Add or refresh 5–25 preconfigured showcase pipelines/day that exercise the
  conversational builder end to end (AML alert review, social-media
  moderation, public-fact propagation, trades work-order triage, water/food
  quality, used-car sales, SOC alert quality, disaster response, public
  procurement, content creation, …).
- Keep public definitions focused on tools, packs, pipelines, schemas,
  rubrics, and docs that make generation repeatable.
- Keep high-volume candidates in Postgres/pgvector-ready JSONL row families
  until reviewed, deduped, approved, promoted, and versioned.

If one source cannot reach the daily target, **switch paths, do not stop**:
another source-surface matrix, a smaller partition, generate
pipelines/rubrics/benchmarks while ingestion is blocked, route uncertain
sources to review tickets, and document the roadblock and fallback used.

## Promotion boundary (unchanged, enforced harder)

Candidate-table load readiness is **not** publication readiness. A row stays
out of tenant-visible search while it has open/high-risk review tickets,
placeholder embeddings, unresolved source/signature questions, or volatile
public facts without CDC/revocation handling. Use
`scripts.db.daily_promotion_readiness_plan` after large generation. Separate
and report: generated candidates · unique staged rows · candidate-table load
readiness · active promotion readiness · committed Postgres rows · vector
search product readiness.

## Non-negotiables

- Validate with `python3 scripts/validate.py`; rebuild generated docs with
  `python3 scripts/build_catalog_pages.py` (full runs are release gates; use
  the focused fast path for daily turns — see `CLAUDE.md`).
- **No magic values** — counts, dimensions, model IDs, paths, thresholds, and
  versions follow [`no-magic-values.md`](no-magic-values.md).
- **Everything promoted is vectorized** — no dark rows in tenant search.
- No real PII, secrets, confidential data, or proprietary dumps — synthetic or
  public metadata only.
- Do not republish `_reference/`.
- Stay away from insurance pipelines in new work; do not expand legacy ones.
- Preserve provenance, license, trust boundary, privacy boundary, and
  freshness; use signatures, archive captures, hashes, and revocation metadata
  for volatile or publisher-owned facts.
- Never count raw generated lines as committed database state; use staged load
  audits and committed Postgres count reports.
- IDs and hashes follow the ID & hash discipline in `CLAUDE.md` (stable hash
  suffixes; formatting changes never mint false versions).

## Expected closeout

Every serious turn reports: what changed; which files matter; which scaling
path (fast/daily vs full release gate) was used; the component-definition
count when available; generated/staged/committed/**vectorized** database
counts; validation and page-rebuild results; and the next logical factory
area.
