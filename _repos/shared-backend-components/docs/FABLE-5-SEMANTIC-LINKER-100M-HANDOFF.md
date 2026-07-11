# PROMPT FOR CLAUDE FABLE 5 — Align the repo to the 100M+ primitive semantic linker (maximal, no limits)

> Paste this whole file to Claude Fable 5 as its operating brief. It is deliberately **maximal**: it enumerates the
> FULL feature/attribute/scorer/model surface and does **not** pre-prune it. The owner's law here is: **generate the
> full surface; let measured benchmarks (not a priori guessing) decide which columns/embeddings/paths are efficient.**
> Do not silently shrink the design. Where scale forces tiering, TIER it (hot/cold/on-demand) — never delete a
> representation; keep it computable and labelled. Target: **100,000,000+ primitives**, growing without bound.

---

## 0. Mission

Make this repo a **fully working, searchable, findable, and efficiently semantically-linking** registry of code
blocks, primitives, and **groups of primitives (recipes/molecules)** at 100M+ scale. An LLM emits a compact capability
plan; a deterministic linker resolves it to verified primitives across a **rich multi-representation index**, composes
them, and only novel residual code is generated. Every capability, every code block, every group must be **retrievable
by many independent paths** and **linkable by many independent scorers**, all **trainable with custom weights**.

The moat is NOT the vector DB (ANN at 100M is solved: DiskANN, SPANN, IVF-PQ). The moat is the **semantic ABI + the
evidence/compatibility graph + the many-representation index + the trainable multi-path linker + the outcome graph**.

## 1. Honest current state (verify each before building; do not trust prose over a live check)

- **Searchable semantic tier:** a streaming facet store `dist/primitive-facet-embeddings/` (memmap `vectors.f32` +
  `vec_pids.u32` + `vec_family.u8`). As of this handoff it was being rebuilt from **112,732 → ~539,890 cards**
  (edge-foundry + 151 new oracle-tested domain primitives [ML/HTTP/validation/collections/text] + 427,007 promoted
  synthesized transforms). **Built with `model2vec` (256-dim) ONLY** — the weakest-but-one local model. THIS IS THE
  #1 SEARCH-QUALITY GAP. `fastembed_bge_small` (384d) and `fastembed_minilm_l6` (384d) score higher (MRR 0.965/0.967
  vs model2vec ~0.86 on hard paraphrase), and `ollama_nomic` (768d) is available. All are LOCAL and installed
  (`primitive_facet_enrichment.available_facet_backends()`).
- **~4.9M** typed capability descriptors are FTS-indexed in `dist/primitives.db` (lexically searchable, typed edges).
  **~5.8M raw** exist (mostly un-promoted seed corpus). Distinct capability output-types today: **25,141** (the corpus
  is BROAD, not one domain — an in-domain OpenAPI plan resolves 100%).
- **Per primitive today:** ~90 facet descriptions (13 families × 3 registers) × **1 embedding model**. Blocking keys
  exist on cards. **NO** wide/slim LSH, **NO** multi-model stored embeddings, **NO** strong-model rerank stage.
- **Linker pipeline (working, self-tested, serves_truth=false):** `semantic_linker_resolve` (plan→verified prims +
  policy/relevance/typed-port blockers) → `semantic_linker_assemble` (dataflow wiring + typed adapters + mountable
  artifact) → `semantic_linker_mcp_server` (7 meta-tools) → `semantic_linker_token_bench` (coverage→savings curve,
  break-even ~40%, 76% at full). Retrieval graph `pipeline_path_graph` (8 stages, zoo per stage). Multi-method scorer
  `linker_scoring_zoo` (15 scorers × 6 trainable paths). ML scaffold `ml_pipeline_zoo`. Minters `mint_vertical_pack` /
  `mint_ml_kaggle_pack`.
- **Verification:** every module carries `--self-test`; the umbrella is `flywheel_proof_modules.py`.

## 2. The MAXIMAL per-primitive representation — target **500+ attributes/columns per primitive** (generate ALL)

Each primitive (and each code block, and each GROUP of primitives) gets the full surface below. None is optional at
generation time; efficiency is decided by measured retrieval lift, then tiered — never by pre-deletion.

