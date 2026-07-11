# Browser Report → Primitive Candidates Pipeline

> How a read-only browser session becomes governed, reusable **primitive candidates** — capture → report →
> candidates → gates → registry — with every stage `candidate=true, serves_truth=false` and evidence-linked back to
> source spans. Nothing here promotes itself; the LLM/browser PROPOSES, the deterministic gates DISPOSE.

## The stages

```
 web surface                                                            registry
     │                                                                     ▲
     ▼                                                                     │
[1 capture] ─► [2 session report] ─► [3 candidate primitives] ─► [4 gates] ─┘
 receipts +       tabs + tab graph      typed candidate rows      security · lift ·
 CapturedArtifact  + opportunity seeds  (contracts, edges,         dedupe · source/
 (digests, no      (api/form/state/…)   examples, proof reqs)      license · promotion
 raw body)
```

1. **Capture** — a `browser_control` adapter drives the session read-only. Every command emits a
   `browser_action_receipt`; each visited page becomes a harness **CapturedArtifact** (digest + bounded redacted
   text + extracted links/forms/api-refs/downloads + detectors — never the raw body). Engine:
   `scripts/primitive_browser_control_harness.py` (the ONLY capture front-end).
2. **Session report** — `scripts/browser_session_report.py:build_session_report(artifacts, clock=…)` reconstructs
   ONE `browser_session_report`: per-tab state, the **tab graph** (opener edges, cross-origin transitions, popups,
   duplicate tabs), the network/screenshot/dom/form/download surfaces, `side_effect_attempts`
   (detected-but-never-executed), and the **candidate-primitive opportunity SEEDS** the session implies. Adapters
   reach this via `BrowserAdapter.build_session_report()` / `build_tab_graph()`.
3. **Candidate primitives** — each seed expands into a fully-typed candidate row:
   - a page with an **OpenAPI/GraphQL** reference → an **`api_discovery_report`**
     (`schemas/api_discovery_report.schema.json`) → `api_endpoint_primitive` · `request_schema_validator` ·
     `response_normalizer` · `error_mapper` · `mock_server` · `contract_test`;
   - **forms** → `form_field_mapper` · `form_validation_error_parser` · `safe_submit_gate`;
   - **login/side-effect/captcha** markers → `page_state_classifier` · `login_state_detector` ·
     `side_effect_gate` · `captcha_present_detector` (detect only — never solve);
   - **downloads** → `document_ingestor` · `table_extractor`.
   Any LLM step (classify/decompose/schema-gen/verifier-gen) is recorded as an **`llm_browser_task`**
   (`untrusted=true`) — a proposal, not truth. IDs are `canonical_id(...)`; version lives in `schema_version`.
4. **Gates** (a candidate may not become `serves_truth=true` until ALL pass):
   - **security** — `scripts/primitive_security_gate.py` on any generated/self-written helper body
     (`docs/SECURITY_GATE_FOR_PRIMITIVES.md`); agent-written code is **quarantined** until it passes;
   - **lift + durability** — the two-axis admission (`scripts/eval/durable_gap_harness.py`): a primitive must lift
     over the bare model AND the lift must be structural;
   - **source / license / provenance** — real source URL, permissive/vendorable license, trust tier, evidence refs;
   - **dedupe** — content-hash + fuzzy clustering so daily batches don't collapse;
   - **promotion** — `scripts.db.daily_promotion_readiness_plan` (no open review tickets, no placeholder
     embeddings, CDC/revocation for volatile public facts).
5. **Registry** — a promoted primitive enters the federation behind the uniform port
   (`src/teleon/registry/port.py`, `list/lookup/search/explain`). The substrate returns pointers + shapes;
   `serves_truth=false` at this layer regardless (a consuming PRODUCT governs truth).

## Row families each batch preserves

`source_record` · `normalized_object` · `canonical_entity` · `object_entity_ref` · `dedupe_cluster` ·
`label_assignment` · `dimension_value` · `object_embedding` · `index_record` · `review_ticket` (on risk). Report
generated / staged / load-ready / promotion-ready / committed / search-ready as **distinct counts** — never report
raw generated lines as active components.

## What this pipeline does NOT do

- It never submits a form, activates a side-effect control, or bypasses a login/captcha/paywall — those are
  **enumerated as candidates** (`safe_submit_gate`, `side_effect_gate`), never executed by the capture layer.
- It never stores raw bodies or secrets — digests, bounded redacted text, and extracted structured units only.
- It never lets a model flip `serves_truth`. Generation is not promotion (CANDIDATE-TRUTH-BOUNDARY law).

## Ownership note

`browser_session_report` / `tab_state` / `browser_primitive_candidate` schemas and the
`browser_report_to_primitive_candidates` expander are owned by the report/candidate component. `browser_control`
(this package) owns the driver-neutral CAPTURE + the `browser_action_receipt` / `browser_control_capability` /
`api_discovery_report` / `llm_browser_task` schemas, and reuses the report builder rather than duplicating it.
