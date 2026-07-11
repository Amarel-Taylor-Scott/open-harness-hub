# Backend — the substrate (BLACKBOX view)

**What this file is.** The standalone internal picture of the **Backend / substrate** component: the
database-backed registry federation of reusable components + subcomponents and the seven-primitive
model, the factory that generates and stages them, the service-plane of small HTTP services behind
the seams, the code graph, and the two deterministic-naming planes. This is what everything else in
the portfolio consumes. A session managing only this component should be able to work from this file
plus the sources it links.

**Grounding rule.** Every claim below summarizes and links an existing repo doc or machine source; the
cited source wins if they ever disagree. Counts and metrics are **computed by the named script**, never
typed here (the No Magic Values law — `docs/codex/no-magic-values.md`).

**serves_truth = false at this layer.** A registry returns pointers and shapes, never truth; a code
graph is a static derivation of the code, not a truth claim. Truth is Baltor's job, downstream.
Sources: `src/teleon/registry/port.py` (module docstring), `scripts/codegraph.py` (module docstring),
`architecture/registry_layers.json` → `serves_truth`.

---

## 1. What this component IS (its one job)

A **component network**, not a pile of static definitions: a database-backed registry of reusable AI
pipeline components and subcomponents that scales from thousands to millions of rows without turning
every row into a public static file, plus the factory that fills it and the service-plane that serves
it. The systems-layer map frames it as the **"computational substrate for executable capability"** — a
machine-readable model of software at primitive level that a compiler can reason over.
Sources: `CLAUDE.md` §"North Star" / §"Required Row Families"; `docs/concepts/system-overview.md` §3;
`docs/strategy/computational-substrate-and-foundational-law.md`;
`architecture/substrate_layers.json`; `_repos/_shared/ARCHITECTURE-MAP.md` §"6. Backend".

The whole thing in one sentence (from `docs/concepts/system-overview.md`): *a database-backed network
of reusable components, plus a compiler that turns a capability statement into the cheapest bounded,
verified DAG of those components, under governance that keeps truth and efficiency separable — the
model proposes; the registry, the type system, and the descent dispose.*

**Where the code physically lives.** The substrate is **not a fourth brand layer** with its own
package root. It is realized inside the Teleon package (`src/teleon/{registry,storage,components,...}`),
the tooling tree (`scripts/`, which the dependency law treats as tooling, not a brand), the config
registries (`architecture/*.json`), the seven-primitive shells (`scripts/primitives/`), and the JSONL
staging under `data/`. That placement is why the portfolio dependency law puts the substrate's Python
under `src/teleon` — see `_repos/shared-backend-components/context/edges.md` for the boundary consequences.
Sources: `architecture/portfolio_dependency_law.json` → `layers.teleon`; directory listings under
`src/teleon/`, `scripts/`, `architecture/`, `scripts/primitives/`.

---

## 2. The seven primitives + the component taxonomy (the foundation)

Everything reduces to **seven primitives**, each a subtype of one generic shell
`scripts/primitives/base.py::Primitive` whose contract matches the pipeline object (`run(po) -> po`).
One file per primitive under `scripts/primitives/` owns its own label/stage/description (the single
source — no magic-string label tables elsewhere; product labels come from `label_for_type` /
`stage_for_type`):

1. **Input** — the payload to work on.
2. **Knowledge Corpus** — a store of facts, queried by a trigger (product term; not "knowledge pack").
3. **If Statement** — the condition, kept separate from the THEN (not "rule pack"/"logic pack").
4. **Action** — anything that *does* something: persona, tool, processor, harness, adapter, rubric,
   benchmark.
5. **Loop** — control flow / iteration.
6. **Stop / End** — halt early on a guard.
7. **Output** — finalize result + trace.

There is **no eighth primitive**: an unmet need is a **capability-request** (a typed empty slot,
`schemas/capability-request.schema.json`) carrying the `target_type` it will become — never
tenant-visible as a component. "What role" (seven primitives) and "how mature" (lifecycle ladder
`abstract < experimental < beta < stable`, `vocabularies/lifecycle.yaml`) are orthogonal axes.
Sources: `docs/concepts/component-taxonomy-and-stages.md` (canonical); `docs/concepts/layers.md`
(the four layers: primitives → harnesses → pipelines → benchmarks); `scripts/primitives/` (the shells).

