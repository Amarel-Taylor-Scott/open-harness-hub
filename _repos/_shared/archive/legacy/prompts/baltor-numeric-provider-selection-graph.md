# /workflows /baltor-numeric-provider-selection-graph (STAGED — build as focused increments, not one Workflow)

Replace brittle hard-coded string logic for providers/candidates/fallbacks/priorities/alternatives with a
**configuration-backed numeric provider graph**. Triggered because a proof broke when a provider display string
changed `"LLMLingua"` → `"LLMLingua / LLMLingua-2"`. That class of break must not recur.

> **Build discipline:** ship focused, proven increments (Agent subagents / direct edits), NOT a single
> multi-phase Workflow (it stalls on its last agent — recorded lesson). Each part below lands + proves green on
> its own; the flywheel stays green throughout.

## NUMERIC PROVIDER GRAPH CLAUSE (carry in every related prompt)
Do not use provider **display strings**, **role strings**, or **hard-coded fallback arrays** as runtime control
logic. Providers/tools/runtimes/functions/models/fallbacks are **ProviderNode + ProviderEdge** graph data with
**numeric status codes**, **numeric edge types**, and **numeric priority/score weights**. Runtime selection
receives a **ProviderSelectionGraph configuration object**. Cloud providers are **peer candidate nodes** behind
**cloud-agnostic** capability slots; local emulators are **required equivalents**. Proofs check **contracts,
graph relationships, and behavioral invariants — never exact provider names**.
- Display strings are for humans. Stable IDs are for references. **Numeric graph edges are for priority/
  fallback/replacement.** Configuration objects drive runtime decisions.

## DONE (2026-06-06 — first increment, green @ flywheel 308)
- `architecture/provider_status_codes.json` (10 disabled · 20 research · 30 candidate · 40 emulated · 50
  active_local · 60 active_external · 70 preferred · 80 deprecated) + `provider_edge_type_codes.json`
  (100 IMPLEMENTS_SLOT … 120 ALTERNATIVE_TO … 130 SUPERSEDES … 140 SHADOW_OF … 150 CANARY_OF …
  160 FALLBACK_AFTER_FAILURE … 170 BLOCKED_BY_POLICY … 180 REQUIRES_APPROVAL). Numeric codes; labels are display-only.
- `src/baltor/runtime/registry/preference_graph.py` — numeric `priority` + `status_code` per adapter (config-
  sourced, label-derived fallback, non-fragile); graph = nodes + `falls_back_to`/`alternative_of` edges with
  `edge_type_code` + numeric weight; acyclic by construction. `CapabilityRegistry.preference_order()` /
  `.preference_graph()`. Proof: `check_preference_graph_numeric` (renaming providers / unknown roles never
  reorder or crash; explicit numbers override role labels).
- **Cloud-agnostic execution:** `execution_backend_selector.generic_functions()` reads the serverless family
  from CONFIG (`generic_cloud_functions` in the policy matrix), not a code literal; provider-agnostic action
  (`use_cloud_function` for any peer); AWS Lambda is one peer (GCP/Azure/Cloudflare/OpenFaaS added). Proof:
  `check_cloud_agnostic_execution`. Policy-matrix proof made structural (no exact-set match).
- Demonstrated numeric slotting: PaddleOCR inserted at priority 72 BETWEEN Docling(75) and Unstructured(50)
  with no renumbering; compression headroom(78) > llmlingua(70) > stub(20) overrides role labels.

## REMAINING (staged increments — each = schema/code/proof/doc together)
- **PART 1 — Contracts:** `schemas/providers/{CapabilitySlot,ProviderNode,ProviderEdge,ProviderSelectionGraph,
  ProviderSelectionPolicy,ProviderSelectionDecision,ProviderAlias,ProviderHealthSnapshot,ProviderPriceSnapshot}.v1.schema.json`;
  register in `architecture/contract_registry.json`. ProviderNode: node_id·capability_slot·family·version_label·
  display_name·aliases·status_code·status_label·local_equivalent_node_id·contract_id·enabled·tenant_scope·
  provider_kind·created_at·updated_at. ProviderEdge: from·to·edge_type_code·edge_type_label·priority/cost/
  reliability/latency/safety_weight·policy_conditions·active_from·active_to.
- **PART 3 — Graph config:** `architecture/provider_selection_graph.json` seeded from external_capability_catalog
  + repo_replacement_matrix + execution_backend_policy_matrix; nodes + emulator/alternative/fallback/supersedes/
  canary/shadow edges; numeric weights on a 0–10000 scale with gaps for insertion.
- **PART 4 — Selector:** `src/baltor/providers/provider_selector.py` → `ProviderSelectionDecision.v1`
  (selected_node_id·score·fallback_node_ids·rejected_node_ids·reason_codes·graph_path·policy_id·inputs_hash);
  scoring = reliability+cost+latency+safety+local_equivalent+tenant_policy+data_residency+SLA. No name matching.
- **PART 6 — Config DB:** local SQLite tables (provider_nodes/edges/aliases/capability_slots/selection_policies/
  health_snapshots/pricebook_snapshots/tenant_provider_overrides/provider_decision_audit); JSON seed; runtime
  reads the graph object, never raw catalog strings.
- **PART 5/8 — De-brittle + redteam:** `check_no_brittle_provider_string_logic` (grep `provider==`/`role==`/
  vendor names in RUNTIME + PROOFS; classify OK_DOCS/OK_CONFIG/FIX_RUNTIME/FIX_PROOF/FIX_CATALOG; fix the
  runtime/proof exact-matches) + `check_provider_selection_graph_redteam` (display-name change still passes;
  alias change doesn't break; Lambda-unavailable doesn't block; label change but numeric routing holds;
  no-local-equivalent can't enter served path; tenant-disallowed not selected; contract-mismatch not selected).
- **PART 9 — Proofs:** status/edge codes · selection graph · numeric selector · DB config · cloud-agnostic ·
  redteam · full-stack. Regress: optimization_suite · execution_backend_full_stack · no_direct_provider_bypass ·
  baltor_full_stack_perfect · flywheel.

## Acceptance
A graph exists · numeric status + edge codes exist · selector uses graph/config not display strings · cloud
backends are cloud-agnostic peers · Lambda not canonical · local equivalent required for candidates · display-name
changes don't break proofs · versioning is metadata not control logic · tenant policy can override · pricebook/
telemetry changes selection with no code change · redteam fails safely · flywheel green.

*Warrant: clear owner intent (numeric, non-fragile, cloud-agnostic, config-backed). First increment shipped +
proven; remainder staged. No vendor is canonical; local emulators required; proofs check contracts + graph, not names.*
