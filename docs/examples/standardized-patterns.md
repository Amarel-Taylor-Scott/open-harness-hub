# Standardized Patterns — The Canonical Example Per Shape

This page is the **field guide**: for the recurring SHAPES the Baltor Context Engine
builds, it names the ONE existing implementation that is the canonical standard
example to copy. When you build a new component of a given shape, open the example,
follow it, and prove it with a `check_*.py` of the same family.

This is a META index over code that already exists — it introduces no new runtime,
bus, worker, gateway, optimizer, or parser. Every path below is REAL (verified on
disk at authoring time) and every proof command names a real `scripts/check_*.py`.

Single sources this page points into:

- Pattern definitions: `architecture/pattern_registry.json` (the canonical 25).
- Standards (the contract a template/check enforces): `architecture/standard_catalog.json`.
- Templates (the scaffold a standard generates from): `architecture/template_catalog.json`.
- Routines (the named blessed way to do X): `architecture/routine_library.json`.
- Per-pattern roll-up: `architecture/pattern_maturity_matrix.json`.
- Full-stack honesty proof: `scripts/check_pattern_standards_full_stack.py --self-test`.

Verify everything here with `python3 scripts/check_standardized_examples.py --self-test`
(asserts every cited example path exists and every cited proof is a real `check_*.py`).

---

## 1. CFPB source adapter / ingestion — `source_adapter_pattern` + `ingestion_sync_pattern`

- **Canonical example:** `scripts/ingest/sanctions_feed_live.py`
- **pattern_id:** `source_adapter_pattern` (also exercises `ingestion_sync_pattern`)
- **standard_id:** `standard.source_adapter.v1`
- **template_id:** `ingestion.source_adapter.v1`
- **proof command:** `python3 scripts/check_multi_source_ingestion.py --self-test`
- **why it is the standard:** It is the live oracle-source adapter that turns a fetched
  upstream into the SAME governed artifact chain every other source must produce
  (`source_record → source_field → atomic_fact / narrative_allegation`), with
  content-addressed ids (no wall-clock), tenant/scope/lineage on every artifact, and an
  explicit NON-CONSUMABLE boundary when the parser is unavailable. New ingesters copy
  its shape; the proof asserts determinism and the structured-vs-narrative split across
  multiple sources.

## 2. `decompose_structured` atomic-fact routine — `processor_harness_pattern`

- **Canonical example:** `scripts/ingest/decompose_structured.py`
- **pattern_id:** `processor_harness_pattern`
- **standard_id:** `standard.processor.v1`
- **template_id:** `worker.command_handler.v1` (processor handler scaffold)
- **proof command:** `python3 scripts/check_cfpb_decompose_via_harness.py --self-test`
- **why it is the standard:** It is the canonical finer-grain decomposition routine —
  a structured `SourceArtifact` record becomes promotion-eligible `atomic_fact`
  artifacts (free text becomes held-out allegations, never facts). It runs as pure
  logic inside the harness; the routine `structured_record_to_atomic_facts` in the
  routine library points here. The proof asserts decomposition happens through the
  harness (so failures are enveloped) and that structured vs narrative grain is honored.

## 3. Durable worker claim-loop — `worker_claim_loop_pattern` + `durable_command_pattern`

- **Canonical example:** `scripts/flywheel_worker.py` (claim loop) over `scripts/durable_store.py` (the one durable store)
- **pattern_id:** `worker_claim_loop_pattern` (built on `durable_command_pattern`)
- **standard_id:** `standard.worker_claim_loop.v1`
- **template_id:** `worker.command_handler.v1`
- **proof command:** `python3 scripts/check_durable_worker_parallel.py --self-test`
- **why it is the standard:** It is the stateless claim → handler → ack/nack loop over
  the single SQLite durable store. N workers against one queue share work with NO
  double-processing (BEGIN IMMEDIATE + busy_timeout serialize claims across processes);
  retries go to a DLQ, never infinite. The proof runs more than one worker against one
  queue and asserts each job is processed exactly once.

## 4. API projection route — `api_projection_route_pattern`

- **Canonical example:** `scripts/api_context_handler.py`
- **pattern_id:** `api_projection_route_pattern`
- **standard_id:** `standard.api_projection.v1`
- **template_id:** `api.projection_route.v1`
- **proof command:** `python3 scripts/check_consumption_api.py --self-test`
- **why it is the standard:** It is a pure request handler `(method, path, body) -> (status, json)`
  so the route contract is testable WITHOUT a socket. It NEVER fabricates truth — it
  calls the proven consumption engine and returns its contract object — it is
  projection-only and emits no secret markers. The admin server delegates to it (MAIN
  wires the server). The proof drives the handler directly and asserts status + contract
  shape + no secret leakage.

## 5. The `/consume` UI projection page — `ui_projection_page_pattern`

- **Canonical example:** `web/baltor/consume.html`
- **pattern_id:** `ui_projection_page_pattern`
- **standard_id:** `standard.ui_projection.v1`
- **template_id:** `ui.projection_page.v1`
- **proof command:** `python3 scripts/check_consumption_ui.py --self-test`
- **why it is the standard:** It renders the CFPB Reg E correctness invariant by fetching the
  `/api/context/serve` projection and rendering ONLY — it computes, stores, and mutates
  no truth client-side, carries the explicit projection-only marker, hard-codes no
  secret/token, and shows held-out items separately from served truth. The proof asserts
  the page references only projection endpoints and carries no secret literal.

