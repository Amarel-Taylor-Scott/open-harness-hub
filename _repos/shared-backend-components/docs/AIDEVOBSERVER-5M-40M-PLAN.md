# AIDevObserver — the proof layer for a 5M‑minimum / 40M‑scale primitive substrate

> Owner directive (2026-07-09). **North-star claim:** *"Given a very large primitive substrate — minimum 5M,
> designed for 40M+ — AI coding agents waste fewer tokens, less time, and behave more consistently when they
> retrieve, compose, and reuse verified capability primitives instead of rebuilding from scratch."* AIDevObserver
> **observes** real AI-dev sessions, **finds** where agents waste context + reimplement existing capability,
> **retrieves** matching primitives, **composes** deterministic portions, lets the model **fill only the gaps**, and
> **produces receipts** proving token savings, time savings, and consistency. `serves_truth=false` until receipts.

## 0. The one discipline: separate SCALE AMBITION from PROOF STATUS

The discipline is **not "be smaller"** — it is **make the 5M/40M claim un-hand-wave-away-able** via **live inventory +
status labels + receipts**. Never type a corpus count by hand (no-magic-values law) — the dashboard COMPUTES every
number live. Show the target AND which subset is proven.

**Status-label ladder (each COMPUTED live):**
```
raw_primitive_records        5M minimum · 40M scale target
candidate_primitives         generated / mined / decomposed
indexed_primitives           in the search/embedding tier
searchable_primitives        retrievable at product latency
composition_ready_primitives typed edges + callable surface
verified_primitives          passed hidden oracle / self-test
promotion_ready_primitives   durable lift over the bare model
customer_proof_primitives    used in A/B savings receipts
```
Also: source_backed vs synthetic, dedupe_clusters, lineage/embedding/edge coverage. This lets us say "operating toward
5M–40M" while proving exactly which subset yields token/time/consistency gains.

## 0b. LIVE inventory (2026-07-09) + Fable's generation/promotion focus

`scripts/primitive_inventory.py` (run it — counts are live, not typed) reports the status ladder RIGHT NOW:

| tier | live count | vs 5M-min |
|---|---|---|
| raw_records | **5,818,155** | **116% — MET** (14.5% toward 40M) |
| candidate | 5,818,155 | — |
| indexed | 4,942,677 | FTS-indexed in `dist/primitives.db` |
| searchable | 130,385 | 2.6% |
| composition_ready | 78,442 | 1.6% |
| **valid_syntax** | **63** | **0.001%** |
| **working** | **63** | **0.001%** |
| verified | 34,352 | 0.7% |
| promotion_ready | **0** | 0% |
| customer_proof | **0** | 0% |

source-backed: **112,794** · synthetic/gap-fill: **9,202,021**.

**Owner's sharpened target (2026-07-09): 5M INDEXED + SEARCHABLE + VALID-SYNTAX + FULLY-WORKING — then test — then
40M.** The 4.8M SQLite records are **capability descriptors** (title + typed `input_edge`/`output_edge`, no code), so
`valid_syntax`/`working` (code that PARSES then RUNS) sits at **63** (verification_level='execution'). Raw is done;
the real 5M gap is **synthesizing + validating WORKING implementations** for the descriptors. Fable's focus:

1. **Family-based deterministic synthesis (the scalable path — NOT 5M per-primitive LLM calls = billions of tokens).**
   Group descriptors by transform family (validator · mapper · formatter · extractor · filter · aggregator ·
   standardizer · …), write a real deterministic template per family that generates code from the typed edges, + a
   fixture oracle. This is exactly how the working PACKS were built (search_rag / string-standardization / scalar /
   automation). Scale one family at a time.
2. **HONESTY GUARDRAIL (no-proxy law):** "working" MUST mean **oracle-passing**, not "a stub that runs." Do NOT inflate
   the `working` count with 5M no-op stubs — that games the metric. The achievable 5M-working is bounded by how many
   families we can template + oracle; that bound is the real number.
3. **Ratchet + measure** every batch with `primitive_inventory.py` (each tier only goes UP; report funnel retention).
   Also grow `searchable` toward 5M by indexing the valid+working ones into the governed search tier.
