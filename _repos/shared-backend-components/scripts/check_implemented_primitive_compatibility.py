#!/usr/bin/env python3
"""Check implemented-code primitive records against existing primitive formats.

This checker is intentionally stdlib-only. It validates the compact primitive-card
contract used by the generated packs and emits a compatibility export shaped like
the older `.agent/primitive-registry/primitive_candidate_records.jsonl` records.
"""

from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = _resource("data/dev-intel/implemented_code_primitives/daily_20260702_2k/implemented_code_primitives.jsonl")

CORE_FIELDS = (
    "primitive_id",
    "record_type",
    "kind",
    "title",
    "input_edge",
    "output_edge",
    "blackbox",
    "effects",
    "runtime_targets",
    "proof_requirements",
    "candidate",
    "serves_truth",
)

SOURCE_BACKED_FIELDS = (
    "source_path",
    "source_root",
    "source_span",
    "code",
    "code_sha256",
    "dedupe_key",
    "validation",
    "promotion_blockers",
)

CONSUMPTION_FIELDS = (
    "id",
    "name",
    "description",
    "purpose",
    "candidate",
    "serves_truth",
    "input_contract",
    "output_contract",
    "call_surface",
    "composition",
    "license_provenance",
    "mutation_affordances",
    "promotion_status",
    "proof_command",
    "tags",
    "version",
)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{line_no}: invalid JSONL: {exc}") from exc
            if not isinstance(row, dict):
                raise SystemExit(f"{path}:{line_no}: expected object row")
            rows.append(row)
    return rows


def _missing(row: dict[str, Any], fields: tuple[str, ...]) -> list[str]:
    return [field for field in fields if field not in row]


def _as_bool(value: Any) -> bool:
    return value is True


def _source_ref(row: dict[str, Any]) -> str:
    span = row.get("source_span") or {}
    line = span.get("start_line", "?")
    return f"{row.get('source_path', 'unknown')}:{line}"


