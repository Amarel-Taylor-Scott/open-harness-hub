# P2 — Catalog Implementation-Ref Integrity (honest catalog)

Status pass over the advisory drift in `scripts/validate.py`: dangling
`implementations[].path` callables, stale manifest-bridge records, and
unregistered repeated literals. Goal: every catalog impl ref that this agent can
honestly back **resolves**; everything left unbacked is honestly flagged as
not-yet-built (never a false claim that a module exists).

Date: 2026-06-11. Owner-scope for this pass: `catalog/` manifests, new thin
modules under `scripts/db/` and `scripts/processors/platform/` only, plus the
`scripts/_config.py` setting registries and the `scripts/audit_context_storage.py`
audit that reads them. Out of scope (other agents own): `scripts/eval/`,
`scripts/deploy/`, `src/teleon/`, identity/registry/events/runtime/foundry
sources, and `scripts/validate.py` itself.

## Before / after

`python3 scripts/validate.py` exited **0 both before and after** (the impl-path
findings are advisory warnings, not failures, unless `--check-impl-paths` is
passed). The advisory drift changed as follows:

| Advisory finding | Before | After |
|---|---:|---:|
| Dangling in-repo `implementations[].path` callables | 82 | 71 |
| Database-backed catalog drift (stale manifest-bridge records) | 16 | 0 |
| Unregistered repeated setting literal groups (backend) | 4 | 0 |
| Unregistered repeated setting literal groups (model) | 2 | 0 |

The 11-ref reduction (82 → 71) is exactly the set this agent backed with real
modules. The 71 that remain are out-of-this-agent's-code-scope and are left as
the repo's documented not-yet-built convention (see "Deliberately left honest").

Note: the prompt's context estimated "~7" dangling refs; the actual count was
**82**. The bulk are `scripts.processors.*` subpackage paths declared by the
retrieval-taxonomy / clinical / deliver / memory / cache seeding (the package
`scripts/processors/__init__.py` exists, so these paths are in-repo and get
checked, but the subpackages were never created).

## How `implementations[].path` is validated (read first)

`scripts/validate.py::check_impl_paths` only checks entries with
`kind: callable` whose first dotted segment names a package/module that lives in
this repo (`_in_repo_top_levels()` — structural, not a hard-coded list).
`_callable_path_resolves` uses `importlib.util.find_spec` on the longest module
prefix (treating the final segment as a callable attribute) — side-effect free,
never imports. A dangling in-repo callable is a **fatal** error only under
`--check-impl-paths`; otherwise it is collected as a "not-yet-built stub"
warning, which is why the build stays green. The repo's own `planned -> real`
convention (commit `af45bad3`) is to declare the `callable` path up front and
make it real later — the path is an intent declaration the validator surfaces as
not-yet-built, not a false claim.

## Fixes — 11 refs now resolve (real thin modules, option (a))

Every module below does a real, deterministic thing, carries a `--self-test`,
and reuses existing engine/SQL/config rather than re-implementing or stubbing.

### `scripts/db/cdc_event_emitter.py` → `emit_cdc_events`
Backs `tool/cdc-event-emitter`. The manifest declares a version-PAIR input shape
(each JSONL line pairs previous+new `component_version` for one `component_id`).
The real CDC computation (canonical hashing, change-type detection, changed-field
diff, index-record deltas, review tickets, `\copy` load SQL) already lives in
`scripts.db.component_cdc_plan.create_component_cdc_plan`. This module is a THIN
adapter: it splits the version-pair file into the two side-by-side files that
engine consumes, delegates, and re-shapes the summary into the manifest's return
keys (`change_events_emitted`, `index_deltas_emitted`, `review_tickets_emitted`,
`change_type_counts`, `files`). The `high_risk_review_threshold` param is honored
(threshold-based review candidate count, computed via the engine's own
`_changed_fields`). No hashing/diff logic duplicated (lossless single source).

### `scripts/db/object_embedding_batch_loader.py` → `load_embeddings`
Backs `tool/object-embedding-batch-loader`. Reads inline-`embedding` rows,
validates each vector's dimension against the canonical schema dimension
(`scripts._config.DEFAULT_EMBEDDING_DIMENSIONS` → `vector(384)`, single source),
routes incomplete / dimension-mismatched rows to a rejected JSONL sidecar with
reasons, and emits deterministic UPSERT SQL on the table's
`UNIQUE (subject_id, subject_type, embedding_model, text_hash)` constraint (the
natural key the manifest names). Distinct from `pgvector_embedding_load_plan`
(worker-output shape, primary-key conflict); the low-level SQL value/vector
helpers are imported from it (lossless reuse). `text_hash` defaults to a content
hash of `text`; `embedding_id` is a full-hash-derived id (never truncation-only).

