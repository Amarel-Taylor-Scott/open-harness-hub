# CLAUDE.md - AI Done Right Agent Instructions

> **READ `_repos/shared-backend-components/docs/BIBLE.md` FIRST** — the single north-star reference (vision · the 5
> pillars · the ~35 OpenHubForAI surfaces + 103 registries · assumptions · guardrails · laws · contracts · hooks ·
> tools). This file (CLAUDE.md) is the agent operating layer; the BIBLE is the canonical *what + why*. If they ever
> disagree, the BIBLE wins.

This file is for Claude Code, Claude desktop/browser agents, and any Claude 4.x/4.8/4.7-style workflow that opens this repository. Follow `AGENTS.md` first; this file adds speed and organization rules for scaling OpenHubForAI.

## Active Handoff → GPT-5.6 (2026-07-09) — READ THIS FIRST

**Start with `_repos/shared-backend-components/docs/HANDOFF-GPT-5.6.md`** (what this session built + the reconciled
state) and **`docs/RESEARCH_PATHS_AND_IDEATION.md`** (56 ranked paths to test). Reconciled, EXECUTED savings picture
— do not overwrite it with older framing:
- Single-shot OUTPUT-token savings on common code are **marginal**.
- Prompt-injecting "use this verified primitive" is strongly **PROMPT- and MODEL-dependent**: showing the FULL tested
  source + "use as-is, do not re-implement" can work (pass≈0.5–1.0 @ ~68 out-tok); showing only signatures/edges
  often makes models **re-implement and FAIL**. Not universal — a 7-model grid (`scripts/reuse_experiment_grid.py`,
  resumable, MIN_N=8, aggregates-only) is still running; **do not conclude from small cells.**
- The only robust **0-token** win is **deterministic composition** (a manager emits thin wiring from declared config
  and mounts the verified module verbatim → passes hidden oracles, model-independent).
- Realistic senior-dev sessions are **INPUT-token-dominated** (conversation + re-read files re-sent every turn) —
  the biggest, least-explored savings lever (`scripts/realistic_session_harness.py`).
- **Do NOT re-assert "47.5%", "4.7–5.9×", "486×", or "1.17M primitives" as proven token savings** — those are
  projection / context-byte-reduction / raw-count. Honest ledger: `docs/REAL_SAVINGS_NUMBERS.md`,
  `docs/strategy/primitive-system-end-to-end-briefing.md` §4, `docs/PMF_AND_MARKET_STRATEGY.md`.
- Gemma-4-coding is reachable via browser-context CDP (`scripts/openwebui_cdp_bridge.py`), session-dependent.
- **For cleanup work (Claude Fable): read `_repos/shared-backend-components/docs/CLEANUP-BACKLOG.md`** (P0 = untrack
  the 68 GB of generated data from git — 55,606 tracked files, `.git`=2.6 GB; then JSONL→Postgres migration, doc
  reconciliation, grid completion). System-agnostic router for ANY agent: `docs/AGENT-ONBOARDING.md`. Whole-system
  reference: `docs/SYSTEM-OVERVIEW.md`.

## Active Handoff For Claude Fable — 2026-07-07 (SUPERSEDED 2026-07-09 — see the GPT-5.6 handoff above; the foundry-loop commands below remain valid infrastructure)

The active workstream is the **real-world primitive foundry loop**: use real developer sessions, repo files,
websites, apps, Kaggle-style notebooks, LeetCode/competitive-programming problems, papers, and discussions to
decompose systems into components, ask how each could be rebuilt from primitives, generate candidate primitives
and variations, and benchmark token/context savings. This is candidate-only infrastructure: generated rows keep
`candidate=true` and `serves_truth=false` until promotion gates prove source, license, correctness, and utility.

Use `/loop` in Claude Code. The command lives at `.claude/commands/loop.md` and is mirrored at
`_repos/dev-rules-context/commands/loop.md`. Its runnable backend is:

```bash
python3 _repos/shared-backend-components/scripts/source_to_primitive_foundry.py --self-test
python3 _repos/shared-backend-components/scripts/real_world_primitive_loop.py --self-test
python3 _repos/shared-backend-components/scripts/continuous_primitive_scrape_loop.py --self-test
python3 _repos/shared-backend-components/scripts/primitive_deconstruction_plane_pipeline.py --self-test
python3 _repos/shared-backend-components/scripts/real_world_primitive_loop.py --once --repo-root . --file-limit 0 --external-seed-count 1000 --max-components 5 --max-sources-per-partition 50
python3 _repos/shared-backend-components/scripts/continuous_primitive_scrape_loop.py --once --source-limit 100 --question-count 240 --max-components 5 --max-sources-per-partition 25
python3 _repos/shared-backend-components/scripts/primitive_deconstruction_plane_pipeline.py --run --question-count 360 --max-atlas-rows 250 --overlays-per-primitive 4
```

For deterministic tool-call style operation, prefer the JSON hook instead of
free-form shell fragments. It allowlists actions, clamps budgets, writes
request/response receipts, and keeps generated rows candidate-only:

```bash
python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py --request-json '{"action":"actions.list"}'
python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py --request-json '{"action":"session_benchmarks.run","args":{"sessions":16,"turns_per_session":0,"k":8,"components_per_turn":4,"scenario_mode":"mixed","include_supervised":true,"compare_base":true,"context_window":262144}}'
python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py --request-json '{"action":"session_benchmarks.run","args":{"sessions":8,"turns_per_session":0,"k":8,"components_per_turn":4,"scenario_mode":"ml_lifecycle","include_supervised":true,"compare_base":true,"context_window":262144}}'
python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py --request-json '{"action":"session_benchmarks.run","args":{"sessions":6,"turns_per_session":0,"k":8,"components_per_turn":4,"scenario_mode":"large_org","include_supervised":true,"compare_base":true,"context_window":262144}}'
python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py --request-json '{"action":"twenty_million_cycle.run","args":{"seed_rows":100000,"rows_per_shard":10000,"compile_shards":2,"start_shard":-1,"benchmark_n":300,"benchmark_k":5,"paraphrase":true}}'
```

Current benchmark lanes:

- `run_realistic_session_benchmarks.py` measures full multi-prompt sessions for app, warehouse, agent, regulated,
  platform, ML lifecycle, and Google-scale large-organization buildouts. Latest lifecycle and large-org runs write
  receipts under `_repos/shared-backend-components/data/dev-intel/realistic_session_benchmarks/`.
- The ML lifecycle pack generated from the production-ML role matrix lives at
  `_repos/shared-backend-components/data/dev-intel/primitive_factory/specialized_packs/ml_lifecycle_primitive_cards.jsonl`
  with a manifest beside it; it is candidate-only and loaded into the expanded benchmark corpus.
- The large-organization pack generated from the Google-scale operating-model matrix lives at
  `_repos/shared-backend-components/data/dev-intel/primitive_factory/specialized_packs/large_org_primitive_cards.jsonl`
  with a manifest beside it; it is candidate-only and loaded into the expanded benchmark corpus.
- `run_twenty_million_supervised_cycle.py` now uses `--start-shard -1` as "auto next unused shard window" so repeated
  cycles do not silently recompile the same shard slice.

The loop writes receipts under
`_repos/shared-backend-components/data/dev-intel/source_to_primitive_foundry/real_world_loop/`:
`source_objects.jsonl`, `component_breakdowns.jsonl`, `rebuild_plans.jsonl`,
`primitive_candidates.jsonl`, `primitive_variations.jsonl`, `gap_queue.jsonl`, and `latest_status.json`.
The gap queue is fed by the latest primitive-consumption benchmark so hard misses such as algorithm,
competitive-programming, Kaggle/ML, SWE, and agentic workflow gaps become source-acquisition targets.

The continuous source-policy/LLM loop writes receipts under
`_repos/shared-backend-components/data/dev-intel/continuous_primitive_scrape_loop/`. It covers news, apps,
systems, Kaggle notebooks, Medium/blog articles, system-design writeups, textbooks/course material, Google
Scholar/citation clusters, paper publication pages, repos, discussions, and websites. Offline mode is the default:
it builds governed source snapshots, asks a 200+ question bank per source, emits decomposition rows, primitive
graphs, language/design/architecture examples, and `primitive_database_feed.jsonl` rows. Live scraping and LLM
calls are explicit flags (`--live`, `--use-llm`) and must keep raw source bodies out of persisted rows.