### 2A. Descriptions (generate MANY per facet, from MANY models/prompts)
- **42 semantic facets** (the research-bundle set): purpose · user-goal · semantic-transformation · inputs · outputs ·
  inputs+outputs combined · inputs/outputs separated · preconditions · postconditions · invariants · validation ·
  side-effects · permissions · failure-conditions · error-mappings · retry/idempotency · transaction-behavior ·
  concurrency/ordering · streaming/backpressure · performance/memory · security/privacy/compliance ·
  observability/deployment · version/environment · upstream-composition · downstream-composition · alternatives ·
  anti-use · near-miss · positive-examples · counter-examples · bug-symptoms · stack-trace-paraphrases · test-oracles ·
  migration · rationale · limitations · **the problem it solves (multiple framings)** · **the primitive as a whole** ·
  **the primitive in chunks** · domain-terminology · **keyword/keyphrase set**.
- **× 8 linguistic styles:** canonical-catalog · first-person-intent · imperative-developer-request · natural-question ·
  diagnostic-query · domain-synonym-paraphrase · terse-keyword · end-to-end-scenario-narrative.
- **Generated by MULTIPLE models/prompts** (not one): local Ollama/Gemma-4 + several prompt templates + deterministic
  AST/schema summarizers. Every generated description stores: `generator_model`, `generator_version`, `prompt_id`,
  `source_artifact_digest`, `supporting_evidence`, `confidence`, `verification_status`. **Unsupported generated claims
  are excluded from the TRUSTED retrieval tier** (kept, labelled, for the candidate tier). This is 336+ view SLOTS;
  a rich primitive crosses **300+ distinct descriptions**.

### 2B. Embeddings — **5+ models, per description, kept in SEPARATE spaces** (never averaged across models)
- **Model portfolio (all local, all installed or installable):** `model2vec` potion-2m/4m/8m/retrieval-32m/
  multilingual-128m · `fastembed` BGE-small/MiniLM-L6 (ONNX, CPU) · `ollama` nomic-embed-text (768d) · a **from-scratch
  trained** LSA/TF-IDF-SVD (`embedder_zoo.lsa_local_trained`) · a **distilled** static model (`model2vec.distill` from
  any teacher on OUR vocabulary) · a **code-specialized** encoder (CodeBERT/GraphCodeBERT/UniXcoder via fastembed/
  sentence-transformers) · a **learned-sparse** field (SPLADE/uniCOIL) · optional **ColBERT/PLAID** late-interaction on
  the hot/hard-case shortlist. Add models as `embedder_zoo.EMBEDDER_BACKENDS` rows — one row each, raced by receipt.
- **Rule:** each model is its OWN named vector space. Query each independently; fuse RANKINGS with reciprocal-rank
  fusion (RRF); then a learned reranker. **Never average vectors from different models** (different coordinate spaces).
- **Storage tiering at 100M (never delete a representation — tier it):** hot dense (HNSW) over the most-queried
  5–10M; cold dense (DiskANN/SPANN/IVF-PQ, int8/PQ/binary-quantized) over the rest; late-interaction on a premium
  shortlist / on-demand cache; learned-sparse + BM25F lexical over all; **cold/rare descriptions embedded ON PROMOTION
  or ON DEMAND**, not all-hot. Persist the generating model + evidence + verifier result + confidence per vector.

### 2C. Non-vector index columns — generate ALL, per attribute
- **Blocking keys:** exact content hash · normalized-body hash · canonical/alpha-renamed AST hash · callable/API
  signature hash · input/output contract-type hash · per-token blocking keys · **wide LSH** (MinHash over full
  descriptions) + **slim LSH** (MinHash over compact keyword/edge sets) + SimHash/bit-signatures · roaring-bitmap
  attribute bitmaps for hard filters.
- **Tags / labels / triggers:** capability tags · domain/vertical tags · runtime/language/framework tags · trust-tier ·
  license · effect flags · risk flags · **triggers** (query patterns / error-message patterns / stack-trace shapes
  that should surface this primitive).