def _compatible_record(row: dict[str, Any]) -> dict[str, Any]:
    source_ref = _source_ref(row)
    code_kind = row.get("code_kind", "code_object")
    input_shape = "callable_signature_candidate" if code_kind in {"function", "async_function"} else "python_class_candidate"
    output_shape = row.get("return_annotation") or "unknown_candidate"
    name = row.get("qualname") or row.get("code_object_id") or row["primitive_id"]
    parameters = [
        {
            "kind": "python_parameter",
            "name": parameter,
            "required": True,
            "source_line": (row.get("source_span") or {}).get("start_line"),
        }
        for parameter in row.get("parameters", [])
    ]
    python_symbol = row.get("qualname") or name
    path = row.get("source_path", "")
    return {
        "id": row["primitive_id"],
        "primitive_id": row["primitive_id"],
        "name": name,
        "description": row.get("blackbox") or row.get("title") or name,
        "long_description": row.get("docstring") or row.get("blackbox") or row.get("title") or name,
        "purpose": (
            f"Candidate primitive generated from real source object `{name}` "
            f"({code_kind}) at `{source_ref}`. Use as searchable graph evidence; "
            "enrich and prove before promotion."
        ),
        "record_type": row.get("record_type", "implemented_code_primitive_candidate"),
        "candidate": row.get("candidate") is True,
        "serves_truth": row.get("serves_truth") is True,
        "input_edge": row.get("input_edge"),
        "output_edge": row.get("output_edge"),
        "input_contract": {
            "shape": input_shape,
            "source": "implemented_code_ast_mining",
            "parameters": parameters,
            "edge": row.get("input_edge"),
            "signature": row.get("signature"),
        },
        "output_contract": {
            "shape": output_shape,
            "edge": row.get("output_edge"),
            "reason": "Return shape is annotation-derived or unknown; promote only after fixture receipts or observed logs.",
        },
        "call_surface": {
            "kind": "python_callable_candidate" if code_kind in {"function", "async_function"} else "python_class_candidate",
            "call_boundary": "candidate_only_until_proof",
            "entrypoint_candidate": f"{path}:{python_symbol}",
            "python_path": path,
            "python_symbol": python_symbol,
            "input_contract_shape": input_shape,
            "output_contract_shape": output_shape,
            "serves_truth": False,
        },
        "composition": {
            "consumes_state": [input_shape],
            "produces_state": [output_shape],
            "edge_policy": "compiler_must_validate_bindings_before_execution",
            "repeatable": "unknown_candidate",
            "pure": "unknown_candidate",
            "idempotent": "unknown_candidate",
            "side_effect_boundary": row.get("effects", []) != ["unknown_runtime_effects_need_audit"],
            "serves_truth": False,
        },
        "license_provenance": {
            "generated_from_real_artifact": True,
            "synthetic": False,
            "source": "implemented_code_ast_mining",
            "path": path,
            "line": (row.get("source_span") or {}).get("start_line"),
            "symbol_kind": code_kind,
            "symbol_name": name,
            "license": "repo_default_or_unknown",
        },
        "mutation_affordances": {
            "deterministic_first": True,
            "applicable_hints": ["input_envelope_wrapper", "output_receipt_wrapper", "fixture_behavior_wrapper"],
            "llm_generated_adapter_last_resort": True,
            "promotion_required_for_variants": True,
            "serves_truth": False,
        },
        "promotion_status": "candidate_only",
        "proof_command": "python3 scripts/check_implemented_primitive_compatibility.py --input <records.jsonl>",
        "proof_requirements": row.get("proof_requirements", []),
        "promotion_blockers": row.get("promotion_blockers", []),
        "source_ref": source_ref,
        "source_ref_structured": {
            "path": path,
            "line": (row.get("source_span") or {}).get("start_line"),
            "end_line": (row.get("source_span") or {}).get("end_line"),
            "language": row.get("language", "python"),
            "name": name,
        },
        "metadata": {
            "keywords": [part for part in str(name).replace("_", " ").replace(".", " ").split() if part],
            "labels": ["candidate", "real_code_artifact", f"kind:{code_kind}", f"path:{path}"],
            "use_cases": [
                f"use {name} as source-backed primitive evidence",
                f"compose {name} only after compiler binding and proof receipts",
            ],
        },
        "tags": ["primitive_candidate", code_kind, "real_code_artifact", "implemented_code"],
        "version": "0.1.0",
        "code_sha256": row.get("code_sha256"),
        "dedupe_key": row.get("dedupe_key"),
        "validation": row.get("validation", {}),
    }


def _count_generated_md_rows(root: Path) -> tuple[int, int]:
    manifest_path = root / "generated_primitive_packs/manifest.json"
    if not manifest_path.exists():
        return 0, 0
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    packs = manifest.get("packs", [])
    return len(packs), sum(int(pack.get("row_count", 0)) for pack in packs)


