# /workflows /baltor-adjacent-workflow-wrapper-graph (STAGED — focused increments, not one Workflow)

**Owner stance (resolves the "consolidate the sprawl" tension):** adjacent/redundant workflows are an ASSET —
*if* each is registered as a **capability-equivalent implementation behind a common wrapper/selector** with
**numeric, policy-driven fallback** instead of hard-coded branching. The goal is not to delete redundancy; it
is to prevent **unmanaged** duplication.

```
Bad redundancy:  two workflows, same job, different contracts, hidden assumptions, no shared wrapper.
Good redundancy: many workflows implement ONE capability contract behind ONE wrapper, with numeric
                 priority/health/fallback/shadow/canary/compare policies. The caller never knows which ran.
```

## ADJACENT WORKFLOW WRAPPER CLAUSE (carry in the North Star loop)
Adjacent/redundant workflows are allowed **when wrapped**. A workflow is valid redundancy only if it implements
the **same capability slot + same output contract**, is in the workflow/provider graph with **numeric priority/
fallback/shadow/canary edges**, has a **local equivalent if external**, and passes **output-normalization +
redteam** proofs. The wrapper chooses the primary by policy and may fall back to an adjacent workflow by policy.
**Unwrapped redundancy is architectural drift.**

## Architecture
```
CapabilityTask.v1 → CapabilityWrapper → WorkflowSelectionGraph → WorkflowExecutionProvider
                  → OutputNormalizer → ContractValidator → DecisionReceipt
```
- **Wrapper owns:** selection · fallback · normalization · contract validation · telemetry · cost scoring ·
  error handling · redteam blocking. It does NOT implement business logic and does NOT publish truth.
- **Implementation owns:** doing the work. It does NOT own truth promotion, consumer schema, fallback policy,
  tenant policy, or provider priority.
- **Caller receives the stable output contract only** (e.g. `BrowserRunResult.v1`), never a vendor-specific shape.

## Capability-equivalence contract (every adjacent workflow must prove)
same input contract · same output contract · same idempotency semantics · same tenant-scope behavior · same
no-truth-bypass rules · same telemetry fields · same failure envelope. If it can't prove these, it is a
**different** capability, not valid redundancy.

## Fallback modes (local, deterministic)
`primary_only` (production TRUTH paths) · `fallback_on_failure` (infra paths) · `fallback_on_policy`
(tenant/residency/security block) · `shadow` (run adjacent, do NOT use its output) · `parallel_compare`
(store both) · `weighted_canary` · `race_first_valid` · `local_emulator` (offline) · `provider_unavailable`
(structured result, never crash). Defaults: truth → primary_only; infra → fallback_on_failure; new provider →
shadow; migration → parallel_compare; offline → local_emulator; ensemble only when a deterministic validator
picks the final output.

## Numeric, graph-based selection (NOT display strings)
Reuse the provider graph's numeric codes. Workflow status codes (100 disabled … 300 candidate … 500
active_local … 700 preferred … 900 quarantined) + edge type codes (1000 IMPLEMENTS_CAPABILITY · 1100 CAN_REPLACE
· 1200 CAN_SUPPLEMENT · 1300 CAN_FALLBACK_TO · 1400 CAN_SHADOW · 1500 CAN_PARALLEL_COMPARE · 1600 CAN_CANARY ·
1700 SUPERSEDES · 1800 BLOCKED_BY_POLICY · 1900 REQUIRES_LOCAL_EQUIVALENT · 2000 REQUIRES_HUMAN_APPROVAL). Edges
carry priority/reliability/latency/cost/safety weights + policy_conditions (e.g. `same_output_contract`,
`tenant_policy_allows`, `health_status_ok`). Runtime branches on node_id/contract_id/codes/weights/policy —
never on `"Playwright"`/`"candidate"`/`"fallback"`.

## Staged increments (each = schema/code/proof/docs together; flywheel green)
- **PART 1–3 contracts + graph:** `schemas/workflows/{CapabilitySlot,WorkflowNode,WorkflowEdge,
  WorkflowSelectionGraph,WorkflowSelectionPolicy,WorkflowSelectionDecision,WorkflowExecutionResult,
  WorkflowFallbackReceipt,WorkflowComparisonRun,WorkflowOutputNormalizationReport}.v1` (register in
  contract_registry) · `architecture/{workflow_status_codes,workflow_edge_type_codes,workflow_selection_graph}.json`.
  Slots incl: browser_source_capture · source_discovery/ingestion · document_parsing · structured/unstructured
  decomposition · fact_verification · conflict_reconciliation · fragility_refresh · optimization_candidate_gen ·
  context_consumption · memory_recall · native_export · cloud_function/k8s_job/managed_venv execution ·
  leaf_convergence · temporal_graph_projection · observability_export · code_review · sandbox_execution.
- **PART 4–6 wrapper + normalizer:** `src/baltor/workflows/{capability_wrapper,workflow_selector,output_normalizer,
  workflow_receipts}.py` — execute through the EXISTING WorkerRouter/ExecutionBackendSelector; normalize internal
  outputs to the stable contract; record decision + fallback receipt; block contract-failing outputs.
- **PART 7 compare:** `workflow_compare.py` (shadow/parallel/canary/primary-vs-fallback-audit → same_contract,
  same_source_handles, same_claim_status, changed_fields, scores, safe_to_promote).
- **PART 8 bridge (do NOT duplicate the provider graph):** a WorkflowNode is BACKED BY a ProviderNode /
  ExecutionBackendProvider / ToolProvider; `check_workflow_provider_graph_bridge` (provider label change doesn't
  break workflow selection; candidate workflow requires local equivalent; numeric edges drive fallback).
- **PART 9 redteam** `check_adjacent_workflow_wrapper_redteam`: adjacent workflow w/ DIFFERENT output contract
  selected · fallback emits CanonicalFact/ContextResponse · browser/LLM fallback bypasses VerificationGate ·
  selection by display string · candidate w/o local equivalent · shadow output used as authoritative · parallel
  compare duplicates side effects · tenant-blocked selected · hard-coded fallback list bypasses graph — all FAIL.
- **PART 10–11 API/UI/docs:** `/api/workflows/{capabilities,graph,decisions,fallbacks,comparisons}` (+ local
  deterministic test endpoints) · `/workflows` page (projection-only) · `docs/workflows/*`.

## Acceptance
Adjacent workflows only behind wrappers · slots + graph + numeric codes exist · wrapper selects primary by
policy + falls back to equivalent on failure · shadow/parallel/canary work · output normalization works ·
provider-graph bridge works · no display-string selection · candidate requires local equivalent · redteam fails
safely · API/UI exist · offline demo + flywheel GREEN.

*Warrant: clear owner intent ("OK with adjacent/redundant workflows as long as there's a wrapper that chooses
the main one and falls back to an adjacent one with the same capabilities"). Bridges to, not duplicates, the
numeric provider graph (prompts/baltor-numeric-provider-selection-graph.md). Wrapper never publishes truth;
fallback only to same-contract equivalents.*
