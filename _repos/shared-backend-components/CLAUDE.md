# CLAUDE.md — `aidoneright-shared-backend-components` agent operating manual

> **AI Done Right** operating manual for this repo. It is the agent operating layer; the laws it
> inherits live in [`../dev-rules-context/standards/`](../dev-rules-context/standards/README.md) and win
> if this file ever disagrees with them. The laws section below is the inherited standard — do not weaken
> it. Ground every claim in this repo's own context (`context/blackbox.md`, `context/edges.md`,
> `EDGES.md`); a cited source wins on disagreement.

## Project

- **Name:** `aidoneright-shared-backend-components`
- **North star (one line):** The **computational substrate for executable capability** — a
  database-backed registry federation of reusable AI-pipeline components + subcomponents (the seven
  primitives), the factory that generates and stages them, the service-plane that serves them, the code
  graph, and the two deterministic-naming planes. Product-neutral infrastructure every product consumes;
  it returns **pointers and shapes, never truth** (`serves_truth = false` at this layer).
- **Role:** the SUBSTRATE the whole portfolio sits on. Exposes: registry, primitives, codegraph,
  eval-harness, storage-tiers, credential-plane. Consumed by aidevobserver, api-endpoint-wrappers,
  baltor, context-injection, openhubforai, scraping, teleon. Products consume it — **never the reverse**.
- **Target vertical(s) — depth before breadth:** `sanctions / OFAC SDN screening` (the first live
  `serves_truth = true` capability), then `healthcare provider-directory` (a healthcare-ADMIN starter
  vertical, NOT insurance). Every new substrate layer must serve the ONE vertical being proven to a
  paying customer; breadth without a proven revenue vertical is the failure mode. 7 of 8 substrate layers
  already exist (`context/blackbox.md` §9), so the move is **reconcile + close-gap, not build-new**.
- **Reference implementation for the standards:** this repo is the primary **enforcer** of both naming
  planes — `scripts/pyprefix.py` (CODE plane) and `src.teleon.experiments.ids` (DATA plane) — plus the
  registry port (`src/teleon/registry/port.py`), the code graph (`scripts/codegraph.py`), and the storage
  tiers (`src/teleon/storage/record_store.py`). Read those as the worked examples.
- **Common truth for all components:** [`../dev-rules-context/`](../dev-rules-context/) — the shared
  standards, contracts, and check tools. Read from there; never re-declare or copy what already lives
  there.

## Active handoff → GPT-5.6 (2026-07-09) — READ FIRST

The current workstream is **executed token-savings experiments** (does the primitive DB actually save tokens on real
coding tasks?). Read **`docs/HANDOFF-GPT-5.6.md`** + **`docs/RESEARCH_PATHS_AND_IDEATION.md`** first. Reconciled state:
single-shot OUTPUT savings marginal; prompt-reuse is PROMPT/MODEL-dependent (`full_source_asis` works, `signatures_only`
makes models re-implement+fail); **deterministic composition** is the only robust 0-token win; realistic sessions are
INPUT-token-dominated; NOT concluded (7-model grid running via `scripts/reuse_experiment_grid.py`, MIN_N=8). Do NOT
re-assert 47.5%/4.7-5.9×/486×/1.17M as proven savings (projection/context-byte/raw-count). Honest ledger:
`docs/REAL_SAVINGS_NUMBERS.md`, `docs/strategy/primitive-system-end-to-end-briefing.md` §4. The two "Current focus"
blocks below (07-07 foundry loop, 07-06 retrieval graph) are EARLIER WAVES — valid infrastructure, not the current lead.

## Current focus (2026-07-07): real-world primitive foundry loop (earlier wave — infra still valid)

The next substrate priority is a working loop that turns real-world software/problem surfaces into reusable
primitive candidates:

`source object -> component breakdown -> rebuild plan -> primitive candidate -> variation candidate -> proof receipt`.

Primary command:

```bash
python3 scripts/source_to_primitive_foundry.py --self-test
python3 scripts/real_world_primitive_loop.py --self-test
python3 scripts/continuous_primitive_scrape_loop.py --self-test
python3 scripts/primitive_deconstruction_plane_pipeline.py --self-test
python3 scripts/real_world_primitive_loop.py --once --repo-root ../.. --file-limit 0 --external-seed-count 1000 --max-components 5 --max-sources-per-partition 50
python3 scripts/continuous_primitive_scrape_loop.py --once --source-limit 100 --question-count 240 --max-components 5 --max-sources-per-partition 25
python3 scripts/primitive_deconstruction_plane_pipeline.py --run --question-count 360 --max-atlas-rows 250 --overlays-per-primitive 4
```

Deterministic JSON hook from repo root:

```bash
python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py --request-json '{"action":"actions.list"}'
python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py --request-json '{"action":"session_benchmarks.run","args":{"sessions":16,"turns_per_session":0,"k":8,"components_per_turn":4,"scenario_mode":"mixed","include_supervised":true,"compare_base":true,"context_window":262144}}'
python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py --request-json '{"action":"session_benchmarks.run","args":{"sessions":8,"turns_per_session":0,"k":8,"components_per_turn":4,"scenario_mode":"ml_lifecycle","include_supervised":true,"compare_base":true,"context_window":262144}}'
python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py --request-json '{"action":"session_benchmarks.run","args":{"sessions":6,"turns_per_session":0,"k":8,"components_per_turn":4,"scenario_mode":"large_org","include_supervised":true,"compare_base":true,"context_window":262144}}'
python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py --request-json '{"action":"twenty_million_cycle.run","args":{"seed_rows":100000,"rows_per_shard":10000,"compile_shards":2,"start_shard":-1,"benchmark_n":300,"benchmark_k":5,"paraphrase":true}}'
```

