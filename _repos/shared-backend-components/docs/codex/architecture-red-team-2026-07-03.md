# Architecture Red-Team — Claimed vs Proven (2026-07-03)

A 5-agent adversarial red-team measured the flexible-multi-path primitive architecture
(`docs/codex/flexible-multi-path-primitive-architecture.md`) against the actual code + data. Unanimous verdict:
**the substrate is rich (117,892 primitive rows, dozens of packs, real portfolios) but the RUNTIME is ~5% built.**
Nearly every load-bearing runtime claim is aspirational — AND, encouragingly, the missing machinery mostly EXISTS in
the tree but is UNPLUGGED from the live path. The fixes are largely *integration + gates + a few real
implementations*, not ground-up builds. This doc is the durable scorecard + the unified, flexibly-structured fix plan.

## The scorecard (claim → measured reality → severity)

| Subsystem | Doc claim | Measured reality | Sev |
|---|---|---|---|
| **Search** | 10 paths incl. BM25/dense/hybrid-RRF/graph; blocking keys prune in one hop | ~13.7s **linear token-set-intersection scan** over 115k rows; **2 of 10 paths run**; real matcher `primitive_match.assemble_match_plan` + RRF `retrieval.hybrid` **exist but are never imported by the live seam** `registry_search.py` | CRIT |
| **Embeddings** | named multi-profiles stored long-form; rerank by profile | **one 64-dim lexical-hash** vector per primitive; **4 disjoint dims** (64/256/384/768) that never meet; cosine **silently returns 0.0 on mismatch**; `embedding-profile-registry/` **did not exist** (phantom); **no ANN index anywhere**; only reranker is BM25-lite | CRIT |
| **Composition** | edges compose (output type == next input type); a small model strings routes | **2/5 composable, max chain=1 (a shared TOKEN, not a type)**; **<0.1%** of primitives carry a canonical edge type; real edge namespace is **4,409 free-text strings**; the 28-type vocabulary is a **dead pack (0 runtime consumers)** | CRIT |
| **Proof / mutators** | zero-token provable deterministic mutation; "proofed capability at runtime" | **0 of 7.28M rows `serves_truth=true`** (nothing ever proven); the 20 named mutators = **2.7M vocabulary strings, 0 executable impls**; verifier checks **string count**, never runs proofs, and **fabricates** proof entries | CRIT |
| **Storage** | wide uniform columnar record; variation_profile → one row many variants | two heterogeneous sparse schemas unioned; `mutations[]` = **67.6% of storage, re-serialized every query**, searched by no one; blocking keys are **30-50%-selectivity path-debris** (`src`, `scripts`, `gemma4`); `variation_profile` on **0.8%** of rows | HIGH |
| **Peel-back (L1→L7)** | open a doll only when needed | **no escalation engine exists**; every L1..L7 reference is a genome param / scorecard axis / advice string | HIGH |
| **Nesting-doll** | leaf → group → route hierarchy | **198 groups over 112,692 leaves (0.17%)**; group machinery is build-time only | MED |

## The recurring theme (the good news)

Across all five reports the same pattern: **the right component was already written, self-tested green, and left
unplugged.** `primitive_match` (real 4-class fit + adapter plans), `retrieval.hybrid` (real RRF), `groups.py`
`compile_exact_edge_route` (a real typed BFS composer), the blocking `blocking_index()` — all exist; the live seam
`registry_search.py` reimplements a weaker lexical version and ignores them. So the highest-ROI work is
**integration, not invention.**

## What was IMPLEMENTED in response (2026-07-03, flexibly — every fix is a portfolio, not a lock-in)

- **Retrieval backend portfolio + resolver** (`scripts/build_retrieval_backend_portfolio.py`, registered): a single
  source of truth for embedders (7) / indexes (5, incl. the planned pgvector-HNSW fix target) / rerankers (4) /
  search-methods (6), each with `wired|optional|planned` status, a hard **dim-compatibility rule** (`dim_compatible()`
  replaces silent-zero cosine), and an importable `resolve_active_backends()`. Flexibly resolves the 4-dim mess: one
  wired active default now, any embedder/dim/index/method plugs in as a row — not locked to one.