**Component vs subcomponent.** A component is an active reusable unit (searchable, versioned, rated,
evaluated, wired, deployed, updated). A subcomponent is a smaller unit inside it (fact, rule, check,
review question, eval criterion, prompt fragment, schema field, cost dimension, label, dimension value,
entity reference, index record, embedding work item, review route, deployment step). This is how the
platform scales to millions of records without pretending each is a hand-curated file.
Source: `docs/architecture/database-backed-component-store.md`.

Vocabulary discipline: use **components / subcomponents** in new prose; avoid new uses of
"artifact"/"manifest" except when quoting an existing schema/filename. "Primitive" is canonical only
for the seven-primitive model.
Source: `CLAUDE.md` §"North Star" (vocabulary paragraph).

---

## 3. The registry federation (the substrate proper)

The registry is a **federation of many source catalogs, each behind ONE universal interface** — the
"registry-of-registries" (owner vision: a machine-readable model of all executable capability). The
index of load-bearing registries, each mapped to its real backing module + the Open\*Hub that exposes
it + the compiler stage it serves + a `live|partial|gap` status, is
`architecture/registry_ontology.json` (existence-checked by `scripts/check_registry_ontology.py`).
Source: `architecture/registry_ontology.json` (`principle`).

**One ordering protocol over the buffet.** `src/teleon/registry/port.py` wraps every
`architecture/*.json` list-of-records catalog as one adapter exposing the same verbs
(`list` / `lookup` / `search` / `explain`) so an agent picks ingredients uniformly:
`catalog("geospatial_sources").search("weather")`. The lexical scorer swaps for a learned one behind
the same port without changing a call site (the agnostic-adapter pattern). The registry package also
carries `populate` / `compose` / `enrich` / `search` / `browse` / `index` / `variations` /
`primitive_match` / `composition_affinity` / `reinvention_guard`.
Sources: `src/teleon/registry/port.py` (docstring + `CATALOGS`); `src/teleon/registry/__init__.py`;
directory listing of `src/teleon/registry/`.

**Layered so it scales without drowning the model** (`architecture/registry_layers.json`):

- **core_curated** — `architecture/tool_registry.json`, scale *hundreds*, vetted/promoted,
  hand-authored, read by the descent + checks; every row real + license-classified.
- **staged_massive** — `data/dev-intel/tool_registry_staging.jsonl`, scale *thousands → millions*,
  candidate-only (discovery ≠ trust), scraped by `scripts/harvest_tools.py`, deduped by content hash,
  license + plane classified, **NOT read by the descent until promoted**.
- **candidate_feeds** — `data/dev-intel/discovered_*.jsonl`, ideated candidates feeding the staged
  layer.

**Promotion boundary:** staged → core requires a permissive/vendorable license OR a service/technique
tag, a real source URL, dedupe-clean, and a vetting pass. Counts are **computed** (`registry_stats`),
never written into prose.
Source: `architecture/registry_layers.json` (`layers`, `promotion_boundary`, `harvester`).

**The primitive data plane's flexible shapes** are single-sourced in
`architecture/primitive_data_plane.json` (owner directive 2026-07-01): per-registry embedding **column
manifests** (a primitive may carry several embeddings, each over a different field with its own method +
dimensions — small dims for compact vocabularies like edges, larger for prose; deterministic
lexical-hash stays the keyless floor per the local-first law), table-shape policy per tier (normalized
truth / denormalized search projections / long-format staging), and affinity-boost path policies.
Consumers import these values; never re-type a dimension, column name, or path id (No Magic Values).
Source: `architecture/primitive_data_plane.json`.

---

## 4. The factory (how rows get made and staged)

The factory generates database-backed component candidates and stages them for load — high-volume rows
belong in JSONL staging + a Postgres/pgvector load plan, never thousands of hand-written static pages.
Source: `CLAUDE.md` §§"North Star", "Daily Factory Target".

