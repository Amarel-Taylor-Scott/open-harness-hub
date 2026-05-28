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
- ✅ **DONE 2026-05-28 — real embeddings (P1)** via Ollama (`all-minilm`, 384-dim, GPU); semantic retrieval live in the showcase (`embed=all-minilm promotable=True`). Next: more capability-lift verticals.
- **Deterministic code-edit family** (high priority; the "small models can't do exact-match patch" objection): structured/line-anchored/AST patch-apply as a *deterministic processor*, plus a verify-and-repair harness gate — move edit reliability OUT of the model so a cheap model can drive it. Pairs with the cost-routing principle: orchestration has a coherence floor (capable model or deterministic routing), narrow well-scoped sub-tasks route to small/local models.
- **Supervisor / model-babysits-model loops** (user idea): automate the manual "babysitting/herding/re-wording" of even frontier models — evaluator-optimizer, critic/verify-and-repair, escalation-on-low-confidence, multi-model cross-check/debate. The *supervisor* runs on a capable model (coherence floor) or a deterministic checker; the *worker* can be cheaper. Seeds exist (patterns reflexion / self-refine / evaluator-optimizer / multi-agent-debate; `processor/llm-judge`). Ship as a reusable supervisor harness + rubric + benchmark proving fewer-failures vs unsupervised.
- **Model-efficiency knowledge corpus** (user idea, DS4 news): governed knowledge-pack of quantization / KV-cache / runtime strategies (asymmetric MoE quant, KV-offload-to-disk, no-PyTorch runtimes like DS4) so the builder can recommend cost/latency strategies for the "make it cheaper / run it local" refinement. Source via news/governed scraping (permissive, attributed) — feeds the cost-routing layer, not a model replacement claim.

### Knowledge-pack enhancements (queued 2026-05-28)
- **KP retrieval/trigger typing** (user idea): add a `retrieval` field to knowledge-packs — enum `rag_vector | regex | keyword | exact_id | classifier | graph` — so each pack declares HOW it is consumed; surface it in the builder + flowchart (e.g. "Knowledge (RAG)" vs "Knowledge (regex/keyword)"). Schema + vocab + backfill existing KPs.
- **More esoteric capability-lift knowledge packs**: specialized/long-tail domains where base models are weak (the generation priority; each clears the capability-lift bar with a benchmark).

### Builder / showcase UX roadmap (queued 2026-05-28, from live review)
1. **Provenance/trust surfacing** per component (license · source · freshness · trust_boundary) in the flowchart — the governance moat made visible. Needs the store to carry these fields (extend build_vector_store rows) — separation of concerns: store enrichment vs. UI.
2. **Gap detection + abstract components**: when a stage has no on-domain match, say so and offer an *abstract/proposed* component (evidence-backed: paper/post, confidence + provenance, maturity = abstract→proposed→experimental→validated). New `maturity` field.
3. **Interactive refinement**: wire "cheaper"/"stricter" as buttons that rebuild with a refinement flag (not just text).
4. **Per-stage alternatives + swap** (registry value = alternatives + tradeoffs).
5. **Real cost calibration** from component `cost_model` + the model-registry pricing (replace illustrative ranges).
6. **Latency/QoL**: merge the two Gemma calls (select + narrate) into one; stream stages; cache build results per task (response-cache component).
7. **Wiring-rule validation surfaced** (rule-pack reaches model via harness; draw trust boundaries).
8. **Builder benchmark** (pasted task → expected component set) with a visible regression score (master-goal P3).
9. **Supervisor / verify-and-repair stage** baked into assembled flows (the model-babysits-model idea).

### 2026-05-28 full-power review cycle (DONE + new backlog)
DONE: parallel discovery fleet (5 sub-agents) → **45 vetted capability-gap KP candidates** persisted to `data/capability-gaps/discovered-2026-05-28.jsonl`; standing `scripts/factory/capability_gap_scout.py` (LLM-assisted, dedup-aware, priority-scored — the 24/7 single-process discovery engine); fixed the **silent orchestration collapse** + stratified retrieval + under/over-match detection + 2 code-review safety bugs; `docs/strategy/executive-review-rubrics.md` (8 C-suite grading rubrics + current grades) and `docs/strategy/competitive-positioning-deep-dive.md` (compete+integrate per player).

