# Evidence-Driven Component Factory (the no-filler design)

> **Status:** design. Supersedes the combinatorial clone generator
> (`scripts/factory/daily_thousand_component_seeds.py`) as the path to volume.
> Operationalizes `_repos/_shared/codex/master-goal.md` (the lift bar, screen→confirm, the
> two-axis gate, useful-promoted/day, partitioned 10×1k) by adding the one piece
> the codebase is missing: a **measurement loop** that proves lift instead of
> asserting it.

## The problem with what we have

Two factory paths exist, and each fails the bar in opposite ways:

| Path | What it is | Why it fails |
|---|---|---|
| `daily_thousand_component_seeds.py` | `domain × primitive × source_type` cross-product → IDs `daily-0007-trades-hvac-…` | **Pure filler.** No source, no agent, no dedup, no measured lift. 1,000 clones in 6.8s. |
| `run_factory.py` | Good modular spine: walk → propose → quality-gate → SimHash-dedup → emit | Proposer is a **deterministic stub** (one knowledge-pack per node, no real extraction); never runs the **lift gate**; network-bound. |
| `capability_lift_gate.py` | Hard lift-floor + SimHash/LSH novelty | **Orphaned** (nothing imports it) and scores **structural heuristics only** — never a measured `pipeline_score − bare_model_score`. |

**Filler is a structural consequence of *enumeration*.** If you generate by taking a
cross-product of dimensions, you get clones. The fix is not a better filter on top of
enumeration — it is to **never enumerate**. Generate from *evidence*.

## The principle: every component is born from evidence

A component may exist **only if** all three are true and recorded on the component:

1. **A measured gap** — a real task an out-of-the-box model does *not* do reliably
   (caught by running the bare model and checking it, not by asserting it).
2. **A real source** — a fetchable, licensed, attributable artifact that supplies what
   the model lacks (a regulation, dataset, standard, API, procedure, repo).
3. **A measured lift** — `pipeline_score − bare_model_score > 0` on held-out instances
   of that task, with a durability classification.

No cross-product can satisfy these. A clone has no gap evidence, no distinct source,
and no positive delta — so it can never be minted. **This is the anti-filler guarantee,
enforced by construction, not by cleanup.**

## The crux that makes volume affordable

Measuring lift costs model calls, so "10,000/day with real measurement" sounds
impossible. It isn't, because of one move:

> **Volume comes from rich sources mined *deterministically*, not from per-component
> model calls — and lift is measured per *family*, amortized across the components that
> share a gap.**

A single authoritative source is a *high-yield vein*: the EU CSDDD yields ~71 article
facts (→ Knowledge Corpus entries), dozens of forced-labor indicators (→ Conditionals),
exact-id lookups (→ retrieval triggers). Mining it is **deterministic** (parse, extract,
chunk, hash) — no model call per fact. The expensive steps (confirm the gap is real;
measure the lift) run **once per task-family / per source**, not once per row. So:

- **Cheap & deterministic (bulk of the work):** source mining, extraction, formatting,
  standardization, hashing, dedup, row emission, embeddings (batched).
- **Model/agent calls (rationed, amortized):** gap confirmation (per area), component
  authoring where extraction needs judgment (per source), lift measurement + judging
  (per family). Reserve the big model; push deterministic and small-model work down
  (the project thesis: *small models + narrow scope + deterministic harnesses*).

That is how the funnel reaches 10k genuine components/day without 10k×N model calls.

## The pipeline (eight modular stages)

```
 0 GAP DISCOVERY      where does the bare model fail? (measure, don't assert)
 1 SOURCE ACQUISITION search for the licensed source that fixes it
 2 CONSTRUCTION       agent + tools mine the source into typed components
 3 STANDARDIZE        canonical body, schema-valid, ID + content/version hash
 4 DEDUP              SimHash + LSH (+ embedding near-dup) — drop/merge clones
 5 LIFT MEASUREMENT   run bare vs pipeline on held-out tasks → delta + durability
 6 GATE               admit iff measured delta>0 AND durable AND sourced AND novel
 7 STAGE & LOAD       row families → real embeddings → JSONL → Postgres/pgvector
```

