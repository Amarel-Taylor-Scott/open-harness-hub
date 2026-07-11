#!/usr/bin/env python3
"""Build the compiled primitive route benchmark seed pack.

Implements the build slice from
``_repos/shared-backend-components/docs/codex/claude-fable-compiled-primitive-routes-handoff.md``: a generated
seed pack under ``_repos/shared-backend-components/catalog/knowledge-packs/data/compiled-primitive-route-benchmark-seeds/``
that seeds the Compiled-Primitive-AI benchmark harness (intent -> primitive
search -> CandidateBundle -> route/remix -> PlanDelta -> PlanLock ->
deterministic execution -> proof receipt -> promotion or negative memory).

The pack is deliberately wider than "compile code once and run it". Beyond the
benchmark sources / task demands / path portfolios, it seeds the ADAPTIVE
OPTIMIZATION layer the handoff requires: model/LoRA/ranker/mini-agent lanes
for every step, simultaneous trial runs, random path sprouting with held-out
promotion, ongoing telemetry that feeds ranking, primitive co-occurrence and
decomposition learning, cache/materialization policy, champion/challenger
best-to-worst ranking, and a route-attempt -> training-data capture policy
(experimental sprouts stay isolated from production truth until promotion).

Every row is a CANDIDATE seed: ``candidate=true`` / ``serves_truth=false``.
External paper and benchmark claims stay prior-art signals — nothing here is
local measured evidence, and no benchmark claim may be promoted without
adapter receipts (enforced by the paired checker,
``_repos/shared-backend-components/scripts/check_compiled_primitive_route_benchmark_seeds.py``).

Reuse, don't rebuild: comparison arms cross-reference the Benchmark Lab
adapter catalog's A0..A8 arms and L1..L7 depth ladder (imported from
``_repos/shared-backend-components/scripts/build_benchmark_lab_adapter_catalog.py`` — the single source), and
registry-factory sources align with the marketplace primitive source-surface
pack rather than redefining it.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (  # noqa: E402
    COMPILED_PRIMITIVE_ROUTE_BENCHMARK_SEEDS_DIR,
    COMPILED_PRIMITIVE_ROUTE_BENCHMARK_SEEDS_EVIDENCE_STATUS,
    COMPILED_PRIMITIVE_ROUTE_BENCHMARK_SEEDS_SOURCE_FAMILY,
    COMPILED_PRIMITIVE_ROUTE_BENCHMARK_SEEDS_SOURCE_STATUS,
    REPO_ROOT,
)
from scripts.build_benchmark_lab_adapter_catalog import (  # noqa: E402
    COMPARISON_ARMS as BENCHMARK_LAB_COMPARISON_ARMS,
    DEPTH_LADDER as BENCHMARK_LAB_DEPTH_LADDER,
    FAMILIES as BENCHMARK_LAB_FAMILIES,
)

PACK_DIR = _resource(COMPILED_PRIMITIVE_ROUTE_BENCHMARK_SEEDS_DIR)
BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

BENCHMARK_LAB_ARM_IDS = [str(arm["arm"]) for arm in BENCHMARK_LAB_COMPARISON_ARMS]
DEPTH_LEVELS = [str(level["level"]) for level in BENCHMARK_LAB_DEPTH_LADDER]
BENCHMARK_LAB_FAMILY_KEYS = {str(family["key"]) for family in BENCHMARK_LAB_FAMILIES}

# ── Shared enums (single source for rows AND the checker) ─────────────────
# The lanes a model slot can be served by, ordered cheap/deterministic first.
SERVED_BY_LANES: list[str] = [
    "deterministic_rule",
    "sql_or_graph_query",
    "local_classifier",
    "embedding_model",
    "cross_encoder_ranker",
    "small_local_language_model",
    "domain_lora_adapter",
    "vision_language_model",
    "cloud_frontier_model",
    "human_review_queue",
]

# Every model-path selection must be receipted with these fields.
MODEL_ROUTE_RECEIPT_FIELDS: list[str] = [
    "slot",
    "selected_model_path",
    "adapter",
    "fallbacks_considered",
    "selection_reason",
    "metrics_recorded",
]

# Adapter records must carry full lineage so swaps are reversible.
ADAPTER_RECORD_FIELDS: list[str] = [
    "base_model_ref",
    "adapter_ref",
    "training_data_lineage",
    "eval_task_set",
    "allowed_slots",
    "disallowed_slots",
    "latency_profile",
    "memory_profile",
    "cost_profile",
    "calibration_profile",
    "known_failure_modes",
    "promotion_receipts",
    "rollback_receipts",
]

# Downstream-lift criteria an adapter must win on (persuasion is not lift).
ADAPTER_LIFT_CRITERIA: list[str] = [
    "better_candidate_recall",
    "better_route_compile_success",
    "less_source_escalation",
    "fewer_false_primitive_matches",
    "faster_proof_generation",
    "better_repair_success",
    "lower_cost_at_same_quality",
]

# Comparison receipt emitted by every simultaneous trial run.
COMPARISON_RECEIPT_FIELDS: list[str] = [
    "path_id",
    "random_seed",
    "parameters",
    "model_slot_assignments",
    "primitive_bundle",
    "route_candidate",
    "compile_status",
    "proof_status",
    "latency",
    "token_cost",
    "source_read_depth",
    "side_effects",
    "artifact_quality_metrics",
    "downstream_reuse_signal",
    "winner_reason",
    "loser_negative_memory",
]

# The feedback loops ongoing telemetry must feed (each covered by >=1 signal).
FEEDBACK_LOOPS: list[str] = [
    "champion_challenger_ranking",
    "sprout_selection",
    "cache_policy_tuning",
    "decomposition_learning",
    "cooccurrence_learning",
    "negative_memory_suppression",
    "adapter_training_data",
    "route_economics_accounting",
]

CACHE_INVALIDATION_TRIGGERS: list[str] = [
    "schema_change",
    "api_version_change",
    "legal_effective_date_change",
    "benchmark_regression",
    "model_or_adapter_change",
    "retention_policy_expiry",
]

# Scorecard fields every task demand must carry (token/proof/depth/reuse law).
TASK_CORE_SCORECARD: list[str] = [
    "score:task_success",
    "score:tokens_to_plan",
    "score:tokens_to_pass",
    "score:runtime_llm_tokens",
    "score:depth_to_solution",
    "score:proof_success",
    "score:route_reuse",
    "score:negative_memory_created",
    "score:cost_per_success",
]

COMPARISON_ARM_IDS: list[str] = [
    "arm:baseline_runtime_agent",
    "arm:baseline_search_agent",
    "arm:compiled_code_template",
    "arm:primitive_route_compile",
    "arm:source_fallback",
]

MICRO_AGENT_BUDGET_NOTE = "seed default envelope; tune only via exploration_policies with receipts"


def _rows(record_type: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"record_type": record_type, **BOUNDARY, **row} for row in rows]


# ── benchmark_sources.jsonl ────────────────────────────────────────────────
def _benchmark_sources() -> list[dict[str, Any]]:
    rows = [
        {
            "source_id": "benchsrc:bfcl",
            "title": "BFCL-style function/tool routing",
            "task_style": "tool selection, argument binding, abstention, parallel calls",
            "benchmark_lab_family_key": "B_function_calling_tool_use_workflow",
        },
        {
            "source_id": "benchsrc:docile",
            "title": "DocILE-style document extraction",
            "task_style": "field extraction, line-item reconstruction, confidence receipts",
            "benchmark_lab_family_key": "D_data_science_ml_document_table_rag_retrieval",
        },
        {
            "source_id": "benchsrc:swe_bench",
            "title": "SWE-bench-style repo repair and source escalation",
            "task_style": "fault localization, minimal patch, depth-to-solution discipline",
            "benchmark_lab_family_key": "A_coding_repo_swe_terminal",
        },
        {
            "source_id": "benchsrc:terminal_bench",
            "title": "Terminal-Bench-style CLI/runtime tasks",
            "task_style": "environment setup, command plans, sandboxed execution",
            "benchmark_lab_family_key": "A_coding_repo_swe_terminal",
        },
        {
            "source_id": "benchsrc:appworld",
            "title": "AppWorld-style API-state transition tasks",
            "task_style": "multi-app call plans, state verification, collateral-damage guards",
            "benchmark_lab_family_key": "C_web_os_desktop_mobile_company_agent",
        },
        {
            "source_id": "benchsrc:mle_bench_kaggle",
            "title": "Kaggle / MLE-bench-style data-science workflows",
            "task_style": "profiling, leakage scans, baseline model routes, metric parsing",
            "benchmark_lab_family_key": "D_data_science_ml_document_table_rag_retrieval",
        },
        {
            "source_id": "benchsrc:openapi_asyncapi_mcp_registries",
            "title": "OpenAPI/AsyncAPI/MCP registry primitive factories",
            "task_style": "contract extraction, tool wrapping, proof-plan emission",
            "benchmark_lab_family_key": None,
            "aligns_with": "catalog/knowledge-packs/data/marketplace-primitive-source-surfaces",
        },
        {
            "source_id": "benchsrc:terraform_actions_kubernetes_wrappers",
            "title": "Terraform/GitHub Actions/Kubernetes deployment wrappers",
            "task_style": "plan gating, guardrail policy, dry-run receipts",
            "benchmark_lab_family_key": "E_security_devsecops_incident_infra_agent",
        },
        {
            "source_id": "benchsrc:expanded_branch_internal_fixtures",
            "title": "Internal fixtures for expanded primitive branches",
            "task_style": "entity resolution / record linkage, visual+math scene generation, rendering receipts",
            "benchmark_lab_family_key": None,
            "aligns_with": "handoff expanded-branch sections (ER, visual/math, ray tracing, algorithms)",
        },
    ]
    for row in rows:
        row.setdefault("aligns_with", "catalog/knowledge-packs/data/benchmark-lab-adapter-catalog")
        row["source_status"] = (
            "internal_fixture_suite_to_build"
            if row["source_id"] == "benchsrc:expanded_branch_internal_fixtures"
            else "external_prior_art_needs_local_adapter"
        )
        row["adapter_state"] = "unbuilt"
        row["evidence_status"] = COMPILED_PRIMITIVE_ROUTE_BENCHMARK_SEEDS_EVIDENCE_STATUS
    return _rows("compiled_primitive_benchmark_source", rows)


# ── benchmark_task_demands.jsonl ───────────────────────────────────────────
def _task(source: str, task_id: str, title: str, input_edge: str, output_edge: str,
          demands: list[str], depth_target: str, slots: list[str]) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "source_family": source,
        "title": title,
        "input_edge": input_edge,
        "output_edge": output_edge,
        "primitive_demands": demands,
        "comparison_arms": list(COMPARISON_ARM_IDS),
        "scorecard_fields": list(TASK_CORE_SCORECARD),
        "depth_target": depth_target,
        "model_slot_demands": slots,
    }


def _benchmark_task_demands() -> list[dict[str, Any]]:
    rows = [
        _task("benchsrc:bfcl", "task:bfcl.tool_route.single_call",
              "Single validated tool call from intent",
              "UserIntent+ToolSchemaSet", "ValidatedToolCallPlan+ExecutionReceipt",
              ["tool_schema_validate", "tool_select", "argument_bind",
               "abstain_when_no_safe_tool", "receipt_emit"],
              "L2_CONTRACT", ["modelslot:intent_classifier", "modelslot:route_planner"]),
        _task("benchsrc:bfcl", "task:bfcl.tool_route.parallel_calls",
              "Parallel multi-tool dispatch plan",
              "UserIntent+ToolSchemaSet+ParallelPolicy", "ParallelToolCallPlan+ExecutionReceipt",
              ["tool_dependency_graph_build", "parallel_dispatch_plan", "argument_bind",
               "idempotency_key_generate", "receipt_emit"],
              "L3_BEHAVIOR", ["modelslot:route_planner"]),
        _task("benchsrc:docile", "task:docile.field_extract.core_fields",
              "Core field extraction from business documents",
              "DocumentBatch+FieldSchema", "ExtractedFieldTable+ExtractionReceipt",
              ["document_layout_profile", "field_locate", "value_normalize",
               "confidence_score_emit", "receipt_emit"],
              "L3_BEHAVIOR", ["modelslot:schema_mapper"]),
        _task("benchsrc:docile", "task:docile.line_items.table_reconstruction",
              "Line-item table reconstruction with quarantine",
              "DocumentBatch+LineItemSchema", "LineItemTable+ExtractionReceipt",
              ["table_region_detect", "line_item_reconstruct", "amount_reconcile",
               "quarantine_with_reason", "receipt_emit"],
              "L3_BEHAVIOR", ["modelslot:schema_mapper"]),
        _task("benchsrc:swe_bench", "task:swe_bench.repo_repair.minimal_patch",
              "Minimal patch from failing tests",
              "FailingTestReport+RepoSnapshot", "CandidatePatch+ProofReceipt",
              ["failure_receipt_read", "fault_localize", "patch_candidate_generate",
               "regression_test_run", "receipt_emit"],
              "L6_SOURCE_SLICE", ["modelslot:code_micro_patch"]),
        _task("benchsrc:swe_bench", "task:swe_bench.source_escalation.depth_discipline",
              "Route-or-escalate decision with depth receipt",
              "IssueReport+PrimitiveRegistryIndex", "RouteOrEscalationDecision+DepthReceipt",
              ["primitive_search", "candidate_bundle_build", "escalation_decision_record",
               "depth_receipt_emit"],
              "L4_ROUTE", ["modelslot:cross_encoder_reranker"]),
        _task("benchsrc:terminal_bench", "task:terminal_bench.cli_workflow.environment_setup",
              "Deterministic environment setup plan",
              "TaskSpec+SandboxPolicy", "ExecutedCommandPlan+ExecutionReceipt",
              ["environment_profile", "dependency_install_plan", "command_plan_compile",
               "sandbox_execute", "receipt_emit"],
              "L3_BEHAVIOR", ["modelslot:route_planner"]),
        _task("benchsrc:terminal_bench", "task:terminal_bench.cli_workflow.data_wrangle",
              "File transformation with idempotent writes",
              "TaskSpec+InputFiles+SandboxPolicy", "TransformedFiles+ExecutionReceipt",
              ["file_profile", "transform_plan_compile", "idempotent_write",
               "output_validate", "receipt_emit"],
              "L3_BEHAVIOR", ["modelslot:request_decomposer"]),
        _task("benchsrc:appworld", "task:appworld.api_state.multi_app_transaction",
              "Multi-app API transaction with state verification",
              "GoalSpec+AppApiSchemas+StatePolicy", "ApiCallPlan+StateTransitionReceipt",
              ["api_schema_bind", "state_precondition_check", "call_sequence_plan",
               "state_transition_verify", "receipt_emit"],
              "L4_ROUTE", ["modelslot:route_planner", "modelslot:plan_delta_writer"]),
        _task("benchsrc:appworld", "task:appworld.api_state.collateral_damage_guard",
              "Side-effect guarded API plan",
              "GoalSpec+AppApiSchemas+SideEffectPolicy", "GuardedApiCallPlan+SideEffectAuditReceipt",
              ["side_effect_enumerate", "blast_radius_check", "approval_gate_insert",
               "compensation_plan_attach", "receipt_emit"],
              "L4_ROUTE", ["modelslot:proof_obligation_generator"]),
        _task("benchsrc:mle_bench_kaggle", "task:mle_bench.data_science.leakage_scan",
              "Target-leakage scan on tabular data",
              "TabularDatasetRef+TargetSpec", "LeakageFindings+ScanReceipt",
              ["dataset_profile", "target_leakage_scan", "split_integrity_check",
               "finding_emit", "receipt_emit"],
              "L2_CONTRACT", ["modelslot:request_decomposer"]),
        _task("benchsrc:mle_bench_kaggle", "task:mle_bench.data_science.baseline_model_route",
              "Baseline model route under compute budget",
              "TabularDatasetRef+TaskObjective+ComputeBudget", "BaselineModelPlan+EvalReceipt",
              ["task_objective_bind", "baseline_model_select", "eval_harness_run",
               "metric_parse", "receipt_emit"],
              "L4_ROUTE", ["modelslot:route_planner"]),
        _task("benchsrc:openapi_asyncapi_mcp_registries", "task:openapi_mcp.factory.endpoint_primitive_emit",
              "Endpoint primitive card from an OpenAPI operation",
              "OpenApiOperationObject+AuthPolicy", "EndpointPrimitiveCard+ProofPlan",
              ["openapi_operation_extract", "auth_scope_review", "contract_test_generate",
               "primitive_card_emit", "receipt_emit"],
              "L2_CONTRACT", ["modelslot:edge_signature_infer"]),
        _task("benchsrc:openapi_asyncapi_mcp_registries", "task:openapi_mcp.factory.mcp_tool_wrap",
              "MCP tool route card with proof plan",
              "McpToolDescriptor+RuntimePolicy", "McpToolRouteCard+ProofPlan",
              ["mcp_descriptor_parse", "tool_schema_validate", "runtime_wrapper_emit",
               "proof_plan_attach", "receipt_emit"],
              "L2_CONTRACT", ["modelslot:edge_signature_infer"]),
        _task("benchsrc:terraform_actions_kubernetes_wrappers", "task:terraform_k8s.wrapper.plan_gate",
              "Terraform plan gate under guardrail policy",
              "TerraformPlanJson+GuardrailPolicy", "GatedDeployPlan+PolicyReceipt",
              ["terraform_plan_parse", "guardrail_policy_eval", "drift_check",
               "approval_packet_emit", "receipt_emit"],
              "L3_BEHAVIOR", ["modelslot:proof_obligation_generator"]),
        _task("benchsrc:terraform_actions_kubernetes_wrappers", "task:terraform_k8s.wrapper.kubernetes_job_emit",
              "Kubernetes job manifest with dry-run receipt",
              "JobSpecIntent+ClusterPolicy", "KubernetesJobManifest+DryRunReceipt",
              ["job_spec_bind", "resource_budget_check", "manifest_emit",
               "dry_run_verify", "receipt_emit"],
              "L3_BEHAVIOR", ["modelslot:schema_mapper"]),
        _task("benchsrc:expanded_branch_internal_fixtures", "task:expanded_internal.entity_resolution.customer_dedupe",
              "Transparent probabilistic customer dedupe (Splink-style edge)",
              "RawRecordTable+BlockingRules+ComparisonSettings+ThresholdPolicy",
              "ClusteredEntityTable+MatchWeights+DiagnosticsReceipt",
              ["record_standardize", "blocking_rule_generate", "candidate_pair_generate",
               "fellegi_sunter_score", "cluster_links", "clerical_review_packet"],
              "L3_BEHAVIOR", ["modelslot:cross_encoder_reranker"]),
        _task("benchsrc:expanded_branch_internal_fixtures", "task:expanded_internal.visual.formula_to_interactive_scene",
              "Formula to interactive scene with render receipts",
              "FormulaLatexExpression+RenderPolicy", "InteractiveSceneArtifact+RenderReceipt",
              ["formula_latex_parse", "symbol_ledger_build", "scene_template_fill",
               "render_smoke_test", "receipt_emit"],
              "L4_ROUTE", ["modelslot:visual_scene_generator"]),
    ]
    return _rows("compiled_primitive_benchmark_task_demand", rows)


# ── primitive_generation_paths.jsonl ───────────────────────────────────────
def _primitive_generation_paths() -> list[dict[str, Any]]:
    rows = [
        {"path_id": "genpath:source_adapter_extract",
         "what_it_does": "mines OpenAPI/AsyncAPI/MCP/PyPI/npm/Actions/Terraform/Helm/docs/benchmarks into candidate cards",
         "wins_when": ["source surface is machine-readable or well-structured"],
         "fails_when": ["surface is unstructured prose", "license or rate limits block extraction"]},
        {"path_id": "genpath:marketplace_listing_extract",
         "what_it_does": "converts marketplace listings, workflow templates, app directories, and cloud packages into capability cards",
         "wins_when": ["the market already exposes repeated buyer problems"],
         "fails_when": ["listings are marketing prose without contracts"]},
        {"path_id": "genpath:benchmark_task_demand_extract",
         "what_it_does": "converts BFCL/DocILE/SWE-bench/Terminal-Bench/AppWorld/MLE-bench tasks into primitive demands",
         "wins_when": ["benchmark has executable or labeled evaluation"],
         "fails_when": ["evaluation is not executable, so demands stay unverifiable"]},
        {"path_id": "genpath:trace_to_workflow_mine",
         "what_it_does": "converts successful agent/tool traces into structured route candidates",
         "wins_when": ["a task was solved once but should become reusable"],
         "fails_when": ["trace embeds tenant-private or non-reusable context"],
         "model_slot_refs": ["modelslot:receipt_summarizer"]},
        {"path_id": "genpath:workflow_template_mine",
         "what_it_does": "mines n8n/Zapier/Make/Pipedream datasets, CI files, DAGs, and runbooks",
         "wins_when": ["existing workflow ecosystem encodes domain practice"],
         "fails_when": ["templates encode platform-specific glue with no general contract"]},
        {"path_id": "genpath:repo_symbol_surface_extract",
         "what_it_does": "extracts public APIs, CLI commands, functions, schemas, config surfaces, and tests from repos",
         "wins_when": ["codebase has reusable local capabilities"],
         "fails_when": ["private or unstable internals get mistaken for public capability"]},
        {"path_id": "genpath:schema_to_primitive_emit",
         "what_it_does": "converts schemas and standards into validators, mappers, wrappers, and proof obligations",
         "wins_when": ["JSON Schema/FHIR/XBRL/GS1/OpenAPI/protobuf/GraphQL/dbt contracts exist"],
         "fails_when": ["schema lacks semantics and field names lie"]},
        {"path_id": "genpath:human_curated_seed",
         "what_it_does": "lets a curator define a compact primitive or route demand manually",
         "wins_when": ["domain is high-risk, underdocumented, or strategically important"],
         "fails_when": ["curation does not scale and encodes curator bias"]},
        {"path_id": "genpath:model_draft_candidate",
         "what_it_does": "uses a model to draft a candidate from a clear brief",
         "wins_when": ["useful only as an L1 draft after search misses"],
         "fails_when": ["draft is promoted without source refs or proof (hallucinated capability)"],
         "model_slot_refs": ["modelslot:primitive_candidate_generator"]},
        {"path_id": "genpath:negative_memory_to_gap",
         "what_it_does": "turns repeated failures and near misses into new primitive demands",
         "wins_when": ["agents repeatedly choose wrong tools, stale sources, or unsafe adapters"],
         "fails_when": ["failure classes are misclustered, creating phantom demand"],
         "model_slot_refs": ["modelslot:negative_memory_classifier"]},
    ]
    return _rows("compiled_primitive_generation_path", rows)


# ── primitive_search_paths.jsonl ───────────────────────────────────────────
def _primitive_search_paths() -> list[dict[str, Any]]:
    rows = [
        {"path_id": "searchpath:exact_edge_search",
         "wins_when": ["a promoted route already matches the exact input/output edge"],
         "fails_when": ["near matches and new variants are invisible"]},
        {"path_id": "searchpath:type_compatible_edge_search",
         "wins_when": ["contracts are typed and a near-match can be adapted"],
         "fails_when": ["type compatibility hides semantic mismatch"]},
        {"path_id": "searchpath:schema_contract_search",
         "wins_when": ["schemas/field fingerprints identify the capability"],
         "fails_when": ["schema drift since indexing"]},
        {"path_id": "searchpath:lexical_bm25_search",
         "wins_when": ["exact business objects, error messages, or platform names are in the query"],
         "fails_when": ["vocabulary gap between intent and card text"]},
        {"path_id": "searchpath:embedding_similarity_search",
         "wins_when": ["semantic neighborhoods matter more than exact words"],
         "fails_when": ["out-of-domain vocabulary or placeholder embeddings"],
         "model_slot_refs": ["modelslot:local_embedding"]},
        {"path_id": "searchpath:hybrid_lexical_dense_search",
         "wins_when": ["neither lexical nor dense alone recalls the bundle"],
         "fails_when": ["fusion weights are stale for the task family"],
         "model_slot_refs": ["modelslot:local_embedding", "modelslot:cross_encoder_reranker"]},
        {"path_id": "searchpath:graph_route_search",
         "wins_when": ["multi-step routes must be composed through typed edges"],
         "fails_when": ["missing middle edges break the path"]},
        {"path_id": "searchpath:route_template_search",
         "wins_when": ["a known chain / route template family covers the demand"],
         "fails_when": ["variant dimensions fall outside the template slots"]},
        {"path_id": "searchpath:source_ref_search",
         "wins_when": ["the query names a source surface, doc, or standard"],
         "fails_when": ["source refs are unresolved or stale"]},
        {"path_id": "searchpath:benchmark_task_search",
         "wins_when": ["the demand mirrors a known benchmark task shape"],
         "fails_when": ["benchmark shape diverges from the production shape"]},
        {"path_id": "searchpath:marketplace_source_search",
         "wins_when": ["a marketplace listing already packages the capability"],
         "fails_when": ["listing quality is low and contracts are missing"]},
        {"path_id": "searchpath:negative_memory_search",
         "wins_when": ["a failure class for this demand was already recorded"],
         "fails_when": ["over-general negative memory suppresses valid routes"],
         "model_slot_refs": ["modelslot:negative_memory_classifier"]},
        {"path_id": "searchpath:overlay_search",
         "wins_when": ["industry/country/schema overlays discriminate candidates"],
         "fails_when": ["overlay metadata is sparse or wrong"]},
        {"path_id": "searchpath:runtime_shape_search",
         "wins_when": ["the runtime target (queue/MCP/browser/cron) constrains the route"],
         "fails_when": ["runtime tags are missing on older cards"]},
        {"path_id": "searchpath:proof_requirement_search",
         "wins_when": ["the demand is proof-led (e.g. needs idempotency or PII boundary)"],
         "fails_when": ["proof obligations were never declared on candidates"]},
    ]
    for row in rows:
        row["returns"] = "CandidateBundle"
    return _rows("compiled_primitive_search_path", rows)


# ── route_planning_paths.jsonl ─────────────────────────────────────────────
def _route_planning_paths() -> list[dict[str, Any]]:
    rows = [
        {"planner_id": "planner:exact_route_lookup",
         "shape": "fetch promoted route by matching edge",
         "wins_when": ["high-confidence repeated demand"],
         "fails_when": ["misses near matches and new variants"]},
        {"planner_id": "planner:template_slot_fill",
         "shape": "fill a primitive group template with selected overlays",
         "wins_when": ["known family with variant dimensions"],
         "fails_when": ["variant falls outside declared slots"]},
        {"planner_id": "planner:deterministic_graph_search",
         "shape": "find a compatible multi-step path through typed edges",
         "wins_when": ["contracts are well-typed"],
         "fails_when": ["edge annotations are incomplete, so no path is found"]},
        {"planner_id": "planner:contract_diff_remix",
         "shape": "adapt a near-match route using deterministic mutators",
         "wins_when": ["similar route exists but fields/runtime differ"],
         "fails_when": ["bad adapter selection hides semantic mismatch"]},
        {"planner_id": "planner:llm_plan_delta",
         "shape": "model proposes a compact PlanDelta over candidate cards",
         "wins_when": ["ambiguity remains after deterministic search"],
         "fails_when": ["planner invents members that are not in the registry"],
         "model_slot_refs": ["modelslot:route_planner", "modelslot:plan_delta_writer"]},
        {"planner_id": "planner:tree_or_graph_of_routes",
         "shape": "explore alternative route branches with scoring",
         "wins_when": ["many plausible paths exist"],
         "fails_when": ["branch scoring is uncalibrated, so search wanders"]},
        {"planner_id": "planner:mcts_route_search",
         "shape": "sample and score route plans using proof/cost feedback",
         "wins_when": ["search space is large and metrics are available"],
         "fails_when": ["no cheap rollout signal exists"]},
        {"planner_id": "planner:evolutionary_route_search",
         "shape": "mutate and recombine successful route fragments",
         "wins_when": ["ML/data-science or optimization workflows"],
         "fails_when": ["fitness receipts are too sparse to select on"]},
        {"planner_id": "planner:trace_replay_compile",
         "shape": "reconstruct a route from a successful trace",
         "wins_when": ["a prior ad hoc agent run worked"],
         "fails_when": ["trace context was environment-specific and does not replay"]},
        {"planner_id": "planner:human_review_route",
         "shape": "human chooses or edits the route before compile",
         "wins_when": ["regulated or high-side-effect workflow"],
         "fails_when": ["review throughput becomes the bottleneck"]},
    ]
    return _rows("compiled_primitive_route_planning_path", rows)


# ── compilation_paths.jsonl ────────────────────────────────────────────────
def _compilation_paths() -> list[dict[str, Any]]:
    rows = [
        {"compiler_id": "compiler:deterministic_template_fill",
         "lowering_targets": ["PlanLock canonical JSON", "Python callable", "CLI command"],
         "wins_when": ["route members and slots are fully known"],
         "fails_when": ["template drift versus the runtime wrapper"]},
        {"compiler_id": "compiler:schema_driven_codegen",
         "lowering_targets": ["TypeScript function", "FastAPI endpoint", "OpenAPI client wrapper"],
         "wins_when": ["schemas fully describe the io contract"],
         "fails_when": ["schema under-specifies behavior (errors, retries)"]},
        {"compiler_id": "compiler:ast_transform",
         "lowering_targets": ["Python callable", "SQL query or view"],
         "wins_when": ["an existing artifact needs a mechanical, verifiable change"],
         "fails_when": ["semantic behavior depends on runtime state the AST cannot see"]},
        {"compiler_id": "compiler:typed_graph_lowering",
         "lowering_targets": ["queue consumer", "Temporal activity", "Airflow task", "Dagster asset"],
         "wins_when": ["typed multi-step route lowers to a worker/workflow engine"],
         "fails_when": ["edge types are too loose to pick adapters safely"]},
        {"compiler_id": "compiler:grammar_constrained_generation",
         "lowering_targets": ["PlanLock canonical JSON", "SQL query or view", "GLSL/WGSL shader module"],
         "wins_when": ["output must be formally valid (JSON/SQL/shader grammar)"],
         "fails_when": ["grammar validity masks semantic wrongness"],
         "model_slot_refs": ["modelslot:visual_scene_generator", "modelslot:code_micro_patch"]},
        {"compiler_id": "compiler:model_generated_bounded_function",
         "lowering_targets": ["Python callable", "TypeScript function"],
         "wins_when": ["search failed and only a small missing edge must be generated"],
         "fails_when": ["bounded function grows into an unreviewed program"],
         "model_slot_refs": ["modelslot:code_micro_patch"]},
        {"compiler_id": "compiler:source_backed_wrapper_generation",
         "lowering_targets": ["OpenAPI client wrapper", "MCP tool wrapper", "Terraform plan/module wrapper"],
         "wins_when": ["an authoritative source contract exists to wrap"],
         "fails_when": ["wrapper hides provider-side behavior changes"]},
        {"compiler_id": "compiler:policy_as_code_compilation",
         "lowering_targets": ["guardrail policy bundle", "Kubernetes job or Helm values"],
         "wins_when": ["the route is a policy/gate, not a transformation"],
         "fails_when": ["policy language cannot express the required exception"]},
        {"compiler_id": "compiler:manual_approval_and_lock",
         "lowering_targets": ["human-review checklist", "PlanLock canonical JSON"],
         "wins_when": ["regulated domain requires a human to lock the route"],
         "fails_when": ["approvals go stale as upstream contracts move"]},
    ]
    return _rows("compiled_primitive_compilation_path", rows)


# ── proof_paths.jsonl ──────────────────────────────────────────────────────
def _proof_paths() -> list[dict[str, Any]]:
    rows = [
        {"proof_id": "proof:schema_validation", "wins_when": ["every structured artifact"], "fails_when": ["valid shape, wrong meaning"]},
        {"proof_id": "proof:contract_tests", "wins_when": ["io contract is declared"], "fails_when": ["contract omits error paths"]},
        {"proof_id": "proof:unit_tests", "wins_when": ["pure logic with known cases"], "fails_when": ["tests mirror the bug"]},
        {"proof_id": "proof:golden_fixtures", "wins_when": ["known input/output pairs exist"], "fails_when": ["fixtures age out of the real distribution"]},
        {"proof_id": "proof:roundtrip_tests", "wins_when": ["encode/decode or map/unmap routes"], "fails_when": ["lossy corners outside sampled data"]},
        {"proof_id": "proof:idempotency_tests", "wins_when": ["any retried write path"], "fails_when": ["hidden state outside the idempotency key"]},
        {"proof_id": "proof:side_effect_audit", "wins_when": ["route declares effects beyond artifact_write"], "fails_when": ["undeclared effects escape the audit surface"]},
        {"proof_id": "proof:privacy_pii_boundary_test", "wins_when": ["records may carry personal data"], "fails_when": ["PII detectors miss domain-specific identifiers"]},
        {"proof_id": "proof:source_span_verification", "wins_when": ["extraction claims must cite spans"], "fails_when": ["span drift after re-OCR or re-render"]},
        {"proof_id": "proof:citation_support_check", "wins_when": ["generated claims cite sources"], "fails_when": ["citation exists but does not support the claim"]},
        {"proof_id": "proof:license_terms_gate", "wins_when": ["mined content enters the registry"], "fails_when": ["license metadata is missing upstream"]},
        {"proof_id": "proof:security_static_analysis_scan", "wins_when": ["generated code or wrappers"], "fails_when": ["dynamic-only vulnerabilities"]},
        {"proof_id": "proof:sandbox_execution", "wins_when": ["artifact must run before promotion"], "fails_when": ["sandbox diverges from production runtime"]},
        {"proof_id": "proof:benchmark_scorecard", "wins_when": ["comparable arms exist for the task family"], "fails_when": ["scorecard fields are gamed by one arm"]},
        {"proof_id": "proof:freshness_effective_date_check", "wins_when": ["laws, APIs, packages, market data"], "fails_when": ["effective dates are unpublished"]},
        {"proof_id": "proof:human_review", "wins_when": ["healthcare/finance/legal/cloud-mutation/data-export routes"], "fails_when": ["review load exceeds reviewer budget"]},
        {"proof_id": "proof:regression_replay", "wins_when": ["route changes against recorded receipts"], "fails_when": ["replay corpus is unrepresentative"]},
        {"proof_id": "proof:shadow_production_comparison", "wins_when": ["replacing an existing workflow"], "fails_when": ["shadow traffic misses rare branches"]},
    ]
    for row in rows:
        row["receipt_emitted"] = row["proof_id"].split(":", 1)[1] + "_receipt"
    return _rows("compiled_primitive_proof_path", rows)


# ── runtime_execution_paths.jsonl ──────────────────────────────────────────
def _runtime_execution_paths() -> list[dict[str, Any]]:
    runtimes = [
        {"path_id": "runtime:local_pure_function", "wins_when": ["zero-effect transforms with tight latency"], "fails_when": ["state or scale outgrows one process"]},
        {"path_id": "runtime:container_job", "wins_when": ["heavier deps, render jobs, sandboxed repair"], "fails_when": ["cold-start cost dominates small tasks"]},
        {"path_id": "runtime:serverless_function", "wins_when": ["bursty, stateless, per-call billing"], "fails_when": ["long-running or stateful routes"]},
        {"path_id": "runtime:api_middleware", "wins_when": ["route sits inline on an existing API"], "fails_when": ["middleware latency budget is exceeded"]},
        {"path_id": "runtime:mcp_prehook", "wins_when": ["agent tool-calls need guarding/enrichment"], "fails_when": ["hook must never block and cannot guarantee that"]},
        {"path_id": "runtime:queue_worker", "wins_when": ["retryable batch work with idempotency keys"], "fails_when": ["strict ordering requirements"]},
        {"path_id": "runtime:browser_worker", "wins_when": ["rendering, canvas receipts, web extraction"], "fails_when": ["headless environment diverges from real browsers"]},
        {"path_id": "runtime:workflow_engine", "wins_when": ["long multi-step routes with compensation"], "fails_when": ["engine lock-in for trivial routes"]},
        {"path_id": "runtime:kubernetes_job", "wins_when": ["resource-bounded batch at cluster scale"], "fails_when": ["cluster access is not available to the tenant"]},
        {"path_id": "runtime:cicd_action", "wins_when": ["route gates a repo change"], "fails_when": ["secrets/permissions outside CI scope"]},
        {"path_id": "runtime:database_job", "wins_when": ["set-based transforms next to the data (SQL/BigQuery)"], "fails_when": ["row-by-row logic that SQL expresses poorly"]},
        {"path_id": "runtime:human_review_queue", "wins_when": ["clerical review, regulated approvals"], "fails_when": ["queue latency starves the pipeline"]},
    ]
    patterns = [
        {"path_id": "execpattern:strict_deterministic_execution", "wins_when": ["promoted PlanLock routes"], "fails_when": ["inputs outside the locked contract"]},
        {"path_id": "execpattern:bounded_llm_subcall", "wins_when": ["one schema-validated model step under policy"], "fails_when": ["subcall output escapes its schema budget"]},
        {"path_id": "execpattern:parallel_tool_execution", "wins_when": ["independent calls dominate latency"], "fails_when": ["hidden dependencies between calls"]},
        {"path_id": "execpattern:future_async_tool_execution", "wins_when": ["slow tools overlap with planning/decoding"], "fails_when": ["futures leak unresolved into receipts"]},
        {"path_id": "execpattern:retry_with_idempotency_key", "wins_when": ["transient failures on write paths"], "fails_when": ["key omits a mutating parameter"]},
        {"path_id": "execpattern:compensation_rollback_route", "wins_when": ["multi-step effects need undo"], "fails_when": ["non-compensatable external effects"]},
        {"path_id": "execpattern:human_approval_before_side_effect", "wins_when": ["high-blast-radius mutations"], "fails_when": ["approval fatigue rubber-stamps"]},
        {"path_id": "execpattern:dry_run_preview", "wins_when": ["mutation can be previewed cheaply"], "fails_when": ["dry-run diverges from real execution"]},
        {"path_id": "execpattern:shadow_execution", "wins_when": ["candidate route runs beside the champion"], "fails_when": ["shadow side effects are not fully isolated"]},
    ]
    for row in runtimes:
        row["kind"] = "runtime"
        row["receipt_required"] = True
    for row in patterns:
        row["kind"] = "execution_pattern"
        row["receipt_required"] = True
    return _rows("compiled_primitive_runtime_execution_path", runtimes + patterns)


# ── repair_ladder.jsonl ────────────────────────────────────────────────────
def _repair_ladder() -> list[dict[str, Any]]:
    steps = [
        ("repair:read_failure_receipt", "read the failure receipt before anything else",
         ["every failure"], ["receipt is missing or unstructured"], []),
        ("repair:retrieve_negative_memory", "retrieve negative memory for this demand/failure class",
         ["failure class was seen before"], ["negative memory is over-general"],
         ["modelslot:negative_memory_classifier"]),
        ("repair:classify_failure_layer", "classify the failure layer: search, contract, adapter, runtime, source, proof",
         ["layer is identifiable from the receipt"], ["cross-layer failures resist one label"], []),
        ("repair:try_deterministic_mutator", "apply a deterministic mutator from the route family",
         ["near-match contract diffs"], ["mutator catalog has no matching operator"], []),
        ("repair:try_alternate_route_from_bundle", "try the next route in the same CandidateBundle",
         ["bundle carried viable alternates"], ["all alternates share the same failing member"], []),
        ("repair:escalate_one_context_ladder_level", "escalate exactly one disclosure-depth level",
         ["missing information is one level deeper"], ["escalation overshoots to full source"], []),
        ("repair:run_focused_source_ref_resolver", "resolve the specific stale/unresolved source ref",
         ["failure names a source ref"], ["source is gone or moved without redirect"],
         ["modelslot:source_fragility_detector"]),
        ("repair:allow_bounded_model_micro_repair", "allow a bounded model micro-repair targeted by validation errors",
         ["small missing edge after deterministic paths exhausted"], ["repair loops open-endedly instead of targeting the error"],
         ["modelslot:compiler_error_repair", "modelslot:code_micro_patch"]),
        ("repair:recompile_and_rerun_proof", "recompile the route and rerun the full proof set",
         ["a repair was applied"], ["proof set was too weak to catch the original failure"], []),
        ("repair:write_negative_memory_if_still_failing", "write negative memory so the failure is never silently repeated",
         ["route still fails after repair"], ["failure signature is too noisy to key"], []),
        ("repair:create_new_primitive_demand_if_gap_real", "convert a real gap into a new primitive demand",
         ["the registry genuinely lacks the capability"], ["gap was actually a search miss"], []),
    ]
    rows = []
    for order, (repair_id, action, wins, fails, slots) in enumerate(steps, start=1):
        row: dict[str, Any] = {"repair_id": repair_id, "order": order, "action": action,
                               "wins_when": wins, "fails_when": fails}
        if slots:
            row["model_slot_refs"] = slots
        rows.append(row)
    return _rows("compiled_primitive_repair_step", rows)


# ── comparison_arms.jsonl ──────────────────────────────────────────────────
def _comparison_arms() -> list[dict[str, Any]]:
    rows = [
        {"arm_id": "arm:baseline_runtime_agent",
         "title": "Baseline runtime agent",
         "allowed_model_use": "unbounded runtime LLM calls, no primitive registry access",
         "allowed_runtime_behavior": "free-form tool use inside the task sandbox",
         "forbidden": ["primitive search", "route reuse"],
         "benchmark_lab_arm_refs": ["A1"],
         "wins_when": ["novel tasks with no reusable structure"],
         "fails_when": ["repeated tasks burn full planning cost every run"]},
        {"arm_id": "arm:baseline_search_agent",
         "title": "Baseline agent with repo/search/RAG context",
         "allowed_model_use": "unbounded runtime LLM calls plus retrieval context",
         "allowed_runtime_behavior": "free-form tool use with repo/docs search",
         "forbidden": ["primitive registry access", "compiled route reuse"],
         "benchmark_lab_arm_refs": ["A2"],
         "wins_when": ["context retrieval alone closes the gap"],
         "fails_when": ["retrieval reads deep source for shallow questions"]},
        {"arm_id": "arm:compiled_code_template",
         "title": "Compiled-code / template generation",
         "allowed_model_use": "compile-time LLM only; zero runtime model calls after validation",
         "allowed_runtime_behavior": "deterministic execution of the generated artifact",
         "forbidden": ["runtime model calls", "unvalidated artifact execution"],
         "benchmark_lab_arm_refs": ["A4"],
         "wins_when": ["stable repeated workflow lowered to one artifact"],
         "fails_when": ["variant demand outside the generated artifact"]},
        {"arm_id": "arm:primitive_route_compile",
         "title": "Primitive-first CandidateBundle + deterministic remix",
         "allowed_model_use": "compile-time LLM for compact PlanDelta only, bounded by candidate cards",
         "allowed_runtime_behavior": "deterministic PlanLock execution with receipts",
         "forbidden": ["free-form runtime agent control", "promotion without proof receipts"],
         "benchmark_lab_arm_refs": ["A5", "A6"],
         "wins_when": ["registry already covers most of the demand"],
         "fails_when": ["registry gap forces escalation anyway"]},
        {"arm_id": "arm:source_fallback",
         "title": "Primitive-first source fallback",
         "allowed_model_use": "bounded micro-repair/codegen after primitive search fails, targeted by validation errors",
         "allowed_runtime_behavior": "sandboxed execution, then container promotion path",
         "forbidden": ["skipping primitive search before source escalation"],
         "benchmark_lab_arm_refs": ["A7", "A8"],
         "wins_when": ["novel gaps after search honestly fails"],
         "fails_when": ["higher token cost and source-review burden"]},
    ]
    return _rows("compiled_primitive_comparison_arm", rows)


# ── scorecard_fields.jsonl ─────────────────────────────────────────────────
def _scorecard_fields() -> list[dict[str, Any]]:
    rows = [
        {"field_id": "score:task_success", "metric_category": "success", "unit": "ratio", "direction": "higher_is_better",
         "definition": "task passed its acceptance criteria and proof gates"},
        {"field_id": "score:tokens_to_plan", "metric_category": "token", "unit": "tokens", "direction": "lower_is_better",
         "definition": "model tokens spent before a compiled route existed"},
        {"field_id": "score:tokens_to_pass", "metric_category": "token", "unit": "tokens", "direction": "lower_is_better",
         "definition": "total model tokens until all proofs passed"},
        {"field_id": "score:runtime_llm_tokens", "metric_category": "token", "unit": "tokens", "direction": "lower_is_better",
         "definition": "model tokens consumed at execution time (target: zero or bounded)"},
        {"field_id": "score:source_files_or_docs_read", "metric_category": "depth", "unit": "count", "direction": "lower_is_better",
         "definition": "distinct source files/docs opened to solve the task"},
        {"field_id": "score:source_context_tokens", "metric_category": "token", "unit": "tokens", "direction": "lower_is_better",
         "definition": "source/context tokens loaded to solve the task"},
        {"field_id": "score:depth_to_solution", "metric_category": "depth", "unit": "depth_level", "direction": "lower_is_better",
         "definition": "deepest disclosure level needed (benchmark-lab ladder)",
         "allowed_values": list(DEPTH_LEVELS)},
        {"field_id": "score:compile_success", "metric_category": "compile", "unit": "ratio", "direction": "higher_is_better",
         "definition": "route compiled to a valid artifact on the first pass"},
        {"field_id": "score:proof_success", "metric_category": "proof", "unit": "ratio", "direction": "higher_is_better",
         "definition": "all required proof obligations passed"},
        {"field_id": "score:route_reuse", "metric_category": "reuse", "unit": "count", "direction": "higher_is_better",
         "definition": "existing promoted routes reused instead of regenerated"},
        {"field_id": "score:new_group_created", "metric_category": "reuse", "unit": "count", "direction": "higher_is_better",
         "definition": "new reusable primitive groups created by the run"},
        {"field_id": "score:negative_memory_created", "metric_category": "memory", "unit": "count", "direction": "higher_is_better",
         "definition": "failure records written so the miss is never silently repeated"},
        {"field_id": "score:break_even_tasks", "metric_category": "economics", "unit": "count", "direction": "lower_is_better",
         "definition": "runs needed before compile cost is amortized (computed from receipts)"},
        {"field_id": "score:tokens_avoided_to_date", "metric_category": "economics", "unit": "tokens", "direction": "higher_is_better",
         "definition": "cumulative tokens avoided by reusing the compiled route"},
        {"field_id": "score:cost_per_success", "metric_category": "economics", "unit": "usd", "direction": "lower_is_better",
         "definition": "total cost divided by successful task count"},
    ]
    return _rows("compiled_primitive_scorecard_field", rows)


# ── route_portfolio_examples.jsonl ─────────────────────────────────────────
def _portfolio_path(path_id: str, generation: str, search: str, planner: str, compiler: str,
                    runtime: str, patterns: list[str], proofs: list[str],
                    assignments: dict[str, str], strength: str, failure: str) -> dict[str, Any]:
    return {
        "path_id": path_id,
        "generation_path": generation,
        "search_path": search,
        "planner": planner,
        "compiler": compiler,
        "runtime": runtime,
        "execution_patterns": patterns,
        "proof_refs": proofs,
        "model_slot_assignments": assignments,
        "expected_strength": strength,
        "known_failure": failure,
    }


def _route_portfolio_examples() -> list[dict[str, Any]]:
    rows = [
        {
            "portfolio_id": "portfolio:bfcl.tool_route.single_call",
            "task_ref": "task:bfcl.tool_route.single_call",
            "input_edge": "UserIntent+ToolSchemaSet",
            "output_edge": "ValidatedToolCallPlan+ExecutionReceipt",
            "strategy_genome_ref": "strategy:tool_route_single_call",
            "trial_policy_ref": "trial:routine_champion_with_challenger_sampling",
            "ranking_features": ["proof_strength", "contract_fit", "source_authority",
                                 "runtime_llm_tokens", "source_escalation_depth",
                                 "route_reuse_count", "effect_risk", "negative_memory_risk"],
            "candidate_paths": [
                _portfolio_path("path:exact_route_lookup", "genpath:source_adapter_extract",
                                "searchpath:exact_edge_search", "planner:exact_route_lookup",
                                "compiler:deterministic_template_fill", "runtime:local_pure_function",
                                ["execpattern:strict_deterministic_execution"], ["proof:contract_tests"],
                                {"modelslot:edge_signature_infer": "deterministic_rule"},
                                "fastest when a promoted route exists",
                                "misses near matches and new variants"),
                _portfolio_path("path:contract_diff_remix", "genpath:source_adapter_extract",
                                "searchpath:type_compatible_edge_search", "planner:contract_diff_remix",
                                "compiler:typed_graph_lowering", "runtime:queue_worker",
                                ["execpattern:retry_with_idempotency_key"],
                                ["proof:golden_fixtures", "proof:side_effect_audit"],
                                {"modelslot:schema_mapper": "deterministic_rule",
                                 "modelslot:cross_encoder_reranker": "cross_encoder_ranker"},
                                "adapts near matches without new model code",
                                "bad adapter selection can hide semantic mismatch"),
                _portfolio_path("path:llm_plan_delta_source_fallback", "genpath:model_draft_candidate",
                                "searchpath:hybrid_lexical_dense_search", "planner:llm_plan_delta",
                                "compiler:model_generated_bounded_function", "runtime:container_job",
                                ["execpattern:shadow_execution", "execpattern:bounded_llm_subcall"],
                                ["proof:sandbox_execution", "proof:benchmark_scorecard"],
                                {"modelslot:route_planner": "small_local_language_model",
                                 "modelslot:plan_delta_writer": "cloud_frontier_model",
                                 "modelslot:local_embedding": "embedding_model"},
                                "handles novel gaps after search fails",
                                "higher token cost and source-review burden"),
            ],
        },
        {
            "portfolio_id": "portfolio:entity_resolution.customer_dedupe.compliance",
            "task_ref": "task:expanded_internal.entity_resolution.customer_dedupe",
            "input_edge": "RawRecordTable+BlockingRules+ComparisonSettings+ThresholdPolicy",
            "output_edge": "ClusteredEntityTable+MatchWeights+DiagnosticsReceipt",
            "strategy_genome_ref": "strategy:entity_resolution_compliance",
            "trial_policy_ref": "trial:high_value_task_paired_comparison",
            "ranking_features": ["proof_strength", "privacy_risk", "human_review_required",
                                 "contract_fit", "effect_risk", "negative_memory_risk",
                                 "runtime_cost", "route_reuse_count"],
            "candidate_paths": [
                _portfolio_path("path:splink_transparent_route", "genpath:schema_to_primitive_emit",
                                "searchpath:overlay_search", "planner:template_slot_fill",
                                "compiler:schema_driven_codegen", "runtime:database_job",
                                ["execpattern:dry_run_preview"],
                                ["proof:benchmark_scorecard", "proof:human_review"],
                                {"modelslot:schema_mapper": "deterministic_rule"},
                                "transparent match weights, tunable thresholds, clerical diagnostics",
                                "threshold tuned on one population fails on another"),
                _portfolio_path("path:bigquery_managed_route", "genpath:source_adapter_extract",
                                "searchpath:marketplace_source_search", "planner:exact_route_lookup",
                                "compiler:source_backed_wrapper_generation", "runtime:database_job",
                                ["execpattern:human_approval_before_side_effect"],
                                ["proof:side_effect_audit", "proof:privacy_pii_boundary_test"],
                                {"modelslot:legal_geography_escalation": "human_review_queue"},
                                "in-place provider matching with explicit permissions and job receipts",
                                "provider identity-graph logic is opaque to diagnostics"),
                _portfolio_path("path:local_blocking_brute_force", "genpath:repo_symbol_surface_extract",
                                "searchpath:exact_edge_search", "planner:deterministic_graph_search",
                                "compiler:deterministic_template_fill", "runtime:local_pure_function",
                                ["execpattern:strict_deterministic_execution"], ["proof:golden_fixtures"],
                                {"modelslot:edge_signature_infer": "deterministic_rule"},
                                "small N, high precision, zero cloud dependency",
                                "quadratic pair blowup when blocking keys are loose"),
            ],
        },
        {
            "portfolio_id": "portfolio:visual.formula_to_interactive_scene",
            "task_ref": "task:expanded_internal.visual.formula_to_interactive_scene",
            "input_edge": "FormulaLatexExpression+RenderPolicy",
            "output_edge": "InteractiveSceneArtifact+RenderReceipt",
            "strategy_genome_ref": "strategy:formula_to_interactive_scene",
            "trial_policy_ref": "trial:high_uncertainty_fanout",
            "ranking_features": ["proof_strength", "contract_fit", "runtime_cost",
                                 "runtime_llm_tokens", "route_reuse_count",
                                 "negative_memory_risk", "effect_risk", "freshness_confidence"],
            "candidate_paths": [
                _portfolio_path("path:manim_scene_template", "genpath:workflow_template_mine",
                                "searchpath:route_template_search", "planner:template_slot_fill",
                                "compiler:deterministic_template_fill", "runtime:container_job",
                                ["execpattern:strict_deterministic_execution"],
                                ["proof:sandbox_execution", "proof:golden_fixtures"],
                                {"modelslot:visual_scene_generator": "domain_lora_adapter"},
                                "pedagogical scene templates with render smoke tests",
                                "symbol drift between formula, scene, and narration"),
                _portfolio_path("path:threejs_component_remix", "genpath:source_adapter_extract",
                                "searchpath:type_compatible_edge_search", "planner:contract_diff_remix",
                                "compiler:schema_driven_codegen", "runtime:browser_worker",
                                ["execpattern:dry_run_preview"],
                                ["proof:sandbox_execution", "proof:regression_replay"],
                                {"modelslot:schema_mapper": "deterministic_rule"},
                                "interactive scenes remixed from near-match components",
                                "blank canvas when WebGL context loss is unhandled"),
                _portfolio_path("path:webgpu_shader_plan_delta", "genpath:model_draft_candidate",
                                "searchpath:hybrid_lexical_dense_search", "planner:llm_plan_delta",
                                "compiler:grammar_constrained_generation", "runtime:browser_worker",
                                ["execpattern:shadow_execution", "execpattern:bounded_llm_subcall"],
                                ["proof:sandbox_execution", "proof:benchmark_scorecard"],
                                {"modelslot:visual_scene_generator": "domain_lora_adapter",
                                 "modelslot:code_micro_patch": "small_local_language_model"},
                                "novel shader routes when no template covers the demand",
                                "shader compiles but renders the wrong mathematics"),
            ],
        },
    ]
    return _rows("compiled_primitive_route_portfolio", rows)


# ── compiled_route_lifecycle.jsonl ─────────────────────────────────────────
def _compiled_route_lifecycle() -> list[dict[str, Any]]:
    stages = [
        ("L0_discovered_candidate", "discovered candidate", "source or demand identified",
         ["discovery_note"]),
        ("L1_source_backed_candidate", "source-backed candidate", "source refs attached and resolvable",
         ["source_ref_receipt"]),
        ("L2_contract_extracted", "contract extracted", "input/output edges and schemas declared",
         ["contract_card"]),
        ("L3_effects_declared", "effects declared", "side-effect set enumerated and typed",
         ["effect_declaration"]),
        ("L4_proof_obligations_generated", "proof obligations generated", "obligations derived from effects and domain",
         ["proof_obligation_set"]),
        ("L5_route_compiled", "route compiled", "route lowered to a compiled artifact",
         ["compile_receipt"]),
        ("L6_planlock_emitted", "PlanLock emitted", "canonical PlanLock hashed and stored",
         ["planlock_digest"]),
        ("L7_deterministic_execution_tested", "deterministic execution tested", "artifact executed in sandbox",
         ["execution_receipt"]),
        ("L8_receipt_recorded", "receipt recorded", "execution and proof receipts persisted",
         ["proof_receipt", "execution_receipt"]),
        ("L9_benchmark_score_recorded", "benchmark score recorded",
         "scorecard recorded via a VERIFIED local benchmark adapter — external paper numbers never substitute",
         ["benchmark_scorecard", "adapter_receipt"]),
        ("L10_promoted_deprecated_or_negative_memory", "promoted, deprecated, or negative-memory only",
         "held-out wins + full receipts + human/owner gate for high-risk domains",
         ["held_out_win_receipt", "promotion_receipt_or_negative_memory"]),
    ]
    rows = []
    for index, (stage_key, title, gate, receipts) in enumerate(stages):
        rows.append({
            "stage_id": "lifecycle:" + stage_key,
            "stage_index": index,
            "title": title,
            "gate_to_advance": gate,
            "receipts_required": receipts,
        })
    rows[-1]["promotion_outcomes"] = ["promoted", "deprecated", "negative_memory_only"]
    rows[-1]["promotion_requires"] = [
        "held_out_task_wins",
        "proof_receipts",
        "adapter_receipts_for_any_benchmark_claim",
        "human_or_owner_gate_for_high_risk_domains",
    ]
    return _rows("compiled_primitive_route_lifecycle_stage", rows)


# ── model_slot_lanes.jsonl ─────────────────────────────────────────────────
def _model_slot_lanes() -> list[dict[str, Any]]:
    slots = [
        ("modelslot:intent_classifier", "decompose",
         ["deterministic_rule", "local_classifier", "small_local_language_model"],
         ["routes cheap tasks without frontier calls"], ["novel intents misrouted to a stale class"]),
        ("modelslot:request_decomposer", "decompose",
         ["deterministic_rule", "small_local_language_model", "cloud_frontier_model"],
         ["repeated request shapes with cached schemas"], ["over-decomposes novel compound intents"]),
        ("modelslot:primitive_candidate_generator", "generate",
         ["sql_or_graph_query", "small_local_language_model", "cloud_frontier_model"],
         ["L1 drafts from clear briefs"], ["hallucinates capabilities without source refs"]),
        ("modelslot:edge_signature_infer", "search",
         ["deterministic_rule", "small_local_language_model"],
         ["schemas are present to derive edges from"], ["ambiguous free-text io descriptions"]),
        ("modelslot:schema_mapper", "compile",
         ["deterministic_rule", "domain_lora_adapter", "cloud_frontier_model"],
         ["field aliasing with fixtures to verify against"], ["name similarity hides semantic mismatch"]),
        ("modelslot:search_query_rewriter", "search",
         ["deterministic_rule", "small_local_language_model"],
         ["vocabulary gap between intent and card text"], ["rewrite drifts off the task intent"]),
        ("modelslot:local_embedding", "search",
         ["embedding_model", "sql_or_graph_query"],
         ["semantic neighborhoods at scale"], ["out-of-domain vocabulary or placeholder embeddings"]),
        ("modelslot:cross_encoder_reranker", "search",
         ["cross_encoder_ranker", "deterministic_rule"],
         ["top-k precision before planning"], ["latency budget blown on large candidate sets"]),
        ("modelslot:route_planner", "plan",
         ["deterministic_rule", "small_local_language_model", "cloud_frontier_model"],
         ["ambiguity remains after deterministic search"], ["plans past the registry and invents members"]),
        ("modelslot:plan_delta_writer", "plan",
         ["small_local_language_model", "cloud_frontier_model"],
         ["compact deltas over candidate cards"], ["emits free-form plans instead of deltas"]),
        ("modelslot:compiler_error_repair", "repair",
         ["deterministic_rule", "small_local_language_model", "domain_lora_adapter"],
         ["retries targeted by validation errors"], ["open-ended regeneration loops"]),
        ("modelslot:proof_obligation_generator", "proof",
         ["deterministic_rule", "small_local_language_model"],
         ["obligations derived mechanically from the effect set"], ["under-proofs side-effectful routes"]),
        ("modelslot:negative_memory_classifier", "memory",
         ["local_classifier", "small_local_language_model"],
         ["repeated failure classes clustered cleanly"], ["over-general suppression blocks valid routes"]),
        ("modelslot:source_fragility_detector", "govern",
         ["deterministic_rule", "small_local_language_model"],
         ["flags drift-prone context (API versions, legal dates)"], ["misses silent schema drift"]),
        ("modelslot:legal_geography_escalation", "govern",
         ["deterministic_rule", "human_review_queue"],
         ["jurisdiction triggers route to human gates"], ["false confidence on cross-border rules"]),
        ("modelslot:visual_scene_generator", "compile",
         ["domain_lora_adapter", "vision_language_model", "cloud_frontier_model"],
         ["scene templates with render receipts"], ["renders cleanly but teaches the wrong thing"]),
        ("modelslot:code_micro_patch", "repair",
         ["small_local_language_model", "domain_lora_adapter", "cloud_frontier_model"],
         ["bounded patches from failing fixtures"], ["patch scope creeps beyond the failing edge"]),
        ("modelslot:receipt_summarizer", "telemetry",
         ["deterministic_rule", "small_local_language_model"],
         ["human-readable digests of receipt piles"], ["summary drops the load-bearing failure detail"]),
    ]
    rows = []
    for slot_id, stage, served_by, wins, fails in slots:
        rows.append({
            "slot_id": slot_id,
            "stage": stage,
            "served_by": served_by,
            "receipt_fields": list(MODEL_ROUTE_RECEIPT_FIELDS),
            "swap_policy": "hot-swappable; every selection recorded in a model_route_receipt",
            "wins_when": wins,
            "fails_when": fails,
        })
    return _rows("compiled_primitive_model_slot_lane", rows)


# ── adapter_lanes.jsonl ────────────────────────────────────────────────────
def _adapter_lanes() -> list[dict[str, Any]]:
    adapters = [
        ("adapter:entity_resolution_explain", ["modelslot:receipt_summarizer"],
         ["modelslot:route_planner"], ["lower_cost_at_same_quality", "faster_proof_generation"],
         ["clerical reviewers need per-match explanations at volume"],
         ["explanation sounds persuasive while the match is wrong"]),
        ("adapter:healthcare_fhir_mapper", ["modelslot:schema_mapper"],
         ["modelslot:legal_geography_escalation"], ["better_route_compile_success", "fewer_false_primitive_matches"],
         ["FHIR field aliasing recurs across customers"],
         ["rare extensions outside the adapter training set"]),
        ("adapter:legal_effective_date_detector", ["modelslot:source_fragility_detector", "modelslot:legal_geography_escalation"],
         ["modelslot:code_micro_patch"], ["less_source_escalation"],
         ["effective-date detection on legal sources is narrow and repeated"],
         ["novel jurisdictions phrase effectivity differently"]),
        ("adapter:geography_source_ranker", ["modelslot:cross_encoder_reranker"],
         ["modelslot:plan_delta_writer"], ["better_candidate_recall"],
         ["country/region-specific source authority reranking"],
         ["sparse geographies degrade to the base ranker"]),
        ("adapter:visual_threejs_scene", ["modelslot:visual_scene_generator"],
         ["modelslot:proof_obligation_generator"], ["better_route_compile_success"],
         ["Three.js scene emission from typed scene specs"],
         ["API version drift between adapter and runtime"]),
        ("adapter:shader_error_repair", ["modelslot:compiler_error_repair", "modelslot:code_micro_patch"],
         ["modelslot:route_planner"], ["better_repair_success"],
         ["GLSL/WGSL compile errors map to known fix classes"],
         ["driver-specific errors outside the training distribution"]),
        ("adapter:sql_bigquery_optimizer", ["modelslot:schema_mapper", "modelslot:code_micro_patch"],
         ["modelslot:legal_geography_escalation"], ["lower_cost_at_same_quality"],
         ["dialect-specific SQL rewrite with measurable cost deltas"],
         ["optimizer confidently rewrites semantics, not just cost"]),
        ("adapter:primitive_problem_solution_card", ["modelslot:primitive_candidate_generator"],
         ["modelslot:route_planner"], ["better_candidate_recall", "faster_proof_generation"],
         ["problem-solution card drafting from source-backed briefs"],
         ["fluent cards that overstate proof status"]),
        ("adapter:route_failure_classifier", ["modelslot:negative_memory_classifier"],
         ["modelslot:plan_delta_writer"], ["fewer_false_primitive_matches", "better_repair_success"],
         ["failure-layer classification feeding the repair ladder"],
         ["cross-layer failures collapse into one noisy class"]),
    ]
    rows = []
    for adapter_id, allowed, disallowed, lift, wins, fails in adapters:
        rows.append({
            "adapter_id": adapter_id,
            "allowed_slots": allowed,
            "disallowed_slots": disallowed,
            "required_record_fields": list(ADAPTER_RECORD_FIELDS),
            "lift_criteria": lift,
            "promotion_rule": "adopt only on measurable downstream lift versus rules/retrieval/larger models on held-out tasks",
            "wins_when": wins,
            "fails_when": fails,
        })
    return _rows("compiled_primitive_adapter_lane", rows)


# ── micro_agent_envelopes.jsonl ────────────────────────────────────────────
def _micro_agent_envelopes() -> list[dict[str, Any]]:
    agents = [
        ("microagent:source_surface_scout", "find and card new primitive source surfaces",
         24, 60000, 900, ["new marketplace/registry surfaces appear faster than curators"],
         ["scout cards surfaces that fail the license/terms gate"]),
        ("microagent:fragile_context_scout", "flag drift-prone context (versions, dates, schemas) in existing cards",
         20, 40000, 600, ["fragility fields are missing on older cards"],
         ["flags noise, burying real fragility"]),
        ("microagent:geography_source_scout", "find authoritative per-country/jurisdiction sources",
         24, 60000, 900, ["geography overlays are sparse"],
         ["mistakes aggregator sites for authorities"]),
        ("microagent:legal_source_scout", "find and date-stamp legal/regulatory sources",
         24, 60000, 900, ["legal freshness policies need effective dates"],
         ["misreads effective vs publication dates"]),
        ("microagent:api_version_scout", "detect API version changes against carded contracts",
         16, 30000, 600, ["provider changelogs move faster than manual review"],
         ["announces breaking changes that are additive"]),
        ("microagent:primitive_bundle_curator", "assemble and prune CandidateBundles for repeated demands",
         20, 50000, 600, ["bundle quality drives plan quality"],
         ["over-prunes and hides the winning alternate"]),
        ("microagent:route_portfolio_builder", "draft candidate path portfolios for a new task family",
         28, 80000, 1200, ["a new family needs >=3 comparable candidate paths"],
         ["drafts paths that reference nonexistent registry members"]),
        ("microagent:negative_memory_writer", "convert failure receipts into keyed negative-memory records",
         16, 30000, 600, ["failures repeat because nothing recorded them"],
         ["keys are too specific to ever match again"]),
        ("microagent:benchmark_case_synthesizer", "synthesize benchmark task fixtures from carded demands",
         28, 80000, 1200, ["a source family lacks runnable fixtures"],
         ["synthesizes fixtures the arm under test was tuned on"]),
        ("microagent:visual_render_debugger", "diagnose blank-canvas/render failures from receipts",
         20, 50000, 900, ["render failures need structured diagnosis, not rerolls"],
         ["chases driver quirks that receipts cannot show"]),
        ("microagent:entity_resolution_threshold_tuner", "tune ER thresholds against labeled pairs",
         24, 60000, 900, ["threshold curves need periodic re-fit per population"],
         ["tunes on one population and ships to another"]),
    ]
    rows = []
    for agent_id, job, max_steps, max_tokens, max_wall, wins, fails in agents:
        rows.append({
            "agent_id": agent_id,
            "job": job,
            "envelope": {
                "input_budget": "bounded brief + carded refs only",
                "source_allowlist": "declared per run; no open web without allowlist",
                "tool_allowlist": "declared per run; read-heavy, side-effect-free by default",
                "max_steps": max_steps,
                "max_tokens": max_tokens,
                "max_wall_time_seconds": max_wall,
                "stop_conditions": ["budget_exhausted", "goal_satisfied", "stop_file_present"],
                "artifact_outputs": ["candidate rows only"],
                "receipt_outputs": ["run_receipt", "budget_receipt"],
                "human_review_trigger": "any legal/health/finance surface or side-effectful proposal",
            },
            "budget_note": MICRO_AGENT_BUDGET_NOTE,
            "must_beat": "the deterministic alternative on proofed outcomes, not on persuasiveness",
            "wins_when": wins,
            "fails_when": fails,
        })
    return _rows("compiled_primitive_micro_agent_envelope", rows)


# ── trial_run_policies.jsonl ───────────────────────────────────────────────
def _trial_run_policies() -> list[dict[str, Any]]:
    rows = [
        {"policy_id": "trial:high_uncertainty_fanout",
         "trigger": "no promoted route and route_score variance across candidates is high",
         "parallelism": "run 3-5 candidate paths simultaneously on the same fixtures",
         "wins_when": ["uncertainty is high and the task value justifies parallel spend"],
         "fails_when": ["fanout on routine tasks burns budget for no ranking gain"]},
        {"policy_id": "trial:high_value_task_paired_comparison",
         "trigger": "task family is high-stakes and arms must be compared apples-to-apples",
         "parallelism": "paired runs: same task, same source refs, same acceptance criteria, same sandbox",
         "wins_when": ["a promotion decision needs defensible paired evidence"],
         "fails_when": ["pairing constraints cannot be held (fixtures drift between runs)"]},
        {"policy_id": "trial:path_family_evidence_gathering",
         "trigger": "a path family lacks receipts for the ranking model",
         "parallelism": "scheduled sweep across the family's candidate paths",
         "wins_when": ["the system is deliberately buying evidence for a family"],
         "fails_when": ["sweeps run against unrepresentative synthetic tasks"]},
        {"policy_id": "trial:routine_champion_with_challenger_sampling",
         "trigger": "champion route exists and traffic is routine",
         "parallelism": "champion serves; challengers sampled at the genome exploration_rate",
         "wins_when": ["steady traffic amortizes low-rate challenger sampling"],
         "fails_when": ["non-stationary drift outpaces the sampling rate"]},
        {"policy_id": "trial:adapter_vs_rule_ab",
         "trigger": "a LoRA/adapter lane claims lift over the deterministic rule",
         "parallelism": "A/B the adapter lane against the rule lane on a bounded task set",
         "wins_when": ["adapter admission needs measured downstream lift"],
         "fails_when": ["A/B metric is persuasion (rubric text) instead of proofed outcomes"]},
    ]
    for row in rows:
        row["comparison_receipt_fields"] = list(COMPARISON_RECEIPT_FIELDS)
        row["isolation"] = "trial runs are sandboxed; no production side effects; losers write negative memory"
    return _rows("compiled_primitive_trial_run_policy", rows)


# ── exploration_policies.jsonl ─────────────────────────────────────────────
def _exploration_policies() -> list[dict[str, Any]]:
    rows = [
        {"policy_id": "explore:random_search", "wins_when": ["cheap baseline over unknown, high-dimensional spaces"], "fails_when": ["wastes budget near known optima"]},
        {"policy_id": "explore:grid_search_small_spaces", "wins_when": ["<=3 discrete, low-cardinality dimensions"], "fails_when": ["combinatorial explosion beyond small grids"]},
        {"policy_id": "explore:bayesian_optimization", "wins_when": ["expensive evaluations over smooth responses"], "fails_when": ["noisy, discontinuous receipt landscapes"]},
        {"policy_id": "explore:successive_halving", "wins_when": ["many arms that can be partially evaluated cheaply"], "fails_when": ["early performance misleads about final performance"]},
        {"policy_id": "explore:population_based_training", "wins_when": ["long-running populations that tune while running"], "fails_when": ["small budgets that cannot sustain a population"]},
        {"policy_id": "explore:evolutionary_mutation", "wins_when": ["recombinable route fragments with fitness receipts"], "fails_when": ["fitness receipts too sparse to select on"]},
        {"policy_id": "explore:multi_armed_bandit", "wins_when": ["stationary path families with steady traffic"], "fails_when": ["non-stationary drift invalidates arm estimates"]},
        {"policy_id": "explore:contextual_bandit", "wins_when": ["per-task-context routing after receipts accumulate"], "fails_when": ["cold start with no receipts"]},
        {"policy_id": "explore:mcts_route_search", "wins_when": ["large route spaces with cheap rollout scoring"], "fails_when": ["no cheap simulator for rollouts"]},
        {"policy_id": "explore:novelty_search", "wins_when": ["escaping a stale champion plateau"], "fails_when": ["unbounded novelty without proof gates"]},
        {"policy_id": "explore:active_learning", "wins_when": ["human labels are costly and must be targeted"], "fails_when": ["miscalibrated uncertainty targets the wrong items"]},
        {"policy_id": "explore:human_review_sampling", "wins_when": ["high-risk domains need periodic ground truth"], "fails_when": ["reviewer throughput caps the sample size"]},
    ]
    for row in rows:
        row["budget_discipline"] = "runs inside a declared experiment budget; every trial emits a comparison receipt"
    return _rows("compiled_primitive_exploration_policy", rows)


# ── path_sprout_rules.jsonl ────────────────────────────────────────────────
def _path_sprout_rules() -> list[dict[str, Any]]:
    sprouts = [
        ("sprout:mutate_blocking_rule", "search", ["ER candidate-pair reduction vs recall trade-off shifts"], ["loose rules explode pair counts"]),
        ("sprout:mutate_threshold", "plan", ["threshold curves drift with population"], ["threshold overfits the sprouting task"]),
        ("sprout:mutate_retriever_weights", "search", ["hybrid fusion weights are stale for a family"], ["weights chase one query family and regress others"]),
        ("sprout:mutate_context_depth_limit", "search", ["tasks resolve shallower than the current depth cap"], ["cap starves genuinely deep tasks"]),
        ("sprout:mutate_candidate_bundle_size", "search", ["bundle too small to contain the winner"], ["oversized bundles blow the rerank latency budget"]),
        ("sprout:mutate_model_slot_assignment", "model", ["a cheaper lane may serve the slot at equal quality"], ["quality cliff hidden by a weak proxy metric"]),
        ("sprout:mutate_lora_adapter_choice", "model", ["a domain adapter may beat the base lane"], ["adapter wins the sprouting task, loses held-out"]),
        ("sprout:mutate_route_member_order", "plan", ["reordering members may cut latency or effects"], ["order-dependent semantics break silently"]),
        ("sprout:mutate_proof_gate_order", "proof", ["cheaper gates first may fail faster"], ["reordering delays the gate that catches real damage"]),
        ("sprout:mutate_cache_policy", "cache", ["hit rates suggest a longer/shorter TTL"], ["stale hits leak into promoted routes"]),
        ("sprout:mutate_visual_render_settings", "compile", ["render quality/cost trade-off unexplored"], ["settings pass smoke tests but degrade pedagogy"]),
        ("sprout:mutate_shader_precision", "compile", ["lower precision may hold receipts at lower cost"], ["precision loss surfaces only on edge geometries"]),
    ]
    rows = []
    for sprout_id, layer, wins, fails in sprouts:
        rows.append({
            "sprout_id": sprout_id,
            "target_layer": layer,
            "status": "candidate",
            "isolation_rule": "experiment lane only; never serves production traffic until promoted",
            "promotion_rule": "must win on held-out tasks, not only the task that created it",
            "rollback": "parent path remains champion; losing sprout is retired into negative memory",
            "wins_when": wins,
            "fails_when": fails,
        })
    return _rows("compiled_primitive_path_sprout_rule", rows)


# ── telemetry_signals.jsonl ────────────────────────────────────────────────
def _telemetry_signals() -> list[dict[str, Any]]:
    spans = [
        ("decompose_request", ["decomposition_learning"]),
        ("retrieve_candidates", ["cooccurrence_learning", "cache_policy_tuning"]),
        ("rerank_candidates", ["adapter_training_data"]),
        ("compile_route", ["route_economics_accounting"]),
        ("run_trial_path", ["champion_challenger_ranking", "sprout_selection"]),
        ("execute_proofs", ["champion_challenger_ranking"]),
        ("emit_receipts", ["route_economics_accounting", "adapter_training_data"]),
        ("promote_or_record_negative_memory", ["negative_memory_suppression", "champion_challenger_ranking"]),
    ]
    traces = [
        ("request_decomposition_trace", ["decomposition_learning"]),
        ("candidate_retrieval_trace", ["cooccurrence_learning", "cache_policy_tuning"]),
        ("reranking_trace", ["adapter_training_data"]),
        ("primitive_cooccurrence_trace", ["cooccurrence_learning", "decomposition_learning"]),
        ("route_compile_trace", ["route_economics_accounting"]),
        ("proof_execution_trace", ["champion_challenger_ranking"]),
        ("model_slot_trace", ["adapter_training_data", "sprout_selection"]),
        ("cache_hit_miss_trace", ["cache_policy_tuning"]),
        ("source_escalation_trace", ["route_economics_accounting", "decomposition_learning"]),
        ("repair_loop_trace", ["negative_memory_suppression", "sprout_selection"]),
        ("human_review_trace", ["champion_challenger_ranking"]),
    ]
    metrics = [
        ("task_success", "ratio", "gauge", ["champion_challenger_ranking"]),
        ("proof_success", "ratio", "gauge", ["champion_challenger_ranking"]),
        ("compile_success", "ratio", "gauge", ["champion_challenger_ranking", "sprout_selection"]),
        ("tokens_to_plan", "tokens", "histogram", ["route_economics_accounting"]),
        ("tokens_to_pass", "tokens", "histogram", ["route_economics_accounting", "cache_policy_tuning"]),
        ("latency_p50", "ms", "histogram", ["champion_challenger_ranking"]),
        ("latency_p95", "ms", "histogram", ["champion_challenger_ranking"]),
        ("source_read_depth", "depth_level", "histogram", ["route_economics_accounting", "decomposition_learning"]),
        ("source_files_read", "count", "histogram", ["route_economics_accounting"]),
        ("model_calls_by_slot", "count", "counter", ["adapter_training_data", "sprout_selection"]),
        ("adapter_calls_by_slot", "count", "counter", ["adapter_training_data"]),
        ("cache_hit_rate", "ratio", "gauge", ["cache_policy_tuning"]),
        ("primitive_reuse_count", "count", "counter", ["cooccurrence_learning", "decomposition_learning"]),
        ("route_reuse_count", "count", "counter", ["route_economics_accounting", "cooccurrence_learning"]),
        ("false_match_rate", "ratio", "gauge", ["sprout_selection", "negative_memory_suppression"]),
        ("false_block_rate", "ratio", "gauge", ["negative_memory_suppression"]),
        ("repair_attempts", "count", "counter", ["sprout_selection"]),
        ("negative_memory_created", "count", "counter", ["negative_memory_suppression"]),
        ("human_review_rate", "ratio", "gauge", ["champion_challenger_ranking"]),
        ("artifact_quality_score", "score", "gauge", ["adapter_training_data", "champion_challenger_ranking"]),
        ("downstream_regression_rate", "ratio", "gauge", ["champion_challenger_ranking", "cache_policy_tuning"]),
        ("cost_per_success", "usd", "gauge", ["champion_challenger_ranking", "route_economics_accounting"]),
    ]
    rows: list[dict[str, Any]] = []
    for order, (name, loops) in enumerate(spans, start=1):
        rows.append({"signal_id": f"telemetry:span:{name}", "signal_kind": "trace_span",
                     "span_order": order, "otel_shape": "span", "feeds_back_into": loops})
    for name, loops in traces:
        rows.append({"signal_id": f"telemetry:trace:{name}", "signal_kind": "trace_family",
                     "otel_shape": "span", "feeds_back_into": loops})
    for name, unit, shape, loops in metrics:
        rows.append({"signal_id": f"telemetry:metric:{name}", "signal_kind": "metric",
                     "unit": unit, "otel_shape": shape, "feeds_back_into": loops})
    return _rows("compiled_primitive_telemetry_signal", rows)


# ── primitive_cooccurrence_examples.jsonl ──────────────────────────────────
def _primitive_cooccurrence_examples() -> list[dict[str, Any]]:
    examples = [
        ("cooc:csv_profile__schema_infer__schema_validate",
         ["csv_profile", "schema_infer", "schema_validate"],
         "tabular intake almost always chains profile -> infer -> validate"),
        ("cooc:blocking_key__candidate_pair__comparison_vector",
         ["blocking_key_generate", "candidate_pair_generate", "comparison_vector_emit"],
         "the ER front half is one skeleton; splitting it loses the reduction receipts"),
        ("cooc:openapi_extract__auth_review__contract_test",
         ["openapi_operation_extract", "auth_scope_review", "contract_test_generate"],
         "endpoint carding without auth review ships unsafe wrappers"),
        ("cooc:threejs_scene__camera_controls__canvas_receipt",
         ["threejs_scene_create", "camera_controls_bind", "canvas_nonblank_receipt"],
         "interactive scenes need controls plus a non-blank proof to count"),
        ("cooc:shader_validate__frame_budget__visual_regression",
         ["shader_compile_validate", "frame_budget_receipt", "visual_regression_receipt"],
         "shader work is only done when compile, budget, and visual receipts agree"),
        ("cooc:legal_search__effective_date__jurisdiction_filter",
         ["legal_source_search", "effective_date_check", "jurisdiction_filter"],
         "legal answers without date+jurisdiction gates are wrong answers waiting"),
    ]
    derived = [
        ("derived:primitive_pair_affinity", ["better request decomposition", "route autocomplete"]),
        ("derived:primitive_group_affinity", ["primitive group discovery", "CandidateBundle construction"]),
        ("derived:route_skeleton", ["route autocomplete", "benchmark task generation"]),
        ("derived:frequent_subroute", ["cache key selection", "CandidateBundle construction"]),
        ("derived:anti_affinity", ["negative-memory suppression", "planner pruning"]),
        ("derived:missing_middle_edge", ["new primitive demand discovery"]),
        ("derived:cache_candidate", ["cache key selection", "cache policy tuning"]),
        ("derived:promotion_candidate", ["promotion queue ranking"]),
        ("derived:decomposition_template", ["better request decomposition", "proof plan inference"]),
    ]
    rows: list[dict[str, Any]] = []
    for cooc_id, members, edge_note in examples:
        rows.append({"cooc_id": cooc_id, "kind": "cooccurrence_example", "members": members,
                     "edge_note": edge_note,
                     "derived": ["derived:primitive_group_affinity", "derived:route_skeleton"]})
    for derived_id, used_for in derived:
        rows.append({"cooc_id": derived_id, "kind": "derived_record_kind", "used_for": used_for})
    return _rows("compiled_primitive_cooccurrence_record", rows)


# ── cache_policies.jsonl ───────────────────────────────────────────────────
def _cache_policies() -> list[dict[str, Any]]:
    caches = [
        ("cache:source_surface_card_cache", ["api_version_change", "schema_change"],
         ["surfaces are re-read constantly during search"], ["stale cards route to dead surfaces"]),
        ("cache:schema_fingerprint_cache", ["schema_change"],
         ["fingerprints gate cheap schema-compatible search"], ["fingerprint collision across similar schemas"]),
        ("cache:edge_signature_cache", ["schema_change"],
         ["edge search is the hottest lookup"], ["signature drift after contract edits"]),
        ("cache:embedding_cache", ["model_or_adapter_change"],
         ["re-embedding unchanged cards wastes local compute"], ["embeddings from a retired model mix into search"]),
        ("cache:candidate_bundle_cache", ["schema_change", "model_or_adapter_change", "benchmark_regression"],
         ["repeated demands re-request the same bundle"], ["bundle hides newly promoted routes"]),
        ("cache:route_skeleton_cache", ["benchmark_regression", "schema_change"],
         ["skeletons accelerate decomposition"], ["skeleton fossilizes a superseded chain"]),
        ("cache:planlock_cache", ["schema_change", "api_version_change"],
         ["promoted PlanLocks are the zero-token fast path"], ["locked plan outlives its upstream contract"]),
        ("cache:proof_fixture_cache", ["schema_change", "benchmark_regression"],
         ["fixtures are expensive to synthesize"], ["fixtures age out of the real distribution"]),
        ("cache:execution_receipt_cache", ["retention_policy_expiry"],
         ["receipts feed ranking and economics"], ["unbounded retention becomes a privacy liability"]),
        ("cache:negative_memory_cache", ["benchmark_regression", "model_or_adapter_change"],
         ["failure suppression must be instant"], ["a new model fixes old failures but memory still blocks"]),
        ("cache:render_asset_cache", ["model_or_adapter_change", "retention_policy_expiry"],
         ["render assets are costly to regenerate"], ["stale assets mask regressions in the render route"]),
        ("cache:entity_resolution_block_cache", ["schema_change", "model_or_adapter_change"],
         ["blocking keys are recomputed on every batch"], ["normalization change silently shifts block membership"]),
    ]
    rows = []
    for cache_id, triggers, wins, fails in caches:
        rows.append({
            "cache_id": cache_id,
            "policy_rules": [
                "never_cache_sensitive_data",
                "cache_source_refs_not_raw_private_payloads",
                "cache_promoted_routes_longer",
                "cache_candidate_routes_shorter",
            ],
            "invalidation_triggers": triggers,
            "value_metrics": ["tokens_saved", "latency_saved", "source_reads_avoided",
                              "proofs_reused", "regressions_caused", "stale_cache_hits", "privacy_risk"],
            "privacy_rule": "cache source refs, never raw private payloads; tenant-private lineage never becomes global",
            "wins_when": wins,
            "fails_when": fails,
        })
    return _rows("compiled_primitive_cache_policy", rows)


# ── strategy_genome_examples.jsonl ─────────────────────────────────────────
def _strategy_genome_examples() -> list[dict[str, Any]]:
    rows = [
        {
            "genome_id": "strategy:customer_record_import",
            "task_family": "customer_record_import",
            "components": {
                "decomposer": "modelslot:request_decomposer",
                "retriever": "searchpath:hybrid_lexical_dense_search",
                "reranker": "modelslot:cross_encoder_reranker",
                "planner": "planner:llm_plan_delta",
                "compiler": "compiler:deterministic_template_fill",
                "proof_policy": ["proof:contract_tests", "proof:golden_fixtures", "proof:idempotency_tests"],
                "cache_policy": ["cache:candidate_bundle_cache", "cache:planlock_cache"],
            },
            "prompt_profile": "prompt-profile/route-planner-compact",
            "retrieval_profile": "retrieval-profile/edge-first-hybrid",
            "parameters": {
                "candidate_bundle_size": 12,
                "max_context_depth": "L3_BEHAVIOR",
                "source_fallback_threshold": 0.62,
                "exploration_rate": 0.05,
            },
            "rollout_policy": {
                "mode": "shadow_then_champion_challenger",
                "promotion_gate": "held_out_wins_plus_full_receipts",
                "rollback": "previous champion PlanLock retained losslessly",
            },
            "mutation_surface": ["sprout:mutate_candidate_bundle_size", "sprout:mutate_context_depth_limit",
                                 "sprout:mutate_model_slot_assignment"],
        },
        {
            "genome_id": "strategy:tool_route_single_call",
            "task_family": "tool_route_single_call",
            "components": {
                "decomposer": "modelslot:intent_classifier",
                "retriever": "searchpath:exact_edge_search",
                "reranker": "modelslot:cross_encoder_reranker",
                "planner": "planner:exact_route_lookup",
                "compiler": "compiler:deterministic_template_fill",
                "proof_policy": ["proof:contract_tests", "proof:schema_validation"],
                "cache_policy": ["cache:edge_signature_cache", "cache:planlock_cache"],
            },
            "prompt_profile": "prompt-profile/intent-classifier-minimal",
            "retrieval_profile": "retrieval-profile/exact-edge-first",
            "parameters": {
                "candidate_bundle_size": 8,
                "max_context_depth": "L2_CONTRACT",
                "source_fallback_threshold": 0.7,
                "exploration_rate": 0.05,
            },
            "rollout_policy": {
                "mode": "champion_with_sampled_challengers",
                "promotion_gate": "held_out_wins_plus_full_receipts",
                "rollback": "previous champion PlanLock retained losslessly",
            },
            "mutation_surface": ["sprout:mutate_model_slot_assignment", "sprout:mutate_retriever_weights"],
        },
        {
            "genome_id": "strategy:entity_resolution_compliance",
            "task_family": "entity_resolution_compliance",
            "components": {
                "decomposer": "modelslot:request_decomposer",
                "retriever": "searchpath:overlay_search",
                "reranker": "modelslot:cross_encoder_reranker",
                "planner": "planner:template_slot_fill",
                "compiler": "compiler:schema_driven_codegen",
                "proof_policy": ["proof:benchmark_scorecard", "proof:privacy_pii_boundary_test", "proof:human_review"],
                "cache_policy": ["cache:entity_resolution_block_cache", "cache:proof_fixture_cache"],
            },
            "prompt_profile": "prompt-profile/match-explainer-clerical",
            "retrieval_profile": "retrieval-profile/overlay-jurisdiction-first",
            "parameters": {
                "candidate_bundle_size": 10,
                "max_context_depth": "L3_BEHAVIOR",
                "source_fallback_threshold": 0.55,
                "exploration_rate": 0.02,
            },
            "rollout_policy": {
                "mode": "shadow_then_human_gated_promotion",
                "promotion_gate": "held_out_wins_plus_clerical_review_receipts",
                "rollback": "previous champion retained; false merges re-reviewed",
            },
            "mutation_surface": ["sprout:mutate_blocking_rule", "sprout:mutate_threshold"],
        },
        {
            "genome_id": "strategy:formula_to_interactive_scene",
            "task_family": "formula_to_interactive_scene",
            "components": {
                "decomposer": "modelslot:request_decomposer",
                "retriever": "searchpath:route_template_search",
                "reranker": "modelslot:cross_encoder_reranker",
                "planner": "planner:template_slot_fill",
                "compiler": "compiler:grammar_constrained_generation",
                "proof_policy": ["proof:sandbox_execution", "proof:regression_replay"],
                "cache_policy": ["cache:render_asset_cache", "cache:route_skeleton_cache"],
            },
            "prompt_profile": "prompt-profile/scene-spec-typed",
            "retrieval_profile": "retrieval-profile/template-family-first",
            "parameters": {
                "candidate_bundle_size": 8,
                "max_context_depth": "L4_ROUTE",
                "source_fallback_threshold": 0.6,
                "exploration_rate": 0.1,
            },
            "rollout_policy": {
                "mode": "trial_fanout_then_champion",
                "promotion_gate": "held_out_wins_plus_render_receipts",
                "rollback": "previous champion retained losslessly",
            },
            "mutation_surface": ["sprout:mutate_visual_render_settings", "sprout:mutate_shader_precision",
                                 "sprout:mutate_lora_adapter_choice"],
        },
    ]
    return _rows("compiled_primitive_strategy_genome", rows)


# ── route_economics_model.json ─────────────────────────────────────────────
def _route_economics_model() -> dict[str, Any]:
    return {
        "record_type": "compiled_primitive_route_economics_model",
        "model_id": "economics:route_amortization",
        **BOUNDARY,
        "amortization": {
            "compile_cost_fields": ["score:tokens_to_plan", "score:tokens_to_pass"],
            "runtime_cost_fields": ["score:runtime_llm_tokens", "score:cost_per_success"],
            "reuse_fields": ["score:route_reuse", "score:tokens_avoided_to_date"],
            "break_even_definition": "break_even_tasks is computed per route from receipts (compile cost over per-run tokens avoided); never hand-typed",
        },
        "route_score": {
            "positive_terms": ["proof_strength", "source_authority", "contract_fit", "reuse_value"],
            "negative_terms": ["effect_risk", "negative_memory_risk", "freshness_risk",
                               "total_cost", "source_escalation_depth"],
            "score_is_ranking_aid_not_truth": True,
            "initial_weighting": "transparent equal weights until receipts accumulate",
            "upgrade_path": "contextual bandit / online ranking only after comparison receipts accumulate",
        },
        "ranking_features": [
            "task_success_probability", "compile_success_probability", "proof_strength",
            "source_authority", "freshness_confidence", "contract_fit", "negative_memory_risk",
            "effect_risk", "privacy_risk", "runtime_latency", "runtime_cost", "compile_cost",
            "tokens_to_plan", "runtime_llm_tokens", "source_context_tokens",
            "source_escalation_depth", "route_reuse_count", "tokens_avoided_to_date",
            "promotion_level", "human_review_required",
        ],
    }


# ── champion_challenger_policy.json ────────────────────────────────────────
def _champion_challenger_policy() -> dict[str, Any]:
    return {
        "record_type": "compiled_primitive_champion_challenger_policy",
        "policy_id": "policy:champion_challenger_retirement",
        **BOUNDARY,
        "task_family_policy": {
            "champion_route": "one current champion per task family, served by default",
            "challenger_routes": "challengers sampled at the genome exploration_rate",
            "exploration_rate_default": 0.05,
            "promotion_gate": ["held_out_task_wins", "proof_receipts", "no_regression_on_replay",
                               "adapter_receipts_for_any_benchmark_claim"],
            "retirement_gate": ["sustained_loss_to_champion", "repeated_negative_memory",
                                "freshness_violation"],
            "rollback_path": "previous champion PlanLock retained losslessly; retirement is reversible",
        },
        "ranking": {
            "multi_objective_features": ["success_rate", "proof_strength", "cost", "latency",
                                         "source_escalation_depth", "privacy_risk", "side_effect_risk",
                                         "maintenance_cost", "reuse_count", "freshness",
                                         "human_review_burden"],
            "contextual": True,
            "note": "best-to-worst is explicit per comparable path family but contextual by task type; one global winner is never declared",
        },
        "per_task_type_winner_slots": [
            "best_for_repeated_promoted_route",
            "best_for_near_match_schema_variants",
            "best_for_new_marketplace_surface",
            "best_for_high_risk_regulated_domain",
            "best_for_large_tool_graph",
            "best_for_repo_repair",
            "best_for_data_science_search",
            "best_for_browser_or_terminal_workflow",
        ],
    }


# ── route_attempt_training_capture_policy.json ─────────────────────────────
def _route_attempt_training_capture_policy() -> dict[str, Any]:
    return {
        "record_type": "compiled_primitive_route_attempt_training_capture_policy",
        "policy_id": "policy:route_attempt_training_capture",
        **BOUNDARY,
        "every_route_attempt_becomes_training_data": True,
        "captured_records": [
            "comparison_receipt", "model_route_receipt", "proof_receipt", "execution_receipt",
            "negative_memory_record", "telemetry_trace_span", "human_review_outcome",
        ],
        "training_consumers": [
            "cross_encoder_reranker_training", "lora_adapter_training", "route_ranking_model",
            "negative_memory_classifier_training", "decomposition_template_mining",
        ],
        "lineage_fields": [
            "dataset_id", "dataset_version", "source_snapshot_hash", "schema_hash", "row_count",
            "sample_policy", "privacy_boundary", "license_or_terms_status", "freshness_timestamp",
            "run_date", "commit_sha", "producer_strategy", "validation_receipts",
        ],
        "isolation": {
            "experimental_sprouts": "experiment lane only; excluded from production truth and promoted-route serving until the promotion gate passes",
            "privacy": "cache source refs, never raw private payloads; tenant-private lineage never becomes global",
        },
        "lossless_distillation_clause": "raw receipts, intermediates, held-out items, and rejected candidates are preserved and versioned; distilled training sets carry lineage back to receipts and a rollback target",
    }


# ── Pack assembly ──────────────────────────────────────────────────────────
JSONL_BUILDERS: dict[str, Any] = {
    "benchmark_sources.jsonl": _benchmark_sources,
    "benchmark_task_demands.jsonl": _benchmark_task_demands,
    "primitive_generation_paths.jsonl": _primitive_generation_paths,
    "primitive_search_paths.jsonl": _primitive_search_paths,
    "route_planning_paths.jsonl": _route_planning_paths,
    "compilation_paths.jsonl": _compilation_paths,
    "proof_paths.jsonl": _proof_paths,
    "runtime_execution_paths.jsonl": _runtime_execution_paths,
    "repair_ladder.jsonl": _repair_ladder,
    "comparison_arms.jsonl": _comparison_arms,
    "scorecard_fields.jsonl": _scorecard_fields,
    "route_portfolio_examples.jsonl": _route_portfolio_examples,
    "compiled_route_lifecycle.jsonl": _compiled_route_lifecycle,
    "model_slot_lanes.jsonl": _model_slot_lanes,
    "adapter_lanes.jsonl": _adapter_lanes,
    "micro_agent_envelopes.jsonl": _micro_agent_envelopes,
    "trial_run_policies.jsonl": _trial_run_policies,
    "exploration_policies.jsonl": _exploration_policies,
    "path_sprout_rules.jsonl": _path_sprout_rules,
    "telemetry_signals.jsonl": _telemetry_signals,
    "primitive_cooccurrence_examples.jsonl": _primitive_cooccurrence_examples,
    "cache_policies.jsonl": _cache_policies,
    "strategy_genome_examples.jsonl": _strategy_genome_examples,
}

JSON_BUILDERS: dict[str, Any] = {
    "route_economics_model.json": _route_economics_model,
    "champion_challenger_policy.json": _champion_challenger_policy,
    "route_attempt_training_capture_policy.json": _route_attempt_training_capture_policy,
}


def build_pack() -> dict[str, Any]:
    """Return {filename: rows-or-object} for every non-manifest pack file."""
    pack: dict[str, Any] = {name: builder() for name, builder in JSONL_BUILDERS.items()}
    pack.update({name: builder() for name, builder in JSON_BUILDERS.items()})
    return pack


def _canonical_bytes(pack: dict[str, Any]) -> bytes:
    parts: list[str] = []
    for name in sorted(pack):
        value = pack[name]
        if isinstance(value, list):
            parts.extend(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in value)
        else:
            parts.append(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return ("\n".join(parts) + "\n").encode("utf-8")


def build_manifest(pack: dict[str, Any]) -> dict[str, Any]:
    row_counts = {name: len(rows) for name, rows in pack.items() if isinstance(rows, list)}
    files = {name.rsplit(".", 1)[0]: name for name in sorted(pack)}
    return {
        "record_type": "compiled_primitive_route_benchmark_seed_pack_manifest",
        "pack_id": "compiled-primitive-route-benchmark-seeds",
        **BOUNDARY,
        "version": "0.1.0",
        "generator": "scripts/build_compiled_primitive_route_benchmark_seeds.py",
        "generated_utc": dt.datetime.now(dt.timezone.utc).date().isoformat(),
        "source_family": COMPILED_PRIMITIVE_ROUTE_BENCHMARK_SEEDS_SOURCE_FAMILY,
        "source_status": COMPILED_PRIMITIVE_ROUTE_BENCHMARK_SEEDS_SOURCE_STATUS,
        "evidence_status": COMPILED_PRIMITIVE_ROUTE_BENCHMARK_SEEDS_EVIDENCE_STATUS,
        "boundary": "candidate=true; serves_truth=false; external paper/benchmark numbers are prior art, never local measured evidence; no benchmark claim promoted without adapter receipts",
        "files": files,
        "file_count": len(files),
        "row_counts": row_counts,
        "total_rows": sum(row_counts.values()),
        "content_sha256": hashlib.sha256(_canonical_bytes(pack)).hexdigest(),
        "reuses": [
            "catalog/knowledge-packs/data/benchmark-lab-adapter-catalog",
            "catalog/knowledge-packs/data/marketplace-primitive-source-surfaces",
        ],
        "wired_into": "docs/codex/claude-fable-compiled-primitive-routes-handoff.md",
    }


def write_pack() -> dict[str, Any]:
    pack = build_pack()
    manifest = build_manifest(pack)
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    for name, value in pack.items():
        path = PACK_DIR / name
        if isinstance(value, list):
            with path.open("w", encoding="utf-8") as handle:
                for row in value:
                    handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        else:
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
    (PACK_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _ids(rows: list[dict[str, Any]], field: str) -> set[str]:
    values = [str(row.get(field) or "") for row in rows]
    assert "" not in values, f"missing {field} on a row"
    assert len(values) == len(set(values)), f"duplicate {field} detected"
    return set(values)


def self_test() -> int:
    pack = build_pack()
    manifest = build_manifest(pack)

    for name, value in pack.items():
        rows = value if isinstance(value, list) else [value]
        for row in rows:
            assert row.get("candidate") is True and row.get("serves_truth") is False, \
                f"{name}: truth boundary violated"

    sources = pack["benchmark_sources.jsonl"]
    source_ids = _ids(sources, "source_id")
    for row in sources:
        assert row["adapter_state"] == "unbuilt", "no source may claim a built adapter yet"
        family = row.get("benchmark_lab_family_key")
        assert family is None or family in BENCHMARK_LAB_FAMILY_KEYS, f"unknown lab family {family!r}"

    tasks = pack["benchmark_task_demands.jsonl"]
    _ids(tasks, "task_id")
    arm_ids = _ids(pack["comparison_arms.jsonl"], "arm_id")
    score_ids = _ids(pack["scorecard_fields.jsonl"], "field_id")
    slot_ids = _ids(pack["model_slot_lanes.jsonl"], "slot_id")
    for task in tasks:
        assert task["source_family"] in source_ids, f"{task['task_id']}: unknown source_family"
        assert set(task["comparison_arms"]) <= arm_ids
        assert set(task["scorecard_fields"]) <= score_ids
        assert set(task["model_slot_demands"]) <= slot_ids
        assert task["depth_target"] in DEPTH_LEVELS
        assert "->" not in task["input_edge"] and "->" not in task["output_edge"]

    for arm in pack["comparison_arms.jsonl"]:
        assert set(arm["benchmark_lab_arm_refs"]) <= set(BENCHMARK_LAB_ARM_IDS)

    categories = {row["metric_category"] for row in pack["scorecard_fields.jsonl"]}
    assert {"token", "proof", "depth", "reuse"} <= categories, "scorecard must cover token/proof/depth/reuse"

    gen_ids = _ids(pack["primitive_generation_paths.jsonl"], "path_id")
    search_ids = _ids(pack["primitive_search_paths.jsonl"], "path_id")
    planner_ids = _ids(pack["route_planning_paths.jsonl"], "planner_id")
    compiler_ids = _ids(pack["compilation_paths.jsonl"], "compiler_id")
    proof_ids = _ids(pack["proof_paths.jsonl"], "proof_id")
    runtime_rows = pack["runtime_execution_paths.jsonl"]
    runtime_ids = {r["path_id"] for r in runtime_rows if r["kind"] == "runtime"}
    pattern_ids = {r["path_id"] for r in runtime_rows if r["kind"] == "execution_pattern"}
    sprout_ids = _ids(pack["path_sprout_rules.jsonl"], "sprout_id")
    trial_ids = _ids(pack["trial_run_policies.jsonl"], "policy_id")
    genome_ids = _ids(pack["strategy_genome_examples.jsonl"], "genome_id")
    cache_ids = _ids(pack["cache_policies.jsonl"], "cache_id")

    for portfolio in pack["route_portfolio_examples.jsonl"]:
        paths = portfolio["candidate_paths"]
        assert len(paths) >= 3, f"{portfolio['portfolio_id']}: needs >=3 candidate paths"
        assert portfolio["task_ref"] in {t["task_id"] for t in tasks}
        assert portfolio["strategy_genome_ref"] in genome_ids
        assert portfolio["trial_policy_ref"] in trial_ids
        econ_features = set(_route_economics_model()["ranking_features"])
        assert set(portfolio["ranking_features"]) <= econ_features
        for path in paths:
            assert path["generation_path"] in gen_ids
            assert path["search_path"] in search_ids
            assert path["planner"] in planner_ids
            assert path["compiler"] in compiler_ids
            assert path["runtime"] in runtime_ids
            assert set(path["execution_patterns"]) <= pattern_ids
            assert set(path["proof_refs"]) <= proof_ids
            for slot, lane in path["model_slot_assignments"].items():
                assert slot in slot_ids and lane in SERVED_BY_LANES

    for slot in pack["model_slot_lanes.jsonl"]:
        assert len(slot["served_by"]) >= 2, f"{slot['slot_id']}: needs a portfolio of >=2 lanes"
        assert set(slot["served_by"]) <= set(SERVED_BY_LANES)

    for adapter in pack["adapter_lanes.jsonl"]:
        assert set(adapter["allowed_slots"]) <= slot_ids
        assert set(adapter["disallowed_slots"]) <= slot_ids
        assert not set(adapter["allowed_slots"]) & set(adapter["disallowed_slots"])
        assert set(adapter["lift_criteria"]) <= set(ADAPTER_LIFT_CRITERIA)
        assert "training_data_lineage" in adapter["required_record_fields"]
        assert "rollback_receipts" in adapter["required_record_fields"]

    for agent in pack["micro_agent_envelopes.jsonl"]:
        envelope = agent["envelope"]
        for key in ("max_steps", "max_tokens", "max_wall_time_seconds",
                    "stop_conditions", "human_review_trigger"):
            assert envelope.get(key), f"{agent['agent_id']}: envelope missing {key}"

    for sprout in pack["path_sprout_rules.jsonl"]:
        assert sprout["status"] == "candidate"
        assert "held-out" in sprout["promotion_rule"]

    for genome in pack["strategy_genome_examples.jsonl"]:
        components = genome["components"]
        for key in ("decomposer", "retriever", "reranker", "planner", "compiler",
                    "proof_policy", "cache_policy"):
            assert components.get(key), f"{genome['genome_id']}: missing component {key}"
        assert components["retriever"] in search_ids
        assert components["planner"] in planner_ids
        assert components["compiler"] in compiler_ids
        assert set(components["proof_policy"]) <= proof_ids
        assert set(components["cache_policy"]) <= cache_ids
        assert set(genome["mutation_surface"]) <= sprout_ids
        assert genome["parameters"]["max_context_depth"] in DEPTH_LEVELS
        assert genome["rollout_policy"].get("promotion_gate"), "genome needs a rollout promotion gate"

    covered_loops: set[str] = set()
    for signal in pack["telemetry_signals.jsonl"]:
        loops = signal["feeds_back_into"]
        assert loops and set(loops) <= set(FEEDBACK_LOOPS)
        covered_loops.update(loops)
    assert covered_loops == set(FEEDBACK_LOOPS), f"uncovered feedback loops: {set(FEEDBACK_LOOPS) - covered_loops}"
    spans = sorted(s["span_order"] for s in pack["telemetry_signals.jsonl"] if s["signal_kind"] == "trace_span")
    assert spans == list(range(1, len(spans) + 1)), "trace spans must be contiguous"

    for cache in pack["cache_policies.jsonl"]:
        assert cache["invalidation_triggers"] and set(cache["invalidation_triggers"]) <= set(CACHE_INVALIDATION_TRIGGERS)
        assert cache["privacy_rule"]

    lifecycle = pack["compiled_route_lifecycle.jsonl"]
    assert [s["stage_index"] for s in lifecycle] == list(range(11)), "lifecycle must be L0..L10"
    assert "adapter_receipts_for_any_benchmark_claim" in lifecycle[-1]["promotion_requires"]

    repairs = pack["repair_ladder.jsonl"]
    orders = {r["repair_id"]: r["order"] for r in repairs}
    assert sorted(orders.values()) == list(range(1, len(repairs) + 1))
    assert orders["repair:allow_bounded_model_micro_repair"] > orders["repair:try_deterministic_mutator"]
    assert orders["repair:allow_bounded_model_micro_repair"] > orders["repair:try_alternate_route_from_bundle"]

    for name, rows in pack.items():
        if not isinstance(rows, list):
            continue
        for row in rows:
            for field in ("model_slot_refs",):
                if field in row:
                    assert set(row[field]) <= slot_ids, f"{name}: unknown model slot ref"

    assert manifest["total_rows"] == sum(len(v) for v in pack.values() if isinstance(v, list))
    assert manifest["file_count"] == len(pack)
    assert manifest["row_counts"]["benchmark_task_demands.jsonl"] >= 16, "harness needs a broad first task set"
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="validate the generated pack without writing")
    parser.add_argument("--write", action="store_true", help="write the pack + manifest to disk")
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    manifest = write_pack()
    print(json.dumps({"pack_id": manifest["pack_id"], "files": manifest["file_count"],
                      "total_rows": manifest["total_rows"],
                      "content_sha256": manifest["content_sha256"]}, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
