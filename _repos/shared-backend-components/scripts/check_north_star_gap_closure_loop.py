#!/usr/bin/env python3
"""Proof: north-star gap closure loop command is present and contract-shaped."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import json
import subprocess
import sys
from pathlib import Path


py_const_scripts_check_north_star_gap_closure_loop__REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])


def _res_path(rel: str) -> Path:
    # dot-prefixed dirs (.codex/, .agent/) stayed at the monorepo root and are not mapped by _resource
    # (which strips the leading dot); resolve those against the root, everything else via _resource.
    return (py_const_scripts_check_north_star_gap_closure_loop__REPO / rel) if rel.startswith(".") else _resource(rel)
py_const_scripts_check_north_star_gap_closure_loop__CONTRACT = (
    _resource("architecture/north_star_gap_closure_loop.json")
)
py_const_scripts_check_north_star_gap_closure_loop__REQUIRED_GAPS = {
    "repo_wide_unique_naming",
    "blast_radius_graph",
    "disagreement_management",
    "primitive_derivation",
    "registry_vectorization_search",
    "promotion_gate",
}


def py_function_scripts_check_north_star_gap_closure_loop__load_contract():
    return json.loads(py_const_scripts_check_north_star_gap_closure_loop__CONTRACT.read_text(encoding="utf-8"))


def py_function_scripts_check_north_star_gap_closure_loop___self_test():
    py_var_failures = []

    def py_function_scripts_check_north_star_gap_closure_loop___self_test__check(py_arg_name, py_arg_ok, py_arg_detail=""):
        print(f"  [{'ok' if py_arg_ok else 'FAIL'}] {py_arg_name}{(': ' + py_arg_detail) if py_arg_detail and not py_arg_ok else ''}")
        if not py_arg_ok:
            py_var_failures.append(py_arg_name)

    py_var_contract = py_function_scripts_check_north_star_gap_closure_loop__load_contract()
    py_var_tracked_gaps = set(py_var_contract.get("tracked_gaps", []))
    py_var_required_paths = [
        py_var_contract.get("command"),
        py_var_contract.get("prompt"),
        py_var_contract.get("docs"),
    ]
    py_function_scripts_check_north_star_gap_closure_loop___self_test__check(
        "contract is candidate evidence, not truth",
        py_var_contract.get("serves_truth") is False,
    )
    py_function_scripts_check_north_star_gap_closure_loop___self_test__check(
        "contract tracks all six north-star gaps",
        py_const_scripts_check_north_star_gap_closure_loop__REQUIRED_GAPS <= py_var_tracked_gaps,
        str(sorted(py_const_scripts_check_north_star_gap_closure_loop__REQUIRED_GAPS - py_var_tracked_gaps)),
    )
    py_function_scripts_check_north_star_gap_closure_loop___self_test__check(
        "command, prompt, and docs exist",
        all(_res_path(py_var_path).exists() for py_var_path in py_var_required_paths),
        str(py_var_required_paths),
    )
    py_var_rule_text = " ".join(py_var_contract.get("loop_rules", [])).lower()
    py_function_scripts_check_north_star_gap_closure_loop___self_test__check(
        "loop rules guard proof gate, unsafe sweeps, placeholders, dynamic refs, enterprise controls",
        "proof gate" in py_var_rule_text
        and "repo-wide rename" in py_var_rule_text
        and "placeholder" in py_var_rule_text
        and "dynamic refs" in py_var_rule_text
        and "byok" in py_var_rule_text,
    )
    py_var_result = subprocess.run(
        [sys.executable, str(_resource("scripts/north_star_gap_closure_loop.py")), "--self-test"],
        cwd=py_const_scripts_check_north_star_gap_closure_loop__REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    py_function_scripts_check_north_star_gap_closure_loop___self_test__check(
        "north_star_gap_closure_loop self-test passes",
        py_var_result.returncode == 0,
        py_var_result.stdout + py_var_result.stderr,
    )

    if py_var_failures:
        print(f"\nFAIL - check_north_star_gap_closure_loop: {len(py_var_failures)} failure(s)")
        return 1
    print("\nPASS - check_north_star_gap_closure_loop: north-star gap loop command/prompt/docs are governed")
    return 0


def py_function_scripts_check_north_star_gap_closure_loop__main():
    return py_function_scripts_check_north_star_gap_closure_loop___self_test()


if __name__ == "__main__":
    raise SystemExit(py_function_scripts_check_north_star_gap_closure_loop__main())
