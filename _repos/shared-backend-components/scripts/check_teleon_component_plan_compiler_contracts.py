#!/usr/bin/env python3
"""Proof: Teleon has a deterministic ComponentCard/PipelinePlan compiler contract.

The contract keeps the owner's architecture load-bearing: RAG retrieves compact primitive/component
cards; the LLM proposes a constrained plan; deterministic code validates, orders, locks, and later emits
runtime manifests. The checker proves the contract exists, covers the required research families and
validation gates, and that the stdlib compiler can lock a candidate plan while blocking unsafe side
effects. Nothing here serves truth.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import json
import sys
from pathlib import Path


py_const_scripts_check_teleon_component_plan_compiler_contracts__REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(py_const_scripts_check_teleon_component_plan_compiler_contracts__REPO) not in sys.path:
    sys.path.insert(0, str(py_const_scripts_check_teleon_component_plan_compiler_contracts__REPO))

from src.teleon.synthesis import component_plan_compiler as py_var_scripts_check_teleon_component_plan_compiler_contracts__component_plan_compiler


py_const_scripts_check_teleon_component_plan_compiler_contracts__CONTRACT = (
    _resource("architecture/teleon_component_plan_compiler_contracts.json")
)
py_const_scripts_check_teleon_component_plan_compiler_contracts__DOC = (
    py_const_scripts_check_teleon_component_plan_compiler_contracts__REPO
    / "_repos" / "shared-backend-components" / "context" / "codex"
    / "component-plan-compiler-research-and-architecture.md"
)

py_const_scripts_check_teleon_component_plan_compiler_contracts__REQUIRED_RESEARCH_FAMILIES = {
    "model_orchestration",
    "visual_programming",
    "video_plan_composition",
    "api_tool_retrieval",
    "parallel_function_calling",
    "primitive_api_programming",
    "catalog_scaffolder",
    "workflow_runtime",
    "pipeline_graph",
    "schema_policy",
}
py_const_scripts_check_teleon_component_plan_compiler_contracts__REQUIRED_IR_LAYERS = {
    "intent_plan",
    "logical_pipeline_plan",
    "physical_execution_lock",
}
py_const_scripts_check_teleon_component_plan_compiler_contracts__REQUIRED_COMPONENT_FIELDS = {
    "component_id",
    "version",
    "purpose",
    "input_contract",
    "output_contract",
    "runtime",
    "policy",
    "proofs",
    "logs_schema",
    "source_sha256",
    "serves_truth",
}
py_const_scripts_check_teleon_component_plan_compiler_contracts__REQUIRED_VALIDATION_GATES = {
    "plan_schema_valid",
    "component_was_retrieved",
    "component_exists",
    "version_resolves",
    "input_binding_exists",
    "output_binding_exists",
    "binding_source_allowed",
    "side_effect_after_required_gate",
    "deterministic_mutation_attempted_before_generation",
    "nondeterministic_candidate_stays_untrusted",
    "proof_required_before_promotion",
    "topological_order_exists",
    "lockfile_emitted",
    "serves_truth_false",
}
py_const_scripts_check_teleon_component_plan_compiler_contracts__REQUIRED_MUTATIONS = {
    "scalar_to_sequence",
    "output_field_wrapper",
    "retry_cache_rate_limit_adapter",
    "model_cost_downshift",
    "browser_to_deterministic_extractor",
    "local_api_implementation_swap",
}
py_const_scripts_check_teleon_component_plan_compiler_contracts__REQUIRED_RUNTIMES = {
    "temporal_activity",
    "cloud_run_job",
    "kubernetes_job",
    "celery_worker",
    "local_runner",
}
py_const_scripts_check_teleon_component_plan_compiler_contracts__REQUIRED_HYBRID_ARTIFACTS = {
    "llm_enriched_compact_view",
    "generated_adapter_candidate",
    "generated_primitive_candidate",
    "generated_template_candidate",
    "pipeline_ir_patch_candidate",
    "planner_rerank_or_explanation",
}
py_const_scripts_check_teleon_component_plan_compiler_contracts__REQUIRED_HYBRID_BOUNDARIES = {
    "serves_truth_false",
    "proof_required",
    "provenance_required",
    "logs_schema_required",
    "graph_edges_required",
    "promotion_required_before_trusted_registry",
}


def py_function_scripts_check_teleon_component_plan_compiler_contracts__load_contract() -> dict:
    return json.loads(py_const_scripts_check_teleon_component_plan_compiler_contracts__CONTRACT.read_text(encoding="utf-8"))


def py_function_scripts_check_teleon_component_plan_compiler_contracts___self_test() -> int:
    py_var_failures: list[str] = []

    def py_function_scripts_check_teleon_component_plan_compiler_contracts___self_test__check(
        py_arg_name: str,
        py_arg_ok: bool,
        py_arg_detail: str = "",
    ) -> None:
        print(f"  [{'ok' if py_arg_ok else 'FAIL'}] {py_arg_name}{(': ' + py_arg_detail) if py_arg_detail and not py_arg_ok else ''}")
        if not py_arg_ok:
            py_var_failures.append(py_arg_name)

    py_var_contract = py_function_scripts_check_teleon_component_plan_compiler_contracts__load_contract()
    py_var_doc_text = py_const_scripts_check_teleon_component_plan_compiler_contracts__DOC.read_text(encoding="utf-8")
    py_var_source_families = {py_var_source.get("family") for py_var_source in py_var_contract.get("research_sources", [])}
    py_var_ir_layers = {py_var_layer.get("id") for py_var_layer in py_var_contract.get("ir_layers", [])}
    py_var_component_fields = set(py_var_contract.get("required_component_card_fields", []))
    py_var_validation_gates = set(py_var_contract.get("validation_gates", []))
    py_var_mutations = set(py_var_contract.get("mutation_before_regeneration", []))
    py_var_runtimes = set(py_var_contract.get("runtime_targets", []))
    py_var_hybrid_policy = py_var_contract.get("hybrid_lane_policy", {})
    py_var_hybrid_artifacts = set(py_var_hybrid_policy.get("nondeterministic_candidate_artifacts", []))
    py_var_hybrid_boundaries = set(py_var_hybrid_policy.get("required_candidate_boundaries", []))
    py_var_required_functions = py_var_contract.get("required_library_functions", [])
    py_var_planner_laws = " ".join(py_var_contract.get("planner_laws", [])).lower()

    py_function_scripts_check_teleon_component_plan_compiler_contracts___self_test__check(
        "contract and compiler outputs are candidate evidence, not truth",
        py_var_contract.get("serves_truth") is False
        and py_var_scripts_check_teleon_component_plan_compiler_contracts__component_plan_compiler.py_const_src_teleon_synthesis_component_plan_compiler__SERVES_TRUTH is False,
    )
    py_function_scripts_check_teleon_component_plan_compiler_contracts___self_test__check(
        "research sources cover orchestration, visual/video composition, APIs, compilers, catalogs, runtimes, schemas",
        py_const_scripts_check_teleon_component_plan_compiler_contracts__REQUIRED_RESEARCH_FAMILIES <= py_var_source_families,
        str(sorted(py_const_scripts_check_teleon_component_plan_compiler_contracts__REQUIRED_RESEARCH_FAMILIES - py_var_source_families)),
    )
    py_function_scripts_check_teleon_component_plan_compiler_contracts___self_test__check(
        "doc includes source trail and explicit LLM-planner/compiler-builder boundary",
        "HuggingGPT" in py_var_doc_text
        and "VideoDirectorGPT" in py_var_doc_text
        and "LLM may choose candidate components" in py_var_doc_text
        and "only deterministic code may validate" in py_var_doc_text,
    )
    py_function_scripts_check_teleon_component_plan_compiler_contracts___self_test__check(
        "doc preserves hybrid lane nuance: deterministic-first, nondeterministic candidate-until-proven",
        "deterministic-first" in py_var_doc_text
        and "nondeterministic-when-needed" in py_var_doc_text
        and "candidate-until-proven" in py_var_doc_text
        and "Every representation can be hybrid" in py_var_doc_text,
    )
    py_function_scripts_check_teleon_component_plan_compiler_contracts___self_test__check(
        "IR layers split intent, logical plan, physical lock",
        py_const_scripts_check_teleon_component_plan_compiler_contracts__REQUIRED_IR_LAYERS <= py_var_ir_layers,
        str(sorted(py_const_scripts_check_teleon_component_plan_compiler_contracts__REQUIRED_IR_LAYERS - py_var_ir_layers)),
    )
    py_function_scripts_check_teleon_component_plan_compiler_contracts___self_test__check(
        "ComponentCard fields include I/O, runtime, policy, proofs, logs, source digest, truth boundary",
        py_const_scripts_check_teleon_component_plan_compiler_contracts__REQUIRED_COMPONENT_FIELDS <= py_var_component_fields,
        str(sorted(py_const_scripts_check_teleon_component_plan_compiler_contracts__REQUIRED_COMPONENT_FIELDS - py_var_component_fields)),
    )
    py_function_scripts_check_teleon_component_plan_compiler_contracts___self_test__check(
        "validation gates cover retrieval, versions, bindings, side effects, topo order, lock, truth boundary",
        py_const_scripts_check_teleon_component_plan_compiler_contracts__REQUIRED_VALIDATION_GATES <= py_var_validation_gates,
        str(sorted(py_const_scripts_check_teleon_component_plan_compiler_contracts__REQUIRED_VALIDATION_GATES - py_var_validation_gates)),
    )
    py_function_scripts_check_teleon_component_plan_compiler_contracts___self_test__check(
        "hybrid lane policy defines nondeterministic candidate artifacts",
        py_const_scripts_check_teleon_component_plan_compiler_contracts__REQUIRED_HYBRID_ARTIFACTS <= py_var_hybrid_artifacts,
        str(sorted(py_const_scripts_check_teleon_component_plan_compiler_contracts__REQUIRED_HYBRID_ARTIFACTS - py_var_hybrid_artifacts)),
    )
    py_function_scripts_check_teleon_component_plan_compiler_contracts___self_test__check(
        "hybrid lane policy keeps nondeterministic outputs candidate-only until proof/promotion",
        py_const_scripts_check_teleon_component_plan_compiler_contracts__REQUIRED_HYBRID_BOUNDARIES <= py_var_hybrid_boundaries
        and (py_var_hybrid_policy.get("deterministic_first_order") or [])[-1:] == ["nondeterministic_candidate_generation"],
        str(sorted(py_const_scripts_check_teleon_component_plan_compiler_contracts__REQUIRED_HYBRID_BOUNDARIES - py_var_hybrid_boundaries)),
    )
    py_function_scripts_check_teleon_component_plan_compiler_contracts___self_test__check(
        "mutation-before-regeneration covers cheap deterministic adapter classes",
        py_const_scripts_check_teleon_component_plan_compiler_contracts__REQUIRED_MUTATIONS <= py_var_mutations,
        str(sorted(py_const_scripts_check_teleon_component_plan_compiler_contracts__REQUIRED_MUTATIONS - py_var_mutations)),
    )
    py_function_scripts_check_teleon_component_plan_compiler_contracts___self_test__check(
        "runtime targets cover durable workflows, container jobs, workers, and local runner",
        py_const_scripts_check_teleon_component_plan_compiler_contracts__REQUIRED_RUNTIMES <= py_var_runtimes,
        str(sorted(py_const_scripts_check_teleon_component_plan_compiler_contracts__REQUIRED_RUNTIMES - py_var_runtimes)),
    )
    py_function_scripts_check_teleon_component_plan_compiler_contracts___self_test__check(
        "planner laws forbid arbitrary source/execution and require lockfile execution",
        "not arbitrary executable source" in py_var_planner_laws
        and "only componentcards returned by retrieval" in py_var_planner_laws
        and "executor runs a lockfile" in py_var_planner_laws,
    )
    py_function_scripts_check_teleon_component_plan_compiler_contracts___self_test__check(
        "planner laws require deterministic-first before nondeterministic candidate generation",
        "deterministic search/check/mutation lanes run before nondeterministic candidate generation" in py_var_planner_laws
        and "cannot serve truth or execute without deterministic validation" in py_var_planner_laws,
    )
    py_function_scripts_check_teleon_component_plan_compiler_contracts___self_test__check(
        "every required compiler function exists",
        all(hasattr(py_var_scripts_check_teleon_component_plan_compiler_contracts__component_plan_compiler, py_var_name) for py_var_name in py_var_required_functions),
        str([py_var_name for py_var_name in py_var_required_functions if not hasattr(py_var_scripts_check_teleon_component_plan_compiler_contracts__component_plan_compiler, py_var_name)]),
    )
    py_function_scripts_check_teleon_component_plan_compiler_contracts___self_test__check(
        "compiler self-test passes",
        py_var_scripts_check_teleon_component_plan_compiler_contracts__component_plan_compiler.py_function_src_teleon_synthesis_component_plan_compiler___self_test() == 0,
    )

    if py_var_failures:
        print(f"\nFAIL - check_teleon_component_plan_compiler_contracts: {len(py_var_failures)} failure(s)")
        return 1
    print("\nPASS - check_teleon_component_plan_compiler_contracts: ComponentPlan compiler methodology and deterministic lock compiler are contract-checked")
    return 0


def py_function_scripts_check_teleon_component_plan_compiler_contracts__main() -> int:
    return py_function_scripts_check_teleon_component_plan_compiler_contracts___self_test()


if __name__ == "__main__":
    raise SystemExit(py_function_scripts_check_teleon_component_plan_compiler_contracts__main())
