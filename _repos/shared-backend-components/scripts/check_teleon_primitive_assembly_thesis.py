#!/usr/bin/env python3
"""Proof: Teleon's product thesis is primitive graph assembly, not repeated code generation.

This checker keeps the owner's thesis load-bearing:
users define capability + context + guardrails; Teleon retrieves proven primitives by contract/search;
the system assembles a graph, manages edges, logs execution, tunes variants, and promotes new primitives
only after proof. The proof validates the contract artifact. It does not claim any primitive serves truth.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import json
from pathlib import Path


py_const_scripts_check_teleon_primitive_assembly_thesis__REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
py_const_scripts_check_teleon_primitive_assembly_thesis__CONTRACT = (
    _resource("architecture/teleon_primitive_assembly_thesis.json")
)

py_const_scripts_check_teleon_primitive_assembly_thesis__REQUIRED_PRIMITIVE_FIELDS = {
    "id",
    "version",
    "purpose",
    "input_contract",
    "output_contract",
    "dependencies",
    "guardrails",
    "proofs",
    "logs_schema",
    "graph_edges",
}

py_const_scripts_check_teleon_primitive_assembly_thesis__REQUIRED_ASSEMBLY_STEPS = {
    "capability-intake",
    "hybrid-primitive-retrieval",
    "contract-first-planning",
    "edge-management",
    "minimal-new-code",
    "execution-and-json-logging",
    "self-tuning-under-guardrails",
    "git-like-variation-store",
    "primitive-promotion",
}

py_const_scripts_check_teleon_primitive_assembly_thesis__REQUIRED_NODE_TYPES = {
    "capability",
    "primitive",
    "adapter",
    "input_contract",
    "output_contract",
    "guardrail",
    "execution_surface",
    "log_event",
    "proof",
    "version",
    "fork",
    "third_party_api",
}

py_const_scripts_check_teleon_primitive_assembly_thesis__REQUIRED_EDGE_TYPES = {
    "requires",
    "satisfies",
    "accepts_input",
    "emits_output",
    "maps_output_to_input",
    "guarded_by",
    "proved_by",
    "logged_by",
    "forked_from",
    "optimized_from",
    "calls_external_api",
}


def py_function_scripts_check_teleon_primitive_assembly_thesis__load_contract():
    return json.loads(py_const_scripts_check_teleon_primitive_assembly_thesis__CONTRACT.read_text(encoding="utf-8"))


def py_function_scripts_check_teleon_primitive_assembly_thesis___self_test():
    py_var_failures = []

    def py_function_scripts_check_teleon_primitive_assembly_thesis___self_test__check(py_arg_name, py_arg_ok, py_arg_detail=""):
        print(f"  [{'ok' if py_arg_ok else 'FAIL'}] {py_arg_name}{(': ' + py_arg_detail) if py_arg_detail and not py_arg_ok else ''}")
        if not py_arg_ok:
            py_var_failures.append(py_arg_name)

    py_var_contract = py_function_scripts_check_teleon_primitive_assembly_thesis__load_contract()
    py_var_essence_text = json.dumps(py_var_contract.get("essence", {})).lower()
    py_var_required_fields = set(py_var_contract.get("primitive_record_required_fields", []))
    py_var_step_ids = {py_var_step.get("id") for py_var_step in py_var_contract.get("assembly_loop", [])}
    py_var_node_types = set(py_var_contract.get("graph_node_types", []))
    py_var_edge_types = set(py_var_contract.get("graph_edge_types", []))
    py_var_policy = py_var_contract.get("generated_output_policy", {})
    py_var_external_policy_text = json.dumps(py_var_contract.get("external_api_policy", {})).lower()
    py_var_must_not_text = " ".join(py_var_contract.get("must_not", [])).lower()

    py_function_scripts_check_teleon_primitive_assembly_thesis___self_test__check(
        "contract is candidate evidence, not truth",
        py_var_contract.get("serves_truth") is False,
    )
    py_function_scripts_check_teleon_primitive_assembly_thesis___self_test__check(
        "essence says Teleon assembles primitives instead of rewriting solved code",
        "primitive" in py_var_essence_text and "graph" in py_var_essence_text and "not write fresh code" in py_var_essence_text,
        py_var_essence_text[:260],
    )
    py_function_scripts_check_teleon_primitive_assembly_thesis___self_test__check(
        "primitive records carry input/output/proof/log/edge contracts",
        py_const_scripts_check_teleon_primitive_assembly_thesis__REQUIRED_PRIMITIVE_FIELDS <= py_var_required_fields,
        str(sorted(py_const_scripts_check_teleon_primitive_assembly_thesis__REQUIRED_PRIMITIVE_FIELDS - py_var_required_fields)),
    )
    py_function_scripts_check_teleon_primitive_assembly_thesis___self_test__check(
        "assembly loop covers intake, retrieval, planning, edges, logging, tuning, versions, promotion",
        py_const_scripts_check_teleon_primitive_assembly_thesis__REQUIRED_ASSEMBLY_STEPS <= py_var_step_ids,
        str(sorted(py_const_scripts_check_teleon_primitive_assembly_thesis__REQUIRED_ASSEMBLY_STEPS - py_var_step_ids)),
    )
    py_function_scripts_check_teleon_primitive_assembly_thesis___self_test__check(
        "graph node vocabulary covers capabilities, primitives, contracts, logs, proofs, versions, APIs",
        py_const_scripts_check_teleon_primitive_assembly_thesis__REQUIRED_NODE_TYPES <= py_var_node_types,
        str(sorted(py_const_scripts_check_teleon_primitive_assembly_thesis__REQUIRED_NODE_TYPES - py_var_node_types)),
    )
    py_function_scripts_check_teleon_primitive_assembly_thesis___self_test__check(
        "graph edge vocabulary covers contract satisfaction, mapping, proof, logging, variants, APIs",
        py_const_scripts_check_teleon_primitive_assembly_thesis__REQUIRED_EDGE_TYPES <= py_var_edge_types,
        str(sorted(py_const_scripts_check_teleon_primitive_assembly_thesis__REQUIRED_EDGE_TYPES - py_var_edge_types)),
    )
    py_function_scripts_check_teleon_primitive_assembly_thesis___self_test__check(
        "generated output policy prefers compact graph plans over regenerated source dumps",
        "compact capability graph plan" in py_var_policy.get("preferred_output", "").lower()
        and "large regenerated source" in py_var_policy.get("avoid", "").lower(),
    )
    py_function_scripts_check_teleon_primitive_assembly_thesis___self_test__check(
        "external APIs are modeled as primitives with local/private alternatives where possible",
        "third-party" in py_var_external_policy_text
        and "same contract" in py_var_external_policy_text
        and "local" in py_var_external_policy_text,
    )
    py_function_scripts_check_teleon_primitive_assembly_thesis___self_test__check(
        "must-not rules forbid unverified regeneration/promotion and hidden dependencies",
        "do not regenerate" in py_var_must_not_text
        and "do not promote" in py_var_must_not_text
        and "do not hide external api" in py_var_must_not_text,
    )

    if py_var_failures:
        print(f"\nFAIL - check_teleon_primitive_assembly_thesis: {len(py_var_failures)} failure(s)")
        return 1
    print("\nPASS - check_teleon_primitive_assembly_thesis: Teleon primitive graph-assembly thesis is explicit and contract-checked")
    return 0


def py_function_scripts_check_teleon_primitive_assembly_thesis__main():
    return py_function_scripts_check_teleon_primitive_assembly_thesis___self_test()


if __name__ == "__main__":
    raise SystemExit(py_function_scripts_check_teleon_primitive_assembly_thesis__main())