4. **Then "test and see"** (owner): feed a batch of synthesized working primitives through the reuse/savings
   experiments (Codex's lane) to prove they actually reduce agent tokens/time — the customer_proof tier.

The generation/synthesis loop is Fable's next build; use `generation_focus`/`biggest_bottleneck` to target the lowest
under-min tier (now `valid_syntax`/`working`). Raw minting resumes only if a scan shows raw < 5M.

## 1. Architecture — assume millions from day 1 (not a 100K demo)

**Services (behind same-origin seams `/api/observer/…`, `/registry/…`):** Primitive Registry · Retrieval/Ranking ·
Embedding/ANN · Composition · Experiment/Replay · Session Observer · Economic Ledger · Factory Feedback.

**Storage (the P1 migration in `CLEANUP-BACKLOG.md` + `SYSTEM-OVERVIEW.md` §5 — flat-file/JSONL is the debt):**
- **Postgres (operational):** `component · component_version · primitive_card · primitive_status · primitive_edge ·
  primitive_capability · primitive_lineage · primitive_eval_result · primitive_usage_receipt`.
- **pgvector / ANN:** `object_embedding · primitive_embedding · capability_embedding · task_embedding` (HNSW).
- **Lexical search:** Postgres GIN-FTS or OpenSearch-style BM25 (incremental).
- **Warehouse (history):** `session_event · token_receipt · time_receipt · consistency_receipt ·
  economic_observation · benchmark_result`.
- **Object storage:** raw mined source · full primitive bodies · session logs · replay bundles · oracle artifacts.

## 2. The seven-primitive vocabulary (classification target)
Input · Knowledge Corpus · If Statement · Action · Loop · Stop/End · Output. Every mined/generated/observed candidate
is normalized → deduped → classified into these seven → lineage → embedded → indexed → edge-typed → oracle-tested →
promoted → composed → usage-observed → savings-measured → fed back into the factory.

## 3. Ingestion pipeline (5M → 40M) — grow the corpus, don't just consume it
Sources: existing repo primitives · verified modules · edge cards · gap-fill cards · generated candidates · mined
public workflow ecosystems (n8n/Zapier/… — `automation_directory_forge.py`) · decomposed real SaaS/backend buildouts
(`saas_buildout_decomposer.py`) · **observed agent sessions** · repeated patterns (code/bug-fix/migration/test-harness/
infra/API/seam). Pipeline: `mine|observe|generate → normalize → dedupe → classify(7 families) → lineage → embed →
index → edge-type → self-test/oracle → promote → compose → observe usage → measure savings → feed back`.

## 4. Prove savings across THREE axes (not just tokens)
**Lanes to compare:** `without · prompt:{signatures_only, full_source_asis, usage_example, docstring, negative_guarded}
· compose · edge_gapfill · realistic_session · compact_card_session · large_corpus_retrieval`.
- **TOKENS** (input-dominated — the big lever): input/output/total, `tokens_per_pass`, primitive_hit/reuse_rate,
  reimplementation_rate, composition_coverage, gap_fill_size. Optimize around **full-session input** savings; compact
  cards cut ~87% of input on a 50-turn session (`input_token_lever.py`), NOT single-shot output.
- **TIME:** `wall_clock_seconds · time_to_first_correct_patch · time_to_hidden_oracle_pass · retry_count ·
  failed_generation_count · tool_call_count`. Receipt per task; dashboard shows time saved, retries/loops/tool-calls
  avoided, median/p75 time-to-pass by task family.
- **CONSISTENCY (likely the strongest 5M claim):** variance across **n ≥ 8** repeats — pass-rate/token/time/patch-shape/
  API-shape variance, retrieval + primitive-choice stability. A large substrate makes agents less dependent on
  improvising → lower variance; **deterministic composition = lowest variance on covered portions.**

## 5. Retrieval is make-or-break at scale
Metrics: `precision@5/20 · recall@100 · MRR · primitive_hit_rate · false_positive_rate · candidate_vs_verified_mix ·
latency_p50/p95 · embedding/lexical/edge coverage`. Given a task/session: retrieve top-5/20/100, classify each
usable/irrelevant/duplicate/unsafe/candidate-only, measure whether the winner is in top-k, whether the agent USES it,
whether it prevents reimplementation. **Scale gates —** 5M: no full-scan in prod, ANN indexed, incremental lexical,
dedupe active, p95 under threshold. 40M: sharded/ANN, warehouse analytics, object-storage bodies, **compact-cards by
default (full bodies on demand)**, hot/cold tiers; benchmark latency at 10M/20M/40M.

## 6. The winning context architecture (where the token savings come from)
`large corpus → search/rank → compact capability card → typed edge → deterministic compose where possible → full
source only when necessary → LLM fills the remaining gap`. **Primitive bodies never enter context unless needed.**
Report: full-source context avoided · duplicate rereads avoided · compact cards mounted · prompt-cacheable cards
reused · bodies loaded on demand · deterministic calls substituted · LLM gap size reduced.

## 7. Milestones
1. **5M inventory** — inventory scanner computing the status-ladder counts; `/api/observer/primitive-corpus`; dashboard
   shows "5M min / 40M target" + live counts.
2. **5M retrieval** — load primitives into operational DB/search tier; embeddings; lexical index; edge/type filters;
   benchmark top-k + p50/p95 latency.
3. **Session observer** — import real AI-coding sessions; normalize events; count input/output tokens; detect repeated
   context, file rereads, generated-code↔primitive overlap, reimplementation.
4. **Primitive recommendations** — recommend compact card / full-source-only-when-needed / deterministic compose /
   edge gap-fill / **new primitive candidate when a gap repeats**.
5. **Savings replay** — replay same task across the lanes → hidden oracle → receipts.
6. **Consistency proof** — n ≥ 8 repeats × model zoo; report by model + task family; show variance reduction.
7. **40M readiness** — shard retrieval; hot/cold tiers; object-storage bodies; compact-cards default; scale ANN;
   warehouse analytics; latency benchmark at 10M/20M/40M.

## 8. Customer receipt (the proof artifact)
```json
{ "primitive_corpus_declared_target": 5000000, "primitive_corpus_live_count": "computed",
  "task_family": "webhook-worker", "model": "…", "lane_a": "without", "lane_b": "compact_card_session",
  "n": 8, "oracle": "hidden", "both_pass": true, "input_tokens_saved": 0, "output_tokens_saved": 0,
  "wall_clock_seconds_saved": 0, "consistency_delta": 0, "reimplementation_rate_delta": 0 }
```

## 9. Positioning
"**AIDevObserver is the proof layer for a 5M-minimum, 40M-scale primitive substrate.** It observes real AI development
sessions, finds where agents waste context and reimplement existing capability, retrieves matching primitives from the
corpus, composes deterministic portions, lets the model fill only the gaps, and produces receipts proving token
savings, time savings, and consistency." Push 5M minimum · build for 40M · let the dashboard compute live counts · let
the receipts prove the savings.

*Related: `SYSTEM-OVERVIEW.md` (§5 infra), `HANDOFF-GPT-5.6.md` (experiment spine), `RESEARCH_PATHS_AND_IDEATION.md`
(56 paths), `CLEANUP-BACKLOG.md` (P1 migration), `AGENT-COORDINATION.md` (Codex+Claude lanes).*
