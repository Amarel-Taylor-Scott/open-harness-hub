# Autonomous Session Ledger

Runbook: `docs/codex/autonomous-session-runbook.md`
Goal: `docs/codex/billion-component-goal.md`
Branch: `feat/scale-goals-and-hygiene`
Started: 2026-05-26

## P0 checklist (one-time hygiene, from the 2026-05-26 repo review)

- [x] `.gitignore` added — stop staging `dist/` scratch + `_reference/` clones + OS cruft
- [x] README hand-typed counts → generated + drift-checked stats block (`scripts/build_readme_stats.py`, `--check` for CI). Remaining in-prose counts ("20 patterns", "5 model adapters" [lists 9], "13 emitters" line) still hardcoded — fold into the generator next.
- [~] `scripts/_config.py` created (single source: embedding dim + model registry + canonical paths); flagship `pgvector_embedding_load_plan.py` refactored. Remaining: ~6 more `scripts/db/*.py` with `384` literals + scattered model-ID strings to migrate.
- [ ] finish `manifest`/`primitive` → `component` vocabulary rename in user-facing prose

## Backlog (new component families requested this session)

- **I/O efficiency & format control** — captured in goal doc (cycle 1); seed
  patterns shipped (cycle 2). Still pending: executable processors + a
  logic-pack/tool (e.g. json-envelope validator) and benchmarks for each.
  - [x] `pattern/input-token-compression`
  - [x] `pattern/terse-output-budget`
  - [x] `pattern/strict-output-format-contract`
- Kaggle competition corpus → use-case + `pasted challenge → expected flow`
  builder benchmarks.
- **Trending-repos-as-components + DevOps section** (user request, 2026-05-26):
  seeded cycle 5. Relevance triage of 10 repos done; **CloakBrowser excluded**
  (bot-detection evasion — not operationalized). Remaining: catalog
  academic-research-skills (skill/pipeline), ViMax (video-synthesis),
  12-factor already done; flesh out the DevOps pipeline section with a review
  harness + rubric/benchmark.

## Cycle log

| # | path | change | validation | commit |
|---|------|--------|------------|--------|
| 1 | P0 hygiene | `.gitignore`; billion-component goal, no-magic-values rules, autonomous runbook docs + wiring (CLAUDE/AGENTS/mkdocs/goal prompt) | catalog untouched → still green (full run earlier: all 4,347 valid) | see branch log |
| 2 | I/O efficiency & format control (backlog) | 3 patterns: `input-token-compression`, `terse-output-budget`, `strict-output-format-contract` | validate + global-ref-check green (3/3) | see branch log |
| 3 | no-magic-values P0 | `scripts/_config.py` (single source: embedding dim, model registry, paths) + refactor flagship `pgvector_embedding_load_plan.py` (`pgvector_type()`; killed parallel `vector(384)` literal) | self-test 256/0 rows; message derives `vector(N)`; no stray `384` in file | see branch log |
| 4 | no-magic-values P0 | `scripts/build_readme_stats.py` generates README catalog-stats block (manifests by type, sqlite objects/edges/embeddings=0, emitters); replaced hand-typed "172 / v0.3.0" | generator runs; `--check` fresh (exit 0) | see branch log |
| 5 | trending-repos-as-components + DevOps section | `pattern/twelve-factor-agent`; tools `codegraph-code-graph-query`, `agentmemory-persistent-memory`, `supertonic-tts`; new `catalog/pipelines/devops/` section + `pipeline/codegraph-assisted-code-review` (composes the 2 tools). **CloakBrowser excluded** (bot-detection evasion). | validate 5/5 + global-ref-check on pipeline green | see branch log |
| 6 | FOUNDATION: vectorization working | `scripts/db/build_vector_store.py` — multi-embedding (`object_embedding` keyed by model, multi-dim) + multi-label (`label_assignment` keyed by `assignment_method`: regex live, llm/classifier/human extension points) SQLite store + pure-stdlib cosine KNN search w/ type/label filters. Offline hash embedder (placeholder, blocks promotion); real `all-MiniLM-L6-v2` path when sentence-transformers present. Output gitignored (`dist/vector-store/`). | self-test green: 2 models coexist, regex labels, filtered KNN works | see branch log |

## Foundation status (vectorization)
- env has **no numpy/sentence-transformers/torch** → real-model vectors need a (heavy) install or hosted route; offline default is the deterministic hash embedder (**placeholder, non-promotable**).
- Canonical schema already supports multi-type: `object_embedding(embedding_model)` = many vectors/object; `label_assignment(assignment_method, model_route_id, confidence, review_status)` = regex/llm/deterministic/classifier/human labels with provenance. Gap: pgvector single `vector(384)` column = one dim; the local store stores dim-per-row (multi-dim). Note for hosted: per-model/per-dim embedding tables or a metadata-tagged store.
- To make vectors **real/promotable**: install sentence-transformers (or wire a hosted embedding route via the model registry in `scripts/_config.py`), rerun with `--model all-MiniLM-L6-v2`, then load via `pgvector_embedding_load_plan.py` + `daily_promotion_readiness_plan`.

## Database object reality (queried 2026-05-26, answering "how many objects in the DB")

- **Committed/queryable** (`dist/catalog.sqlite`): **505 objects, 1,024 edges, 0 embeddings** (FTS5 lexical search works; vector search empty).
- **Source catalog (YAML manifests, validated):** 4,350 (512 committed to git, 3,838 machine-generated candidates pending).
- **Generated candidate rows (staged JSONL in `dist/`):** ~1.78M+ lines across row-family files — generated factory output, **not loaded** into any DB.
- **Live Postgres committed rows:** 0 — `db/postgres/schema.sql` is 36-table DDL + load plans only; no running DB.
- **Vector-search-ready embeddings:** 0 (needs `sentence-transformers` + `OH_BUILD_EMBEDDINGS=1`, or the pgvector load path executed).
- **Conclusion:** binding constraint to "build this out" is the *foundation* (stand up store + embeddings + run promotion), not more generation. Corpuses fuel it; the conversational builder consumes it.

## Notes / pre-existing working state (not authored this session)

- Working tree at branch point had 367 modified + ~9,088 untracked files
  (machine-generated `scale*/` candidates, the in-flight `manifest→component`
  rename, in-flight `mkdocs.yml` nav work). These are **left untouched**;
  this session commits only files it authored/edited, by explicit path.