- **Scalars & metrics per description/edge:** length · token count · datatype families · operation families · impact
  class · **letter/language metrics** (vowel ratio, consonant ratio, char-n-gram profile, per-letter counts, phonetic
  consonant-skeleton, syllable estimate) — both retrieval features AND cheap blocking dimensions.
- **Contracts (the semantic ABI, §3).**

### 2D. The semantic ABI, evidence graph, compatibility system (the moat)
- **Semantic ABI per primitive:** typed ports (nominal + refinement types, units, nullability, cardinality) ·
  sync/async/stream/batch · optional/fallible/partial outputs · idempotency · retry-safety · transaction participation ·
  ordering · cancellation/timeout · data classification/taint · effects (fs/net/db/proc/secret scopes) · resource
  envelope (latency/mem/cpu/gpu) · protocol/state-machine (for OAuth/txn/streaming) · deprecation/migration.
- **Evidence graph:** contract tests · property tests · deterministic-seed tests · behavior fingerprints (from tests +
  execution traces) · provenance (SLSA-style) · signatures (Sigstore-style) · dependency closure · security-scan
  results · historical outcome edges. **A description/claim is search EVIDENCE; only signed artifacts + passing tests +
  policy decide EXECUTION.**
- **Compatibility system + edges:** `identical_to` · `variant_of` · `compatible_with` · `implements_same_contract` ·
  `incompatible_with` · `adapts_to` (via which adapter) · `composes_with` · `consumes/produces` · `verified_with` ·
  **negative memory** (failed routes, context-specific — a primitive can fail for one framework/version/data-shape
  without a global blacklist). Dedup COLLAPSES search results; it NEVER deletes the zoo (two impls with different perf/
  license/deps/effects stay distinct — the append-only implementation zoo).
- **Groups of primitives (recipes/molecules):** a group is a first-class indexed object with its OWN full
  representation (descriptions/embeddings/blockers/contracts) so common subgraphs (authenticate→authorize→validate→
  txn→audit→map-errors) are retrievable + composable as a unit. Recursive promotion compresses whole workflows.

## 3. The MULTI-METHOD LINKING/SCORING surface — ALL methods, trainable, multi-path (already seeded)

`linker_scoring_zoo.py` exists with 15 scorers across 11 families. EXTEND it to the full set; keep every one; make the
mix **trainable per corpus AND per query-class** (a learned router over scorers, e.g. a contextual bandit):
- **Deterministic/exact:** exact title/edge/signature/AST-hash/content-hash match; bitmap/blocker hits.
- **Keyword & frequency:** token Jaccard · token overlap (recall) · idf-weighted overlap · BM25/BM25F · word-frequency
  cosine · keyword-count vectors · learned-sparse (SPLADE) dot.
- **Semantic:** cosine over EACH embedding model's space (queried independently, RRF-fused) · ColBERT late-interaction
  on the shortlist.
- **Fuzzy / edit / character:** SequenceMatcher ratio · token-sort/token-set ratio · Levenshtein (+ Damerau) · Jaro-
  Winkler · char n-gram Jaccard · SimHash Hamming.
- **Phonetic / language / letter metrics:** consonant-skeleton distance · Soundex/Metaphone · vowel/consonant ratio
  similarity · syllable/length ratios · per-letter-count cosine.
- **Structural / NLP:** operation/datatype/impact facet overlap · AST/data-flow similarity · type-fit / refinement-fit ·
  graph-neighborhood overlap · behavior-fingerprint match.
- **Fusion + training:** weighted-mean under named **weight-profile PATHS** (lexical/fuzzy/semantic/structural/letter/
  balanced/…); **custom weights are the trainable knob**; `train_weights` (coordinate ascent → upgrade to logistic /
  gradient / learned-to-rank / bandit) fits weights to labelled (query→used-primitive, and outcome-receipt) data;
  **race the paths and pick per query-class**. Losers stay as labelled fallbacks.

## 4. The 100M+ retrieval/linking funnel (probabilistic retrieval → deterministic acceptance)