New backlog (queued for `/goal` + the scout):
- **Generate the 45 discovered KPs**, prioritizing exact_id/graph high-lift ones (CVE/CWE, FDA 510k, OFAC 50%, HTS+AD/CVD, HGVS/ClinVar, CAS/SMILES, IANA/RFC, VA combined-ratings, IATA DG, ICS/NIMS, …).
- **Conditional model-call gate** (user): a `gate` component/pattern — "only spend a model call if these deterministic conditions are NOT met"; generalize the cost-gate family into a reusable skip-the-model gate.
- **Token-saving language packs** (user): synonym-compression + multilingual/CJK keyword substitution to cut tokens; controlled-language packs incl. **ASD-STE100 (Simplified Technical English)** as output-shaping capability-lift components with a validator. Fits the token-efficiency + output-format families. Also **slang / community-lexicon packs** (user): community/domain slang evolves faster than models retrain, so a fast-refreshed slang KP (`keyword`/`exact_id`, dated, provenance to the community source) is high-lift — and a prime target for the scout's continuous refresh.
- **First-class MCP server** (user): promote `scripts/emit/mcp_server.py` from emitter to a running endpoint exposing search/build/export so any agent (Claude/Cursor/…) consumes the registry. The agent-access protocol = MCP.
- **PathNav.ai integration** (user project): serve PathNav's life-goal agent-pipeline building via the registry + builder + MCP + export; KPs/grep/regex/exact-match components for goal alignment (agents + humans).
- **Builder UX** (carryover): provenance/trust surfacing, streaming, interactive refine, real cost calibration, builder benchmark, KP retrieval-typing.
- **Continuous parallel discovery**: cron the scout per cluster; periodically run the multi-agent burst for breadth.

### Capability-valley discovery axis (Karpathy framework, user 2026-05-28)
`capability_spike = verifiability × training_attention × data_coverage × economic_value` (already the goal-doc formula). The **highest-lift, least-served gaps are the VALLEYS** — domains where those factors are LOW, so frontier R&D ignores them: migrant labor, developing-country labor codes & governance, refugee/asylum + statelessness, under-resourced languages, informal/remittance economy, low-resource public health, artisanal mining, smallholder agriculture. Inverts the formula into a targeting heuristic AND a digital-equity mission (the DueCare/migrant-safety heritage). DONE: 10 valley gaps seeded (`data/capability-gaps/valleys-2026-05-28.jsonl`) → packs generated. The scout/loop should explicitly scout valley clusters, and the lift score should up-weight low-economic-value/low-data-coverage domains.

### DONE 2026-05-28b — esoteric capability-lift corpus (55 KPs)
`scripts/factory/knowledge_pack_factory.py` turns discovered gaps into valid, **retrieval-typed**, source-governed catalog KPs (schema gained an optional `retrieval` enum: rag_vector|regex|keyword|exact_id|classifier|graph). Emitted **55 packs** to `catalog/knowledge-packs/esoteric/` (6 with real public-fact seeds: CWE Top-25, OFAC 50% rule, APWA 811 colors, ICS forms, DEA schedules, TLS suites; 49 honest ingestion contracts with declared authoritative sources — never fabricated facts; seeds in `data/esoteric-packs/`). All 55 validate green and PASS the capability-lift gate (cull 0). Next: governed ingestion to populate the contract packs; rebuild vector store so the builder surfaces them.

### DONE 2026-05-28c — corpus to 100 + multi-page showcase
Wave-2 parallel discovery (3 more agents) → 45 new gaps (`discovered-wave2-2026-05-28.jsonl`): 15 deep valleys, 15 paper-anchored failure modes (PopQA/FreshQA/CODATA/MuSiQue/negation/ALCE/FEVER), 15 Kaggle-anchored (EEDI/AIMO/LMSYS/DAIGT/RSNA/BirdCLEF/Optiver/Ribonanza), all with verified permissive sources (licensing pitfalls flagged: avoid SNOMED/ICD-10-ND). Factory → **100 esoteric KPs total**, all validate + pass lift gate. Showcase is now **multi-page**: `/browse` + `/api/components` (search + type facets + nav); esoteric example prompts.

### Product backlog (user articulation 2026-05-28)
- **Four value props** (formalize as `docs/strategy/value-propositions.md`): (1) VALLEYS — capability-gap KPs where Karpathy factors are low (migrant labor, developing-country law/governance, under-AI'd economies); (2) STREAMLINED building — flexibility, verifiability, updatability; (3) COST — token/model-size reduction + tool suggestions (gate components, synonym/CJK/slang/ASD-STE100 packs); (4) TRACKING — I/O, recommendations, improvement, **drift**. Deployment = MAX FLEXIBILITY: run on our platform (Pro) OR BYO platform; our cloud models OR their models; MVP first; if we capture full I/O (platform or data-sharing) → track data + drift and share it.
- **Advanced multi-source gap discovery**: extend `capability_gap_scout` into source adapters — Kaggle, arXiv/papers, **GitHub profiles/repos**, and **feed-in arbitrary text (LinkedIn posts / pasted content)** → extract gaps. Parallel fan-out (the agent-burst) + the standing scout = the "insane gap-finding" engine. Add `--text/--from-file` mode.
- **Prompt-pack families** (source-governed intake): image/video generation prompt packs (GitHub + image-gen sites), coding prompt packs (GitHub, Claude Code, tools) — each a capability-lift pack with attribution; mine knowledge, reference repos.
- **Governed ingestion** to populate the 94 ingestion-contract KPs from their declared authoritative sources (license-filtered, attributed).
- **Diagram/workflow page** (dedicated) beyond the build-page flowchart; provenance/trust surfacing.
- **PathNav.ai**: consume the registry + builder + MCP for life-goal agent-pipeline building.

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