The deconstruction-plane pipeline writes the persistent question/deconstruction database under
`_repos/shared-backend-components/catalog/knowledge-packs/data/primitive-deconstruction-plane-database/` and receipts
under `_repos/shared-backend-components/data/dev-intel/primitive_deconstruction_plane_pipeline/`. It defines
deconstruction planes, analysis layers, dimensions, question rows, question edges, and a completeness rubric, then
materializes fully-defined primitive candidate rows with visible edges, contracts, examples, graph refs, proof
requirements, benchmark hooks, promotion blockers, and `serves_truth=false`. The latest bounded run created 18
planes, 14 layers, 343 dimensions, 955 questions, and 175 fully-defined primitive candidate feed rows from the latest
continuous-loop receipt. Optional model refinement can use Ollama/OpenRouter/direct OpenWebUI or OpenWebUI CDP, e.g.
`--use-llm --provider openwebui --mode cdp --llm-refine-limit 25`; keep outputs candidate-only.

When continuing this work, do not stop at one favorable benchmark. Keep running large receipts, compare against
Claude Code session logs where possible, improve composition/remix standards, and turn every miss into a source
target plus proof requirement. Raw source bodies should not be stored in primitive rows; store handles, digests,
components, and receipts.

> **Repository layout (post-`_repos/` migration) — read before following any path below.** The repo **root** now holds
> only `_repos/` + meta files (`README.md`, `LICENSE`, `AGENTS.md`, `CLAUDE.md`, `conftest.py`) + tooling-hidden dirs
> (`.venv`, `.claude`, `.codex`, `.github`). Every former top-level dir moved under `_repos/<owner>/`. Maps:
> `_repos/INDEX.md`, `_repos/MIGRATION-STATUS.md`, `_repos/_moved_dirs.json`. **Path convention throughout this file:**
> a bare `scripts/…`, `docs/…`, `architecture/…`, `catalog/…`, `schemas/…`, `vocabularies/…`, `rubrics/…` resolves under
> **`_repos/shared-backend-components/…`**; the devkit (`standards/`, `prompts/`, `hooks/`, `commands/`, `skills/`) is
> under `_repos/dev-rules-context/…`; strategy/codex/concepts/taxonomy prose is under `_repos/_shared/…`; and product
> code written **`src/<x>/…`** lives physically at `_repos/<x>/backend/src/<x>/…` while `src/<x>/…` stays the canonical,
> location-stable name used by ids and the code graph (do NOT rewrite `src/<x>/` to the physical path in ids/graph).

## Portfolio (owner-decided 2026-06-06; updated 2026-06-09 — read FIRST)

Current parent display brand: **AI Done Right** (`aidoneright.dev`), tagline
**"AI, done right."** The prior ContextIsEverything language is preserved as
founding thesis and legacy path context, not as the parent display brand. The
high-fidelity Claude Code Max handoff lives in
`dist/sites/aidoneright-design/`: start with `START-HERE-CLAUDE-CODE.md`, then
`README.md`, `CLAUDE-CODE.md`, and `HANDOFF.md`.

Current design-family snapshot: parent + **Baltor** + **Teleon** + the
**OpenHubForAI registries** (live open registries + private-bench registries; the exact
count and live/preview split are **computed** by the family check, never hand-counted —
run `python3 scripts/check_ai_done_right_surface_family.py` for the current numbers rather
than trusting any literal in this prose). The private bench includes the
complete Baltor method spine (OpenReconciliationHub, OpenHardeningHub,
OpenEnrichmentHub, OpenOptimizationHub, OpenVerificationHub) and
OpenRoutingHub (model-routing policy; owner-proposed 2026-06-09). The owner-directed Codex loop for
this family is `docs/codex/ai-done-right-family-polish-goal.md`. The
parser-safe `/goal` entrypoint is
`/goal follow the instructions in docs/goals/aidoneright-portfolio-loop.md`.
Run `python3 scripts/check_ai_done_right_surface_family.py --self-test` before
trusting or editing family-surface counts. Run
`python3 scripts/check_handoff_docs_freshness.py --self-test` before handing the
bundle to another agent.

