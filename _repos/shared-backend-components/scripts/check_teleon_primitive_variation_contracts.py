#!/usr/bin/env python3
"""Proof: Teleon has deterministic primitive variation contracts and a working variation library."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import json
from pathlib import Path


py_const_scripts_check_teleon_primitive_variation_contracts__REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
import sys
if str(py_const_scripts_check_teleon_primitive_variation_contracts__REPO) not in sys.path:
    sys.path.insert(0, str(py_const_scripts_check_teleon_primitive_variation_contracts__REPO))

from src.teleon.synthesis import primitive_variations as py_var_scripts_check_teleon_primitive_variation_contracts__primitive_variations


py_const_scripts_check_teleon_primitive_variation_contracts__CONTRACT = (
    _resource("architecture/teleon_primitive_variation_contracts.json")
)

py_const_scripts_check_teleon_primitive_variation_contracts__REQUIRED_PHASE1 = {
    "scalar-to-sequence",
    "output-field-wrapper",
    "linear-graph-composition",
    "structured-run-logging",
}

py_const_scripts_check_teleon_primitive_variation_contracts__REQUIRED_LATER = {
    "model-cost-downshift",
    "browser-to-deterministic-extractor",
    "local-vs-api-implementation-swap",
    "retry-cache-rate-limit-policy",
    "parallel-batch-execution",
}


def py_function_scripts_check_teleon_primitive_variation_contracts__load_contract():
    return json.loads(py_const_scripts_check_teleon_primitive_variation_contracts__CONTRACT.read_text(encoding="utf-8"))


def py_function_scripts_check_teleon_primitive_variation_contracts___self_test():
    py_var_failures = []

    def py_function_scripts_check_teleon_primitive_variation_contracts___self_test__check(py_arg_name, py_arg_ok, py_arg_detail=""):
        print(f"  [{'ok' if py_arg_ok else 'FAIL'}] {py_arg_name}{(': ' + py_arg_detail) if py_arg_detail and not py_arg_ok else ''}")
        if not py_arg_ok:
            py_var_failures.append(py_arg_name)

    py_var_contract = py_function_scripts_check_teleon_primitive_variation_contracts__load_contract()
    py_var_phase1 = {py_var_row.get("id") for py_var_row in py_var_contract.get("supported_mutations_phase1", [])}
    py_var_later = {py_var_row.get("id") for py_var_row in py_var_contract.get("supported_mutations_later", [])}
    py_var_required_functions = py_var_contract.get("required_library_functions", [])

    py_function_scripts_check_teleon_primitive_variation_contracts___self_test__check(
        "contract is candidate evidence, not truth",
        py_var_contract.get("serves_truth") is False,
    )
    py_function_scripts_check_teleon_primitive_variation_contracts___self_test__check(
        "phase-1 mutations cover scalar batching, output wrapping, graph composition, logging",
        py_const_scripts_check_teleon_primitive_variation_contracts__REQUIRED_PHASE1 <= py_var_phase1,
        str(sorted(py_const_scripts_check_teleon_primitive_variation_contracts__REQUIRED_PHASE1 - py_var_phase1)),
    )
    py_function_scripts_check_teleon_primitive_variation_contracts___self_test__check(
        "later mutations cover model downshift, deterministic scraping, local/api swaps, policies, parallelism",
        py_const_scripts_check_teleon_primitive_variation_contracts__REQUIRED_LATER <= py_var_later,
        str(sorted(py_const_scripts_check_teleon_primitive_variation_contracts__REQUIRED_LATER - py_var_later)),
    )
    py_function_scripts_check_teleon_primitive_variation_contracts___self_test__check(
        "every required library function exists",
        all(hasattr(py_var_scripts_check_teleon_primitive_variation_contracts__primitive_variations, py_var_name) for py_var_name in py_var_required_functions),
        str([py_var_name for py_var_name in py_var_required_functions if not hasattr(py_var_scripts_check_teleon_primitive_variation_contracts__primitive_variations, py_var_name)]),
    )
    py_function_scripts_check_teleon_primitive_variation_contracts___self_test__check(
        "contracts explicitly cover CI/CD, BYOK, marketplace, and control-vs-cost",
        "sbom" in py_var_contract.get("ci_cd_law", "").lower()
        and "byok" in py_var_contract.get("byok_law", "").lower()
        and "marketplace" in py_var_contract.get("marketplace_law", "").lower()
        and "control" in py_var_contract.get("control_vs_cost_tradeoff", "").lower(),
    )

    py_var_library_result = py_var_scripts_check_teleon_primitive_variation_contracts__primitive_variations.py_function_src_teleon_synthesis_primitive_variations___self_test()
    py_function_scripts_check_teleon_primitive_variation_contracts___self_test__check(
        "primitive_variations library self-test passes",
        py_var_library_result == 0,
    )

    if py_var_failures:
        print(f"\nFAIL - check_teleon_primitive_variation_contracts: {len(py_var_failures)} failure(s)")
        return 1
    print("\nPASS - check_teleon_primitive_variation_contracts: deterministic primitive variation library and contracts are present")
    return 0


def py_function_scripts_check_teleon_primitive_variation_contracts__main():
    return py_function_scripts_check_teleon_primitive_variation_contracts___self_test()


if __name__ == "__main__":
    raise SystemExit(py_function_scripts_check_teleon_primitive_variation_contracts__main())
