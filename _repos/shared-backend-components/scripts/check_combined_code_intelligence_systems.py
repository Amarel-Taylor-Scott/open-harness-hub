#!/usr/bin/env python3
"""Proof for the combined code-intelligence systems plan.

The repo keeps long, meaningful pyprefix names as the source-level semantic layer, then combines them
with parser/type/lint/data-flow/reference/LLM candidate-review systems. This checker validates that the
machine-readable plan and methodology doc preserve that stance and cover the required layers.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import json
from pathlib import Path


py_const_scripts_check_combined_code_intelligence_systems__REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
py_const_scripts_check_combined_code_intelligence_systems__PLAN = _resource("architecture/combined_code_intelligence_systems.json")
py_const_scripts_check_combined_code_intelligence_systems__DOC = _resource("docs/codex/combined-code-intelligence-research-plan.md")

py_const_scripts_check_combined_code_intelligence_systems__REQUIRED_LAYERS = {
    "semantic_source_names",
    "python_ast_symtable",
    "multi_language_parser",
    "code_property_graph",
    "pattern_and_taint_rules",
    "lint_format_static_quality",
    "type_contract_layer",
    "language_server_references",
    "llm_candidate_review",
}

py_const_scripts_check_combined_code_intelligence_systems__REQUIRED_RULES = {
    "names_plus_analyzers_not_names_only",
    "external_systems_are_evidence_layers",
    "llm_reviews_are_candidate_only",
    "source_names_must_stay_meaningful",
    "generated_code_uses_primitives",
    "query_bad_logic_as_graph_smells",
    "proof_gate_promotes",
}

py_const_scripts_check_combined_code_intelligence_systems__REQUIRED_REFERENCES = {
    "codeql_python_data_flow",
    "joern_code_property_graph",
    "semgrep_taint_analysis",
    "tree_sitter_using_parsers",
    "lsp_3_17_spec",
    "ruff_docs",
    "mypy_type_hints",
}


def py_function_scripts_check_combined_code_intelligence_systems__load_plan():
    return json.loads(py_const_scripts_check_combined_code_intelligence_systems__PLAN.read_text(encoding="utf-8"))


def py_function_scripts_check_combined_code_intelligence_systems___self_test():
    py_var_failures = []

    def py_function_scripts_check_combined_code_intelligence_systems___self_test__check(py_arg_name, py_arg_ok, py_arg_detail=""):
        print(f"  [{'ok' if py_arg_ok else 'FAIL'}] {py_arg_name}{(': ' + py_arg_detail) if py_arg_detail and not py_arg_ok else ''}")
        if not py_arg_ok:
            py_var_failures.append(py_arg_name)

    py_var_plan = py_function_scripts_check_combined_code_intelligence_systems__load_plan()
    py_var_doc = py_const_scripts_check_combined_code_intelligence_systems__DOC.read_text(encoding="utf-8")

    py_function_scripts_check_combined_code_intelligence_systems___self_test__check(
        "combined plan is candidate-only",
        py_var_plan.get("serves_truth") is False,
    )
    py_function_scripts_check_combined_code_intelligence_systems___self_test__check(
        "long meaningful source names are preserved, not replaced by hashes",
        "Keep meaningful long names" in py_var_plan.get("source_name_position", "")
        and "Do not replace them with hashes" in py_var_plan.get("source_name_position", ""),
    )

    py_var_layer_ids = {py_var_layer.get("id") for py_var_layer in py_var_plan.get("layers", [])}
    py_function_scripts_check_combined_code_intelligence_systems___self_test__check(
        "all required evidence layers are represented",
        py_const_scripts_check_combined_code_intelligence_systems__REQUIRED_LAYERS <= py_var_layer_ids,
        str(sorted(py_const_scripts_check_combined_code_intelligence_systems__REQUIRED_LAYERS - py_var_layer_ids)),
    )

    py_var_rule_ids = {py_var_rule.get("id") for py_var_rule in py_var_plan.get("rules", [])}
    py_function_scripts_check_combined_code_intelligence_systems___self_test__check(
        "all required combined-system rules are represented",
        py_const_scripts_check_combined_code_intelligence_systems__REQUIRED_RULES <= py_var_rule_ids,
        str(sorted(py_const_scripts_check_combined_code_intelligence_systems__REQUIRED_RULES - py_var_rule_ids)),
    )

    py_var_reference_ids = {py_var_ref.get("id") for py_var_ref in py_var_plan.get("source_references", [])}
    py_function_scripts_check_combined_code_intelligence_systems___self_test__check(
        "primary external-system references are captured",
        py_const_scripts_check_combined_code_intelligence_systems__REQUIRED_REFERENCES <= py_var_reference_ids,
        str(sorted(py_const_scripts_check_combined_code_intelligence_systems__REQUIRED_REFERENCES - py_var_reference_ids)),
    )

    py_function_scripts_check_combined_code_intelligence_systems___self_test__check(
        "methodology doc names pros and cons of long source names",
        "## Pros Of Long Meaningful Names" in py_var_doc and "## Cons And Failure Modes" in py_var_doc,
    )
    py_function_scripts_check_combined_code_intelligence_systems___self_test__check(
        "methodology doc includes bad-logic graph-smell plan",
        "magic scalar literal" in py_var_doc and "scalar-series" in py_var_doc and "branch chain" in py_var_doc,
    )
    py_function_scripts_check_combined_code_intelligence_systems___self_test__check(
        "methodology doc keeps LLM review candidate-only",
        "It cannot satisfy a contract. It only proposes." in py_var_doc,
    )

    if py_var_failures:
        print(f"\nFAIL - check_combined_code_intelligence_systems: {len(py_var_failures)} failure(s)")
        return 1
    print("\nPASS - check_combined_code_intelligence_systems: long names retained; parser/type/flow/lint/LSP/LLM layers formalized")
    return 0


def py_function_scripts_check_combined_code_intelligence_systems__main():
    return py_function_scripts_check_combined_code_intelligence_systems___self_test()


if __name__ == "__main__":
    raise SystemExit(py_function_scripts_check_combined_code_intelligence_systems__main())