Service-to-service auth is an active architecture track. Read
`docs/architecture/service-auth-and-consumption-model.md` before implementing
API keys, service accounts, delegated calls, private-bench enforcement, or
cross-service consumption. For local testing without paid cloud, read
`docs/architecture/local-dev-tunnels-and-auth.md` and run
`python3 scripts/check_local_dev_tunnel_auth_runtime.py --self-test`.

Canonical portfolio architecture remains:
`docs/strategy/teleon-baltor-openhubforai-portfolio.md`.

## Surfaces: serve the BUILT-OUT apps, never a basic replacement (read before touching any web surface)

The 5 product surfaces are the full apps in `web/{context-is-everything (AI Done Right), teleon, baltor,
openhubforai (OpenHubForAI), aidevobserver}`, served by the **showcase** (`OH_PRODUCT=<brand> python3 -m
scripts.showcase --port N` → `WEB_DIR=web/<OH_PRODUCT>`) over the shared kit (`web/<app>/kit/`), wired to the
service-plane backends through same-origin **seams** (`/api/identity/`, `/registry/`, `/api/teleon/`,
`/api/observer/`, …). Design system: `docs/DESIGN-BIBLE.md`. Frontend↔backend + local/cloud: `docs/INTEGRATION-BIBLE.md`.
Full contract: `docs/codex/surface-and-development-contract.md`.

- **NEVER build a new basic/skinny replacement server for a surface.** Serving a hand-built rich app with a static
  stub (no backend) is the recurring failure mode — `scripts/surface_server.py` (fallback only) and the deleted
  `web_app_server.py` were exactly this mistake. Serve the built-out app via the showcase; if a backend call 501s,
  wire the **seam + a service-plane service**, never stub it.
- **Before serving/tunneling a surface:** confirm it is the rich built-out app (`du -sh web/<app>`; grep for
  login/dashboard/control-tower) AND that the backends are wired (Playwright: rich content + **0 console errors**).
  A page that renders but 501s on its API calls is NOT done.
- **A new frontend↔backend integration** = a service-plane service + a seam + `fetch('/api/<x>/...')`, never a
  hardcoded host (`docs/INTEGRATION-BIBLE.md` §4).
- **Reuse-first:** before building any surface/server/engine, check it already exists (the showcase, the service-plane,
  the shared kit). "This already exists, don't rebuild it" is the highest-ROI decision.

## AIDevObserver Compatibility

Before building a new helper, workflow, parser, scraper, API adapter, data pipeline, UI quality gate, model/eval
harness, or agent integration, ask whether AIDevObserver or the primitive registry already knows the route.

Use the companion project pack when working in Claude Code or another agentic dev framework:

- `commands/find-reuse.md` before implementing a new utility or workflow;
- `commands/review-session.md` at the end of a substantial AI coding session;
- `commands/refresh-primitives.md` when local source-backed primitive candidates should be regenerated;
- `mcp/aidevobserver.md` for the Claude Code MCP connection;
- `hooks/pretooluse-aidevobserver.md` for non-blocking live reuse hints.

Steering rule: do not reinvent code or workflows the primitive database already knows. AIDevObserver findings remain
candidate advice (`serves_truth=false`) until proof and promotion.

A holding company owns three product layers. **Teleon** (`teleon.dev`, domain owned) = the purpose-driven,
eval-gated, self-adaptive compute **runtime SaaS** — it owns PurposeTask/CapabilityTask, runtime selection,
evidence ledger, promotion/policy gates, boundary approvals, adapters, the assurance dashboard. **Baltor**
(`baltor.ai`) = the applied, customer-facing context product, **powered by Teleon** (a tenant). **OpenHubForAI**
= the open ecosystem (evals/harnesses/templates/skills) + the **open CapabilityTask spec (CTS)**.

