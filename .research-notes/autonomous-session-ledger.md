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

## 2026-05-27 session — capability-lift gate + reconciliation

Driven by a project/business review. Theme: the binding constraint is
**usefulness + foundation + consistency, not throughput**. "Useful" defined
(owner steer) as **capability lift over a bare LLM** — a benchmark delta
(`pipeline − bare model`) > 0 — with the project non-goals promoted to
admission filters. New canonical goal: `docs/codex/master-goal.md`.

| # | path | change | validation |
|---|------|--------|------------|
| 10 | `scripts/validate.py` | fix RED build: `check_refs` no longer resolves `type/slug` strings inside `examples` (false positive on illustrative namespaces like `pipeline/gdpr-review`). | full validate RED→green (rc=0) |
| 11 | `docs/codex/master-goal.md` (new), `docs/codex/index.md`, `docs/about/project.md` | single canonical long-horizon goal (P0 reconcile → P1 foundation → P2 component MVPs → P3 paste-to-flow builder → P4 full MVP → P5 scale); 6 supervisor gates; yield = useful-promoted/day; wired index as canonical; added capability-lift non-goal. Refreshed stale README stats. | `build_readme_stats.py --check` fresh |
| 12 | `scripts/factory/capability_lift_gate.py` (new) | capability-lift + SimHash/LSH novelty gate over manifests. Cull triggers: hard filler markers (scale-expansion / boilerplate / numeric clone / fabricated model), near-duplicate, near-empty lift floor. **Never deletes git-tracked**; referential-integrity reprieve prevents dangling refs. Applied: **culled 1,980 untracked filler** (catalog 4,377→2,397 yaml; 530 tracked untouched). | self-test green; full validate stays green (rc=0); 0 tracked deleted |
| 13 | `docs/strategy/product-market-monetization-brief.md` | expanded: capability-lift positioning, named competitive landscape, GTM wedge (regulated compliance), defended moat, OSS-ecosystem ingestion as a source surface, concrete pricing tiers, risk mitigations, reality anchor to phases. | n/a (doc) |

**P1 embeddings remain blocked in this sandbox:** no `pip`/`numpy`/
`sentence-transformers` and no install path. The route is wired and one command
away (`scripts/_config.py` registry → `python3 -m scripts.db.build_vector_store
build` with sentence-transformers, or a hosted route). Did **not** fake vectors
(promotion boundary). Switched paths per the runbook: shipped the gate +
reconciliation instead. P1 is the next session's first move once deps exist.

### 2026-05-27 (continued) — providers, showcase, verticals, launcher, SWOT

| # | path | change | commit |
|---|------|--------|--------|
| 14 | `scripts/embeddings.py`, `scripts/model_routes.py`, `scripts/serve_builder.py`, `build_vector_store.py` | flexible embedding provider (local-st/http-openai/hash, env-driven, fixes a hash-masquerade bug + stale-row pruning); provider-neutral LLM route (Gemma/Ollama); zero-dep paste-to-flow showcase site; resilient `goal.md`+`direction.md`+`.claude/commands/`. | 17013a2, 214ecf3 |
| 15 | `catalog/{knowledge-packs,tools/api,processors/standardization,rubrics,pipelines/public-data-grounding}/…` | **public-data grounding vertical**: US Census ACS + geocoder + Federal Register API tools, geo-FIPS + tabular-schema standardizers, census-grounded verification pipeline + rubric (+ ACS fact file). | 12ab950 |
| 16 | `catalog/tools/image-safety/…`, `catalog/rubrics/generated-image-safety-quality.yaml`, `catalog/pipelines/image-generation/guarded-image-generation.yaml` | **guarded image-generation vertical**: prompt-safety screen + NudeNet NSFW filter + malformed-anatomy (6-finger) detector + aesthetic/quality scorer + composing pipeline + rubric. Validates green. | (this batch) |
| 17 | `scripts/serve_showcase.sh` | one-command local launcher: server + Gemma (auto-detect Ollama tag) + `trycloudflare.com` quick tunnel, graceful fallbacks. | (this batch) |
| 18 | `docs/strategy/competitive-swot.md` | SWOT + competitor matrix (Zapier/IFTTT/Make/n8n/Vertex/Bedrock/LangChain/Dify/HF) — the unserved capability-lift middle layer; honest "combination-moat only bites once populated". | (this batch) |

Catalog now 2,411 validated (530 curated + candidates). Vector store rebuilt
(still hash placeholder; image queries underperform until P1 real embeddings).

**Backlog queued for `/goal` (do not lose):**
- **Premium pipeline grader/advisor** (user idea): a runnable tool that grades a
  pipeline on best-practice + cost-savings (wiring rules, rules-before-model,
  eval coverage, provenance, vectorization) and emits tips. Pattern exists in
  `capability_lift_gate.py`. Ship as `scripts/grade_pipeline.py` +
  `tool/pipeline-best-practice-grader` (premium) + `rubric/pipeline-best-practices`.