```
100,000,000+ primitives + groups
  → family-first ROUTING (tenant/lang/runtime/domain/visibility/kind)         → 0.5M–5M
  → EXACT + LSH (wide+slim) + bitmap BLOCKERS                                 → a few thousand
  → PARALLEL retrievers: BM25F · learned-sparse · dense-per-model · code · graph · behavior-fingerprint
  → RANK FUSION (RRF/CombMNZ) + dedupe-collapse + capability-cluster diversify → 1–3k
  → HARD BLOCKERS (type · refinement · effect · policy · license · trust · resource · version)  → 100–500
  → MULTI-METHOD SCORING (linker_scoring_zoo, trained weights) + STRONG-EMBEDDER RERANK (fastembed/ColBERT/cross-encoder) → 20–100
  → typed, effect-aware GRAPH SOLVE (bounded synthesis over the typed component library)         → 1–20 candidate graphs
  → RESOLVER lock (exact impls + adapters + hashes)                                              → 1–5
  → deterministic ASSEMBLE + VERIFY (compile/contract/property/policy/token-ledger)              → 0 or 1 accepted
```
**Retrieval is probabilistic; ACCEPTANCE is deterministic.** A blocker is invalidation, never a softened rank feature.
Every miss becomes a RESIDUAL (typed hole) → a mint target (never a silent revert to unrestricted generation).

## 5. FIX the embedder gap (the owner's concern) — multi-model store + strong rerank

1. **Add a strong-model RERANK stage** to `pipeline_path_graph` (rerank options today are only mmr/descriptor-sim):
   a `fastembed_minilm`/`bge` (and optional cross-encoder) reranker over the fused top-K shortlist. Cheap model2vec
   RECALL over the millions → strong-model PRECISION on the shortlist. This is the biggest quality win without
   rebuilding 100M vectors, and it's the research-bundle recommendation. WIRE it into `semantic_linker_resolve` so the
   linker resolves off the reranked shortlist.
2. **Build the multi-model store lanes:** persist a SECOND (and third) embedding space over at least the hot/verified
   tier (fastembed BGE + ollama nomic), each its own `dist/primitive-<model>-embeddings/`. Query each independently,
   RRF-fuse. `build_primitive_embeddings` + `primitive_facet_enrichment` already have the model2vec lane — add a
   `--embed-path fastembed_bge_small` lane and a coverage ratchet per model (`primitive_facet_coverage` pattern).
3. **Race + route:** extend `embedder_zoo` / the model×facet race to choose the serving model(s) per query-class by
   receipt; keep model2vec as the cheap first-pass recall model.
4. **Populate every column the design calls for** (§2): run the description generators (multi-model), the LSH
   (wide+slim), the letter/language metrics, the tags/triggers — with a per-column COVERAGE RATCHET so we can PROVE
   completeness (like `primitive_facet_coverage`), and a `--report` that shows, per column, %-populated across the
   corpus. Nothing silently unpopulated.

## 6. Repo alignment — extend these EXACT modules (reuse-first; do not rebuild)

| Concern | Module to extend | What to add |
|---|---|---|
| per-primitive descriptions/embeddings | `primitive_facet_enrichment.py` | 42-facet × 8-style generators; multi-model embed lanes; LSH wide/slim; letter/language metric columns |
| coverage/completeness proof | `primitive_facet_coverage.py` | per-column + per-model coverage ratchet + `--report` (%-populated per attribute) |
| model zoo | `embedder_zoo.py` | add fastembed BGE/MiniLM as SERVING lanes, code encoder, learned-sparse, ColBERT; per-query-class router |
| retrieval graph | `pipeline_path_graph.py` | strong-embedder + cross-encoder RERANK options; learned-sparse + code + graph search rows; RRF multi-model fuse |
| multi-method linking | `linker_scoring_zoo.py` | add BM25F/SPLADE/Jaro-Winkler/Damerau/SimHash/AST-sim/behavior-fingerprint scorers; upgrade train to LTR/bandit; per-query-class router |
| resolve/assemble | `semantic_linker_resolve.py` / `semantic_linker_assemble.py` | resolve off the reranked shortlist; full typed-port + refinement + effect + license + trust blockers; adapter library |
| MCP control plane | `semantic_linker_mcp_server.py` | keep the 7 meta-tools; progressive disclosure L0–L3; token-budgeted search; session alias table |
| minting / corpus growth | `mint_vertical_pack.py` / `mint_ml_kaggle_pack.py` / `promote_synthesized_to_cards.py` | mint the missing verticals; promote the 4.9M FTS descriptors into the typed/searchable/dedup'd tier (tiered, not all-hot) |
| ML/Kaggle | `ml_pipeline_zoo.py` | wire real learners (availability-gated) + the A–F arm harness + TML-Bench/Kaggle-CLI |
| groups/recipes | NEW `primitive_group_index.py` | first-class indexed recipes/molecules with full representation; recursive promotion of repeated subgraphs |
| data plane at scale | `architecture/storage_tier_policy.json` | Postgres (registry/contracts/edges/receipts) · Qdrant (named/multi vectors, hybrid, quantized, sharded) · S3 (bodies) · ClickHouse (telemetry) · Redis (cache); local→cloud config-only |