The Claude slash-command wrapper is root `.claude/commands/loop.md`; the portable command card is
`../dev-rules-context/commands/loop.md`.

What this loop owns:

- inventory repo files by metadata/digest, not raw content dumps;
- add real-world source families: websites, apps, Kaggle notebooks, LeetCode/coding-interview tasks,
  competitive-programming problems, papers, and discussions;
- decompose each source into component families;
- produce candidate rebuild plans that say how to rebuild the source using primitives;
- generate primitive candidates and variation candidates;
- emit `gap_queue.jsonl` from the latest primitive-consumption benchmark so registry misses become source-mining
  targets;
- keep everything generated as `candidate=true` and `serves_truth=false`.

The continuous source-policy loop (`scripts/continuous_primitive_scrape_loop.py`) is the next layer:

- covers news, apps, systems, Kaggle notebooks, Medium/blog articles, system design, textbooks/course material,
  Google Scholar/citation clusters, paper publication pages, repos, discussions, and websites;
- persists governed `source_snapshots.jsonl` rows with handles, digests, source policy, and no raw body storage;
- asks/stores a 200+ question bank per source over languages, runtimes, design systems, architectures, security,
  observability, tests, benchmarks, remix axes, and promotion gates;
- emits `llm_decompositions.jsonl`, `question_answers.jsonl`, `primitive_graphs.jsonl`,
  `primitive_examples.jsonl`, `llm_primitive_candidates.jsonl`, and `primitive_database_feed.jsonl`;
- supports `--watch` for continuous operation and opt-in `--live --use-llm` only after source-policy, credential,
  rate-limit, and license review.

The deconstruction-plane definition pipeline (`scripts/primitive_deconstruction_plane_pipeline.py`) turns candidate
primitives into database-ready fully-defined candidate rows:

- persists the question/deconstruction database under
  `catalog/knowledge-packs/data/primitive-deconstruction-plane-database/`;
- defines deconstruction planes, analysis layers, dimensions, plane-question edges, and a completeness rubric;
- consumes the latest continuous-loop run by default, or runs a fresh continuous pass with `--run-continuous-first`;
- emits `fully_defined_primitive_candidates.jsonl` and `primitive_database_feed.jsonl` under
  `data/dev-intel/primitive_deconstruction_plane_pipeline/`;
- optional model refinement supports Ollama/OpenRouter/direct OpenWebUI and OpenWebUI CDP (`--provider openwebui
  --mode cdp`) while keeping outputs candidate-only.

Latest bounded receipt: 18 planes, 14 layers, 343 dimensions, 955 questions, 175 fully-defined primitive candidate
feed rows, average completeness score 1.0. "Fully defined" means full candidate contract/proofs/examples/bench hooks;
it does not mean promoted truth.

Latest benchmark additions:

- `scripts/run_realistic_session_benchmarks.py` measures full multi-prompt sessions over app, warehouse, agent,
  regulated, platform, ML lifecycle, and Google-scale large-organization buildouts.
- ML lifecycle mode decomposes the production-ML role matrix into product, architecture, data governance, data
  engineering, analytics, science, labeling, ML engineering, MLOps, backend, frontend, infrastructure, SRE, QA,
  security, privacy, responsible AI, support, docs, and program-management surfaces.
- The lifecycle-specialized candidate pack is written to
  `data/dev-intel/primitive_factory/specialized_packs/ml_lifecycle_primitive_cards.jsonl`; it remains
  `candidate=true`, `serves_truth=false`.
- Large-org mode decomposes a Google-scale operating model into corporate, product-area, platform, SRE, security,
  trust, GTM, finance, governance, workflow, and engineering-ladder surfaces.
- The large-org specialized candidate pack is written to
  `data/dev-intel/primitive_factory/specialized_packs/large_org_primitive_cards.jsonl`; it remains
  `candidate=true`, `serves_truth=false`.
- `scripts/run_twenty_million_supervised_cycle.py --start-shard -1` means auto-select the next unused shard window.

This work complements the 2026-07-06 query-understanding graph below. The graph improves retrieval/composition over
the current registry; the real-world primitive loop grows the registry from actual source/problem shapes and feeds
gaps back into the foundry.

## Current focus (2026-07-06): the query-understanding "ZOO OF ZOOS" retrieval graph

The active build is **turning a noisy natural-language dev-task query into the right primitives** — as a
navigable GRAPH where every stage is a zoo of interchangeable options (the multi-path law, law §1, made
literal). Everything below is in `scripts/`, standalone + registered in `flywheel_proof_modules.py`, every
`--self-test` green, all `serves_truth=false`. **Maintain the zoo-of-zoos; expanding a stage = add a row,
never a rewrite.**