def _selected_primitive_surface_counts(root: Path) -> dict[str, Any]:
    paths = [
        ".agent/primitive-registry/primitive_candidate_records.jsonl",
        ".agent/primitive-registry/primitive_search_index.jsonl",
        ".agent/primitive-registry/quality/aidevobserver_surfaceable_primitives.jsonl",
        "data/dev-intel/aidevobserver_context_foundry/primitive_drafts.jsonl",
        "data/dev-intel/aidevobserver_edge_foundry/primitive_edge_cards.jsonl",
        "data/dev-intel/aidevobserver_edge_foundry/source_backed_primitive_group_cards.jsonl",
        "data/dev-intel/aidevobserver_edge_foundry/curated_primitive_groups.jsonl",
        "data/dev-intel/aidevobserver_edge_foundry/primitive_kind_family_cards.jsonl",
        "data/dev-intel/aidevobserver_edge_foundry/runtime_shape_primitive_cards.jsonl",
        "catalog/knowledge-packs/data/primitive-cloud-guardrail-runtime/guardrail_primitives.jsonl",
        "catalog/knowledge-packs/data/primitive-variation-dimension-atlas/primitive_variation_dimensions_250.jsonl",
        "catalog/knowledge-packs/data/primitive-variation-dimension-atlas/primitive_specialization_examples.jsonl",
        "catalog/knowledge-packs/data/primitive-customization-overlays/specialized_primitives.jsonl",
        "catalog/knowledge-packs/data/high-priority-primitive-opportunity-rankings/primitive_opportunities_1000.jsonl",
        "catalog/knowledge-packs/data/compiled-primitive-route-benchmark-seeds/primitive_search_paths.jsonl",
        "catalog/knowledge-packs/data/compiled-primitive-route-benchmark-seeds/primitive_cooccurrence_examples.jsonl",
        "catalog/knowledge-packs/data/compiled-primitive-route-benchmark-seeds/primitive_generation_paths.jsonl",
        "catalog/knowledge-packs/data/marketplace-primitive-source-surfaces/example_marketplace_primitive_cards.jsonl",
    ]
    counts: dict[str, int] = {}
    for rel_path in paths:
        path = root / rel_path
        if path.exists():
            counts[rel_path] = sum(1 for line in path.open("r", encoding="utf-8") if line.strip())
    return {
        "selected_surface_count": len(counts),
        "selected_surface_rows": sum(counts.values()),
        "counts": counts,
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    input_path = Path(args.input).resolve()
    rows = _read_jsonl(input_path)
    out_dir = Path(args.out_dir).resolve() if args.out_dir else input_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    ids = [row.get("primitive_id") for row in rows]
    dedupe = [row.get("dedupe_key") for row in rows]
    core_missing = Counter()
    source_missing = Counter()
    validation_failures: list[dict[str, Any]] = []

    for index, row in enumerate(rows, 1):
        for field in _missing(row, CORE_FIELDS):
            core_missing[field] += 1
        for field in _missing(row, SOURCE_BACKED_FIELDS):
            source_missing[field] += 1
        if row.get("candidate") is not True or row.get("serves_truth") is not False:
            validation_failures.append({"row": index, "primitive_id": row.get("primitive_id"), "failure": "candidate_boundary"})
        validation = row.get("validation") or {}
        if validation.get("snippet_compile_ok") is not True:
            validation_failures.append({"row": index, "primitive_id": row.get("primitive_id"), "failure": "snippet_compile_not_ok"})
        if not row.get("input_edge") or not row.get("output_edge"):
            validation_failures.append({"row": index, "primitive_id": row.get("primitive_id"), "failure": "missing_edge"})
        if not isinstance(row.get("effects"), list) or not row.get("effects"):
            validation_failures.append({"row": index, "primitive_id": row.get("primitive_id"), "failure": "missing_effects"})
        if not isinstance(row.get("proof_requirements"), list) or not row.get("proof_requirements"):
            validation_failures.append({"row": index, "primitive_id": row.get("primitive_id"), "failure": "missing_proof_requirements"})

    compatible_rows = [_compatible_record(row) for row in rows]
    compatible_missing = Counter()
    for record in compatible_rows:
        for field in _missing(record, CONSUMPTION_FIELDS):
            compatible_missing[field] += 1

    compatible_path = out_dir / "primitive_candidate_records_compatible.jsonl"
    compatible_path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in compatible_rows) + "\n", encoding="utf-8")

    pack_count, generated_pack_rows = _count_generated_md_rows(REPO)
    selected_surfaces = _selected_primitive_surface_counts(REPO)
    report = {
        "record_type": "implemented_primitive_compatibility_report",
        "created_at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "input_path": str(input_path.relative_to(REPO) if input_path.is_relative_to(REPO) else input_path),
        "compatible_export_path": str(compatible_path.relative_to(REPO) if compatible_path.is_relative_to(REPO) else compatible_path),
        "existing_reference_surfaces": {
            "generated_primitive_pack_count": pack_count,
            "generated_primitive_pack_rows_from_manifest": generated_pack_rows,
            "selected_primitive_jsonl_surface_count": selected_surfaces["selected_surface_count"],
            "selected_primitive_jsonl_surface_rows": selected_surfaces["selected_surface_rows"],
            "selected_primitive_jsonl_surface_counts": selected_surfaces["counts"],
            "repo_code_registry": ".agent/primitive-registry/primitive_candidate_records.jsonl",
            "source_backed_group_cards": "data/dev-intel/aidevobserver_edge_foundry/source_backed_primitive_group_cards.jsonl",
            "guardrail_primitives": "catalog/knowledge-packs/data/primitive-cloud-guardrail-runtime/guardrail_primitives.jsonl",
        },
        "rows_checked": len(rows),
        "unique_primitive_ids": len(set(ids)),
        "unique_dedupe_keys": len(set(dedupe)),
        "core_contract": {
            "required_fields": list(CORE_FIELDS),
            "missing_counts": dict(core_missing),
            "pass": not core_missing,
        },
        "source_backed_contract": {
            "required_fields": list(SOURCE_BACKED_FIELDS),
            "missing_counts": dict(source_missing),
            "pass": not source_missing,
        },
        "candidate_boundary": {
            "candidate_true": sum(1 for row in rows if row.get("candidate") is True),
            "serves_truth_false": sum(1 for row in rows if row.get("serves_truth") is False),
        },
        "validation": {
            "snippet_compile_pass": sum(1 for row in rows if (row.get("validation") or {}).get("snippet_compile_ok") is True),
            "failures": validation_failures[:100],
            "failure_count": len(validation_failures),
        },
        "compatible_consumption_export": {
            "required_fields": list(CONSUMPTION_FIELDS),
            "missing_counts": dict(compatible_missing),
            "pass": not compatible_missing,
            "rows_written": len(compatible_rows),
        },
        "field_notes": {
            "record_id": "Implemented records use primitive_id as canonical ID; compatible export maps primitive_id to id.",
            "source_ref": "Implemented records store source_path/source_span; compatible export maps those to source_ref and source_ref_structured.",
            "input_contract_output_contract": "Implemented records store input_edge/output_edge and edge_contract; compatible export maps these to input_contract/output_contract.",
            "call_surface": "Implemented records store runtime_targets/signature/source path; compatible export maps these to call_surface.",
        },
        "pass": (
            len(rows) > 0
            and len(set(ids)) == len(rows)
            and len(set(dedupe)) == len(rows)
            and not core_missing
            and not source_missing
            and not compatible_missing
            and not validation_failures
        ),
    }

    report_path = out_dir / "compatibility_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_path = out_dir / "compatibility_report.md"
    md_path.write_text(
        "\n".join(
            [
                "# Implemented Primitive Compatibility Report",
                "",
                f"- input: `{report['input_path']}`",
                f"- rows_checked: `{report['rows_checked']:,}`",
                f"- unique_primitive_ids: `{report['unique_primitive_ids']:,}`",
                f"- unique_dedupe_keys: `{report['unique_dedupe_keys']:,}`",
                f"- core_contract_pass: `{report['core_contract']['pass']}`",
                f"- source_backed_contract_pass: `{report['source_backed_contract']['pass']}`",
                f"- compatible_consumption_export_pass: `{report['compatible_consumption_export']['pass']}`",
                f"- snippet_compile_pass: `{report['validation']['snippet_compile_pass']:,}`",
                f"- validation_failure_count: `{report['validation']['failure_count']:,}`",
                f"- compatible_export: `{report['compatible_export_path']}`",
                "",
                "## Reference Surfaces",
                "",
                f"- generated primitive pack rows from manifest: `{generated_pack_rows:,}` across `{pack_count}` packs",
                f"- selected primitive JSONL surface rows: `{selected_surfaces['selected_surface_rows']:,}` across `{selected_surfaces['selected_surface_count']}` files",
                "- repo code registry: `.agent/primitive-registry/primitive_candidate_records.jsonl`",
                "- source-backed group cards: `data/dev-intel/aidevobserver_edge_foundry/source_backed_primitive_group_cards.jsonl`",
                "- guardrail primitive cards: `catalog/knowledge-packs/data/primitive-cloud-guardrail-runtime/guardrail_primitives.jsonl`",
                "",
                "## Result",
                "",
                f"- overall_pass: `{report['pass']}`",
                "",
                "The raw implemented-code records match the compact primitive-card contract used by the newer primitive packs. The compatibility export maps them into the older repo-code registry consumption envelope with `id`, `name`, `input_contract`, `output_contract`, `call_surface`, `composition`, `license_provenance`, `mutation_affordances`, `promotion_status`, `proof_command`, `tags`, and `version`.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--out-dir", default="")
    return parser.parse_args()


def main() -> int:
    report = run(parse_args())
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
