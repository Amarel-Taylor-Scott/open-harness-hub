#!/usr/bin/env python3
"""Proof: primitive registry builder emits governed real-code candidate/search/vector records."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import json
import sys
import tempfile
from pathlib import Path


py_const_scripts_check_primitive_registry_builder__REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(py_const_scripts_check_primitive_registry_builder__REPO) not in sys.path:
    sys.path.insert(0, str(py_const_scripts_check_primitive_registry_builder__REPO))

from scripts import primitive_registry_builder
from scripts import primitive_quality_promoter
from scripts.db import primitive_registry_operational_load_plan
from src.teleon.registry import primitive_match


py_const_scripts_check_primitive_registry_builder__CONTRACT = _resource("architecture/primitive_registry_builder_contracts.json")


def py_function_scripts_check_primitive_registry_builder__load_contract():
    return json.loads(py_const_scripts_check_primitive_registry_builder__CONTRACT.read_text(encoding="utf-8"))


def py_function_scripts_check_primitive_registry_builder__artifact_names(py_arg_scripts_check_primitive_registry_builder__artifact_names__value):
    py_local_scripts_check_primitive_registry_builder__artifact_names__names = set()
    if isinstance(py_arg_scripts_check_primitive_registry_builder__artifact_names__value, dict):
        for py_local_scripts_check_primitive_registry_builder__artifact_names__child in py_arg_scripts_check_primitive_registry_builder__artifact_names__value.values():
            py_local_scripts_check_primitive_registry_builder__artifact_names__names |= py_function_scripts_check_primitive_registry_builder__artifact_names(py_local_scripts_check_primitive_registry_builder__artifact_names__child)
    elif isinstance(py_arg_scripts_check_primitive_registry_builder__artifact_names__value, list):
        for py_local_scripts_check_primitive_registry_builder__artifact_names__child in py_arg_scripts_check_primitive_registry_builder__artifact_names__value:
            py_local_scripts_check_primitive_registry_builder__artifact_names__names |= py_function_scripts_check_primitive_registry_builder__artifact_names(py_local_scripts_check_primitive_registry_builder__artifact_names__child)
    elif py_arg_scripts_check_primitive_registry_builder__artifact_names__value:
        py_local_scripts_check_primitive_registry_builder__artifact_names__names.add(Path(str(py_arg_scripts_check_primitive_registry_builder__artifact_names__value)).name)
    return py_local_scripts_check_primitive_registry_builder__artifact_names__names


def py_function_scripts_check_primitive_registry_builder__self_test():
    py_local_scripts_check_primitive_registry_builder__self_test__failures = []

    def py_function_scripts_check_primitive_registry_builder__self_test__check(py_arg_scripts_check_primitive_registry_builder__self_test_check__name, py_arg_scripts_check_primitive_registry_builder__self_test_check__ok, py_arg_scripts_check_primitive_registry_builder__self_test_check__detail=""):
        print(f"  [{'ok' if py_arg_scripts_check_primitive_registry_builder__self_test_check__ok else 'FAIL'}] {py_arg_scripts_check_primitive_registry_builder__self_test_check__name}{(': ' + py_arg_scripts_check_primitive_registry_builder__self_test_check__detail) if py_arg_scripts_check_primitive_registry_builder__self_test_check__detail and not py_arg_scripts_check_primitive_registry_builder__self_test_check__ok else ''}")
        if not py_arg_scripts_check_primitive_registry_builder__self_test_check__ok:
            py_local_scripts_check_primitive_registry_builder__self_test__failures.append(py_arg_scripts_check_primitive_registry_builder__self_test_check__name)

    py_local_scripts_check_primitive_registry_builder__self_test__contract = py_function_scripts_check_primitive_registry_builder__load_contract()
    py_local_scripts_check_primitive_registry_builder__self_test__required_fields = set(py_local_scripts_check_primitive_registry_builder__self_test__contract.get("required_record_fields", []))
    py_local_scripts_check_primitive_registry_builder__self_test__required_artifacts = set(py_local_scripts_check_primitive_registry_builder__self_test__contract.get("required_artifacts", []))
    py_local_scripts_check_primitive_registry_builder__self_test__required_quality_artifacts = set(py_local_scripts_check_primitive_registry_builder__self_test__contract.get("quality_required_artifacts", []))
    py_local_scripts_check_primitive_registry_builder__self_test__required_dimensions = set(py_local_scripts_check_primitive_registry_builder__self_test__contract.get("required_search_dimensions", []))
    py_local_scripts_check_primitive_registry_builder__self_test__required_search_index_fields = set(py_local_scripts_check_primitive_registry_builder__self_test__contract.get("required_search_index_fields", []))
    py_local_scripts_check_primitive_registry_builder__self_test__required_blocking_profile_fields = set(py_local_scripts_check_primitive_registry_builder__self_test__contract.get("required_blocking_profile_fields", []))
    py_local_scripts_check_primitive_registry_builder__self_test__required_blocking_index_fields = set(py_local_scripts_check_primitive_registry_builder__self_test__contract.get("required_blocking_index_fields", []))
    py_local_scripts_check_primitive_registry_builder__self_test__required_mutation_surfaces = set(py_local_scripts_check_primitive_registry_builder__self_test__contract.get("verified_mutation_call_surfaces", []))

    py_function_scripts_check_primitive_registry_builder__self_test__check("contract is candidate-only", py_local_scripts_check_primitive_registry_builder__self_test__contract.get("serves_truth") is False)
    py_function_scripts_check_primitive_registry_builder__self_test__check(
        "contract points at builder, load plan, and promotion gate",
        (_resource(py_local_scripts_check_primitive_registry_builder__self_test__contract["builder"])).exists()
        and (_resource(py_local_scripts_check_primitive_registry_builder__self_test__contract["quality_promoter"])).exists()
        and (_resource(py_local_scripts_check_primitive_registry_builder__self_test__contract["quality_promoter_checker"])).exists()
        and (_resource(py_local_scripts_check_primitive_registry_builder__self_test__contract["operational_load_plan"])).exists()
        and (_resource(py_local_scripts_check_primitive_registry_builder__self_test__contract["promotion_gate"])).exists(),
    )
    py_function_scripts_check_primitive_registry_builder__self_test__check("contract lists all builder required fields", primitive_registry_builder.py_const_scripts_primitive_registry_builder__REQUIRED_RECORD_FIELDS <= py_local_scripts_check_primitive_registry_builder__self_test__required_fields)
    py_function_scripts_check_primitive_registry_builder__self_test__check("contract includes all hybrid search dimensions", set(primitive_match.py_const_src_teleon_registry_primitive_match__SEARCH_DIMENSIONS) <= py_local_scripts_check_primitive_registry_builder__self_test__required_dimensions)
    py_function_scripts_check_primitive_registry_builder__self_test__check("contract requires search index blocking profile fields", {"blocking_profile", "blocking_profile_fields"} <= py_local_scripts_check_primitive_registry_builder__self_test__required_search_index_fields and set(primitive_match.py_const_src_teleon_registry_primitive_match__BLOCK_PROFILE_FIELDS) <= py_local_scripts_check_primitive_registry_builder__self_test__required_blocking_profile_fields)
    py_function_scripts_check_primitive_registry_builder__self_test__check("contract requires persisted blocking index fields", set(primitive_match.py_const_src_teleon_registry_primitive_match__BLOCKING_INDEX_FIELDS) <= py_local_scripts_check_primitive_registry_builder__self_test__required_blocking_index_fields)

    with tempfile.TemporaryDirectory() as py_local_scripts_check_primitive_registry_builder__self_test__tmp:
        py_inst_scripts_check_primitive_registry_builder__self_test__root = Path(py_local_scripts_check_primitive_registry_builder__self_test__tmp)
        py_local_scripts_check_primitive_registry_builder__self_test__inventory = primitive_registry_builder.py_function_scripts_primitive_registry_builder__write_fixture_inventory(py_inst_scripts_check_primitive_registry_builder__self_test__root)
        py_local_scripts_check_primitive_registry_builder__self_test__out = py_inst_scripts_check_primitive_registry_builder__self_test__root / "out"
        py_local_scripts_check_primitive_registry_builder__self_test__manifest, py_local_scripts_check_primitive_registry_builder__self_test__records, py_local_scripts_check_primitive_registry_builder__self_test__search_rows, py_local_scripts_check_primitive_registry_builder__self_test__vector_rows = primitive_registry_builder.py_function_scripts_primitive_registry_builder__build(py_local_scripts_check_primitive_registry_builder__self_test__inventory, py_local_scripts_check_primitive_registry_builder__self_test__out, 100, True)
        py_local_scripts_check_primitive_registry_builder__self_test__artifact_names = py_function_scripts_check_primitive_registry_builder__artifact_names(py_local_scripts_check_primitive_registry_builder__self_test__manifest["artifacts"])
        py_local_scripts_check_primitive_registry_builder__self_test__first = py_local_scripts_check_primitive_registry_builder__self_test__records[0]
        py_function_scripts_check_primitive_registry_builder__self_test__check("builder writes every required artifact", py_local_scripts_check_primitive_registry_builder__self_test__required_artifacts <= py_local_scripts_check_primitive_registry_builder__self_test__artifact_names, str(sorted(py_local_scripts_check_primitive_registry_builder__self_test__required_artifacts - py_local_scripts_check_primitive_registry_builder__self_test__artifact_names)))
        py_function_scripts_check_primitive_registry_builder__self_test__check(
            "builder emits operational row families",
            set(primitive_registry_builder.py_const_scripts_primitive_registry_builder__OPERATIONAL_ROW_FILES) <= set(py_local_scripts_check_primitive_registry_builder__self_test__manifest["operational_rows"])
            and py_local_scripts_check_primitive_registry_builder__self_test__manifest["operational_rows"]["registry_record"] == len(py_local_scripts_check_primitive_registry_builder__self_test__records)
            and py_local_scripts_check_primitive_registry_builder__self_test__manifest["operational_rows"]["primitive_edge"] == len(py_local_scripts_check_primitive_registry_builder__self_test__records) * 2,
        )
        py_local_scripts_check_primitive_registry_builder__self_test__blocking_index = json.loads((py_local_scripts_check_primitive_registry_builder__self_test__out / "primitive_blocking_index.json").read_text(encoding="utf-8"))
        py_function_scripts_check_primitive_registry_builder__self_test__check("builder produces candidate records from real artifacts", py_local_scripts_check_primitive_registry_builder__self_test__records and all(record["license_provenance"]["generated_from_real_artifact"] and record["synthetic"] is False for record in py_local_scripts_check_primitive_registry_builder__self_test__records))
        py_function_scripts_check_primitive_registry_builder__self_test__check("every candidate record has required fields", all(set(record) >= py_local_scripts_check_primitive_registry_builder__self_test__required_fields for record in py_local_scripts_check_primitive_registry_builder__self_test__records))
        py_function_scripts_check_primitive_registry_builder__self_test__check("candidate records remain non-truth", all(record["candidate"] is True and record["serves_truth"] is False for record in py_local_scripts_check_primitive_registry_builder__self_test__records))
        py_function_scripts_check_primitive_registry_builder__self_test__check("records carry contracts, proof command, dependencies, provenance, logs, graph edges", isinstance(py_local_scripts_check_primitive_registry_builder__self_test__first["input_contract"], dict) and isinstance(py_local_scripts_check_primitive_registry_builder__self_test__first["output_contract"], dict) and isinstance(py_local_scripts_check_primitive_registry_builder__self_test__first["dependencies"], list) and py_local_scripts_check_primitive_registry_builder__self_test__first["license_provenance"] and py_local_scripts_check_primitive_registry_builder__self_test__first["proof_command"] and py_local_scripts_check_primitive_registry_builder__self_test__first["logs_schema"] and py_local_scripts_check_primitive_registry_builder__self_test__first["graph_edges"])
        py_function_scripts_check_primitive_registry_builder__self_test__check(
            "records expose standardized call surface for deterministic tools and LLMs",
            isinstance(py_local_scripts_check_primitive_registry_builder__self_test__first["call_surface"], dict)
            and py_local_scripts_check_primitive_registry_builder__self_test__first["call_surface"]["entrypoint_candidate"]
            and py_local_scripts_check_primitive_registry_builder__self_test__first["call_surface"]["serves_truth"] is False,
        )
        py_function_scripts_check_primitive_registry_builder__self_test__check(
            "records expose composition affordances",
            isinstance(py_local_scripts_check_primitive_registry_builder__self_test__first["composition"], dict)
            and py_local_scripts_check_primitive_registry_builder__self_test__first["composition"]["consumes_state"]
            and py_local_scripts_check_primitive_registry_builder__self_test__first["composition"]["produces_state"]
            and py_local_scripts_check_primitive_registry_builder__self_test__first["composition"]["edge_policy"],
        )
        py_local_scripts_check_primitive_registry_builder__self_test__first_mutations = {
            row["mutation"]
            for row in py_local_scripts_check_primitive_registry_builder__self_test__first["mutation_affordances"]["verified_call_surfaces"]
        }
        py_function_scripts_check_primitive_registry_builder__self_test__check(
            "records expose verified mutation call surfaces",
            py_local_scripts_check_primitive_registry_builder__self_test__required_mutation_surfaces <= py_local_scripts_check_primitive_registry_builder__self_test__first_mutations
            and py_local_scripts_check_primitive_registry_builder__self_test__first["mutation_affordances"]["deterministic_first"] is True
            and py_local_scripts_check_primitive_registry_builder__self_test__first["mutation_affordances"]["serves_truth"] is False,
            str(sorted(py_local_scripts_check_primitive_registry_builder__self_test__required_mutation_surfaces - py_local_scripts_check_primitive_registry_builder__self_test__first_mutations)),
        )
        py_function_scripts_check_primitive_registry_builder__self_test__check("search rows carry every contract-required field", py_local_scripts_check_primitive_registry_builder__self_test__required_search_index_fields <= set(py_local_scripts_check_primitive_registry_builder__self_test__search_rows[0]))
        py_function_scripts_check_primitive_registry_builder__self_test__check("search rows expose hybrid search dimensions", set(py_local_scripts_check_primitive_registry_builder__self_test__search_rows[0]["search_dimensions"]) >= py_local_scripts_check_primitive_registry_builder__self_test__required_dimensions)
        py_function_scripts_check_primitive_registry_builder__self_test__check("search rows expose precomputed blocking profile fields", py_local_scripts_check_primitive_registry_builder__self_test__required_blocking_profile_fields <= set(py_local_scripts_check_primitive_registry_builder__self_test__search_rows[0]["blocking_profile"]) and py_local_scripts_check_primitive_registry_builder__self_test__search_rows[0]["blocking_profile"]["serves_truth"] is False)
        py_function_scripts_check_primitive_registry_builder__self_test__check("builder emits reusable primitive blocking index", py_local_scripts_check_primitive_registry_builder__self_test__required_blocking_index_fields <= set(py_local_scripts_check_primitive_registry_builder__self_test__blocking_index) and py_local_scripts_check_primitive_registry_builder__self_test__blocking_index["candidate_count"] == len(py_local_scripts_check_primitive_registry_builder__self_test__search_rows))
        py_function_scripts_check_primitive_registry_builder__self_test__check("vector rows carry deterministic embedding dim", py_local_scripts_check_primitive_registry_builder__self_test__vector_rows[0]["embedding_dim"] == primitive_registry_builder.EMBED_DIM and len(py_local_scripts_check_primitive_registry_builder__self_test__vector_rows[0]["embedding"]) == primitive_registry_builder.EMBED_DIM)
        py_local_scripts_check_primitive_registry_builder__self_test__quality_manifest = primitive_quality_promoter.build(py_local_scripts_check_primitive_registry_builder__self_test__out, write=True)
        py_local_scripts_check_primitive_registry_builder__self_test__quality_artifact_names = {
            Path(value).name
            for value in (py_local_scripts_check_primitive_registry_builder__self_test__quality_manifest.get("artifacts") or {}).values()
        }
        py_function_scripts_check_primitive_registry_builder__self_test__check(
            "quality promoter writes every required quality artifact",
            py_local_scripts_check_primitive_registry_builder__self_test__required_quality_artifacts <= py_local_scripts_check_primitive_registry_builder__self_test__quality_artifact_names,
            str(sorted(py_local_scripts_check_primitive_registry_builder__self_test__required_quality_artifacts - py_local_scripts_check_primitive_registry_builder__self_test__quality_artifact_names)),
        )
        py_function_scripts_check_primitive_registry_builder__self_test__check(
            "quality promoter keeps assessments candidate-only",
            py_local_scripts_check_primitive_registry_builder__self_test__quality_manifest["serves_truth"] is False
            and py_local_scripts_check_primitive_registry_builder__self_test__quality_manifest["assessments"] == len(py_local_scripts_check_primitive_registry_builder__self_test__records),
        )
        py_function_scripts_check_primitive_registry_builder__self_test__check("operational load-plan self-test passes", primitive_registry_operational_load_plan.py_function_scripts_db_primitive_registry_operational_load_plan__self_test() == 0)
        py_function_scripts_check_primitive_registry_builder__self_test__check("builder self-test passes", primitive_registry_builder.py_function_scripts_primitive_registry_builder__self_test() == 0)

    if py_local_scripts_check_primitive_registry_builder__self_test__failures:
        print(f"\nFAIL - check_primitive_registry_builder: {len(py_local_scripts_check_primitive_registry_builder__self_test__failures)} failure(s)")
        return 1
    print("\nPASS - check_primitive_registry_builder: primitive registry builder contract and artifacts are governed")
    return 0


def main():
    return py_function_scripts_check_primitive_registry_builder__self_test()


if __name__ == "__main__":
    raise SystemExit(main())