**End-to-end flow:** `session_context` (mine stored logs + memory, deterministic, 0-token) → `request_intake`
(canonical brief, infer-first, never blocks an agent) → **the graph** `pipeline_path_graph` (analyze → preprocess
→ expand → secondary → search → fuse → rerank → compose) → retrieval (lexical + real local embedders + fusion) →
primitives. Every step is 0-token by default; the model lanes (Ollama nomic / model2vec / a trained mini-embedder
/ LoRA) are opt-in seams. Benchmark the whole thing with `path_graph_bench` (paths) and `embedder_zoo` (models).
This session's modules (all registered → auto-gated by `run_proofs`): `session_context`, `session_redundancy`,
`request_intake`, `query_expansion_zoo`, `pipeline_path_graph` (extended, + toggle, + compose zoo),
`path_graph_bench`, `graph_flexibility` (enforcement), `graph_autotune` (self-tuning),
`build_primitive_embeddings`, `embedder_zoo`, `capability_embedding` (model2vec path + stored-matrix lane),
`multi_path_coverage_bench` (independent mode), `compose_token_bench` (reuse/reorder/token receipts),
`primitive_enrichment_coverage` (the make-sure gate), `esoteric_query_bench` (12 corruption probes),
`saas_requirements_bench` (verified SaaS coverage; suite = gold-set seed), `path_router_zoo` (per-class
routing), `workload_token_simulation` (the spend-vs-quality frontier).

- **Measured this wave:** esoteric probes @112K — leetspeak/vowel-drop are the killer corruptions (lexical
  −0.59…−0.63 recall; fusion best on char noise, drop ≤0.13; order/stopword/sms transforms cost ~0) →
  receipt `esoteric_query_receipt.json`. Embedder race now 10 rows: **fastembed BGE-small & MiniLM-L6 =
  nDCG 1.00** (ONNX CPU, tied with ollama_nomic at the set ceiling) > potion-8M 0.86 > multilingual-128M /
  potion-4M / retrieval-32M 0.80 > potion-2M 0.70 > LSA 0.63 > proxy 0.22 — serving fastembed needs a
  `capability_embedding` path row + store rebuild (open). Token frontier (`workload_token_receipt.json`):
  always-LLM 83,450 proxy-tokens/1K queries; difficulty-gate cuts ~31%; results-cache serves the repeat-heavy
  simulated day at 98% hits for 0 tokens, equal nDCG. Router race: per-class `learned_table` ≥ global
  champion (receipt `path_router_race_receipt.json`; table `dist/path-router/learned_table.json`).