Each stage is a module with a single contract: it takes and returns a `Candidate`
(below), so stages are swappable and testable in isolation — the modularization you
asked for. The orchestrator threads one `Candidate` list through the stages, partitioned
by area, run by a worker fleet.

### Stage-by-stage: what does the work, what we reuse, what we build

| Stage | Real work (agents · tools · search) | Reuse | Build (the gap today) |
|---|---|---|---|
| **0 Gap discovery** | A **probe agent** generates candidate tasks in an area, runs the **bare model**, and a **checker** (deterministic vs an authoritative answer, or LLM-judge) detects failure: hallucination, hedge, refusal, wrong-vs-source. Model-independent signals dominate. | `acquisition/gap_screen.py` (model-independent weights), `research_queue.py`, `factory/capability_gap_scout.py` | The **bare-model probe + checker** — the actual measurement. Today gaps are hand-typed hints. |
| **1 Source acquisition** | A **scout agent** searches the web + registries for the authoritative source that closes the gap, license-filters it, and classifies the **target component type** it can yield. | `run_factory.py` walkers (Wikipedia·USCode·Wikidata·NIST), `source_surface_*`, `public_source_scan_jobs.py`; GitHub repos as `source_kind: github_repo` | A generic **search→source→license→classify** scout (not just the 4 fixed walkers). |
| **2 Construction** | An **author agent** mines the source into typed components, calling **deterministic tools** for the mechanical parts: extract facts→Knowledge Corpus; extract IF-patterns→Conditional; wrap API/CLI→Action(tool); rubric/persona/harness as fit. Small models for compression/polish. | the `propose_drafts_fn` plug-point in `run_factory.run_factory` (designed for exactly this swap) | Replace `_stub_propose_drafts` with an **agent+tool author**; deterministic extractors per source kind. |
| **3 Standardize** | No model. Canonical body, vocabulary enforcement (Knowledge Corpus·Conditional·Action), schema validation, ID `{type}/{slug}` + **stable content & version hash suffixes** (no truncation-only IDs). | `processors/draft_manifest_yaml_emitter.py` (schema validation), `scripts/_config.py`, `scripts/validate.py` | A shared **hashing/ID module** (content-hash, version-hash) per CLAUDE.md ID discipline. |
| **4 Dedup** | No model (until embeddings). SimHash + LSH banding, type-blocked, O(n·log n); then embedding near-dup once vectors are real. Drop or merge into canonical. | `processors/semantic_dedup.py`, `processors/lsh_dedup_blocking.py`, the SimHash/LSH in `capability_lift_gate.py` | **Unify** these into ONE `factory/novelty.py` (single source). Fix synonym-clone evasion (the `expansion-vN` family) by also keying on **distinct source_url** — no source ⇒ suspect. |
| **5 Lift measurement** | A **runner** executes (a) the bare model and (b) the pipeline-with-this-component on held-out task instances; a **judge agent** (LLM-judge + deterministic checks) scores both → `delta`, plus durability via `reason_codes.py`. Amortized per family. | `eval/reason_codes.py`, `eval/durable_gap_harness.py`, rubric/benchmark types, `emit/promptfoo`, `emit/lm-eval` | **The measurement loop itself** — the linchpin that exists nowhere today. This is the *builder benchmark* the master-goal P3 requires. |
| **6 Gate** | Deterministic. Admit iff **measured delta > 0** (hard floor) AND structural durability AND provenance complete AND novel. The structural score becomes the cheap *pre-*filter; the measured delta is the *confirm* (the screen→confirm design). | `capability_lift_gate.py` (wire it in!) | Upgrade the gate to consume the **measured** delta, not only heuristics; emit `review_ticket` on uncertainty. |
| **7 Stage & load** | Deterministic + batched. Emit canonical row families, **real** embeddings (batched), index records, CDC events; partitioned load. | `scripts/db/*` load plans, `factory_jsonl_to_postgres.py`, `factory/daily_stage_ledger.py`, `_config.py` (dims/model) | Wire **real embeddings** (sentence-transformers or hosted route) — promotion is blocked on a real vector (gate #6). |

> **Agents** here can be Claude sub-agents (Claude Code Agent tool / Claude Agent SDK):
> a `gap-prober`, a `source-scout`, a `component-author`, a `lift-judge`. Each is narrow,
> tool-equipped, and cheap to run in a fleet. **Tools** are the catalog's own tools +
> web search + the walkers. **Search** is first-class in Stages 0–1 (does the model
> fail? does a source exist?).

## The modular contract (one object threaded through every stage)

```python
@dataclass
class Candidate:
    # provenance of WHY it exists (the anti-filler evidence)
    gap_id: str                 # the measured gap this serves
    gap_evidence: dict          # bare-model failure sample(s) + signal scores
    source: dict                # source_url · author · license · source_kind
    # the component itself
    target_type: str            # knowledge-pack | rule-pack | tool | ... (one of 14)
    primitive: str              # Input | Knowledge Corpus | Conditional | Action | ...
    body: dict                  # the schema-valid component definition
    content_hash: str           # stable; formatting-invariant
    version_hash: str
    # measured outcomes (filled by later stages)
    novelty: dict | None        # simhash, lsh band, nearest, decision
    lift: dict | None           # bare_score, pipeline_score, delta, n, durability_class
    decision: str | None        # keep | cull | review ; + reasons[]
```

A stage is `fn(list[Candidate]) -> list[Candidate]`. Pure, testable, swappable. A stage
that can't satisfy the contract (no source, no positive delta) drops the candidate with a
reason — it never silently passes filler downstream.

## Throughput: the funnel, not a flat number

Report the **funnel**, never "10k generated":

```
areas probed → gaps confirmed → sources found → drafts built → novel → lift-measured → PROMOTED
```

10,000/day is a **promoted** target (useful-promoted, per the master-goal daily contract).
Reaching it:

- **Partition 10×1k** by area/source-surface (the ledger proved 1k is seconds, 10k
  monolithic hangs). One partition = one worker = one rich source mined deterministically.
- **A worker fleet** (`factory/object_factory_workers.py`) runs partitions in parallel;
  model/agent calls are rationed to Stages 0/2/5 and **amortized per family**, not per row.
- **Yield is the metric to optimize.** A rich source with a confirmed gap can yield
  hundreds of genuine components from one gap-confirmation + one family lift-measurement.
- **Honest accounting:** early on, promoted/day will be far below 10k while the
  measurement loop is young. That is correct — scale the fleet (and the source vein list)
  as the promoted-rate and the wedge validate. Never report processed as promoted.

## What to kill / deprecate

- **Retire** `daily_thousand_component_seeds.py` as a *generation* path (keep only as a
  row-shape fixture if useful). It is the cross-product filler engine.
- **Cull** the committed `scale-*` / `expansion-vN` families that evade the current gate
  (they self-label `expansion-vN`, while the gate only matches `scale-expansion`) — and
  fix the gate's marker set + add the source-url novelty key so they can't re-enter.
- **Stop** counting generated candidates as components anywhere in prose/README (the
  no-magic-values rule already mandates computed counts; report the funnel).

## Sequenced build plan

1. **Unify novelty** → one `scripts/factory/novelty.py` (SimHash+LSH from the gate +
   `semantic_dedup` + `lsh_dedup_blocking`), with the source-url key. *(cheap, high value)*
2. **Define `Candidate`** + the stage-contract module; refactor `run_factory.py`'s loop
   to thread it (the spine already matches).
3. **Wire the gate** (`capability_lift_gate.run_gate`) into the pipeline as Stage 6;
   upgrade its marker set; make it consume a measured delta when present.
4. **Build Stage 5 (measurement)** — the bare-vs-pipeline runner + LLM-judge over a
   held-out task set per family. This is the linchpin; start with one wedge family
   (ESG/CSDDD) where we already have assets, prove a positive delta end-to-end.
5. **Build Stage 0 (probe)** — bare-model probe + checker feeding `gap_screen.py` real
   (measured) signals instead of hand-typed hints.
6. **Replace the stub proposer** (Stage 2) with an agent+tool author, one source kind at
   a time (start: regulation/standard → Knowledge Corpus + Conditional).
7. **Wire real embeddings** (Stage 7) so promotion can clear gate #6.
8. **Fleet + partition** the orchestrator to 10×1k; report the funnel in the ledger.

**First concrete step (do next):** Stage 1 unify-novelty + the `Candidate` contract +
wire the gate — all deterministic, no model cost, immediately makes `run_factory` produce
*gated, deduped* output. Then Stage 5 on the ESG family to prove one real measured lift.

## Risks (stated honestly)

- **Measurement cost at scale** — mitigated by amortizing lift per family and mining rich
  sources deterministically; still the dominant cost. Budget model calls explicitly.
- **"Is the gap real?" depends on the checker** — where no deterministic check exists, an
  LLM-judge is itself fallible; require model-independent signals to dominate (per
  `gap_screen.py`) and route uncertain gaps to review.
- **10k/day promoted is a high bar** — treat it as the fleet-scaled target after the loop
  is proven on the wedge, not a day-one number. The funnel keeps us honest.

## Containerized worker orchestration (consolidated)

> Folds the durable design of the merged containerized-object-factory-orchestration plan — how the Stage-7 / fleet workers actually run as containerized queue lanes. The eight-stage pipeline above is the logic; this is the parallel execution substrate.

The registry needs parallel workers, not one local generation loop. Containerize a worker when it needs browser automation, custom system dependencies, source-specific clients, repository checkouts, OCR, media processing, or tenant-isolated execution. Use separate **queue lanes**: discovery (find source surfaces, feeds, repos, papers, datasets, workflow galleries, forms, standards) · spider (crawl approved domains, paginate, archive, hash, emit source records) · snapshot (raw HTML/PDF/media/repo metadata/workflow files → object storage) · normalize (pages/PDFs/notebooks/workflow JSON/READMEs → Markdown or structured records) · enrich (extract candidate primitives, entities, labels, dimensions, dedupe signals) · embed (batch embeddings for hot pgvector slices + cold warehouse exports) · verify (schema, citation, policy, test, eval, safety checks) · promote (review tickets, promotion decisions, index records, catalog component candidates) · warehouse (cold shards → BigQuery / analytic tier).

**Parallelism contract:** each worker leases a shard, emits append-only outputs, and never directly publishes public objects — publication happens through review + promotion. Every shard carries `partition_id` / `run_id` / `source_surface_id` / `tenant_id`, the source-governance decision, object-storage input/output pointers, worker image digest + git commit, prompt template id + prompt hash (when a model is used), model route + pricing snapshot + estimated cost, retry count + error class + review-ticket ids, and output row counts per family. **Prompt-cache savings** compound when harnesses standardize the stable preamble / schema / tool-signature / few-shot / output-order / refusal blocks first and isolate variable user/source content late — versioned by `prompt_template_id` / `prompt_version` / `prompt_hash` — so provider prefix caches reuse stable prefixes and the platform reuses its own trajectory fragments (see the Prompt ABI + trajectory-fragment-cache design). **Cheap default shape:** one API service, one Redis/managed queue, one Postgres/pgvector, one object bucket, three worker containers (discovery/spider, normalize/enrich, verify/promote); split later into specialized containers for browser scraping, repo mining, workflow mining, embedding batches, BigQuery export, and model-heavy polishing. **Safety:** source governance (not discovery) decides scrape/store/index/publish; spiders honor allowlists, robots/policy, rate limits, and license boundaries; raw snapshots stay in object storage; tenant-private outputs never enter shared indexes without explicit promotion; expensive model calls happen only after source filtering, dedupe, and sensitive-data screening.

---

*Grounds: `scripts/factory/run_factory.py` (modular spine + proposer plug-point),
`scripts/factory/daily_thousand_component_seeds.py` (the clone path to retire),
`scripts/factory/capability_lift_gate.py` (orphaned hard-floor gate to wire),
`scripts/processors/{semantic_dedup,lsh_dedup_blocking,draft_quality_gate,draft_manifest_yaml_emitter}.py`,
`scripts/acquisition/{gap_screen,research_queue}.py`, `scripts/eval/{reason_codes,durable_gap_harness}.py`,
`_repos/_shared/codex/master-goal.md`, `docs/concepts/capability-valleys.md`.*