- **Real executable mutators + proof-runner** (`scripts/mutator_registry.py`, registered): `MUTATOR_REGISTRY` of **11
  real callables that transform DATA** (not flip flags) + `run_primitive_proof()` that executes a leaf primitive's
  proofs against a fixture and promotes `serves_truth` false→true **only on pass**. **2 leaf primitives are now proven
  end-to-end — the first `serves_truth=true` in repo history** — and a wrong one correctly stays candidate (the gate
  is real). New mutators/proof-types are registry entries.
- **Doc honesty banner** (change-verification correction): `docs/codex/flexible-multi-path-primitive-architecture.md`
  now leads with a banner pointing here; the phantom `embedding-profile-registry` citation is superseded by the real
  retrieval-backend-portfolio.

## Unified ranked fix plan (do in this order; each plugs into a portfolio)

1. **[CRIT — composition] Composability gate on generation** (`verify_primitive_candidates.py`): require edges to
   resolve to a canonical `type_id` (auto-map free-text→canonical else flag `edge_untyped`) + a reachability check
   (input/output type must match ≥1 existing primitive's opposite edge, else `route_reachable=false`). *Without this,
   the factory keeps minting uncomposable primitives.* This is the single highest-leverage change.
2. **[CRIT — composition] Retrofit the edge-type vocabulary FROM the corpus**: cluster the 4,409 real edge strings,
   canonicalize to type_ids, backfill `input_edge_type_id`/`output_edge_type_id` onto the 117k rows. Mechanical
   migration; takes canonical coverage 0.1%→majority in one pass.
3. **[CRIT — search] Wire the existing matcher/retriever into the live seam**: route `registry_search` through
   `primitive_match.assemble_match_plan` (fit classes + adapter plans = the real CandidateBundle) and/or
   `retrieval.hybrid` (RRF + reranker). Integration, not build. Closes the two-island problem.
4. **[CRIT — storage] Split `mutations[]` out of the searchable row** (sidecar keyed by primitive_id, hydrate only for
   top-k): 253MB→~82MB searchable, ~13s→~4s, with no other change.
5. **[CRIT — search/storage] Build ONE real index in front of the scan**: a full-corpus inverted blocking index
   (with df-cap + stopword the path-debris tokens) capped to 500 candidates → rerank only those; delete the linear
   scan. Then one dense index (pgvector HNSW over ONE embedder, ONE field) as the portfolio's `dense_ann` path flips
   wired.
6. **[CRIT — proof] Extend the proof-runner across leaf primitives + honest labels**: prove 20 real leaf primitives
   to `serves_truth=true`; rename `verified_factory_primitive_cards.jsonl` → `candidate_...` (Status-accuracy law);
   add a `proofs_unexecuted` blocker cleared only by an executed proof.
7. **[HIGH] Real cross-encoder reranker + global negative-memory**: wire one cross-encoder into the stubbed slot;
   extend outcome-memory suppression to the global corpus keyed by primitive_id.
8. **[HIGH] Peel-back engine or delete the claim**: implement `resolve_at_depth(card, needed)` (L1 edge → L2
   edge_contract → L4 member edges on unresolved compose), measured by the benchmark-lab DEPTH_LADDER.
9. **[MED] A real labeled precision/recall harness** (qrels of query→correct-primitive) so ranking changes are
   falsifiable — today "coverage" is self-graded by the same token-overlap the retriever ranks on.

Everything above is a path in a portfolio the system already has (`step-path-portfolios`, `retrieval-backend-portfolio`):
adding the real index / matcher / reranker / composer is flipping a `planned` backend to `wired` + implementing it —
never a commit to one method. The flexible structure is what makes the fixes safe to land incrementally and swap later.