**Required row families** a scalable batch emits or preserves: `source_record`, `normalized_object`,
`canonical_entity`, `object_entity_ref`, `dedupe_cluster`, `label_assignment`, `dimension_value`,
`object_embedding`, `index_record`, and `review_ticket` when risk warrants review.
Source: `CLAUDE.md` §"Required Row Families"; storage shape in
`docs/architecture/database-backed-component-store.md`.

**The primitive registry builder pipeline** has a machine contract:
`architecture/primitive_registry_builder_contracts.json` — builder
`scripts/primitive_registry_builder.py` (checker `scripts/check_primitive_registry_builder.py`),
quality promoter `scripts/primitive_quality_promoter.py`, operational load plan
`scripts/db/primitive_registry_operational_load_plan.py`, promotion gate
`scripts/check_primitive_registry_promotion_gate.py`, default output `.agent/primitive-registry`.
Candidate records must be generated from **real code/artifact inventory**, carry complete
I/O + provenance + proof + log + graph metadata, export search/vector rows, and stay candidate-only
(`serves_truth=false`) until the separate promotion gate accepts them.
Source: `architecture/primitive_registry_builder_contracts.json`.

**Report stages separately — never raw generated lines as active components:** generated candidate rows
vs unique staged rows vs candidate-table load readiness vs active promotion readiness vs committed
Postgres rows vs vector-search product readiness. Run `scripts.db.daily_promotion_readiness_plan` after
large generation.
Sources: `CLAUDE.md` §§"Required Row Families", "Promotion Boundary"; `_repos/_shared/STANDARDS.md`
§8 (Promotion Boundary).

**The fast path (the normal loop; do not start with full rebuilds):**
`validate.py <paths>` → `build_component_id_index.py --update <paths>` →
`build_catalog_pages.py --paths <paths> --update-index` → `validate.py --global-ref-check` →
`build_component_id_index.py --check-fresh`. Full release gates only on schema/vocabulary/broad-ref
changes.
Source: `CLAUDE.md` §"Default Fast Path".

**Capability-gap admission (what enters the registries).** Two-axis: a component must **lift**
(`pipeline_score − bare_model_score > 0`) **AND** the lift must be **structural/durable** (won't close
when the next model ships). Taxonomy single source: `scripts/eval/reason_codes.py`; sorter
`scripts/eval/durable_gap_harness.py`; cheap Stage-1 gap screen `scripts/acquisition/gap_screen.py`
(weighted to model-independent signals) before expensive Stage-2 confirm; research areas ranked by
`scripts/acquisition/research_queue.py` over `data/research-queue/areas.jsonl`. We build for the
**negative space** where base models lack capability.
Sources: `CLAUDE.md` §"Capability-Gap Framework"; `docs/concepts/capability-valleys.md`;
`architecture/substrate_layers.json` → `foundational_law.component_admission`.

---

## 5. Storage tiers (where the rows live and how they scale)

Three tiers, each fit for purpose, behind one `record_store` port
(`src/teleon/storage/record_store.py`, `architecture/storage_tier_policy.json`):

- **Config** — JSON in git (the `architecture/*.json` registries): reviewable, diffable, versioned.
- **Operational** — SQLite locally / **Postgres + pgvector** in the cloud (live records: staged tools,
  discovered tools, the component search index). The primitive data plane's operational shape is
  normalized truth tables (`primitive`, `primitive_family`, `variation`, `compatibility_route`,
  `template`, `template_slot`, `known_chain`, `receipt`, `affinity_event`, `negative_memory`) plus
  denormalized `search_card_wide` projections rebuilt from the normalized truth, plus a **long-format**
  `object_embedding` table (one row per embedding column per primitive — matches the CLAUDE.md
  `object_embedding` row family).
- **History** — the warehouse (CDC events, versions, audits) for scale to millions/billions.

Sources: `docs/concepts/system-overview.md` §4; `architecture/storage_tier_policy.json`;
`architecture/primitive_data_plane.json` → `storage_tiers`;
`docs/architecture/database-backed-component-store.md`; scale/lineage docs
`docs/architecture/hundred-million-component-infrastructure.md`,
`docs/architecture/component-cdc-versioning.md`, `docs/architecture/postgres-pgvector-bootstrap.md`.