- **Every primitive has MULTIPLE persisted surfaces (proven, not asserted):** blackbox embeddings
  (`dist/primitive-embeddings/`) + **3-register description embeddings** plain/technical/semantic
  (`--build-registers` → `dist/primitive-register-embeddings/`, consumed by `intent_query_registers`'
  stored lane = the graph's `semantic_registers` search row; 0.68s warm best-register match at 112K) +
  feature records (operations/datatypes/impact/frame) + blocking keys + edges. Enforced by
  `primitive_enrichment_coverage.py` (registered): EXACT id-set comparison corpus↔stores — all three stores
  at **coverage 1.0 of 112,731** (receipt `enrichment_coverage_receipt.json`); 267 empty-blackbox cards have
  gap repair tickets (`enrichment_gap_records.jsonl`) and retrieve via title fallback meanwhile; RUN mode
  ratchets (coverage may never drop).

- **The graph — `pipeline_path_graph.py`:** 8 ordered stages, each a zoo → **36 options, 76,800 runnable
  paths** (as of 2026-07-06 — the live shape is `graph_summary()`, computed; never trust prose literals over
  it). Stages: `analyze · preprocess · expand · secondary(LLM) · search · fuse · rerank · compose`.
  `run_path(query, cards, path, *, llm=, index=, cache=)` runs ONE path (0-token by default; `cache` memoizes
  expand+search so enumerating the whole graph runs each unique retrieval once); `enumerate_paths(kinds=)`
  yields the graph, kind-filterable (deterministic/heuristic/nlp/frontier_llm/local_llm); `apply_stage()` is
  the single-source stage executor; `graph_summary()` computes the shape (all counts computed, never typed).
- **The compose zoo (the "answer a prompt by piecing primitives together, 0-token" stage):** `wiring`
  (clause-text join, the baseline) · `edge_chain` (exact max-typed-joins REORDER of the fused pieces via
  `primitive_runtime.canonicalize_edge`; danglers ride along, never dropped) · `edge_chain_tokens` (soft:
  shared significant TYPE TOKENS, scored token-first/exact-second so generic tokens can't scramble an
  exact-chainable set — the measured 12× reach unlock for hyper-specific edge names; labelled
  type_token_proxy, an UPPER bound) · `route_compose` (the REAL contract-locked composer
  `primitive_runtime.compose_route` → `groups.compile_exact_edge_route`, endpoints inferred as the piece
  set's source/sink types; emits only edge-VALID routes) · `skip`. Raced by `compose_token_bench.py`:
  REUSE (pieces wired) / REORDER (gold step order + typed-join rate) / TOKENS (0 llm calls end-to-end;
  proxy-token bill: naive card-body reading vs signatures-only vs deterministic 0; + a full-corpus
  end-to-end probe on the stored lane). **Measured at 112K:** exact joins across independently-minted
  cards = 0 (edges like `FederalJobOpportunityBatch` never equal each other; the strict composer honestly
  refuses) — the type-token row and the canonical edge vocabulary are the chainability levers. Receipt:
  `data/dev-intel/session_emulation/compose_token_receipt.json`.
- **The zoos wired into `search`/`expand`/`fuse`:** `robust_query_grains.py` (6 noise grains),
  `hierarchical_semantic_embeddings.py` (4 roles × 4 grains — re-embeds per query today; precompute its keys
  like the dense index), `query_decomposer.py`, `query_preprocess_zoo.py` (HyDE), `query_expansion_zoo.py`
  (PRF/RM3 + Rocchio + facet + neighbor-grain — the 0-token "before retrieve" segment), `rank_fusion_zoo.py`
  (RRF/CombSUM/**CombMNZ**/Borda/max_union). `understand_query.py` is the front-door orchestrator — **not yet
  wired to serving** (target: `primitive_runtime`/`capability_retrieval_mcp_server`/`intent_query`).
- **Structured intake (front-most layer) — `request_intake.py`:** normalize a raw user/agent prompt into a
  canonical REQUEST BRIEF (goal · input · output · integrations · platform · technologies · constraints), each
  field filled by a zoo of extractors (facet / lexicon / pattern / constraint-strip / embed-nearest /
  small-model|LoRA seam), deterministic-first + 0-token, **INFER-FIRST**: gaps are ASSUMED from session/agent
  context + local-first defaults (agents are NOT stopped to ask — clarifying questions are a rare, advisory,
  non-blocking fallback for essential unknowable fields like the goal; `intake` returns `ready`/`blocking:false`),
  and resolved fields become a normalized query. Feeds the graph's `analyze`/`preprocess`. Seed lexicons
  (platform/tech/integration) are extensible → promote to `vocabularies/` as they grow.
- **Session-context mining (feeds intake) — `session_context.py`:** builds that `context` DETERMINISTICALLY,
  0-token, from what's already on disk — tails the stored Claude Code transcripts
  (`~/.claude/projects/<project>/*.jsonl`, BYTE-BOUNDED so a 160MB log costs the same as 1KB) + the memory bank,
  and extracts platform/tech/integrations/entities/goals via the shared lexicons/facets.
  `intake_from_session(prompt)` = mine → intake, so a terse follow-up carries the whole session forward with no
  LLM call and no question. (Verified on this repo: mines python/fastapi/react/postgres/bigquery/aws/gcp/…)
- **AIDevObserver redundancy demo — `session_redundancy.py`:** processes a GROUP of stored coding-session
  transcripts and finds redundant behavior DETERMINISTICALLY (0-token) — duplicate commands, repeated
  reads/edits, redundant searches, cross-session repeats, and a redundancy rate — from a byte-bounded tail so
  huge logs are cheap. `--demo` reports over this project's sessions (measured ~27% redundancy on 4 recent
  sessions). The reuse thesis applied to AI usage.
- **Local embedders (REAL, working) — `capability_embedding.embed_text(path=…)`:** `tokens` (crc32 proxy,
  keyless default), `ollama` (nomic-embed-text via local Ollama, running), `model2vec` (in-process static
  embeddings — `pip install model2vec`, `minishlab/potion-base-8M`, dim 256). `real_text_path()` resolves the
  best available (model2vec > ollama > tokens); the graph's semantic search uses it. **model2vec batch-encodes
  all 112K cards in ~2.3s** — persisting embeddings is nearly free.
- **Benchmark — `path_graph_bench.py`** (the honest re-do of the flawed 0.761 coverage number; retrieval is
  INDEPENDENT per path, NOT a rescored lexical pool): `--self-test` runs ALL 26,880 paths (0 errors) + quality
  race + scale probe · `--runnable --sample N` proves every path runs on real cards (~1.5ms/path) ·
  `--bench --sample N --k K` races expand×search×fuse×rerank on a labelled family set (recall@k/MRR/nDCG) ·
  `--scale --query-sample N` benchmarks the SCALABLE retrievers over the full **112,731-primitive** corpus.
- **Measured findings (reproducible receipts under `data/dev-intel/session_emulation/`):** vocabulary is NOT
  the only tool — a real local embedder beats lexical on paraphrase (**nDCG 0.86 vs 0.60**) and is highly
  complementary at scale (**lexical/dense top-5 overlap 0.13**); **CombMNZ** wins the fuse stage; the naive
  full-union can score *below* the best single path, so the win is **racing + picking (or learned selection),
  not always-union**; dense wins under noise, fusion is most robust. grains/hierarchical recompute their keys
  per query today — precompute them like the dense index to make those paths fast.
- **Open threads (next):** ✅ embeddings+features are now persisted for all primitives
  (`build_primitive_embeddings.py`, ~2.3s/112K → `dist/primitive-embeddings/`); ✅ those stored vectors are now
  WIRED into `intent_query`/the graph's semantic search (the STORED-MATRIX lane below — 91× faster at 112K,
  identical top-10; receipt `data/dev-intel/session_emulation/intent_query_stored_receipt.json`); ✅
  `multi_path_coverage_bench.py` is FIXED — retrieval is now INDEPENDENT per path over the full corpus by
  default (semantic via the stored lane; the old pool-rescore is a labelled `--mode rescore` fallback; the
  self-test proves the cap: a zero-token-overlap card is unreachable in rescore mode, recovered in
  independent mode). Next: precompute the grains/hierarchical keys the same way (a technical-register store
  also unblocks that path's independent mode); wire `understand_query` into serving; grow the labelled gold
  set. Full IR/NLP roadmap: `data/dev-intel/adversarial_findings/ir-nlp-best-practices-2026-07-06.json`.

### Corpus & storage reality (audited 2026-07-06 — read before "we should have more primitives")

- **Searchable corpus = 112,731 distinct cards** = `verified_factory_primitive_cards.jsonl` (34,289, `prim:vf:*`) +
  `primitive_edge_cards.jsonl` (78,442, `prim:*`), **verified disjoint** (0 id overlap), both under
  `data/dev-intel/aidevobserver_edge_foundry/`. The persisted lexical index is **130,385 docs**
  (`catalog/knowledge-packs/data/primitive-search-index/`, manifest `n_docs=130385`) — the extra ~17,654 are
  producer/thin docs written into `search_docs.jsonl` but NOT the card files.
- **The repo actually holds ≈1.17M primitive-bearing records** across disjoint namespaces; only ~9.7% is
  searchable. The "missing" mass is **1,000,000 synthetic `primitive_codeblocks/`** (compiled seed corpus,
  `prim_seed_primitive_*`, candidate/never-indexed) + **37,634 `primitive_drafts.jsonl`** (`prim:candidate:*`,
  needs source evidence) + **15,111 `template_minted_producer_cards_v2.jsonl`** (gap-fill, `codefactory-*`).
  Scorecards (30K) and linkable_cards (24K) are DERIVED views of `prim:vf:*` (0 new); batch_runs/model_outputs
  are process artifacts. **Governed/source-backed figure ≈ 112K searchable (+15K gap-fill ≈ 128K); the jump to
  1.17M is entirely the synthetic seed corpus, un-promoted.** Funnel drops: dedupe-collapse 6,584 + gate-reject
  1,630 at the candidate stage; the 1M seed + 37K drafts never enter the funnel.
- **Storage today:** primitive cards live in **JSONL**. The lexical inverted index is persisted (real,
  df-capped, O(candidates), 120MB on disk). Embeddings are PERSISTED (`dist/primitive-embeddings/`) and
  `intent_query` reads the stored matrix via its STORED-MATRIX lane (superseded 2026-07-06: it used to
  re-embed the corpus per call; the recompute lane is preserved as the labelled fallback). The
  `object_embedding` pgvector table exists
  (`db/postgres/schema.sql:558`) but its **HNSW index is commented out (:573) and never populated for
  primitives**; no faiss/hnswlib anywhere. `blocking_keys` on cards = precomputed SEARCH tokens (NOT dedupe
  blocking — that's MinHash-LSH in `primitive_retrieval_bakeoff.py`/`cluster_primitive_duplicates.py`).
- **Closed this session:** `scripts/build_primitive_embeddings.py --build` persists model2vec embeddings +
  feature records for all 112K to `dist/primitive-embeddings/` (gitignored, ~2.3s rebuild); `load`+`search`
  read the STORED matrix (no recompute) — the local precursor to a real ANN index. **And the store is now
  load-bearing:** `capability_embedding.intent_query(store="auto")` serves the STORED-MATRIX lane whenever the
  persisted store matches the requested embed space (one matmul + id lookup, delta-embed for out-of-store
  cards, `vector_source` labelled per hit; geometry never silently swapped — a `tokens` caller like
  `primitive_runtime` keeps the recompute lane bit-for-bit). Measured at 112,731 cards: **0.207s warm vs 18.9s
  recompute (91×), top-10 identical**. The graph's `semantic_embedding` search option engages it via
  `real_text_path()`; the single embed surface is `capability_embedding.card_embed_text` (blackbox-or-title,
  shared by the store build, the bench dense index, and the delta lane).
- **Drop-in infra swaps for when we scale up (each already stubbed here — the local→cloud swap is config-only
  via `architecture/storage_tier_policy.json`; build locally now, these slot in behind the same calls):**
  ① populate `object_embedding` for `subject_type='primitive'` + a `VECTOR_INDEX_PROFILES` entry;
  ② enable the pgvector HNSW index (or faiss/hnswlib) for sub-linear semantic search; ③ Postgres GIN-FTS / ES
  BM25 for the lexical index; ④ wire the bakeoff's MinHash-LSH blocking into serve-time candidate generation;
  ⑤ add a learned-sparse (SPLADE) field + make the real static embedder the persisted default.

### Model zoo & training (the embedder is a PORT → a zoo; research + add many more, and train our own)

The model port is a zoo like the retrieval paths — `scripts/embedder_zoo.py` races embedder backends by receipt;
adding any model is one `EMBEDDER_BACKENDS` row + a re-run. **Current leaderboard** (220 cards, paraphrased
queries, nDCG@5, all LOCAL): `ollama_nomic` (768d) **1.00** > `model2vec_potion_8m` (256d) **0.86** >
`model2vec_retrieval_32m` (512d) **0.80** > `lsa_local_trained` (our own from-scratch, 64d) **0.63** >
`proxy_crc32` **0.22**.

- **Research + add the thousands of models out there** (each a new backend row): dense bi-encoders
  (sentence-transformers **BGE / GTE / E5 / mxbai / jina / arctic / nomic**, via `sentence-transformers` or
  `fastembed` ONNX — CPU-local); more static model2vec/potion variants; cross-encoder **rerankers** (MiniLM /
  MonoT5); text **mini-LLM routers**. Race them; keep the receipt.
- **Train our own (the lane is open and proven):** `lsa_local_trained` (TF-IDF + truncated SVD from scratch on
  our corpus, numpy-only) already races at 0.63 — extend to word2vec/GloVe/PMI-SVD; **distill** a static
  embedder from any teacher (`model2vec.distill`) for our own vocabulary; **fine-tune / contrastive-train** on
  (query→used-primitive) pairs once the online-feedback loop lands (ir-nlp roadmap #1/#7/#8); train a **router**
  (which path/model per query-class — a contextual bandit over the graph, since the benchmark shows always-union
  loses). Everything benchmarks through `embedder_zoo.race_embedders` and `path_graph_bench`.

### EXTENSION POINTS — where a NEW method plugs in (one row each; never a rewrite)

Every decision point is a zoo behind a selector. To add a future method, find its seam here — each is a single
row + the §3 re-race, and `graph_flexibility` enforces that the graph seams stay open:

| To add a… | The seam (one row) |
|---|---|
| retrieval path / stage option | `pipeline_path_graph.STAGE_OPTIONS[stage][name]` (new stage → `STAGES` too) |
| embedding model | `embedder_zoo.EMBEDDER_BACKENDS` row — kinds: proxy · trained_from_scratch · static_pretrained (model2vec) · onnx_local (fastembed) · api_local (Ollama); race with `--race` |
| fusion method | `rank_fusion_zoo` row |
| compose strategy | compose-stage row (`edge_chain`/`edge_chain_tokens`/`route_compose` are the worked examples) |
| router methodology | `path_router_zoo.ROUTERS` row (query → config; bandit/learned models plug in here) |
| token-spend policy | `workload_token_simulation.POLICIES` row (budget caps, tiered model lanes, per-tenant) |
| corruption/robustness probe | `esoteric_query_bench.PROBES` row (pure, hash-seeded) |
| SaaS/gold benchmark query | a data row in `saas_requirements_suite.jsonl` (no code change) |
| persisted per-primitive surface | `build_primitive_embeddings` build/persist/load trio + a `primitive_enrichment_coverage` check (the register store is the worked example) |
| benchmark | a module with a real `--self-test`, registered in `flywheel_proof_modules.py` |

### Flexibility & self-tuning (ENFORCED — the graph stays maximally malleable, proven not asserted)

Everything is a row you add or toggle; there is **no rewrite**, and this is a **gated conformance test**, not a
promise:
- **Add an option:** `STAGE_OPTIONS[stage][name] = {"fn": fn(ctx,llm)->ctx, "kind": ...}` → `graph_summary` +
  `enumerate_paths` adapt (counts are computed from `STAGE_OPTIONS`, never a literal).
- **Insert a NEW stage BETWEEN existing ones:** add it to `STAGES` (any position) + `STAGE_OPTIONS[newstage]`.
  `run_path` runs it in order; a path routes *around* it if it has a `none`/`skip` option. Pick-one mandatory
  stages (`preprocess`/`search`/`fuse`) are declared in `graph_flexibility.MANDATORY_STAGES`. `path_graph_bench`
  auto-covers a new stage (fixed to a neutral default via computed `_fixed_prefix()`); add it to `_RANKING_STAGES`
  only to have it *raced*.
- **Turn things on/off:** `pipeline_path_graph.set_enabled(stage, option, bool)` — a disabled option drops from
  enumeration + the path count; re-enable restores it. No deletion.
- **Add a primitive:** append the card to the searchable JSONL (or pass any card list) → `build_index` +
  `build_primitive_embeddings` ingest it; the graph retrieves over whatever cards you pass.
- **Self-tune:** `graph_autotune.autotune(cards, labelled)` races the ranking configs, persists the champion as
  `active_config()` (receipt-backed), and **self-heals** to a safe fallback if an option is later removed. Re-run
  to re-adapt.
- **ENFORCEMENT — `graph_flexibility.py`** (in `run_proofs`): mutates a **sandbox** of the live graph the way a
  real edit would and asserts *all of the above still hold* — add-option, insert-stage-mid-pipeline, toggle,
  computed counts, contract-substitutable `fn(ctx,llm)->ctx` options, and routability — then restores the graph
  untouched. It goes **RED the moment flexibility regresses**. Run it after any graph change.

## Read first

1. [`../dev-rules-context/standards/README.md`](../dev-rules-context/standards/README.md) — the laws
   index, in order (the two headline laws first).
2. This file — the operating layer.
3. This repo's own context: [`context/blackbox.md`](context/blackbox.md) (what the substrate owns —
   the seven primitives, the registry federation, the factory, storage tiers, the service-plane, the
   code graph, the naming planes, current live/partial status), [`context/edges.md`](context/edges.md)
   and [`EDGES.md`](EDGES.md) (who consumes you, what you may consume, the forbidden edges, the seam
   table, the compatibility contracts to preserve).
4. **Competitive & research landscape:**
   [`docs/strategy/compiled-primitives-research-landscape.md`](docs/strategy/compiled-primitives-research-landscape.md)
   — the six 2026 works that validate the compile-time-LLM / deterministic-runtime / reuse-curated-skills
   thesis (Compiled AI · SkillsBench · SkVM · Agent Primitives · SkillMigrator · Harbor), why **none of
   them ship a primitive registry** (that is our layer), the competitor read on **XY.AI/CompiledAI** (a
   benchmark harness + vertical healthcare-RCM app, not a library), and the **five practices to adopt**
   (a security gate on generated code · the 7-metric benchmark taxonomy incl. break-even N* · SLSA-style
   provenance · OpenTelemetry · a 5-stage promotion lifecycle). Read before benchmark, security, or
   "50M primitives" work; methodology is **audit → schema → generate → benchmark**, never generate before
   the gate exists.

## The inherited laws (do not weaken; each links its full standard)

### 1. Non-commitment / multi-path is the default — [MULTI-PATH-DEVELOPMENT](../dev-rules-context/standards/MULTI-PATH-DEVELOPMENT.md)
Never hardwire one strategy where several are viable. A design choice is a **portfolio of
contract-substitutable paths behind one selector**, not an `if`. The current behavior is *one selectable
path* (`ACTIVE_DEFAULT`) that reproduces today exactly — adopting the portfolio replaces nothing. Adding a
strategy is a new row + a resolver entry, never a rewrite. Race every path on the **same input** via a fair
comparator, rank by **measured receipts** (cost + accuracy + budget), keep the losers as labelled
fallbacks, and re-benchmark to re-adapt. A candidate is **never** served as truth by the race.

### 2. Globally-unique naming — [GLOBALLY-UNIQUE-NAMING](../dev-rules-context/standards/GLOBALLY-UNIQUE-NAMING.md)
Code here is read by AI first. Every defined thing gets a **globally-unique, location-derived,
meaning-bearing** name so the name alone resolves it with zero ambiguity — long names are good (context the
model uses). Two planes, one law: **code objects** follow the `py_<kind>__<file>__<scope>__<name>` scheme;
**generated data ids** are minted only through the one `canonical_id(prefix, *parts)` authority over
canonical bytes. **Version lives in `schema_version` metadata — never in a name or id** (no `.vN`, no
`@N`). New / generated code follows the scheme from the first draft. User-facing names are full words, no
abbreviations, and records name their `input_edge` / `output_edge` so agents compose by reading names +
edges, not bodies.

### 3. Candidate / truth boundary — [CANDIDATE-TRUTH-BOUNDARY](../dev-rules-context/standards/CANDIDATE-TRUTH-BOUNDARY.md)
Every generated row is **born `candidate = true, serves_truth = false`**. Generation is not promotion.
Keep generated / staged / load-ready / promotion-ready / committed / search-ready as **distinct counts** —
never report raw generated lines as active components. A row becomes served truth only after **source
review + an executed passing proof + the gates**. Nothing promotes itself; no demo, model, or agent flips
the bit by assertion.

### 4. Change verification — a warrant before every change — [CHANGE-VERIFICATION](../dev-rules-context/standards/CHANGE-VERIFICATION.md)
Every change carries a **warrant**, cited in the commit and ledger, in one of three forms:
`warrant: user-intent — "<quote>"` · `warrant: corroboration — <≥2 independent sources>` ·
`warrant: principle — <which>`. Match it to the blast radius: **design / brand / strategy / vocabulary /
pricing / product-structure is NEVER a unilateral single-agent call** — it needs clear user intent or
strong corroboration. "It's green" is necessary, not sufficient. Supersede stale artifacts in the **same**
change; re-verify any doc/memory before relying on it; a different agent verifies than builds.

### 5. Verify the verifier — [VERIFY-THE-VERIFIER](../dev-rules-context/standards/VERIFY-THE-VERIFIER.md)
A green suite that cannot go red proves nothing. Every verifier ships (a) a **mutation gate** — a real
injected defect makes it go red (a pure `--self-test`); (b) a **determinism gate** — the artifact builds
**byte-identical** twice; (c) a **quality ratchet** — each headline metric is a **floor computed from a
manifest** (never hand-typed), a regression below it is a hard failure, and an unsupplied external metric
is a gap record, not a fabricated pass. Never seed a reproducible harness with `hash()`; run edit/restore
harnesses under `PYTHONDONTWRITEBYTECODE=1`. Wire every `--self-test` into one `run_proofs` umbrella.

### 6. No magic values — single source of truth — [NO-MAGIC-VALUES](../dev-rules-context/standards/NO-MAGIC-VALUES.md)
Never hand-type a value used in more than one place; at scale a value typed twice is a value that drifts.
Repo-state numbers (counts, totals, versions, build dates) are **computed from the source of truth**, never
typed into prose. One definition, many readers; build strings from the constant
(`f"vector({DEFAULT_SCHEMA_DIMENSIONS})"`), never a parallel literal. Canonical lists live in
`vocabularies/` / `schemas/`, not re-enumerated in code. Where a value must be mirrored, add a CI check
that recomputes both sides and fails on drift.

### 7. Lossless distillation — distillation is never replacement — [LOSSLESS-DISTILLATION](../dev-rules-context/standards/LOSSLESS-DISTILLATION.md)
Any distillation, decomposition, compression, optimization, reconciliation, promotion, or
LLM-to-deterministic-rule conversion creates a new **versioned** derived layer while **preserving** the raw
layer, intermediates, lineage, source handles, held-out items, rejected candidates, model/tool traces,
configs, and a rollback target. Omitted ≠ deleted; held-out ≠ forgotten; rejected ≠ erased; superseded ≠
deleted. Run side-by-side before promotion, shadow new rules, and prove rehydration. Tenant-private lineage
never becomes global.

### 8. Archival — move, never delete; never untrack — [ARCHIVAL-MOVE-NEVER-DELETE](../dev-rules-context/standards/ARCHIVAL-MOVE-NEVER-DELETE.md)
Outdated context is **moved, not deleted, and not untracked** — relocated under
`archive/legacy/<original-path>`, kept in git for lineage, with a **mandatory status label** recorded in
the manifest and status index. Archived files leave the model context but stay on disk. Restore is a
`git mv`. Never mislabel live or generated data as "legacy."

## Default fast path

- Change one thing; validate and index **only the changed paths**; run the umbrella `run_proofs`; do not
  start with a full rebuild. The normal substrate loop is `validate.py <paths>` →
  `build_component_id_index.py --update <paths>` → `build_catalog_pages.py --paths <paths> --update-index`
  → `validate.py --global-ref-check` → `build_component_id_index.py --check-fresh`. Full release gates
  only on schema / vocabulary / broad-ref changes. If a full rebuild is slow, capture the bottleneck and
  improve the incremental path — do not keep repeating the slow one.
- **Reuse-first.** Before building any component, server, engine, or "new" layer, check it does not already
  exist — run the reinvention guard (`src/teleon/registry/reinvention_guard.py`), the substrate map check
  (`scripts/check_substrate_layers.py`), and `scripts/codegraph.py --audit`. *"This already exists, don't
  rebuild it"* is the highest-ROI decision here — and the naming law (§2) exists so that check resolves
  exactly.
- **Audit neighbors before and after a code change.** Before and after editing a `.py`
  file/function/class/method, run `PYTHONPATH=. python3 scripts/codegraph.py --audit <target>` to rank the
  strong connections (importers/callers by call-sites × resolution-confidence) and update load-bearing
  neighbors in the **same** change — a green suite says the code runs; the dependency graph says what else
  the change can break.

## Adding work

- **A new decision point** = a portfolio (§1), not an `if`.
- **A new registry / source catalog** = a `CATALOGS` entry on `src/teleon/registry/port.py` keyed by its
  `architecture/registry_ontology.json` id, reachable through the uniform `list / lookup / search / explain`
  verbs — never a bespoke accessor. Preserve the port verbs and `serves_truth = false` (`EDGES.md` §6).
- **A new generated id** = one call to `src.teleon.experiments.ids` (`canonical_id`, §2), stamped
  `candidate = true, serves_truth = false` (§3); version in `schema_version` metadata, never a name. A new
  direct `import hashlib` in `src/**` fails the gate.
- **A factory batch** preserves the required row families (`source_record`, `normalized_object`,
  `canonical_entity`, `object_entity_ref`, `dedupe_cluster`, `label_assignment`, `dimension_value`,
  `object_embedding`, `index_record`, + `review_ticket` on risk) and reports the six stages separately.
  Staged → core promotion needs a permissive/vendorable license or a service/technique tag, a real source
  URL, dedupe-clean, and a vetting pass; the descent reads only the promoted core.
- **A new frontend↔backend integration** = a service-plane service + a same-origin seam + `fetch('/api/<x>/...')`,
  never a hardcoded host and never a static stub over a rich app. Frontends address the substrate only
  through the `/registry/...` seam (`local_openhubforai_projection_api`, port 9423 locally,
  `OH_SEAM_REGISTRY_BASE` in the cloud).
- **Consume a neighbor only via its exposed interface** (`EDGES.md`) — never read or import its source.
  You may consume `dev-rules-context`. You must **never** `import src.baltor.*` or otherwise depend on
  teleon/baltor as products — the substrate is product-neutral; products consume it, not the reverse
  (enforced by `scripts/check_portfolio_dependency_law.py` + `check_import_boundaries_manifest.py`).

## Safety and scope

- **No real PII, secrets, confidential data, or proprietary dumps.** Synthetic or public metadata only.
  Never commit keys. Do not republish `_reference/`.
- **Sensitive domains** get review queues, verified facts, signed publishers, redaction, provenance, and
  deterministic gates — not "just ask the model."
- **Insurance** — do not build new insurance-related pipelines and do not expand any legacy insurance
  examples. Target claims-SHAPE adjacent verticals instead.

## When stuck

If one path is blocked, switch paths — do not stop. Generate showcase pipelines, add promotion/readiness
tooling, improve load audits, add source-surface seeds, add repair planners for missing row families, or
add documentation that prevents a repeated slow or wrong path. Do not stop because one scraper, API,
provider, or full rebuild is slow. Every serious turn improves at least one durable thing.