## 7. Verification + benchmarks (prove it; never assert)

- **Every module ships `--self-test`** wired into `flywheel_proof_modules.py` (mutation + determinism + no-magic gates).
- **PrimitiveLink-Bench (7 arms A–G) + PrimitiveML-Kaggle (arms A–F)**: measure **verified token efficiency** =
  verified_tasks × 1e6 / cache-weighted-tokens; failed runs count ALL tokens, 0 verified. Report per-domain coverage,
  first-graph validity, hard-negative rejection, adapter depth, residual size, post-assembly edit distance, security/
  policy violations, reproducibility, rollback. `semantic_linker_token_bench` computes the structural floor
  (coverage→savings curve, break-even ~40%); the LIVE number needs the executed harness + hidden oracles.
- **Retrieval quality:** precision@k / recall@100 / MRR / nDCG PER model PER facet PER scorer-path; the facet race +
  model×facet race decide what to serve; the per-column coverage ratchet proves completeness.
- **Anti-leakage:** leave-one-competition-out / leave-one-domain-out; never let evaluation-domain solutions into the
  corpus; provenance-gate every minted primitive.

## 8. Operating laws (inherited — do not weaken)

candidate/truth boundary (born `candidate=true, serves_truth=false`; generation ≠ promotion) · no-magic-values
(counts computed, one source of truth) · lossless distillation (never delete a representation/loser/lineage; tier it) ·
multi-path (every decision is a portfolio behind a selector, add-a-row not a rewrite) · verify-the-verifier (mutation +
determinism + quality-ratchet gates) · globally-unique naming · archival move-never-delete · security-as-types
(effects declared + enforced; undeclared effect = reject). Read `_repos/dev-rules-context/standards/`.

## 9. Concrete build sequence (each ends with a green `--self-test` + a committed receipt)

1. **Strong-rerank + multi-model store** (§5.1–5.3) — biggest search-quality win. Wire into resolve. Bench before/after.
2. **Full description/embedding/LSH/metric columns** (§2) + **per-column coverage ratchet + `--report`** (§5.4) —
   prove completeness, tier storage.
3. **Extend `linker_scoring_zoo`** to the full scorer set + LTR/bandit training + per-query-class router (§3).
4. **Groups/recipes index** (`primitive_group_index.py`) — recipes as first-class searchable objects (§2D).
5. **Mint the missing verticals** + promote the 4.9M FTS descriptors into the typed/searchable/dedup'd tier (tiered).
6. **PrimitiveML-Kaggle A–F harness** on `ml_pipeline_zoo` (TML-Bench + post-cutoff S6E7; Kaggle CLI held by the host,
   never the agent; internet-off; hidden holdout).
7. **Data-plane migration** (Postgres/Qdrant/S3/ClickHouse/Redis) — config-only local→cloud; shard at 100M.
8. **Outcome graph + self-tuning** — train ranker/route/scorer weights from receipts; conservative bandit canaries;
   correctness/security remain hard gates.

**Do not shrink this.** Generate the full surface; tier by measured lift; keep every representation computable and
labelled; prove completeness and savings with gated benchmarks; and keep retrieval probabilistic while acceptance
stays deterministic.