### `scripts/processors/platform/` (package) → 9 `run()` callables
Backs the nine `processor/*` Platform-actions manifests (`cache-write`,
`create-data-store-view`, `memory-write`, `persist-object-store`,
`persist-pgvector`, `persist-postgres`, `persist-run-store`, `register-component`,
`update-dashboard-widget`). Each `run()` takes the manifest's named inputs and
returns the manifest's named outputs. These are deterministic **planners**: they
compute a content-addressed description of the write that WOULD be persisted
(`planned: True`, `content_hash`, a natural-key/derived id) and never open a
network/database/object-store connection — the same posture as the
`scripts/db/*` load planners, and honest about not touching live infra.
Shared hashing/id/plan-envelope logic lives once in `_platform_base.py`
(`content_hash` reuses the established `sha256:`-over-canonical-JSON convention
from `component_cdc_plan`); the nine action modules stay thin. `register-component`
honestly marks its output `promotion_state: candidate` (CLAUDE.md promotion
boundary — a run's output never auto-activates).

All 11 manifests pass even in HARD mode:
`validate.py --global-ref-check --check-impl-paths <the 11>` → exit 0, all valid.

## Fixes — manifest-bridge staleness (16 → 0)

The 16 stale entries were pre-existing: catalog YAMLs were newer than the bridge
output `dist/catalog-manifest-bridge/manifest_import_records.jsonl`. Refreshed by
running the documented regenerator `python3 -m scripts.db.catalog_manifest_bridge`
(defaults to all manifests, writes the dist bridge records; self-test green
first). No catalog manifest was edited. Drift cleared to 0.

## Fixes — unregistered repeated literals (6 groups → 0)

No-magic-values: a value that recurs gets one definition in `scripts/_config.py`
and is recognized by the audit. The 6 flagged groups live in files this agent
does not own as source (`scripts/validate_compose.py`, `architecture/*.json`,
`fly/*.toml`, `scripts/check_handoff_docs_freshness.py`, `scripts/model_gateway.py`,
a routing doc), so the honest fix is to **register their canonical identity** in
`_config.py` (the single source of truth the audit reads), not to rewrite those
files.

- `gpt-3.5-turbo` (model, ×2; `model_gateway.py` default + routing doc) →
  added to `REGISTERED_EXAMPLE_MODEL_VALUES` as `CHATANYWHERE_DEMO_MODEL`
  (env-overridable demo-lane default), exactly like the existing `gpt-4o`/`llama3`.
- `vector.pgvector@v1` (backend, ×3; `external_capability_catalog.json`,
  `repo_replacement_matrix.json`) → it is an **adapter_id** (versioned capability
  provider ref) → added to `REGISTERED_COMPONENT_REF_IDS` as
  `PGVECTOR_RETRIEVAL_ADAPTER_ID` (`component_type: adapter`, `role: fallback_adapter`).
- `pgvector/pgvector:pg16` (container image), `https://github.com/pgvector/pgvector`
  (project URL), `Qdrant` (backend product name) → these are concrete external
  backend identifiers, not logical backend-choice keys and not load-plan terms,
  so they get a new self-documenting registry `REGISTERED_BACKEND_INFRA_IDENTIFIERS`
  in `_config.py`, whose keys are folded into the audit's `REGISTERED_BACKEND_VALUES`.
- `CLAUDE-CODE.md` (model, ×2; `check_handoff_docs_freshness.py`) → a **false
  positive**: a handoff-doc filename matched by the `claude-` model regex. Fixed
  honestly in the audit by skipping quoted tokens ending in a doc/source file
  suffix (`NON_MODEL_FILE_SUFFIXES`) — a filename is never a model id. This does
  not weaken real model-literal detection.

`audit_hardcoded_settings()` after: `unregistered_repeated_model_literal_count = 0`,
`unregistered_repeated_backend_literal_count = 0`.

## Deliberately left as honest-planned (71 refs, NOT fixed)

These dangling `scripts.processors.*` callables fall **outside this agent's
code-ownership** (only `scripts/db/` and `scripts/processors/platform/` modules
were granted). Backing them would require creating modules in subpackages other
agents/areas own, or fabricating stubs that pretend to do work — both forbidden
(scope + evidence-driven/no-clone laws). They are already the repo's documented
not-yet-built convention: `validate.py` exits 0 and labels them "not-yet-built
stubs". They are intent declarations, not false claims. Breakdown:

| Cluster | Count | Example path |
|---|---:|---|
| `scripts.processors.retrieval.*` | 23 | `…retrieval.bm25_keyword_retrieve.run` |
| `scripts.processors.deliver.*` | 10 | `…deliver.deliver_webhook.run` |
| `scripts.processors.clinical.*` | 8 | `…clinical.icd10_code_grounder.run` |
| `scripts.processors.memory.*` | 6 | `…memory.memory_recall.run` |
| `scripts.processors.cache.*` | 4 | `…cache.cache_semantic.run` |
| `scripts.processors.connectors.*` | 3 | `…connectors.mcp_postgres_connector.run` |
| flat `scripts.processors.<name>` | 17 | `…doc_to_markdown_rag_ingest.run` |

Recommended follow-up (a future in-scope pass per subpackage): implement each as
a real thin processor with a `--self-test`, mirroring the platform package, or —
if a component is genuinely abandoned — remove the manifest under an owner
decision. Do not switch `kind` away from `callable` to dodge the check; that
would be dishonest (it would assert a shell/http impl that also does not exist).

## Found but NOT fixed — pre-existing duplicate component ids (owner decision)

Rebuilding the component-id index (`build_component_id_index.py`, needed because
the cache was globally stale: "manifest path set changed") surfaced **4 duplicate
`id` collisions** — each an older `catalog/processors/<category>/` manifest and a
newer `catalog/processors/retrieval/` manifest sharing one id with *different*
impl paths:

- `processor/recursive-character-chunker` — `chunk/recursive-character.yaml` vs `retrieval/recursive-character-chunker.yaml`
- `processor/cross-encoder-reranker` — `rerank/cross-encoder.yaml` vs `retrieval/cross-encoder-reranker.yaml`
- `processor/hyde-query-expander` — `query/hyde.yaml` vs `retrieval/hyde-query-expander.yaml`
- `processor/page-aware-chunker` — `format-convert/page-aware-chunker.yaml` vs `retrieval/page-aware-chunker.yaml`

These are **pre-existing** (none modified by this pass) and choosing which
manifest is canonical (or renaming an id) is a product-structure decision that
the change-verification contract says must not be a unilateral single-agent call.
`build_component_id_index.py` (full build) exits 1 while these exist; the prompt's
gate `--check-fresh` is **green (exit 0)** because it checks path-set/mtime
freshness, not duplicate-freeness. Flagged here for an owner/curator decision.

## Verification (all green)

- `python3 -m py_compile` — all new/changed modules: **OK**.
- New-module `--self-test`, twice each (deterministic):
  - `scripts.db.cdc_event_emitter` — PASS, PASS
  - `scripts.db.object_embedding_batch_loader` — PASS, PASS
  - `scripts.processors.platform.{cache_write, create_data_store_view, memory_write,
    persist_object_store, persist_pgvector, persist_postgres, persist_run_store,
    register_component, update_dashboard_widget}` — PASS, PASS (each)
- `python3 scripts/validate.py` — exit **0**, "all manifests valid"; 71 advisory
  not-yet-built warnings (down from 82); 0 manifest-bridge drift; 0 setting drift.
- `validate.py --global-ref-check --check-impl-paths <the 11 backed manifests>` —
  exit **0** (impl refs genuinely resolve, even in hard mode).
- `build_component_id_index.py --check-fresh` — `fresh: true`, exit **0**.
- Regression: `component_cdc_plan --self-test`, `settings_registry_export`,
  `import scripts.model_gateway`, `import scripts.run_pipeline` — all OK after the
  `_config.py` additions.

## Files changed by this pass

New: `scripts/db/cdc_event_emitter.py`, `scripts/db/object_embedding_batch_loader.py`,
`scripts/processors/platform/__init__.py`, `scripts/processors/platform/_platform_base.py`,
and the 9 platform action modules; this doc.
Edited: `scripts/_config.py` (registries: example model, adapter component-ref,
backend-infra identifiers, loader/CDC output-filename constants),
`scripts/audit_context_storage.py` (register the new backend-infra set; skip
filename false positives in model-literal detection).
Regenerated (dist artifacts): `dist/catalog-manifest-bridge/*`,
`dist/catalog-component-ids.json`. No catalog manifest YAML was edited.