---

## 6. The service-plane (small HTTP services behind the seams)

The frontends never hardcode a backend host; they call a same-origin **seam** that the showcase
rewrites to a real service resolved from `architecture/local_service_registry.json` (or an
`OH_SEAM_*_BASE` override in the cloud). The registry/catalog projection the frontends read is
`local_openhubforai_projection_api` (port 9423) behind the `/registry/...` seam; the full local port
map and the seam table live in the service registry + `scripts/showcase/server.py`.
Sources: `architecture/local_service_registry.json`; `docs/INTEGRATION-BIBLE.md` §§1–2;
`_repos/_shared/ARCHITECTURE-MAP.md` §"The seams". (The full seam table is in `_repos/shared-backend-components/context/edges.md`.)

---

## 7. The code graph (grep-as-graph over the substrate's own code)

`scripts/codegraph.py` fuses two AST graphs into ONE strength-ranked model and answers "I'm about to
change X — what strong connections must I audit?": a **FILE layer** (`scripts/code_graph.py`,
module→module import edges, weight = symbols crossing the boundary) and a **SYMBOL layer**
(`scripts/symbol_graph.py`, call+inherit edges, weight = distinct call sites, confidence = exact|name).
Resolution is confident-only — ambiguous/builtin-shadow calls are dropped and counted, never guessed —
so the ranking is trustworthy. `--audit` ranks neighbors; `--emit` writes the bounded
`docs/context/codegraph.generated.{json,md}` (never hand-edited); `--self-test` is a registered proof.
The change-audit protocol: audit strong connections **before AND after** editing a `.py`
file/function/class/method and update load-bearing neighbors in the same change.
Sources: `scripts/codegraph.py` (docstring); `docs/codex/codegraph-change-audit-protocol.md`;
`CLAUDE.md` §"Code-Graph Change Audit"; `_repos/_shared/STANDARDS.md` §5.

---

## 8. The two deterministic-naming planes (why grep-as-graph is exact)

Every defined thing gets a globally-unique, location-derived, meaning-bearing name; uniqueness lives IN
the name so the code graph resolves by name with zero ambiguity. Two planes, one law:

- **CODE plane (pyprefix)** — `py_<kind>__<file>__<scope>__<name>` (kind ∈
  class·function·method·const·instance·var·arg·local; dunders exempt). Engine `scripts/pyprefix.py`;
  law `docs/codex/ai-first-naming-and-graph-spec.md`; migration manifest
  `architecture/pyprefix_migration.json`; gates `check_pyprefix_conformance.py` +
  `check_pyprefix_methodology.py` (a migrated path stays 100% conformant, never drifts back).
  New/generated code follows the scheme from the first draft
  (`architecture/teleon_codegen_contracts.json`). The `src/teleon/registry/port.py` symbols above show
  the scheme live (`py_const_src_teleon_registry_port__CATALOGS`, etc.).
- **DATA plane (canonical id single source)** — generated ids/records are minted ONLY by
  `src.teleon.experiments.ids` (`canonical_id = "{prefix}-{sha256(canonical_bytes)[:16]}"`; Baltor via
  the `src/baltor/experiments/ids.py` shim). Version lives in `schema_version` METADATA — never in a
  name or id (no `.vN`, no `@N`; external `@N` ids are moved into metadata on intake). Direct
  `import hashlib` in `src/**` is the drift signal — the legacy sites in
  `architecture/canonical_id_migration.json` ratchet DOWN, enforced by
  `scripts/check_canonical_id_single_source.py` (a NEW site fails; a migrated file leaves the baseline
  same-change). Never truncation-only.

Sources: `CLAUDE.md` §§"Deterministic Global Object Naming", "ID And Hash Discipline";
`docs/codex/ai-first-naming-and-graph-spec.md`; `_repos/_shared/STANDARDS.md` §§2–3;
`architecture/pyprefix_migration.json`; `architecture/canonical_id_migration.json`.

---

## 9. Current state (partial vs live — from the systems-layer map)

