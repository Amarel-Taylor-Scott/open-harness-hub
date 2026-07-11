#!/usr/bin/env python3
"""North-star gap closure loop.

This command turns the remaining north-star gaps into a resumable deterministic status artifact. It reads
the current repo inventory/review/packet artifacts, classifies each gap, writes a state file + summary, and
prints the next highest-leverage workstream. It is a loop coordinator, not a proof of completion.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


py_const_scripts_north_star_gap_closure_loop__REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
py_const_scripts_north_star_gap_closure_loop__DEFAULT_OUT = (
    (py_const_scripts_north_star_gap_closure_loop__REPO / ".agent") / "north-star-gap-closure"
)


def py_function_scripts_north_star_gap_closure_loop__now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def py_function_scripts_north_star_gap_closure_loop__load_json(py_arg_path, py_arg_default=None):
    if not py_arg_path.exists():
        return py_arg_default
    try:
        return json.loads(py_arg_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return py_arg_default


def py_function_scripts_north_star_gap_closure_loop__status(py_arg_open, py_arg_evidence, py_arg_next):
    return {
        "status": "open" if py_arg_open else "ready_or_green",
        "evidence": py_arg_evidence,
        "next_action": py_arg_next,
    }


def py_function_scripts_north_star_gap_closure_loop__build(py_arg_out):
    py_arg_out.mkdir(parents=True, exist_ok=True)
    py_var_inventory = py_function_scripts_north_star_gap_closure_loop__load_json(
        (py_const_scripts_north_star_gap_closure_loop__REPO / ".agent") / "repo-code-inventory" / "manifest.json",
        {},
    ) or {}
    py_var_hybrid = py_function_scripts_north_star_gap_closure_loop__load_json(
        (py_const_scripts_north_star_gap_closure_loop__REPO / ".agent") / "hybrid-repo-review" / "full-repo" / "manifest.json",
        {},
    ) or {}
    py_var_line_state = py_function_scripts_north_star_gap_closure_loop__load_json(
        (py_const_scripts_north_star_gap_closure_loop__REPO / ".agent") / "repo-line-review" / "state.json",
        {},
    ) or {}
    py_var_primitive_thesis_exists = (
        _resource("architecture") / "teleon_primitive_assembly_thesis.json"
    ).exists()
    py_var_variation_contract_exists = (
        _resource("architecture") / "teleon_primitive_variation_contracts.json"
    ).exists()
    py_var_variation_library_exists = (
        _resource("src") / "teleon" / "synthesis" / "primitive_variations.py"
    ).exists()
    py_var_registry_builder_exists = (
        _resource("scripts") / "primitive_registry_builder.py"
    ).exists()
    py_var_adjudication_contract_exists = (
        _resource("architecture") / "disagreement_adjudication_contracts.json"
    ).exists()
    py_var_promotion_gate_exists = (
        _resource("scripts") / "check_primitive_registry_promotion_gate.py"
    ).exists()

    py_var_finding_kinds = py_var_inventory.get("finding_kinds", {})
    py_var_structural_counts = py_var_hybrid.get("structural_graph_counts", {})
    py_var_operation_counts = py_var_hybrid.get("operation_graph_counts", {})
    py_var_open_gaps = {
        "repo_wide_unique_naming": py_function_scripts_north_star_gap_closure_loop__status(
            int(py_var_inventory.get("pyprefix_violations", 0)) > 0,
            {
                "pyprefix_violations": py_var_inventory.get("pyprefix_violations", 0),
                "symbols": py_var_inventory.get("symbols", 0),
                "violations_by_kind": py_var_inventory.get("violations_by_kind", {}),
            },
            "Run package-sized pyprefix migration: report -> migrate scoped/module/arg safe groups -> focused checks -> full proof gate -> manifest update.",
        ),
        "blast_radius_graph": py_function_scripts_north_star_gap_closure_loop__status(
            not py_var_operation_counts
            or int(py_var_finding_kinds.get("dynamic_python_call", 0)) > 0
            or int(py_var_finding_kinds.get("dynamic_reference_text", 0)) > 0,
            {
                "structural_graph_counts": py_var_structural_counts,
                "operation_graph_counts": py_var_operation_counts,
                "dynamic_python_call_findings": py_var_finding_kinds.get("dynamic_python_call", 0),
                "dynamic_reference_text_findings": py_var_finding_kinds.get("dynamic_reference_text", 0),
            },
            "Persist operation graph in hybrid packets, add data-flow/def-use edges, add JS/JSX route/UI seam graph, and classify dynamic refs as resolved/unresolved.",
        ),
        "disagreement_management": py_function_scripts_north_star_gap_closure_loop__status(
            not py_var_adjudication_contract_exists,
            {
                "hybrid_packets": py_var_hybrid.get("packets", 0),
                "llm_candidates": py_var_hybrid.get("llm_candidates", 0),
                "adjudication_contract_exists": py_var_adjudication_contract_exists,
            },
            "Create disagreement_adjudication_contracts.json + checker: multi-model candidate votes, deterministic evidence lanes, owner decisions, promotion/rejection records.",
        ),
        "primitive_derivation": py_function_scripts_north_star_gap_closure_loop__status(
            not (py_var_primitive_thesis_exists and py_var_variation_contract_exists and py_var_variation_library_exists),
            {
                "primitive_thesis_exists": py_var_primitive_thesis_exists,
                "variation_contract_exists": py_var_variation_contract_exists,
                "variation_library_exists": py_var_variation_library_exists,
            },
            "Extend primitive_variations from runtime wrappers to source-level mutation plans: AST codemod candidates, proof fixtures, rollback records, and variant diffs.",
        ),
        "registry_vectorization_search": py_function_scripts_north_star_gap_closure_loop__status(
            not py_var_registry_builder_exists,
            {
                "primitive_registry_builder_exists": py_var_registry_builder_exists,
                "inventory_symbols": py_var_inventory.get("symbols", 0),
                "inventory_edges": py_var_inventory.get("edges", 0),
            },
            "Build primitive_registry_builder: real-code candidate records, placeholder rejection, contract/proof/license/log schema requirements, embeddings/search export with serves_truth=false.",
        ),
        "promotion_gate": py_function_scripts_north_star_gap_closure_loop__status(
            not py_var_promotion_gate_exists,
            {
                "promotion_gate_exists": py_var_promotion_gate_exists,
                "registry_builder_exists": py_var_registry_builder_exists,
            },
            "Create promotion gate that blocks placeholders/synthetic rows, requires contracts/proofs/license/deps/log schema/graph edges, and records owner/human approval.",
        ),
    }
    py_var_priority = [
        "registry_vectorization_search",
        "promotion_gate",
        "repo_wide_unique_naming",
        "blast_radius_graph",
        "disagreement_management",
        "primitive_derivation",
    ]
    py_var_next_gap = next((py_var_gap for py_var_gap in py_var_priority if py_var_open_gaps[py_var_gap]["status"] == "open"), None)
    py_var_manifest = {
        "created_at": py_function_scripts_north_star_gap_closure_loop__now(),
        "serves_truth": False,
        "purpose": "Deterministic north-star gap loop state; candidate evidence only.",
        "line_review": {
            "cursor": py_var_line_state.get("cursor"),
            "completed_files": py_var_line_state.get("completed_files"),
            "findings": py_var_line_state.get("findings"),
        },
        "inventory": {
            "files": py_var_inventory.get("files"),
            "python_modules": py_var_inventory.get("python_modules"),
            "symbols": py_var_inventory.get("symbols"),
            "references": py_var_inventory.get("references"),
            "imports": py_var_inventory.get("imports"),
            "edges": py_var_inventory.get("edges"),
            "pyprefix_violations": py_var_inventory.get("pyprefix_violations"),
        },
        "hybrid_review": {
            "deterministic_findings": py_var_hybrid.get("deterministic_findings"),
            "packets": py_var_hybrid.get("packets"),
            "llm_candidates": py_var_hybrid.get("llm_candidates"),
        },
        "gaps": py_var_open_gaps,
        "next_gap": py_var_next_gap,
        "next_action": py_var_open_gaps[py_var_next_gap]["next_action"] if py_var_next_gap else "All tracked gaps are ready_or_green; refresh artifacts and run proofs.",
    }
    (py_arg_out / "state.json").write_text(json.dumps(py_var_manifest, indent=2, sort_keys=True), encoding="utf-8")
    py_function_scripts_north_star_gap_closure_loop__write_summary(py_arg_out, py_var_manifest)
    return py_var_manifest


def py_function_scripts_north_star_gap_closure_loop__write_summary(py_arg_out, py_arg_manifest):
    py_var_lines = [
        "# North Star Gap Closure Loop",
        "",
        f"- Updated: `{py_arg_manifest['created_at']}`",
        f"- Serves truth: `{py_arg_manifest['serves_truth']}`",
        f"- Next gap: `{py_arg_manifest['next_gap']}`",
        f"- Next action: {py_arg_manifest['next_action']}",
        "",
        "## Current Evidence",
        "",
        "```json",
        json.dumps({
            "line_review": py_arg_manifest["line_review"],
            "inventory": py_arg_manifest["inventory"],
            "hybrid_review": py_arg_manifest["hybrid_review"],
        }, indent=2, sort_keys=True),
        "```",
        "",
        "## Gaps",
        "",
    ]
    for py_var_gap, py_var_record in py_arg_manifest["gaps"].items():
        py_var_lines.extend([
            f"### {py_var_gap}",
            "",
            f"- Status: `{py_var_record['status']}`",
            f"- Next: {py_var_record['next_action']}",
            "",
            "```json",
            json.dumps(py_var_record["evidence"], indent=2, sort_keys=True),
            "```",
            "",
        ])
    (py_arg_out / "summary.md").write_text("\n".join(py_var_lines), encoding="utf-8")


def py_function_scripts_north_star_gap_closure_loop___self_test():
    py_var_failures = []

    def py_function_scripts_north_star_gap_closure_loop___self_test__check(py_arg_name, py_arg_ok, py_arg_detail=""):
        print(f"  [{'ok' if py_arg_ok else 'FAIL'}] {py_arg_name}{(': ' + py_arg_detail) if py_arg_detail and not py_arg_ok else ''}")
        if not py_arg_ok:
            py_var_failures.append(py_arg_name)

    import tempfile
    with tempfile.TemporaryDirectory() as py_var_dir:
        py_var_out = Path(py_var_dir)
        py_var_state = py_function_scripts_north_star_gap_closure_loop__build(py_var_out)
        py_function_scripts_north_star_gap_closure_loop___self_test__check(
            "loop writes state and summary",
            (py_var_out / "state.json").exists() and (py_var_out / "summary.md").exists(),
        )
        py_function_scripts_north_star_gap_closure_loop___self_test__check(
            "loop tracks all six north-star gaps",
            set(py_var_state["gaps"]) == {
                "repo_wide_unique_naming",
                "blast_radius_graph",
                "disagreement_management",
                "primitive_derivation",
                "registry_vectorization_search",
                "promotion_gate",
            },
        )
        py_function_scripts_north_star_gap_closure_loop___self_test__check(
            "loop stays candidate-only and selects a next action",
            py_var_state["serves_truth"] is False and bool(py_var_state["next_action"]),
        )

    if py_var_failures:
        print(f"\nFAIL - north_star_gap_closure_loop: {len(py_var_failures)} failure(s)")
        return 1
    print("\nPASS - north_star_gap_closure_loop: emits candidate north-star gap state and next action")
    return 0


def py_function_scripts_north_star_gap_closure_loop__main(py_arg_argv=None):
    py_var_parser = argparse.ArgumentParser(description="Build north-star gap closure loop state.")
    py_var_parser.add_argument("--out", default=str(py_const_scripts_north_star_gap_closure_loop__DEFAULT_OUT))
    py_var_parser.add_argument("--self-test", action="store_true")
    py_var_args = py_var_parser.parse_args(py_arg_argv)
    if py_var_args.self_test:
        return py_function_scripts_north_star_gap_closure_loop___self_test()
    py_var_out = Path(py_var_args.out)
    if not py_var_out.is_absolute():
        py_var_out = (_resource(py_var_out)).resolve()
    py_var_state = py_function_scripts_north_star_gap_closure_loop__build(py_var_out)
    print(json.dumps(py_var_state, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(py_function_scripts_north_star_gap_closure_loop__main())