- **Architectural law (enforced by `scripts/check_portfolio_dependency_law.py` over
  `architecture/portfolio_dependency_law.json`):** Baltor → Teleon → OpenHubForAI, **never the reverse**.
  Teleon must never import Baltor; OpenHubForAI imports neither. PurposeTask is **Teleon**, not a Baltor
  subsystem — generic runtime code is being extracted `_repos/baltor/backend/src/baltor/` → `_repos/teleon/backend/src/teleon/` incrementally (lossless;
  see the law file's `migration_status`).
- **Naming:** product = **Teleon**; staff dashboard = **Teleon Control Tower**; customer dashboard =
  **Capability Assurance Portal**; object = **PurposeTask** (formal/spec synonym **CapabilityTask**). Brand
  doc: `docs/strategy/teleon-naming-and-domain.md`. ("Purpose Runtime"/"Anneal"/"Cairn"/"OCTS" are superseded.)
  Teleon's control & trust plane is a **separate greenfield TS build**: `prompts/teleon-build-kit.md`.
- **Hosting:** Teleon + Baltor deploy **same region/private network** (low Baltor→Teleon latency) but stay
  **separable** (separate service/data/identity/IaC + a versioned API + graceful local fallback).

## North Star

Active `/goal` runs are now Baltor-first. Read
`docs/codex/baltor-clean-context.md` and
`docs/codex/baltor-autonomous-goal.md` before older factory-scale context. The
component registry remains the substrate; Baltor context control is the product
focus.

### The Foundational Law (owner-installed 2026-06-24 — frames what we build)

We are building a **systems layer for executable capability** (Teleon indexes/optimizes it, Baltor governs its
truth, OpenHubForAI structures it, Observer watches its usage), not point products. Four reconciled filters govern it
(single source: `architecture/substrate_layers.json` → `foundational_law`; map of layers↔existing-assets↔gaps:
`docs/strategy/computational-substrate-and-foundational-law.md`):

1. **System filter** — *Does this improve compiler intelligence?* If no, don't build it.
2. **Execution filter (descent)** — *Can intelligence be removed from this execution path?* Descend toward that
   forever (the Teleon make-it-work→make-it-cheap→deterministic-substitution thesis).
3. **Component admission** — must LIFT over the bare model AND the lift must be STRUCTURAL/durable (the
   Capability-Gap Framework below).
4. **Binding constraint** — **DEPTH BEFORE BREADTH**: every new layer must serve the ONE vertical being proven to a
   paying customer (gated by `scripts/proposal_backlog.py`). Breadth without a revenue vertical is the failure mode.

Filter #1 is necessary; #3+#4 make it sufficient. **Before building any "new" layer, check it doesn't already
exist** — run `scripts/check_substrate_layers.py`, `scripts/codegraph.py --audit`, and the reinvention guard.
*"This already exists, don't rebuild it"* is the highest-ROI decision in the architecture — including about our own
work.

Build a database-backed registry of reusable AI pipeline components and subcomponents that can scale from thousands to millions of rows without turning every row into a public static file.

The product is not a pile of static definitions. It is a component network:

- pre-LLM components: intake, OCR, normalization, source governance, entity linking, dedupe, routing, cost gates;
- LLM/model components: local models, hosted model routes, browser models, embedding models, rerankers, fine-tuning/training jobs, multimodal generators;
- post-LLM components: verification, scoring, review queues, CDC propagation, signed publisher updates, deployment blueprints;
- runtimes: local Python, Docker, Render workers, Cloud Run, Kubernetes, MCP servers, pgvector, BigQuery/ClickHouse telemetry, object storage.

Use "components" and "subcomponents" in new prose and user-facing docs. Avoid introducing new uses of "artifact" or "manifest" unless quoting an existing schema, filename, or legacy phrase. ("Primitive" IS canonical for the seven-primitive model — Input · Knowledge Corpus · If Statement · Action · Loop · Stop/End · Output; see `docs/concepts/component-taxonomy-and-stages.md`.) Product vocabulary: **Knowledge Corpus** (not "knowledge pack"), **If Statement** (not "rule pack"/"logic pack"), **Action** (a persona/tool/processor/harness/rubric is an Action). Version lives in metadata, never in names or IDs.

## Capability-Gap Framework (canonical — read before deciding what to build/collect)

We build for the **negative space** — where base models lack capability — not the head of the distribution. Two load-bearing rules:

- **Two-axis admission:** a component must lift (`pipeline_score − bare_model_score > 0`) AND the lift must be **structural** (won't close when the next model ships), not transient. Single source of the taxonomy (lift_reason → durability_class, mechanisms, retrievability tiers, decay_signal): `scripts/eval/reason_codes.py` — never re-define these enums elsewhere. Sorter: `scripts/eval/durable_gap_harness.py`.
- **Screen before you collect:** cheap Stage-1 gap screen (`scripts/acquisition/gap_screen.py`, weighted toward MODEL-INDEPENDENT signals so the model can't draw its own map) → expensive Stage-2 confirm on a sample. The owner feeds research areas at `data/research-queue/areas.jsonl` → `scripts/acquisition/research_queue.py` ranks them.

Canonical reading: `docs/concepts/capability-valleys.md`, `docs/strategy/north-stars.md` (+ `corpus-acquisition-grid-spec.md`, `gap-detection-screen-spec.md`, `external-research-brief-2026-05-28.md`). Governance/provenance is the external moat; the lift bar is the internal selection criterion.

## Default Fast Path

Do not start with full catalog rebuilds. The normal loop is:

```bash
python3 scripts/validate.py <changed catalog paths>
python3 scripts/build_component_id_index.py --update <changed catalog paths>
python3 scripts/build_catalog_pages.py --paths <changed catalog paths> --update-index
python3 scripts/validate.py --global-ref-check <changed pipeline paths>
python3 scripts/build_component_id_index.py --check-fresh
```

Use full release gates only when explicitly requested or when changing schemas, vocabularies, or broad catalog references:

```bash
python3 scripts/validate.py
python3 scripts/build_catalog_pages.py
```

If a full rebuild takes too long, do not keep repeating it. Capture the bottleneck and improve the incremental path.

## Code-Graph Change Audit (audit neighbors before/after a code change)

Before AND after editing a `.py` file/function/class/method, audit its **strong connections** on the unified
weighted code graph and update load-bearing neighbors in the **same** change — a green suite says the code runs, the
graph says what else the change can break:

```bash
PYTHONPATH=. python3 scripts/codegraph.py --audit <file-path | dotted.module | symbol.name>
```

It ranks (by strength = call-sites × resolution-confidence) the importers/callers that break if the API changes,
plus the transitive blast radius. Resolution is confident-only (ambiguous/builtin-shadow calls are dropped+counted,
never guessed), so the ranking is trustworthy. The graph is a seam: `codegraph.py` / `symbol_graph.py` /
`code_graph.py` carry `--self-test` (in `run_proofs.py`); regenerate artifacts with `scripts/codegraph.py --emit`.
Full protocol: `docs/codex/codegraph-change-audit-protocol.md`.

## Daily Factory Target

Every serious development turn should improve at least one of these:

- generate 1,000 to 5,000 database-backed component candidates per day;
- generate 5 to 25 showcase pipelines per day;
- reduce duplicate collapse during row merges;
- improve source governance, entity linking, fuzzy dedupe, index records, review routing, embedding execution, or promotion readiness;
- make staged rows easier to load into Postgres/pgvector safely;
- make component IDs, hashes, CDC events, and index deltas more deterministic.

High-volume rows belong in JSONL staging and Postgres/pgvector load plans, not thousands of new hand-written static pages.

## Required Row Families

A scalable factory batch should emit or preserve:

- `source_record`
- `normalized_object`
- `canonical_entity`
- `object_entity_ref`
- `dedupe_cluster`
- `label_assignment`
- `dimension_value`
- `object_embedding`
- `index_record`
- `review_ticket` when risk warrants review

Do not report raw generated lines as active components. Separate:

- generated candidate rows;
- unique staged rows;
- candidate-table load readiness;
- active promotion readiness;
- committed Postgres rows;
- vector search product readiness.

## ID And Hash Discipline

Never rely on truncation alone for generated IDs. Long generated component IDs must include stable hash suffixes so daily batches do not collapse during dedupe, index merge, or CSV load planning.

Use canonical hashes for:

- normalized object body;
- component version definition;
- source content;
- index record identity;
- command approval records;
- replay and CDC events.

Formatting changes should not create false versions. Source content changes should be detectable even when the wrapper stays the same.

## Deterministic Global Object Naming (AI-first — owner law 2026-06-27; hardened 2026-07-01)

Code here is read by AI first; future review is LLM review. Every defined thing gets a **globally unique,
location-derived, meaning-bearing name** — long names are GOOD (a name is context the model uses); no name is
ever reused; uniqueness lives IN the name (no opaque keys in code-object names). Unique names make
**grep-as-graph exact**: the code graph, primitive edges, and cross-codebase search resolve by NAME with zero
ambiguity (`codegraph.py` drops ~6k ambiguous call edges today — every collision removed increases graph recall).
Two planes, one law:

- **CODE objects (Python)** — the pyprefix scheme `py_<kind>__<file>__<scope>__<name>`
  (kind ∈ class·function·method·const·instance·var·arg·local; dunders exempt). Engine: `scripts/pyprefix.py`;
  law: `docs/codex/ai-first-naming-and-graph-spec.md`; migration manifest:
  `architecture/pyprefix_migration.json` (leaf-first, package-by-package, full gate green after each — a
  migrated path never diverges; gates: `check_pyprefix_conformance.py` + `check_pyprefix_methodology.py`).
  New/generated code follows the scheme from the first draft (`architecture/teleon_codegen_contracts.json`).
- **DATA objects (generated ids/records)** — minted ONLY by `src.teleon.experiments.ids`
  (`canonical_id` = `"{prefix}-{sha256[:16]}"` over `canonical_bytes`; Baltor imports the
  `_repos/baltor/backend/src/baltor/experiments/ids.py` shim). Version lives in `schema_version` METADATA — never in a name or id
  (no `.vN`, no `@N` suffixes; external briefs using `@1` ids must be adapted on intake). Direct
  `import hashlib` in `src/**` is the drift signal — 71 legacy sites are recorded in
  `architecture/canonical_id_migration.json` and ratchet DOWN, enforced by
  `scripts/check_canonical_id_single_source.py` (a NEW site fails; a migrated file leaves the baseline
  same-change).
- **User-facing names** — full words, no abbreviations, no jargon codenames; primitive records name their
  edges (`input_edge`/`output_edge` contracts) so agents compose by reading names + edges, not bodies.

## No Magic Values (Single Source Of Truth)

Never hand-type a value that has to be remembered and updated in more than
one place. At scale, a value typed twice is a value that drifts.

- Numbers that describe the repo (component counts, totals per type, "N
  emitters", spec/catalog version, build date) are **computed**, never typed
  into prose. The README count drifting from `172` to thousands is the
  canonical bug — do not reintroduce it.
- A value used in more than one place (embedding dimension, model IDs,
  thresholds, canonical paths, row-family/type names) gets **one definition**
  and is imported everywhere else. Put shared constants in a config module;
  put shared lists in `vocabularies/`/`schemas/` and read them.
- A string that embeds a constant's value is built from the constant
  (`f"vector({DEFAULT_SCHEMA_DIMENSIONS})"`), never a parallel literal
  (`"vector(384)"`).
- Every meaningful literal in logic is a named constant with a unit/rationale
  comment. Where a value must be mirrored, add a validate/CI check that fails
  on drift.

Full rules, examples, and remediation: `docs/codex/no-magic-values.md`.

## Change Verification (warrant before change)

Every update or design change carries a **warrant** before it is committed — one of: **clear user
intent** (cite it in the commit/ledger), **≥2 independent agreeing sources**, or **an established repo
principle**. Match the bar to the blast radius: trivial/reversible → a principle suffices; **design /
brand / strategy / vocabulary / pricing / product-structure → clear user intent OR strong corroboration,
NEVER a unilateral single-agent call**; irreversible / outward-facing → explicit intent + confirmation.
"It's green" is necessary, not sufficient. Exceptions (small + reversible) are allowed but **recorded in
the ledger**. Verifiers — and the autonomous loop — check the *warrant*, not just that it passed; when a
decision supersedes an earlier one, update/delete the stale artifact in the **same** change (no orphaned
contradictions); a memory/doc that names a file or flag is a claim about a past state — re-verify it
before relying on it. Full contract: `docs/codex/change-verification-contract.md`.

## Lossless Distillation (distillation is never replacement)

**Distillation is never replacement.** Any distillation, decomposition, compression, optimization,
reconciliation, promotion, or LLM→deterministic-rule conversion creates a new **versioned** derived
layer while PRESERVING the raw layer, intermediates, lineage, source handles, held-out items, rejected
candidates, model/tool traces, configs, receipts, and a rollback target. Omitted / held-out / rejected /
superseded ≠ deleted. No destructive overwrite, irreversible compression, lossy promotion of truth-bearing
facts, or a winner without lineage to the losers. Compression may shrink the text surface only if
answer-critical facts + source handles + held-out warnings survive; tenant-private lineage never becomes
global. Run side-by-side before promotion, shadow new rules, monitor after, and prove rehydration. Carry
the **LOSSLESS DISTILLATION CLAUSE** in every workflow prompt. Full law:
`docs/codex/lossless-distillation.md`.

## Archived / Legacy Files (move, never delete; never untrack)

Outdated / superseded context is **moved, not deleted, and not untracked** — it stays in git for lineage + rollback,
relocated under **`archive/legacy/<original-path>`** with its status recorded. Rules:

- **Mover:** `scripts/archive_legacy_docs.py` (`--scan` to list, `--apply` to move losslessly). Conservative,
  header-marker detection only (superseded-by / deprecated / do-not-use) so a live doc is never archived.
- **Status label is mandatory:** every move is recorded in `archive/legacy/_manifest.jsonl` (original_path, reason,
  status, reversible) and surfaced in **`archive/legacy/README.md`** (the human status index + restore instructions).
- **Codemap/context exclude `archive/`** (`scripts/context_pack_builder.py` `_TREE_EXCLUDE`) so archived files drop
  out of the model context automatically — but stay on disk + in git.
- **Restore** = `git mv archive/legacy/<path> <path>` (the manifest has the exact origin).
- **Status accuracy law:** never mislabel LIVE/GENERATED data as "legacy." The component catalog (root `catalog/` =
  live registry read by `dev_status.py`/the build; `docs/catalog/*.md` = GENERATED output of
  `scripts/build_catalog_pages.py`, only `index.md` in the mkdocs nav) is **not** legacy — it carries a `_STATUS.md`
  marking it generated/live, and is never archived as outdated.

## Promotion Boundary

Candidate-table load readiness is not active publication readiness.

A candidate can be structurally load-ready when it has source, dedupe, content hash, embedding work, and index records. It must not become tenant-visible while it has:

- open review tickets;
- high-risk review requirements;
- placeholder embeddings;
- unresolved source or signature questions;
- volatile public facts without CDC/revocation handling.

Use `scripts.db.daily_promotion_readiness_plan` after large row generation.

## Safety And Scope

Do not store real PII, secrets, confidential data, or proprietary dumps. Use synthetic or public metadata only. Do not republish `_reference/`.

Stay away from insurance-related pipelines in new work. If legacy insurance examples already exist, do not expand them.

For sensitive domains, prefer review queues, verified facts, signed publishers, redaction, provenance, and deterministic gates over "just ask the model."

## What To Do When Stuck

If one source path is blocked, switch paths:

- generate showcase pipelines;
- add promotion/readiness tooling;
- improve load audits;
- add source-surface seeds;
- add repair planners for missing row families;
- add documentation that prevents repeated slow or incorrect paths.

Do not stop because one scraper, API, provider, or full rebuild is slow.
