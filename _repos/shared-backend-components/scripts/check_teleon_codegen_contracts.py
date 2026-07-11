#!/usr/bin/env python3
"""Proof: Teleon generated-code contracts are explicit and backed by reusable primitive blocks.

This checker binds three things:
  1. _repos/shared-backend-components/architecture/teleon_codegen_contracts.json names the generation laws.
  2. _repos/teleon/backend/src/teleon/synthesis/primitive_blocks.py provides flexible scalar/batch/loop/dispatch primitives.
  3. _repos/shared-backend-components/scripts/hybrid_repo_review_pipeline.py detects the graph smells these contracts are meant to prevent.

Generated code is candidate-only. This proof verifies the rails, not any generated artifact as truth.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import ast
import json
import tempfile
from pathlib import Path

py_const_scripts_check_teleon_codegen_contracts__REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
import sys
if str(py_const_scripts_check_teleon_codegen_contracts__REPO) not in sys.path:
    sys.path.insert(0, str(py_const_scripts_check_teleon_codegen_contracts__REPO))

from src.teleon.synthesis import primitive_blocks as py_var_scripts_check_teleon_codegen_contracts__primitive_blocks

from scripts import hybrid_repo_review_pipeline as py_var_scripts_check_teleon_codegen_contracts__hybrid_review
py_const_scripts_check_teleon_codegen_contracts__CONTRACT = _resource("architecture/teleon_codegen_contracts.json")
py_const_scripts_check_teleon_codegen_contracts__PRIMITIVES = _resource("src/teleon/synthesis/primitive_blocks.py")

py_const_scripts_check_teleon_codegen_contracts__REQUIRED_RULE_IDS = {
    "generated-code-is-candidate-only",
    "full-qualified-names",
    "purpose-input-output-contract",
    "scalar-to-sequence-first",
    "looping-is-explicit-and-bounded",
    "dispatch-is-data-driven",
    "arrays-over-numbered-scalars",
    "proof-before-promotion",
}


def py_function_scripts_check_teleon_codegen_contracts__load_contract():
    return json.loads(py_const_scripts_check_teleon_codegen_contracts__CONTRACT.read_text(encoding="utf-8"))


def py_function_scripts_check_teleon_codegen_contracts__primitive_export_names():
    py_var_names = []
    for py_var_name in dir(py_var_scripts_check_teleon_codegen_contracts__primitive_blocks):
        if py_var_name.startswith("py_function_src_teleon_synthesis_primitive_blocks__"):
            py_var_names.append(py_var_name)
    return sorted(py_var_names)


def py_function_scripts_check_teleon_codegen_contracts__primitive_source_has_no_unbounded_while():
    py_var_tree = ast.parse(py_const_scripts_check_teleon_codegen_contracts__PRIMITIVES.read_text(encoding="utf-8"))
    return not any(isinstance(py_var_node, ast.While) for py_var_node in ast.walk(py_var_tree))


def py_function_scripts_check_teleon_codegen_contracts__hybrid_review_detects_codegen_smells():
    with tempfile.TemporaryDirectory() as py_var_dir:
        py_var_root = Path(py_var_dir)
        py_var_file = py_var_root / "generated_candidate.py"
        py_var_file.write_text(
            "def run(item, debug=False, force=False, cache=[]):\n"
            "    threshold = 37\n"
            "    value1 = item\n"
            "    value2 = item\n"
            "    if threshold == 1:\n"
            "        return getattr(item, 'name')\n"
            "    elif threshold == 2:\n"
            "        return value1\n"
            "    elif threshold == 3:\n"
            "        return value2\n"
            "    elif threshold == 4:\n"
            "        return item\n"
            "    return item\n",
            encoding="utf-8",
        )
        py_var_rows = py_var_scripts_check_teleon_codegen_contracts__hybrid_review._logic_findings(py_var_file)
    py_var_kinds = {py_var_row["kind"] for py_var_row in py_var_rows}
    return {
        "magic_literal:number",
        "dynamic_reference_contract",
        "boolean_flag_control_surface",
        "mutable_default_argument",
        "rigid_branch_chain",
        "scalar_series_candidate",
    }.issubset(py_var_kinds)


def py_function_scripts_check_teleon_codegen_contracts___self_test():
    py_var_failures = []

    def py_function_scripts_check_teleon_codegen_contracts___self_test__check(py_arg_name, py_arg_ok, py_arg_detail=""):
        print(f"  [{'ok' if py_arg_ok else 'FAIL'}] {py_arg_name}{(': ' + py_arg_detail) if py_arg_detail and not py_arg_ok else ''}")
        if not py_arg_ok:
            py_var_failures.append(py_arg_name)

    py_var_contract = py_function_scripts_check_teleon_codegen_contracts__load_contract()
    py_var_rule_ids = {py_var_rule.get("id") for py_var_rule in py_var_contract.get("rules", [])}
    py_function_scripts_check_teleon_codegen_contracts___self_test__check(
        "contract file declares every generated-code rule",
        py_const_scripts_check_teleon_codegen_contracts__REQUIRED_RULE_IDS <= py_var_rule_ids,
        str(sorted(py_const_scripts_check_teleon_codegen_contracts__REQUIRED_RULE_IDS - py_var_rule_ids)),
    )
    py_function_scripts_check_teleon_codegen_contracts___self_test__check(
        "contract keeps generated/model code candidate-only",
        py_var_contract.get("serves_truth") is False and "candidate" in py_var_contract.get("purpose", "").lower(),
    )
    py_function_scripts_check_teleon_codegen_contracts___self_test__check(
        "contract defers strict parameter typing until optimization",
        "defer" in py_var_contract.get("typing_law", "").lower()
        and "optimization" in py_var_contract.get("typing_law", "").lower(),
    )

    py_var_export_names = py_function_scripts_check_teleon_codegen_contracts__primitive_export_names()
    py_function_scripts_check_teleon_codegen_contracts___self_test__check(
        "primitive module exports long qualified pyprefix functions",
        len(py_var_export_names) >= 6 and all("__" in py_var_name for py_var_name in py_var_export_names),
        str(py_var_export_names[:3]),
    )
    py_function_scripts_check_teleon_codegen_contracts___self_test__check(
        "primitive loops are bounded; no while loops in generated-code primitive library",
        py_function_scripts_check_teleon_codegen_contracts__primitive_source_has_no_unbounded_while(),
    )

    py_var_normalized = py_var_scripts_check_teleon_codegen_contracts__primitive_blocks.py_function_src_teleon_synthesis_primitive_blocks__normalize_to_sequence("abc")
    py_function_scripts_check_teleon_codegen_contracts___self_test__check(
        "normalize_to_sequence treats string as one scalar item",
        py_var_normalized["items"] == ["abc"] and py_var_normalized["input_kind"] == "scalar",
    )

    def py_function_scripts_check_teleon_codegen_contracts___self_test__double(py_arg_value):
        return py_arg_value * 2

    py_var_lifted = py_var_scripts_check_teleon_codegen_contracts__primitive_blocks.py_function_src_teleon_synthesis_primitive_blocks__lift_scalar_step_to_sequence_step(
        py_function_scripts_check_teleon_codegen_contracts___self_test__double
    )
    py_var_batch = py_var_lifted([1, 2, 3])
    py_function_scripts_check_teleon_codegen_contracts___self_test__check(
        "scalar function lifts to batch without rewriting business logic",
        [py_var_row["value"] for py_var_row in py_var_batch["outputs"]] == [2, 4, 6],
    )
    py_function_scripts_check_teleon_codegen_contracts___self_test__check(
        "hybrid review detects generated-code scalability smells",
        py_function_scripts_check_teleon_codegen_contracts__hybrid_review_detects_codegen_smells(),
    )

    if py_var_failures:
        print(f"\nFAIL - check_teleon_codegen_contracts: {len(py_var_failures)} failure(s)")
        return 1
    print("\nPASS - check_teleon_codegen_contracts: Teleon codegen has candidate-only naming, scalar/batch, loop, dispatch, and review contracts")
    return 0


def py_function_scripts_check_teleon_codegen_contracts__main():
    return py_function_scripts_check_teleon_codegen_contracts___self_test()


if __name__ == "__main__":
    raise SystemExit(py_function_scripts_check_teleon_codegen_contracts__main())
