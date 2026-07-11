#!/usr/bin/env python3
"""Export primitive-registry operational JSONL rows as CSV plus a psql load script.

The primitive builder remains the evidence producer. This script is the reviewable
database handoff: it reads `.agent/primitive-registry/operational/*.jsonl`, writes
table-shaped CSV files, and emits an idempotent Postgres upsert script. It does
not connect to Postgres or mutate a database.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import csv
import json
import tempfile
import time
from pathlib import Path
from typing import Any


py_const_scripts_db_primitive_registry_operational_load_plan__REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2])
import sys

if str(py_const_scripts_db_primitive_registry_operational_load_plan__REPO) not in sys.path:
    sys.path.insert(0, str(py_const_scripts_db_primitive_registry_operational_load_plan__REPO))

from scripts import primitive_registry_builder
from scripts._config import PRIMITIVE_QUALITY_ARTIFACT_FILES, PRIMITIVE_QUALITY_DIRNAME


py_const_scripts_db_primitive_registry_operational_load_plan__DEFAULT_REGISTRY_OUT = (py_const_scripts_db_primitive_registry_operational_load_plan__REPO / ".agent") / "primitive-registry"
py_const_scripts_db_primitive_registry_operational_load_plan__DEFAULT_OUT = _resource("dist") / "primitive-registry-operational-load"
py_const_scripts_db_primitive_registry_operational_load_plan__RUN_ID = "primitive-registry-operational-load"
py_const_scripts_db_primitive_registry_operational_load_plan__COPY_ORDER = (
    "mutator_agent",
    "registry_source",
    "registry_record",
    "primitive_edge",
    "primitive_effect",
    "registry_embedding",
    "primitive_blocking_profile",
    "primitive_blocking_key",
    "primitive_mutation_option",
    "primitive_quality_assessment",
    "registry_source_link",
)
py_const_scripts_db_primitive_registry_operational_load_plan__TABLE_COLUMNS = {
    "registry_record": (
        "registry_record_id", "tenant_id", "kind", "slug", "version", "status",
        "trust_status", "readiness_level", "serves_truth", "title",
        "blackbox_description", "canonical_json", "record_hash", "source_license",
        "privacy_boundary",
    ),
    "primitive_edge": (
        "primitive_edge_id", "registry_record_id", "edge_role", "edge_name",
        "contract_uid", "contract_notation", "shape", "field_keys", "schema_json",
        "artifact_policy", "secret_policy", "edge_hash",
    ),
    "primitive_effect": (
        "primitive_effect_id", "registry_record_id", "effect_kind", "effect_scope",
        "requires_gate", "requires_receipt", "idempotency_required",
    ),
    "registry_embedding": (
        "registry_embedding_id", "registry_record_id", "object_embedding_id",
        "view_profile", "embedding_model_id", "text_hash", "embedded_text",
        "embedding", "metadata",
    ),
    "primitive_blocking_profile": (
        "blocking_profile_id", "registry_record_id", "exact_keys", "keyword_keys",
        "label_keys", "input_signature", "output_signature", "graph_signature",
        "semantic_text_hash", "semantic_bucket_keys", "mutation_hints",
        "profile_hash", "serves_truth",
    ),
    "primitive_blocking_key": (
        "blocking_key_id", "tenant_id", "registry_record_id", "lane", "key",
        "weight", "profile_hash",
    ),
    "mutator_agent": (
        "mutator_agent_id", "tenant_id", "kind", "short_code", "name",
        "from_shape", "to_shape", "preconditions", "effect_delta", "memory_delta",
        "cache_delta", "runtime_delta", "proof_obligations", "auto_apply_policy",
        "implementation_ref", "serves_truth",
    ),
    "primitive_mutation_option": (
        "mutation_option_id", "registry_record_id", "mutator_agent_id",
        "from_edge_id", "target_edge_template", "fit_class", "precondition_status",
        "confidence", "reason", "serves_truth",
    ),
    "primitive_quality_assessment": (
        "primitive_quality_assessment_id", "registry_record_id", "assessor_id",
        "quality_score", "quality_class", "surfaceable", "readiness_before",
        "readiness_after", "trust_before", "trust_after", "domains", "signals",
        "blockers", "enriched_input_contract", "enriched_output_contract",
        "mutation_options", "recommended_action", "assessment_hash",
        "serves_truth",
    ),
    "registry_source": (
        "registry_source_id", "source_kind", "source_uri", "archive_uri",
        "publisher", "license", "content_hash", "privacy_boundary",
        "republish_policy", "metadata",
    ),
    "registry_source_link": (
        "registry_record_id", "registry_source_id", "role", "evidence_span",
        "license_status",
    ),
}
py_const_scripts_db_primitive_registry_operational_load_plan__JSON_COLUMNS = {
    "canonical_json", "schema_json", "artifact_policy", "secret_policy",
    "effect_scope", "metadata", "input_signature", "output_signature",
    "target_edge_template", "republish_policy", "evidence_span",
    "preconditions", "effect_delta", "memory_delta", "cache_delta",
    "runtime_delta", "proof_obligations", "implementation_ref",
    "enriched_input_contract", "enriched_output_contract",
}
py_const_scripts_db_primitive_registry_operational_load_plan__JSON_ARRAY_COLUMNS = {
    "field_keys", "exact_keys", "keyword_keys", "label_keys", "graph_signature",
    "semantic_bucket_keys", "mutation_hints", "preconditions", "proof_obligations",
    "domains", "signals", "blockers", "mutation_options",
}
py_const_scripts_db_primitive_registry_operational_load_plan__TEXT_ARRAY_COLUMNS = {
}
py_const_scripts_db_primitive_registry_operational_load_plan__BOOLEAN_COLUMNS = {
    "serves_truth", "requires_gate", "requires_receipt", "idempotency_required",
    "surfaceable",
}
py_const_scripts_db_primitive_registry_operational_load_plan__FLOAT_COLUMNS = {
    "weight", "confidence", "quality_score",
}
py_const_scripts_db_primitive_registry_operational_load_plan__VECTOR_COLUMNS = {
    "embedding",
}
py_const_scripts_db_primitive_registry_operational_load_plan__CONFLICT_TARGETS = {
    "registry_record": "registry_record_id",
    "primitive_edge": "primitive_edge_id",
    "primitive_effect": "primitive_effect_id",
    "registry_embedding": "registry_embedding_id",
    "primitive_blocking_profile": "blocking_profile_id",
    "primitive_blocking_key": "blocking_key_id",
    "mutator_agent": "mutator_agent_id",
    "primitive_mutation_option": "mutation_option_id",
    "primitive_quality_assessment": "primitive_quality_assessment_id",
    "registry_source": "registry_source_id",
    "registry_source_link": "registry_record_id, registry_source_id, role",
}


def py_function_scripts_db_primitive_registry_operational_load_plan__utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def py_function_scripts_db_primitive_registry_operational_load_plan__read_jsonl(py_arg_scripts_db_primitive_registry_operational_load_plan__read_jsonl__path: Path) -> list[dict[str, Any]]:
    py_local_scripts_db_primitive_registry_operational_load_plan__read_jsonl__rows: list[dict[str, Any]] = []
    if not py_arg_scripts_db_primitive_registry_operational_load_plan__read_jsonl__path.exists():
        return py_local_scripts_db_primitive_registry_operational_load_plan__read_jsonl__rows
    for py_local_scripts_db_primitive_registry_operational_load_plan__read_jsonl__line_no, py_local_scripts_db_primitive_registry_operational_load_plan__read_jsonl__line in enumerate(py_arg_scripts_db_primitive_registry_operational_load_plan__read_jsonl__path.read_text(encoding="utf-8").splitlines(), 1):
        if not py_local_scripts_db_primitive_registry_operational_load_plan__read_jsonl__line.strip():
            continue
        py_local_scripts_db_primitive_registry_operational_load_plan__read_jsonl__value = json.loads(py_local_scripts_db_primitive_registry_operational_load_plan__read_jsonl__line)
        if not isinstance(py_local_scripts_db_primitive_registry_operational_load_plan__read_jsonl__value, dict):
            raise ValueError(f"{py_arg_scripts_db_primitive_registry_operational_load_plan__read_jsonl__path}:{py_local_scripts_db_primitive_registry_operational_load_plan__read_jsonl__line_no}: expected JSON object")
        py_local_scripts_db_primitive_registry_operational_load_plan__read_jsonl__rows.append(py_local_scripts_db_primitive_registry_operational_load_plan__read_jsonl__value)
    return py_local_scripts_db_primitive_registry_operational_load_plan__read_jsonl__rows


def py_function_scripts_db_primitive_registry_operational_load_plan__cell(py_arg_scripts_db_primitive_registry_operational_load_plan__cell__value: Any) -> str:
    if py_arg_scripts_db_primitive_registry_operational_load_plan__cell__value is None:
        return ""
    if isinstance(py_arg_scripts_db_primitive_registry_operational_load_plan__cell__value, (dict, list)):
        return json.dumps(py_arg_scripts_db_primitive_registry_operational_load_plan__cell__value, sort_keys=True, ensure_ascii=False)
    if isinstance(py_arg_scripts_db_primitive_registry_operational_load_plan__cell__value, bool):
        return "true" if py_arg_scripts_db_primitive_registry_operational_load_plan__cell__value else "false"
    return str(py_arg_scripts_db_primitive_registry_operational_load_plan__cell__value)


def py_function_scripts_db_primitive_registry_operational_load_plan__write_csv(py_arg_scripts_db_primitive_registry_operational_load_plan__write_csv__path: Path, py_arg_scripts_db_primitive_registry_operational_load_plan__write_csv__columns: tuple[str, ...], py_arg_scripts_db_primitive_registry_operational_load_plan__write_csv__rows: list[dict[str, Any]]) -> None:
    py_arg_scripts_db_primitive_registry_operational_load_plan__write_csv__path.parent.mkdir(parents=True, exist_ok=True)
    with py_arg_scripts_db_primitive_registry_operational_load_plan__write_csv__path.open("w", newline="", encoding="utf-8") as py_local_scripts_db_primitive_registry_operational_load_plan__write_csv__handle:
        py_local_scripts_db_primitive_registry_operational_load_plan__write_csv__writer = csv.DictWriter(py_local_scripts_db_primitive_registry_operational_load_plan__write_csv__handle, fieldnames=py_arg_scripts_db_primitive_registry_operational_load_plan__write_csv__columns, extrasaction="ignore")
        py_local_scripts_db_primitive_registry_operational_load_plan__write_csv__writer.writeheader()
        for py_local_scripts_db_primitive_registry_operational_load_plan__write_csv__row in py_arg_scripts_db_primitive_registry_operational_load_plan__write_csv__rows:
            py_local_scripts_db_primitive_registry_operational_load_plan__write_csv__writer.writerow({
                py_local_scripts_db_primitive_registry_operational_load_plan__write_csv__column: py_function_scripts_db_primitive_registry_operational_load_plan__cell(py_local_scripts_db_primitive_registry_operational_load_plan__write_csv__row.get(py_local_scripts_db_primitive_registry_operational_load_plan__write_csv__column))
                for py_local_scripts_db_primitive_registry_operational_load_plan__write_csv__column in py_arg_scripts_db_primitive_registry_operational_load_plan__write_csv__columns
            })


def py_function_scripts_db_primitive_registry_operational_load_plan__sql_literal(py_arg_scripts_db_primitive_registry_operational_load_plan__sql_literal__value: str) -> str:
    return "'" + py_arg_scripts_db_primitive_registry_operational_load_plan__sql_literal__value.replace("'", "''") + "'"


def py_function_scripts_db_primitive_registry_operational_load_plan__select_expr(py_arg_scripts_db_primitive_registry_operational_load_plan__select_expr__column: str) -> str:
    py_local_scripts_db_primitive_registry_operational_load_plan__select_expr__source = f"s.{py_arg_scripts_db_primitive_registry_operational_load_plan__select_expr__column}"
    if py_arg_scripts_db_primitive_registry_operational_load_plan__select_expr__column in py_const_scripts_db_primitive_registry_operational_load_plan__JSON_ARRAY_COLUMNS:
        return f"COALESCE(NULLIF({py_local_scripts_db_primitive_registry_operational_load_plan__select_expr__source}, '')::jsonb, '[]'::jsonb)"
    if py_arg_scripts_db_primitive_registry_operational_load_plan__select_expr__column in py_const_scripts_db_primitive_registry_operational_load_plan__JSON_COLUMNS:
        return f"COALESCE(NULLIF({py_local_scripts_db_primitive_registry_operational_load_plan__select_expr__source}, '')::jsonb, '{{}}'::jsonb)"
    if py_arg_scripts_db_primitive_registry_operational_load_plan__select_expr__column in py_const_scripts_db_primitive_registry_operational_load_plan__TEXT_ARRAY_COLUMNS:
        return f"ARRAY(SELECT jsonb_array_elements_text(COALESCE(NULLIF({py_local_scripts_db_primitive_registry_operational_load_plan__select_expr__source}, '')::jsonb, '[]'::jsonb)))"
    if py_arg_scripts_db_primitive_registry_operational_load_plan__select_expr__column in py_const_scripts_db_primitive_registry_operational_load_plan__BOOLEAN_COLUMNS:
        return f"COALESCE(NULLIF({py_local_scripts_db_primitive_registry_operational_load_plan__select_expr__source}, '')::boolean, false)"
    if py_arg_scripts_db_primitive_registry_operational_load_plan__select_expr__column in py_const_scripts_db_primitive_registry_operational_load_plan__FLOAT_COLUMNS:
        return f"NULLIF({py_local_scripts_db_primitive_registry_operational_load_plan__select_expr__source}, '')::double precision"
    if py_arg_scripts_db_primitive_registry_operational_load_plan__select_expr__column in py_const_scripts_db_primitive_registry_operational_load_plan__VECTOR_COLUMNS:
        return f"NULLIF({py_local_scripts_db_primitive_registry_operational_load_plan__select_expr__source}, '')::vector"
    return f"NULLIF({py_local_scripts_db_primitive_registry_operational_load_plan__select_expr__source}, '')"


def py_function_scripts_db_primitive_registry_operational_load_plan__load_sql(py_arg_scripts_db_primitive_registry_operational_load_plan__load_sql__csv_paths: dict[str, Path]) -> str:
    py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__parts = [
        "-- Generated by scripts/db/primitive_registry_operational_load_plan.py",
        "-- Apply only after db/postgres/schema.sql has been loaded.",
        "BEGIN;",
    ]
    for py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__table in py_const_scripts_db_primitive_registry_operational_load_plan__COPY_ORDER:
        py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__columns = py_const_scripts_db_primitive_registry_operational_load_plan__TABLE_COLUMNS[py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__table]
        py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__stage = f"stage_{py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__table}"
        py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__csv = py_arg_scripts_db_primitive_registry_operational_load_plan__load_sql__csv_paths[py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__table]
        py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__updates = [
            f"{py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__column}=EXCLUDED.{py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__column}"
            for py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__column in py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__columns
            if py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__column not in {part.strip() for part in py_const_scripts_db_primitive_registry_operational_load_plan__CONFLICT_TARGETS[py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__table].split(",")}
        ]
        py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__parts.extend([
            "",
            f"CREATE TEMP TABLE {py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__stage} (",
            "  " + ",\n  ".join(f"{py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__column} text" for py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__column in py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__columns),
            ");",
            f"\\copy {py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__stage} FROM {py_function_scripts_db_primitive_registry_operational_load_plan__sql_literal(str(py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__csv))} WITH (FORMAT csv, HEADER true)",
            f"INSERT INTO {py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__table} ({', '.join(py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__columns)})",
            "SELECT",
            "  " + ",\n  ".join(py_function_scripts_db_primitive_registry_operational_load_plan__select_expr(py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__column) for py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__column in py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__columns),
            f"FROM {py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__stage} s",
            f"ON CONFLICT ({py_const_scripts_db_primitive_registry_operational_load_plan__CONFLICT_TARGETS[py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__table]}) DO UPDATE SET",
            "  " + ",\n  ".join(py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__updates) + ";",
        ])
    py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__parts.append("COMMIT;\n")
    return "\n".join(py_local_scripts_db_primitive_registry_operational_load_plan__load_sql__parts)


def py_function_scripts_db_primitive_registry_operational_load_plan__build(py_arg_scripts_db_primitive_registry_operational_load_plan__build__registry_out: Path, py_arg_scripts_db_primitive_registry_operational_load_plan__build__out_dir: Path) -> dict[str, Any]:
    py_local_scripts_db_primitive_registry_operational_load_plan__build__operational_dir = py_arg_scripts_db_primitive_registry_operational_load_plan__build__registry_out / "operational"
    py_local_scripts_db_primitive_registry_operational_load_plan__build__quality_dir = py_arg_scripts_db_primitive_registry_operational_load_plan__build__registry_out / PRIMITIVE_QUALITY_DIRNAME
    py_local_scripts_db_primitive_registry_operational_load_plan__build__csv_dir = py_arg_scripts_db_primitive_registry_operational_load_plan__build__out_dir / "csv"
    py_local_scripts_db_primitive_registry_operational_load_plan__build__csv_paths: dict[str, Path] = {}
    py_local_scripts_db_primitive_registry_operational_load_plan__build__counts: dict[str, int] = {}
    for py_local_scripts_db_primitive_registry_operational_load_plan__build__table in py_const_scripts_db_primitive_registry_operational_load_plan__COPY_ORDER:
        if py_local_scripts_db_primitive_registry_operational_load_plan__build__table == "primitive_quality_assessment":
            py_local_scripts_db_primitive_registry_operational_load_plan__build__jsonl = (
                py_local_scripts_db_primitive_registry_operational_load_plan__build__quality_dir
                / PRIMITIVE_QUALITY_ARTIFACT_FILES["assessments"]
            )
        else:
            py_local_scripts_db_primitive_registry_operational_load_plan__build__jsonl = py_local_scripts_db_primitive_registry_operational_load_plan__build__operational_dir / primitive_registry_builder.py_const_scripts_primitive_registry_builder__OPERATIONAL_ROW_FILES[py_local_scripts_db_primitive_registry_operational_load_plan__build__table]
        py_local_scripts_db_primitive_registry_operational_load_plan__build__rows = py_function_scripts_db_primitive_registry_operational_load_plan__read_jsonl(py_local_scripts_db_primitive_registry_operational_load_plan__build__jsonl)
        py_local_scripts_db_primitive_registry_operational_load_plan__build__csv = py_local_scripts_db_primitive_registry_operational_load_plan__build__csv_dir / f"{py_local_scripts_db_primitive_registry_operational_load_plan__build__table}.csv"
        py_function_scripts_db_primitive_registry_operational_load_plan__write_csv(py_local_scripts_db_primitive_registry_operational_load_plan__build__csv, py_const_scripts_db_primitive_registry_operational_load_plan__TABLE_COLUMNS[py_local_scripts_db_primitive_registry_operational_load_plan__build__table], py_local_scripts_db_primitive_registry_operational_load_plan__build__rows)
        py_local_scripts_db_primitive_registry_operational_load_plan__build__csv_paths[py_local_scripts_db_primitive_registry_operational_load_plan__build__table] = py_local_scripts_db_primitive_registry_operational_load_plan__build__csv
        py_local_scripts_db_primitive_registry_operational_load_plan__build__counts[py_local_scripts_db_primitive_registry_operational_load_plan__build__table] = len(py_local_scripts_db_primitive_registry_operational_load_plan__build__rows)
    py_local_scripts_db_primitive_registry_operational_load_plan__build__load_sql = py_arg_scripts_db_primitive_registry_operational_load_plan__build__out_dir / "load.sql"
    py_local_scripts_db_primitive_registry_operational_load_plan__build__load_sql.write_text(py_function_scripts_db_primitive_registry_operational_load_plan__load_sql(py_local_scripts_db_primitive_registry_operational_load_plan__build__csv_paths), encoding="utf-8")
    py_local_scripts_db_primitive_registry_operational_load_plan__build__manifest = {
        "created_at": py_function_scripts_db_primitive_registry_operational_load_plan__utc_now(),
        "run_id": py_const_scripts_db_primitive_registry_operational_load_plan__RUN_ID,
        "source_registry_out": str(py_arg_scripts_db_primitive_registry_operational_load_plan__build__registry_out),
        "load_sql": str(py_local_scripts_db_primitive_registry_operational_load_plan__build__load_sql),
        "csv_paths": {key: str(value) for key, value in sorted(py_local_scripts_db_primitive_registry_operational_load_plan__build__csv_paths.items())},
        "counts": py_local_scripts_db_primitive_registry_operational_load_plan__build__counts,
        "serves_truth": False,
        "execution_note": "Review and run load.sql with psql only against an intended Postgres/pgvector database.",
    }
    py_arg_scripts_db_primitive_registry_operational_load_plan__build__out_dir.mkdir(parents=True, exist_ok=True)
    (py_arg_scripts_db_primitive_registry_operational_load_plan__build__out_dir / "manifest.json").write_text(json.dumps(py_local_scripts_db_primitive_registry_operational_load_plan__build__manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return py_local_scripts_db_primitive_registry_operational_load_plan__build__manifest


def py_function_scripts_db_primitive_registry_operational_load_plan__self_test() -> int:
    with tempfile.TemporaryDirectory() as py_local_scripts_db_primitive_registry_operational_load_plan__self_test__tmp:
        py_local_scripts_db_primitive_registry_operational_load_plan__self_test__root = Path(py_local_scripts_db_primitive_registry_operational_load_plan__self_test__tmp)
        py_local_scripts_db_primitive_registry_operational_load_plan__self_test__inventory = primitive_registry_builder.py_function_scripts_primitive_registry_builder__write_fixture_inventory(py_local_scripts_db_primitive_registry_operational_load_plan__self_test__root)
        py_local_scripts_db_primitive_registry_operational_load_plan__self_test__registry_out = py_local_scripts_db_primitive_registry_operational_load_plan__self_test__root / "registry"
        primitive_registry_builder.py_function_scripts_primitive_registry_builder__build(py_local_scripts_db_primitive_registry_operational_load_plan__self_test__inventory, py_local_scripts_db_primitive_registry_operational_load_plan__self_test__registry_out, 100, True)
        py_local_scripts_db_primitive_registry_operational_load_plan__self_test__manifest = py_function_scripts_db_primitive_registry_operational_load_plan__build(py_local_scripts_db_primitive_registry_operational_load_plan__self_test__registry_out, py_local_scripts_db_primitive_registry_operational_load_plan__self_test__root / "load")
        py_local_scripts_db_primitive_registry_operational_load_plan__self_test__load_sql = Path(py_local_scripts_db_primitive_registry_operational_load_plan__self_test__manifest["load_sql"]).read_text(encoding="utf-8")
        assert "INSERT INTO registry_record" in py_local_scripts_db_primitive_registry_operational_load_plan__self_test__load_sql
        assert "INSERT INTO primitive_edge" in py_local_scripts_db_primitive_registry_operational_load_plan__self_test__load_sql
        assert "INSERT INTO primitive_mutation_option" in py_local_scripts_db_primitive_registry_operational_load_plan__self_test__load_sql
        assert py_local_scripts_db_primitive_registry_operational_load_plan__self_test__manifest["counts"]["registry_record"] > 0
        assert py_local_scripts_db_primitive_registry_operational_load_plan__self_test__manifest["serves_truth"] is False
        print(json.dumps(py_local_scripts_db_primitive_registry_operational_load_plan__self_test__manifest, indent=2, sort_keys=True))
    return 0


def main(py_arg_scripts_db_primitive_registry_operational_load_plan__main__argv: list[str] | None = None) -> int:
    py_local_scripts_db_primitive_registry_operational_load_plan__main__parser = argparse.ArgumentParser(description=__doc__)
    py_local_scripts_db_primitive_registry_operational_load_plan__main__parser.add_argument("--self-test", action="store_true")
    py_local_scripts_db_primitive_registry_operational_load_plan__main__parser.add_argument("--registry-out", default=str(py_const_scripts_db_primitive_registry_operational_load_plan__DEFAULT_REGISTRY_OUT))
    py_local_scripts_db_primitive_registry_operational_load_plan__main__parser.add_argument("--out", default=str(py_const_scripts_db_primitive_registry_operational_load_plan__DEFAULT_OUT))
    py_local_scripts_db_primitive_registry_operational_load_plan__main__args = py_local_scripts_db_primitive_registry_operational_load_plan__main__parser.parse_args(py_arg_scripts_db_primitive_registry_operational_load_plan__main__argv)
    if py_local_scripts_db_primitive_registry_operational_load_plan__main__args.self_test:
        return py_function_scripts_db_primitive_registry_operational_load_plan__self_test()
    py_local_scripts_db_primitive_registry_operational_load_plan__main__manifest = py_function_scripts_db_primitive_registry_operational_load_plan__build(Path(py_local_scripts_db_primitive_registry_operational_load_plan__main__args.registry_out), Path(py_local_scripts_db_primitive_registry_operational_load_plan__main__args.out))
    print(json.dumps(py_local_scripts_db_primitive_registry_operational_load_plan__main__manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