- **Python-library → component standard** (user idea): a convention + reference
  helper so any Python lib exposes callables as OHH tool/processor components.
  See `docs/spec/python-component-standard.md`.
- More capability-lift verticals; real embeddings (P1) to fix semantic retrieval.
- **Deterministic code-edit family** (high priority; the "small models can't do exact-match patch" objection): structured/line-anchored/AST patch-apply as a *deterministic processor*, plus a verify-and-repair harness gate — move edit reliability OUT of the model so a cheap model can drive it. Pairs with the cost-routing principle: orchestration has a coherence floor (capable model or deterministic routing), narrow well-scoped sub-tasks route to small/local models.

## Cycle log

| # | path | change | validation | commit |
|---|------|--------|------------|--------|
| 1 | P0 hygiene | `.gitignore`; billion-component goal, no-magic-values rules, autonomous runbook docs + wiring (CLAUDE/AGENTS/mkdocs/goal prompt) | catalog untouched → still green (full run earlier: all 4,347 valid) | see branch log |
| 2 | I/O efficiency & format control (backlog) | 3 patterns: `input-token-compression`, `terse-output-budget`, `strict-output-format-contract` | validate + global-ref-check green (3/3) | see branch log |
| 3 | no-magic-values P0 | `scripts/_config.py` (single source: embedding dim, model registry, paths) + refactor flagship `pgvector_embedding_load_plan.py` (`pgvector_type()`; killed parallel `vector(384)` literal) | self-test 256/0 rows; message derives `vector(N)`; no stray `384` in file | see branch log |
| 4 | no-magic-values P0 | `scripts/build_readme_stats.py` generates README catalog-stats block (manifests by type, sqlite objects/edges/embeddings=0, emitters); replaced hand-typed "172 / v0.3.0" | generator runs; `--check` fresh (exit 0) | see branch log |
| 5 | trending-repos-as-components + DevOps section | `pattern/twelve-factor-agent`; tools `codegraph-code-graph-query`, `agentmemory-persistent-memory`, `supertonic-tts`; new `catalog/pipelines/devops/` section + `pipeline/codegraph-assisted-code-review` (composes the 2 tools). **CloakBrowser excluded** (bot-detection evasion). | validate 5/5 + global-ref-check on pipeline green | see branch log |
| 6 | FOUNDATION: vectorization working | `scripts/db/build_vector_store.py` — multi-embedding (`object_embedding` keyed by model, multi-dim) + multi-label (`label_assignment` keyed by `assignment_method`: regex live, llm/classifier/human extension points) SQLite store + pure-stdlib cosine KNN search w/ type/label filters. Offline hash embedder (placeholder, blocks promotion); real `all-MiniLM-L6-v2` path when sentence-transformers present. Output gitignored (`dist/vector-store/`). | self-test green: 2 models coexist, regex labels, filtered KNN works | see branch log |
| 7 | PARALLEL SWARM (5 sonnet subagents, concurrent) | backend (4: postgres-pgvector-runtime, redis-queue-worker-runtime, object-embedding-batch-loader, cdc-event-emitter); frontend (3: conversational-pipeline-builder, streaming-result-render, builder-prompt-templates); middleware (4: model-route-gateway, cost-gate-router, response-cache-fragment-reuse, mcp-server-bridge); corpus (`knowledge-pack/nist-ai-rmf-functions` + 89-row JSONL, NIST public domain); hosting doc (`docs/architecture/vectorized-registry-hosting-2026.md`, web-backed, costed 1M→1B tiers) | lead re-validated 12/12 manifests; mtimes prove agents touched no existing file; self-contained (no dangling refs) | see branch log |

| 8 | codegraph-style graph layer | `scripts/db/catalog_graph.py` — context / dependents(callers) / impact(blast-radius) / trace over the existing `edges` adjacency in `catalog.sqlite`. Mirrors codegraph's query ops one level up (components, not code symbols); blast-radius feeds CDC/review. | self-test green: 1,024 edges; hub `processor/audit-trace-emitter` = 91 direct dependents, 118 blast radius; trace path found | see branch log |

### codegraph parallel (why it mirrors us)
- codegraph: nodes=code symbols, edges=calls/imports, SQLite+FTS5, MCP ops (search/context/callers/impact/trace), NO embeddings. We: nodes=components, edges=refs (`harvest_refs`), same SQLite+FTS5 substrate (`catalog.sqlite`), now the same ops via `catalog_graph.py`. **Our edge over it:** we add vector + label layers (`build_vector_store.py`) = true hybrid (graph+vector+FTS5+facet); codegraph is structural+FTS5 only.
- Next codegraph-inspired steps: expose `catalog_graph` ops over the MCP emitter (cheap agent navigation), incremental rebuild + staleness (codegraph file-watcher; we have `--check-fresh`), tag inferred/similarity edges `provenance: heuristic` vs declared.

