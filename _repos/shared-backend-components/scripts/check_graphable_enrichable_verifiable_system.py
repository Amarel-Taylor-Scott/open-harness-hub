#!/usr/bin/env python3
"""Proof for the Graphable, Enrichable, Verifiable (GEV) system contract."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import json
import tempfile
from pathlib import Path

from scripts import hybrid_repo_review_pipeline as py_var_scripts_check_graphable_enrichable_verifiable_system__hybrid
py_const_scripts_check_graphable_enrichable_verifiable_system__REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
py_const_scripts_check_graphable_enrichable_verifiable_system__SPEC = _resource("architecture/graphable_enrichable_verifiable_system.json")
py_const_scripts_check_graphable_enrichable_verifiable_system__DOC = _resource("docs/codex/graphable-enrichable-verifiable-system.md")

py_const_scripts_check_graphable_enrichable_verifiable_system__REQUIRED_RULE_IDS = {
    "maximize_context_in_source",
    "graph_everything_possible",
    "enrichment_is_candidate",
    "verification_promotes",
    "blast_radius_before_fix",
    "unresolved_is_explicit",
    "teleon_codegen_obeys_gev",
    "packets_are_resumable",
}

py_const_scripts_check_graphable_enrichable_verifiable_system__REQUIRED_LANES = {
    "deterministic",
    "hybrid",
    "nondeterministic",
    "human_or_owner_review",
}


def py_function_scripts_check_graphable_enrichable_verifiable_system__load_spec():
    return json.loads(py_const_scripts_check_graphable_enrichable_verifiable_system__SPEC.read_text(encoding="utf-8"))


def py_function_scripts_check_graphable_enrichable_verifiable_system__build_sample_packet():
    py_var_finding = {
        "path": "scripts/example.py",
        "line": 10,
        "kind": "dynamic_reference_contract",
        "severity": "high",
        "message": "Dynamic reference blocks exact rename confidence",
        "excerpt": "getattr(obj, name)",
        "deterministic_rule": "dynamic_reference_contract",
    }
    py_var_structural = {
        "nodes": [
            {"id": "scripts.example:foo", "module": "scripts.example", "kind": "function"},
            {"id": "scripts.example:bar", "module": "scripts.example", "kind": "function"},
        ],
        "edges": [{"src": "scripts.example:foo", "dst": "scripts.example:bar", "type": "calls"}],
    }
    py_var_opgraph = {
        "nodes": [
            {"id": "scripts/example.py:10:0:op_call:1", "file": "scripts/example.py", "kind": "op_call"}
        ],
        "edges": [{"src": "scripts/example.py:9:0:op_assign:1", "dst": "scripts/example.py:10:0:op_call:1", "type": "data_def_use"}],
    }
    return py_var_scripts_check_graphable_enrichable_verifiable_system__hybrid._build_packet(
        py_var_finding,
        py_var_structural,
        py_var_opgraph,
    )


def py_function_scripts_check_graphable_enrichable_verifiable_system___self_test():
    py_var_failures = []

    def py_function_scripts_check_graphable_enrichable_verifiable_system___self_test__check(py_arg_name, py_arg_ok, py_arg_detail=""):
        print(f"  [{'ok' if py_arg_ok else 'FAIL'}] {py_arg_name}{(': ' + py_arg_detail) if py_arg_detail and not py_arg_ok else ''}")
        if not py_arg_ok:
            py_var_failures.append(py_arg_name)

    py_var_spec = py_function_scripts_check_graphable_enrichable_verifiable_system__load_spec()
    py_var_doc = py_const_scripts_check_graphable_enrichable_verifiable_system__DOC.read_text(encoding="utf-8")

    py_function_scripts_check_graphable_enrichable_verifiable_system___self_test__check(
        "GEV spec is candidate-only",
        py_var_spec.get("serves_truth") is False,
    )
    py_var_principle = py_var_spec.get("principle", "").lower()
    py_function_scripts_check_graphable_enrichable_verifiable_system___self_test__check(
        "GEV principle binds names, graphs, evidence, enrichment, and proofs",
        "names carry context" in py_var_principle
        and "proofs carry acceptance" in py_var_principle,
    )

    py_var_rule_ids = {py_var_rule.get("id") for py_var_rule in py_var_spec.get("rules", [])}
    py_function_scripts_check_graphable_enrichable_verifiable_system___self_test__check(
        "all required GEV rules exist",
        py_const_scripts_check_graphable_enrichable_verifiable_system__REQUIRED_RULE_IDS <= py_var_rule_ids,
        str(sorted(py_const_scripts_check_graphable_enrichable_verifiable_system__REQUIRED_RULE_IDS - py_var_rule_ids)),
    )

    py_var_lane_ids = {py_var_lane.get("id") for py_var_lane in py_var_spec.get("lanes", [])}
    py_function_scripts_check_graphable_enrichable_verifiable_system___self_test__check(
        "all verification lanes exist",
        py_const_scripts_check_graphable_enrichable_verifiable_system__REQUIRED_LANES <= py_var_lane_ids,
        str(sorted(py_const_scripts_check_graphable_enrichable_verifiable_system__REQUIRED_LANES - py_var_lane_ids)),
    )

    py_var_packet = py_function_scripts_check_graphable_enrichable_verifiable_system__build_sample_packet()
    py_var_required_packet_fields = set(py_var_spec.get("packet_required_fields", []))
    py_function_scripts_check_graphable_enrichable_verifiable_system___self_test__check(
        "hybrid review packet satisfies required GEV packet fields",
        py_var_required_packet_fields <= set(py_var_packet),
        str(sorted(py_var_required_packet_fields - set(py_var_packet))),
    )
    py_function_scripts_check_graphable_enrichable_verifiable_system___self_test__check(
        "packet carries deterministic/hybrid/nondeterministic verification lanes",
        {"deterministic", "hybrid", "nondeterministic"} <= {py_var_lane["lane"] for py_var_lane in py_var_packet["verification_lanes"]},
    )
    py_function_scripts_check_graphable_enrichable_verifiable_system___self_test__check(
        "high dynamic packet requires human/owner review lane",
        "human_or_owner_review" in {py_var_lane["lane"] for py_var_lane in py_var_packet["verification_lanes"]},
    )
    py_function_scripts_check_graphable_enrichable_verifiable_system___self_test__check(
        "packet carries blast-radius context",
        py_var_packet["blast_radius"]["direct_edge_count"] >= 1 and py_var_packet["blast_radius"]["level"] in {"local_or_unknown", "medium", "wide"},
    )
    py_function_scripts_check_graphable_enrichable_verifiable_system___self_test__check(
        "packet context policy explicitly maximizes context and limits confusion",
        "maximize_context" in py_var_packet["context_policy"] and "limit_confusion" in py_var_packet["context_policy"],
    )
    py_function_scripts_check_graphable_enrichable_verifiable_system___self_test__check(
        "GEV doc names graphable/enrichable/verifiable and blast radius",
        "# Graphable, Enrichable, Verifiable System" in py_var_doc
        and "## 4. Blast Radius" in py_var_doc,
    )

    if py_var_failures:
        print(f"\nFAIL - check_graphable_enrichable_verifiable_system: {len(py_var_failures)} failure(s)")
        return 1
    print("\nPASS - check_graphable_enrichable_verifiable_system: packets are graphable, enrichable, verifiable, and blast-radius aware")
    return 0


def py_function_scripts_check_graphable_enrichable_verifiable_system__main():
    return py_function_scripts_check_graphable_enrichable_verifiable_system___self_test()


if __name__ == "__main__":
    raise SystemExit(py_function_scripts_check_graphable_enrichable_verifiable_system__main())
