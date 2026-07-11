#!/usr/bin/env python3
"""Proof for GEV adversarial corner cases, interrogatories, and skill templates."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import json
from pathlib import Path

from scripts import hybrid_repo_review_pipeline as py_var_scripts_check_gev_adversarial_interrogatories__hybrid
py_const_scripts_check_gev_adversarial_interrogatories__REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
py_const_scripts_check_gev_adversarial_interrogatories__SPEC = _resource("architecture/gev_adversarial_interrogatories.json")
py_const_scripts_check_gev_adversarial_interrogatories__DOC = _resource("docs/codex/gev-adversarial-interrogatories.md")

py_const_scripts_check_gev_adversarial_interrogatories__REQUIRED_CATEGORIES = {
    "dynamic_python",
    "framework_entrypoints",
    "schema_and_serialization",
    "data_shape_scalability",
    "control_flow_fragility",
    "state_and_side_effects",
    "blast_radius_and_reexports",
    "security_privacy_tenant",
    "temporal_and_freshness",
    "long_name_failure_modes",
    "multi_language_surface",
    "generated_code_quality",
}

py_const_scripts_check_gev_adversarial_interrogatories__CORE_TEMPLATES = {
    "graphability_interrogatory",
    "blast_radius_interrogatory",
    "enrichment_interrogatory",
    "verification_interrogatory",
}

py_const_scripts_check_gev_adversarial_interrogatories__SPECIALIZED_TEMPLATES = {
    "data_shape_interrogatory",
    "dynamic_reference_interrogatory",
    "security_privacy_interrogatory",
    "external_contract_interrogatory",
}

py_const_scripts_check_gev_adversarial_interrogatories__SKILL_TEMPLATES = {
    "graph_cartographer",
    "contract_skeptic",
    "data_shape_normalizer",
    "verification_prosecutor",
    "adversarial_breaker",
    "ux_product_mapper",
}


def py_function_scripts_check_gev_adversarial_interrogatories__load_spec():
    return json.loads(py_const_scripts_check_gev_adversarial_interrogatories__SPEC.read_text(encoding="utf-8"))


def py_function_scripts_check_gev_adversarial_interrogatories__sample_packet_for_kind(py_arg_kind):
    py_var_finding = {
        "path": "scripts/example.py",
        "line": 1,
        "kind": py_arg_kind,
        "severity": "medium",
        "message": "sample",
        "excerpt": "sample",
        "deterministic_rule": py_arg_kind,
    }
    return py_var_scripts_check_gev_adversarial_interrogatories__hybrid._build_packet(py_var_finding, None, None)


def py_function_scripts_check_gev_adversarial_interrogatories___self_test():
    py_var_failures = []

    def py_function_scripts_check_gev_adversarial_interrogatories___self_test__check(py_arg_name, py_arg_ok, py_arg_detail=""):
        print(f"  [{'ok' if py_arg_ok else 'FAIL'}] {py_arg_name}{(': ' + py_arg_detail) if py_arg_detail and not py_arg_ok else ''}")
        if not py_arg_ok:
            py_var_failures.append(py_arg_name)

    py_var_spec = py_function_scripts_check_gev_adversarial_interrogatories__load_spec()
    py_var_doc = py_const_scripts_check_gev_adversarial_interrogatories__DOC.read_text(encoding="utf-8")

    py_function_scripts_check_gev_adversarial_interrogatories___self_test__check(
        "adversarial spec is candidate-only",
        py_var_spec.get("serves_truth") is False,
    )

    py_var_category_ids = {py_var_row.get("id") for py_var_row in py_var_spec.get("corner_case_categories", [])}
    py_function_scripts_check_gev_adversarial_interrogatories___self_test__check(
        "all required corner-case families are covered",
        py_const_scripts_check_gev_adversarial_interrogatories__REQUIRED_CATEGORIES <= py_var_category_ids,
        str(sorted(py_const_scripts_check_gev_adversarial_interrogatories__REQUIRED_CATEGORIES - py_var_category_ids)),
    )

    py_var_template_ids = {py_var_row.get("id") for py_var_row in py_var_spec.get("interrogatory_templates", [])}
    py_function_scripts_check_gev_adversarial_interrogatories___self_test__check(
        "core interrogatories are present",
        py_const_scripts_check_gev_adversarial_interrogatories__CORE_TEMPLATES <= py_var_template_ids,
        str(sorted(py_const_scripts_check_gev_adversarial_interrogatories__CORE_TEMPLATES - py_var_template_ids)),
    )
    py_function_scripts_check_gev_adversarial_interrogatories___self_test__check(
        "specialized interrogatories are present",
        py_const_scripts_check_gev_adversarial_interrogatories__SPECIALIZED_TEMPLATES <= py_var_template_ids,
        str(sorted(py_const_scripts_check_gev_adversarial_interrogatories__SPECIALIZED_TEMPLATES - py_var_template_ids)),
    )

    py_var_skill_ids = {py_var_row.get("id") for py_var_row in py_var_spec.get("skill_templates", [])}
    py_function_scripts_check_gev_adversarial_interrogatories___self_test__check(
        "reviewer skill templates are present",
        py_const_scripts_check_gev_adversarial_interrogatories__SKILL_TEMPLATES <= py_var_skill_ids,
        str(sorted(py_const_scripts_check_gev_adversarial_interrogatories__SKILL_TEMPLATES - py_var_skill_ids)),
    )

    for py_var_template in py_var_spec.get("interrogatory_templates", []):
        py_function_scripts_check_gev_adversarial_interrogatories___self_test__check(
            f"interrogatory {py_var_template.get('id')} has questions and evidence",
            len(py_var_template.get("questions", [])) >= 4 and len(py_var_template.get("required_evidence", [])) >= 2,
        )

    py_var_dynamic_packet = py_function_scripts_check_gev_adversarial_interrogatories__sample_packet_for_kind("dynamic_reference_contract")
    py_function_scripts_check_gev_adversarial_interrogatories___self_test__check(
        "dynamic packet gets specialized interrogatory",
        "dynamic_reference_interrogatory" in py_var_dynamic_packet.get("interrogatory_template_ids", []),
    )

    py_var_shape_packet = py_function_scripts_check_gev_adversarial_interrogatories__sample_packet_for_kind("scalar_series_candidate")
    py_function_scripts_check_gev_adversarial_interrogatories___self_test__check(
        "scalar-series packet gets data-shape interrogatory",
        "data_shape_interrogatory" in py_var_shape_packet.get("interrogatory_template_ids", []),
    )

    py_function_scripts_check_gev_adversarial_interrogatories___self_test__check(
        "doc records corner cases and reviewer skill templates",
        "## Corner-Case Families" in py_var_doc and "## Reviewer Skill Templates" in py_var_doc,
    )

    if py_var_failures:
        print(f"\nFAIL - check_gev_adversarial_interrogatories: {len(py_var_failures)} failure(s)")
        return 1
    print("\nPASS - check_gev_adversarial_interrogatories: corner cases, interrogatories, and reviewer skill templates are wired into packets")
    return 0


def py_function_scripts_check_gev_adversarial_interrogatories__main():
    return py_function_scripts_check_gev_adversarial_interrogatories___self_test()


if __name__ == "__main__":
    raise SystemExit(py_function_scripts_check_gev_adversarial_interrogatories__main())