| 9 | prompt-tooling source surface (worked example) | `tool/prompt-master-prompt-optimizer` (nidhinjs/prompt-master, MIT, attribution) — ties to token-efficiency + output-format families | validate ok | see branch log |

### Throughput reality (answering 10k–50k components/day)
- Measured: a **1,000-seed partition with all 10 row families = ~31s** (22s CPU). A **10,000 monolithic run hung >27 min** (batch dedup is non-linear) and was killed.
- ⇒ **10k–50k/day is achievable via PARTITIONED runs** (10–50 × 1k ≈ 5–25 min), NOT a monolithic call and NOT agent hand-authoring. Repo already has partition tooling (`source_surface_partition_planner`, `daily_partition_load_audit`, `partition_registry_replay`).
- **Bottleneck to fix:** make the batch-dedup stage scale (SimHash/LSH blocking) so a single batch can exceed ~1–2k without O(n²) blowup. Capture-and-improve-the-incremental-path per CLAUDE.md.
- Honest tiering still applies: these are **generated candidates** (JSONL staging), not promoted/committed components. Promotion stays gated (review, real embeddings, provenance).

### Prompt-tooling as a source surface (the scalable path for "thousands of prompt repos")
- Do NOT hand-catalog thousands of repos. Route them through source governance: license-filter (permissive only), fetch metadata (not bulk copyrighted text), normalize, fuzzy-dedupe, attribute (source_url/author/license), embed, route uncertain → review ticket.
- prompt-master itself is a rich vein: its 35 anti-patterns → `pattern/anti-*`; 12 templates → logic-packs; token-efficiency audit → reinforces the token-efficiency family. Mine the KNOWLEDGE, reference the repo.

### Swarm notes
- Parallel-safe model worked: each agent created only new files in its own dir, never edited shared files, never ran git; lead serialized commits + re-validation. Zero conflicts.
- **Loose end:** `logic-pack/frontend/builder-prompt-templates` registers 4 prompt-template `.yaml` files under `logic/frontend/builder-prompt-templates/` that are NOT authored yet — valid skeleton (catalog defs are contracts), author the prompt files next.
- Hosting research (`vectorized-registry-hosting-2026.md`): start ~$40–87/mo (Cloudflare Pages + Neon pgvector + Render worker + R2); pgvector holds to ~50M vectors, then Qdrant/Milvus named-vectors for multi-dim; 1B+ ≈ $16–39k/mo with quantization + tiered storage.

## Foundation status (vectorization)
- env has **no numpy/sentence-transformers/torch** → real-model vectors need a (heavy) install or hosted route; offline default is the deterministic hash embedder (**placeholder, non-promotable**).
- Canonical schema already supports multi-type: `object_embedding(embedding_model)` = many vectors/object; `label_assignment(assignment_method, model_route_id, confidence, review_status)` = regex/llm/deterministic/classifier/human labels with provenance. Gap: pgvector single `vector(384)` column = one dim; the local store stores dim-per-row (multi-dim). Note for hosted: per-model/per-dim embedding tables or a metadata-tagged store.
- To make vectors **real/promotable**: install sentence-transformers (or wire a hosted embedding route via the model registry in `scripts/_config.py`), rerun with `--model all-MiniLM-L6-v2`, then load via `pgvector_embedding_load_plan.py` + `daily_promotion_readiness_plan`.

## Database object reality (queried 2026-05-26, answering "how many objects in the DB")

- **Committed/queryable** (`dist/catalog.sqlite`): **505 objects, 1,024 edges, 0 embeddings** (FTS5 lexical search works; vector search empty).
- **Source catalog (YAML manifests, validated):** 2,397 (530 committed to git, 1,867 candidates) — down from 4,377 after the 2026-05-27 capability-lift cull removed 1,980 untracked filler (`dist/reports/capability-lift-gate.json` is the audit record).
- **Generated candidate rows (staged JSONL in `dist/`):** ~1.78M+ lines across row-family files — generated factory output, **not loaded** into any DB.
- **Live Postgres committed rows:** 0 — `db/postgres/schema.sql` is 36-table DDL + load plans only; no running DB.
- **Vector-search-ready embeddings:** 0 (needs `sentence-transformers` + `OH_BUILD_EMBEDDINGS=1`, or the pgvector load path executed).
- **Conclusion:** binding constraint to "build this out" is the *foundation* (stand up store + embeddings + run promotion), not more generation. Corpuses fuel it; the conversational builder consumes it.

## Notes / pre-existing working state (not authored this session)

- Working tree at branch point had 367 modified + ~9,088 untracked files
  (machine-generated `scale*/` candidates, the in-flight `manifest→component`
  rename, in-flight `mkdocs.yml` nav work). These are **left untouched**;
  this session commits only files it authored/edited, by explicit path.