## 6. Provider candidate with a deterministic emulator — `capability_catalog_entry_pattern` + `dependency_emulator_pattern`

- **Canonical example:** `architecture/external_capability_catalog.json` (the `parser_manager` slot: `parser.stub@v1` emulator + `parser.docling@v1` / `parser.unstructured@v1` candidates)
- **pattern_id:** `capability_catalog_entry_pattern` (the slot card) + `dependency_emulator_pattern` (the stub)
- **standard_id:** `standard.provider_adapter.v1`
- **template_id:** `provider.adapter.v1`
- **proof command:** `python3 scripts/check_external_capability_catalog.py --self-test`
- **why it is the standard:** A 3rd-party capability cannot land without a slot card —
  category, the currently-wired adapter, a candidate primary external repo, fallbacks,
  I/O contract, contract proofs, license, and health. Crucially it carries a
  deterministic offline stub (`parser.stub@v1`) that satisfies the SAME port, so every
  proof and demo runs without network or secrets. Domain code depends on the slot, never
  the vendor. The proof keeps the catalog in sync and asserts each slot has a wired
  adapter or stub.

## 7. Optimization candidate / bake-off — `optimization_candidate_pattern`

- **Canonical example:** `scripts/runtime/optimization.py`
- **pattern_id:** `optimization_candidate_pattern`
- **standard_id:** `standard.optimization_candidate.v1`
- **template_id:** `worker.command_handler.v1` (candidate as a governed command)
- **proof command:** `python3 scripts/check_optimization_suite.py --self-test`
- **why it is the standard:** It runs the baseline → candidate → regression-gate →
  promote loop: a candidate context pack is measured against a frozen `BaselineSnapshot`
  for lift, a `RegressionGate` forbids answer-fact loss / held-out promotion / tenant
  leak / fabrication, and the optimizer PROMOTES only on measured lift + zero
  regressions, emitting a content-addressed `OptimizationReceipt`. Optimizations are
  admitted on evidence, never on vibes. The proof asserts promotion only on lift + zero
  regression and that a held-out item can never be promoted.

## 8. Reconciliation held-out warning — `reconciliation_decision_pattern` + `held_out_warning_pattern`

- **Canonical example:** `scripts/artifact_graph/reconciliation.py`
- **pattern_id:** `reconciliation_decision_pattern` (emits the `held_out_warning_pattern`)
- **standard_id:** `standard.reconciliation_decision.v1`
- **template_id:** `worker.command_handler.v1` (reconciler as a governed command)
- **proof command:** `python3 scripts/check_cfpb_reconciliation.py --self-test`
- **why it is the standard:** When sources disagree it produces a deterministic decision
  record (winner + reason + the recorded losers — never a silent merge) using explicit
  authority/recency rules, with a content-addressed decision id. When the loser still
  matters it attaches a held-out warning to the context pack so the consumer cannot
  mistake an uncorroborated claim for a certified fact. The proof asserts determinism and
  that the loser is recorded with a reason.

## 9. A review-pack entry — `review_pack_pattern`

- **Canonical example:** `scripts/make_review_pack.py`
- **pattern_id:** `review_pack_pattern`
- **standard_id:** `standard.review_pack.v1`
- **template_id:** `docs.section_page.v1` (review-pack section doc scaffold)
- **proof command:** `python3 scripts/check_review_pack_recorders.py --self-test`
- **why it is the standard:** When risk warrants review it assembles a review pack — the
  object, its sources, conflicts, and the proposed decision — content-addressed (no
  wall-clock in the id), with explicit risk reasons. An artifact with an open review
  ticket is NOT tenant-visible: the promotion boundary holds. The proof asserts the
  recorders capture the evidence and that an artifact with an open ticket cannot be
  promoted.

## 10. A section_maturity_matrix entry — `section_maturity_entry_pattern`

- **Canonical example:** `architecture/section_maturity_matrix.json` (e.g. the `source_adapters` section entry)
- **pattern_id:** `section_maturity_entry_pattern`
- **standard_id:** _(governance pattern; no standard card — tracked by the matrix proof)_
- **template_id:** _none (the matrix is the single source; entries are added in place)_
- **proof command:** `python3 scripts/check_section_maturity_matrix.py --self-test`
- **why it is the standard:** Each capability section has exactly one matrix entry
  tracking its place on the m0..m10 ladder with `owner_folder`/`owner_module`,
  contracts, ports, adapters, registries, `proof_scripts`, `ui_pages`, `api_routes`,
  `docs`, and `known_gaps`. It is the single source of "how done is X" — a status may
  not be claimed without a registered proof, and a section may not lack an owner. The
  proof enforces exactly that.

---

## How to use this page

1. Find the shape you are about to build in the list above.
2. Open the canonical example and copy its structure.
3. Generate the scaffold from the named `template_id` with
   `python3 scripts/generate_from_template.py --template <id> ...` (where a template exists).
4. Prove it with a `check_*.py` of the same family (the proof command above is the model).
5. Register it where the standard says (contract registry / section maturity matrix /
   capability catalog) — MAIN folds shared-manifest edits.

If a shape you need is NOT here, it is either a `candidate` pattern (see
`architecture/pattern_registry.json`) or an unstandardized repetition the miner should
flag — run `python3 scripts/pattern_miner.py` and check `.agent/pattern_miner_report.json`.