`architecture/substrate_layers.json` records the substrate's layers with a `status` each (the file is
authoritative; do not trust prose over it — proof: `scripts/check_substrate_layers.py`):

- **computational_genome / Primitive Registry** — `partial` (P2). The 7-primitive model + a code-genome
  index of our code exist; the finer ~25 atomic ops as a first-class registry + per-software
  decomposition is the gap. Assets: `architecture/fundamental_primitives_taxonomy.json`,
  `scripts/primitives`, `src/teleon/knowledge/code_genome.py`.
- **infrastructure_registry** — `partial` (P1). Providers + pricebook + topology exist; unified
  per-provider deployment-economics metadata is the gap. Assets: `architecture/deploy_topology.json`,
  `execution_backend_pricebook.json`, `inference_lane_profiles.json`.
- **software_relationship_graph** — `partial` (P2). GitHub/tool harvesting + repo-similarity + a
  registry dependency graph exist; cross-ecosystem co-occurrence stats at scale is the gap.
- **human_behavioral_registry** — `partial` (P3). Intervention heuristics + session capture exist;
  mining repeated human workflows into a registry is the gap.
- **ai_waste_engine** — **`live`** (P1). This IS AIDevObserver + economics + inefficient-pipeline
  archetypes (see `_repos/aidevobserver/context/`).
- **universal_adapter_factory** — `partial` (P2). `adapter_factory.from_openapi(spec)` already turns an
  OpenAPI spec into one typed component per endpoint; Docker/Python-package factories are the gap.
  Asset: `src/teleon/components/adapter_factory.py`.
- **capability_futures** — `deferred` (P4). Predictive substrate exists; the market is deferred by
  design (win one vertical first).
- **existing_systems_registry / "this already exists, don't build it"** — `partial` (P1). The
  reinvention guard + federation + tool harvesting + a no-reinvention rubric implement the decision
  engine; a comprehensive existing-systems corpus is the gap. Asset:
  `src/teleon/registry/reinvention_guard.py`.

The binding law over all of it (from `foundational_law`): **DEPTH BEFORE BREADTH** — every new layer
must serve the ONE vertical being proven to a paying customer; 7 of 8 layers already exist, so the move
is **reconcile + close-gap, not build-new** ("this already exists, don't rebuild it" is the highest-ROI
decision). Run `scripts/check_substrate_layers.py`, `scripts/codegraph.py --audit`, and the reinvention
guard before building any "new" layer.
Source: `architecture/substrate_layers.json` (`layers`, `foundational_law`); `CLAUDE.md`
§"The Foundational Law".

---

## 10. Pointers to the detailed docs

- Taxonomy: `docs/concepts/component-taxonomy-and-stages.md`, `docs/concepts/layers.md`,
  `docs/concepts/system-overview.md`, `docs/concepts/capability-valleys.md`.
- Registry/store: `docs/architecture/database-backed-component-store.md`,
  `architecture/registry_ontology.json`, `architecture/registry_layers.json`,
  `architecture/primitive_data_plane.json`, `src/teleon/registry/port.py`.
- Factory + gates: `architecture/primitive_registry_builder_contracts.json`,
  `scripts/eval/reason_codes.py`, `scripts/eval/durable_gap_harness.py`, `CLAUDE.md`
  §§"Default Fast Path", "Required Row Families", "Daily Factory Target".
- Storage/scale: `architecture/storage_tier_policy.json`,
  `docs/architecture/hundred-million-component-infrastructure.md`,
  `docs/architecture/component-cdc-versioning.md`.
- Code graph + naming: `scripts/codegraph.py`, `docs/codex/codegraph-change-audit-protocol.md`,
  `docs/codex/ai-first-naming-and-graph-spec.md`, `architecture/pyprefix_migration.json`,
  `architecture/canonical_id_migration.json`.
- Systems-layer map + law: `architecture/substrate_layers.json`,
  `docs/strategy/computational-substrate-and-foundational-law.md`.
- Cross-component contracts: `_repos/shared-backend-components/context/edges.md`, `_repos/_shared/ARCHITECTURE-MAP.md`,
  `_repos/_shared/STANDARDS.md`.
