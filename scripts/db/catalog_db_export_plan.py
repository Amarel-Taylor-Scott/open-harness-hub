#!/usr/bin/env python3
"""Plan database-to-manifest row exports for the catalog bridge.

This is the first database read surface for catalog manifests. It emits psql
commands and a generated SQL file that exports loaded Postgres rows into the
same JSONL row shape consumed by `catalog_manifest_export_plan.py`.

The script is side-effect free except for writing the plan/SQL files. It does
not connect to Postgres and it does not read or overwrite live catalog YAML.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parent.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts._config import DEFAULT_DATABASE_URL_ENV
from scripts.db.catalog_row_integrity import ROW_FILES


DEFAULT_ROW_DIR = REPO / "dist" / "catalog-db-export-rows"
DEFAULT_SQL = DEFAULT_ROW_DIR / "export-catalog-db-rows.sql"
DEFAULT_PLAN = DEFAULT_ROW_DIR / "catalog-db-export-plan.json"
DEFAULT_INTEGRITY_REPORT = DEFAULT_ROW_DIR / "catalog-row-integrity-report.json"


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _copy_statement(query: str, output_path: Path) -> str:
    one_line_query = " ".join(query.split())
    copy_options = "WITH (FORMAT csv, DELIMITER E'\\x02', QUOTE E'\\x01')"
    return f"\\copy ({one_line_query}) TO '{output_path}' {copy_options}\n"


def _export_sql(row_dir: Path) -> str:
    files = {name: row_dir / filename for name, filename in ROW_FILES.items()}
    component_query = """
SELECT jsonb_build_object(
  'id', c.id,
  'type', c.type,
  'component_layer', c.component_layer,
  'control_flow_kind', c.control_flow_kind,
  'version', c.version,
  'name', c.name,
  'description', c.description,
  'license', c.license,
  'lifecycle', c.lifecycle,
  'trust_boundary', c.trust_boundary,
  'freshness', c.freshness,
  'created', c.created,
  'updated', c.updated,
  'superseded_by', c.superseded_by,
  'deprecated_on', c.deprecated_on,
  'attribution', c.attribution,
  'links', c.links,
  'body', c.body,
  'seed', jsonb_build_object(
    'path', cv.source_ref,
    'definition_source', cv.definition_source,
    'definition_hash', cv.definition_hash
  )
)::text
FROM component c
LEFT JOIN LATERAL (
  SELECT source_ref, definition_source, definition_hash
  FROM component_version
  WHERE component_id = c.id
  ORDER BY activated_at DESC NULLS LAST, component_version_id DESC
  LIMIT 1
) cv ON true
ORDER BY c.id
""".strip()
    component_version_query = """
SELECT jsonb_build_object(
  'component_version_id', component_version_id,
  'component_id', component_id,
  'version', version,
  'version_status', version_status,
  'change_summary', change_summary,
  'definition_source', definition_source,
  'source_ref', source_ref,
  'definition_hash', definition_hash,
  'body', body
)::text
FROM component_version
ORDER BY component_id, version
""".strip()
    axis_queries = {
        "component_industries": "SELECT jsonb_build_object('component_id', component_id, 'industry', industry)::text FROM component_industry ORDER BY component_id, industry",
        "component_capabilities": "SELECT jsonb_build_object('component_id', component_id, 'capability', capability)::text FROM component_capability ORDER BY component_id, capability",
        "component_modalities": "SELECT jsonb_build_object('component_id', component_id, 'modality', modality)::text FROM component_modality ORDER BY component_id, modality",
        "component_tags": "SELECT jsonb_build_object('component_id', component_id, 'tag', tag)::text FROM component_tag ORDER BY component_id, tag",
    }
    refs_query = """
SELECT jsonb_build_object('src_id', src_id, 'dst_id', dst_id, 'role', role)::text
FROM component_ref
ORDER BY src_id, role, dst_id
""".strip()
    rubric_query = """
SELECT jsonb_build_object(
  'rubric_dimension_id', rubric_dimension_id,
  'rubric_id', rubric_id,
  'dimension_path', dimension_path,
  'parent_path', parent_path,
  'dimension_level', dimension_level,
  'label', label,
  'weight', weight,
  'scale', scale,
  'evidence_required', evidence_required,
  'gate', gate,
  'body', body
)::text
FROM rubric_dimension
ORDER BY rubric_id, dimension_level, dimension_path
""".strip()
    context_object_query = """
SELECT jsonb_build_object(
  'context_object_id', context_object_id,
  'tenant_id', tenant_id,
  'object_type', object_type,
  'subkind', subkind,
  'title', title,
  'summary', summary,
  'source_system', source_system,
  'native_id', native_id,
  'source_url', source_url,
  'classification', classification,
  'source_handles', source_handles,
  'facets', facets,
  'document', document
)::text
FROM context_object
WHERE source_system = 'repo_catalog'
ORDER BY context_object_id
""".strip()
    component_context_query = """
SELECT jsonb_build_object(
  'component_id', component_id,
  'context_object_id', context_object_id,
  'role', role,
  'binding_status', binding_status,
  'source_ref', source_ref,
  'binding_hash', binding_hash,
  'body', body
)::text
FROM component_context_object
ORDER BY component_id, role, context_object_id
""".strip()
    context_mask_contract_query = """
SELECT jsonb_build_object(
  'mask_contract_id', mask_contract_id,
  'context_object_id', context_object_id,
  'component_id', component_id,
  'mask_kind', mask_kind,
  'target_types', target_types,
  'include_paths', include_paths,
  'exclude_paths', exclude_paths,
  'redact_paths', redact_paths,
  'policy_trigger', policy_trigger,
  'redaction_reason', redaction_reason,
  'reversible', reversible,
  'contract', contract
)::text
FROM context_mask_contract
ORDER BY component_id, context_object_id, mask_contract_id
""".strip()
    context_transformer_contract_query = """
SELECT jsonb_build_object(
  'transformer_contract_id', transformer_contract_id,
  'context_object_id', context_object_id,
  'component_id', component_id,
  'transformer_kind', transformer_kind,
  'input_contract', input_contract,
  'output_contract', output_contract,
  'deterministic', deterministic,
  'model_required', model_required,
  'lossiness', lossiness,
  'reversible', reversible,
  'validation', validation,
  'lineage_policy', lineage_policy,
  'contract', contract
)::text
FROM context_transformer_contract
ORDER BY component_id, context_object_id, transformer_contract_id
""".strip()
    batch_query = """
SELECT jsonb_build_object(
  'manifest_import_batch_id', manifest_import_batch_id,
  'source_kind', source_kind,
  'source_ref', source_ref,
  'importer', importer,
  'import_mode', import_mode,
  'policy', policy,
  'summary', summary
)::text
FROM manifest_import_batch
ORDER BY created_at DESC, manifest_import_batch_id
""".strip()
    record_query = """
SELECT jsonb_build_object(
  'manifest_import_record_id', manifest_import_record_id,
  'manifest_import_batch_id', manifest_import_batch_id,
  'component_id', component_id,
  'component_type', component_type,
  'manifest_path', manifest_path,
  'manifest_hash', manifest_hash,
  'manifest_updated', manifest_updated,
  'manifest_lifecycle', manifest_lifecycle,
  'manifest_freshness', manifest_freshness,
  'definition_source', definition_source,
  'import_status', import_status,
  'recommended_action', recommended_action,
  'rotted_context_flags', rotted_context_flags,
  'row_counts', row_counts,
  'source_ref', source_ref,
  'error_message', error_message
)::text
FROM manifest_import_record
ORDER BY manifest_path
""".strip()
    parts = [
        "-- Generated by scripts/db/catalog_db_export_plan.py.",
        "-- Create the output directory before running this file with psql.",
        "\\pset tuples_only on",
        "\\pset format unaligned",
        _copy_statement(component_query, files["components"]),
        _copy_statement(component_version_query, files["component_versions"]),
    ]
    for name, query in axis_queries.items():
        parts.append(_copy_statement(query, files[name]))
    parts.extend([
        _copy_statement(refs_query, files["component_refs"]),
        _copy_statement(rubric_query, files["rubric_dimensions"]),
        _copy_statement(context_object_query, files["context_objects"]),
        _copy_statement(component_context_query, files["component_context_objects"]),
        _copy_statement(context_mask_contract_query, files["context_mask_contracts"]),
        _copy_statement(context_transformer_contract_query, files["context_transformer_contracts"]),
        _copy_statement(batch_query, files["manifest_import_batches"]),
        _copy_statement(record_query, files["manifest_import_records"]),
    ])
    return "\n".join(parts) + "\n"


def _export_sql_coverage(sql: str, row_dir: Path) -> dict[str, Any]:
    """Report whether every registered row family is emitted by export SQL."""
    row_families: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    copy_count = sql.count("\\copy")
    if copy_count != len(ROW_FILES):
        issues.append({
            "severity": "error",
            "code": "copy_statement_count_mismatch",
            "expected": len(ROW_FILES),
            "actual": copy_count,
        })

    for row_family, filename in sorted(ROW_FILES.items()):
        output_path = row_dir / filename
        file_referenced = filename in sql
        path_referenced = str(output_path) in sql
        entry = {
            "row_family": row_family,
            "file": filename,
            "output_path": str(output_path),
            "file_referenced": file_referenced,
            "path_referenced": path_referenced,
        }
        row_families.append(entry)
        if not file_referenced:
            issues.append({
                "severity": "error",
                "code": "export_sql_missing_file_reference",
                "row_family": row_family,
                "file": filename,
            })
        if not path_referenced:
            issues.append({
                "severity": "error",
                "code": "export_sql_missing_output_path_reference",
                "row_family": row_family,
                "output_path": str(output_path),
            })

    return {
        "ok": not any(issue["severity"] == "error" for issue in issues),
        "copy_statement_count": copy_count,
        "expected_row_family_count": len(ROW_FILES),
        "row_families": row_families,
        "issues": issues,
    }


def build_catalog_db_export_plan(
    *,
    row_dir: Path = DEFAULT_ROW_DIR,
    sql_output: Path = DEFAULT_SQL,
    output: Path = DEFAULT_PLAN,
    integrity_report: Path | None = None,
    database_url_env: str = DEFAULT_DATABASE_URL_ENV,
) -> dict[str, Any]:
    row_dir.mkdir(parents=True, exist_ok=True)
    sql_output.parent.mkdir(parents=True, exist_ok=True)
    sql = _export_sql(row_dir)
    sql_output.write_text(sql, encoding="utf-8")
    integrity_report = integrity_report or row_dir / DEFAULT_INTEGRITY_REPORT.name
    rows = {name: str(row_dir / filename) for name, filename in ROW_FILES.items()}
    export_sql_coverage = _export_sql_coverage(sql, row_dir)
    plan = {
        "ok": export_sql_coverage["ok"],
        "generated_at": _utc_now(),
        "row_dir": str(row_dir),
        "sql_output": str(sql_output),
        "integrity_report": str(integrity_report),
        "database_url_env": database_url_env,
        "rows": rows,
        "row_family_count": len(ROW_FILES),
        "export_sql_coverage": export_sql_coverage,
        "commands": [
            {"step": "create_row_dir", "command": f"mkdir -p {row_dir}"},
            {"step": "export_database_rows", "command": f'psql "${database_url_env}" -f {sql_output}'},
            {
                "step": "validate_exported_row_integrity",
                "command": (
                    "python3 scripts/db/catalog_row_integrity.py "
                    f"--row-dir {row_dir} --output {integrity_report}"
                ),
            },
            {
                "step": "export_manifests_from_database_rows",
                "command": (
                    "python3 scripts/db/catalog_manifest_export_plan.py "
                    f"--row-dir {row_dir} --output-dir dist/catalog-db-manifest-export"
                ),
            },
        ],
        "safety_notes": [
            "This planner does not connect to Postgres.",
            "The generated SQL reads database rows and writes JSONL row sets.",
            "Run validate_exported_row_integrity before downstream row-backed consumers or manifest export.",
            "The generated manifest export should be written outside catalog/ for review.",
        ],
    }
    _write_json(output, plan)
    return plan


def _self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="ohh-catalog-db-export-") as tmp:
        row_dir = Path(tmp) / "rows"
        sql_output = Path(tmp) / "export.sql"
        output = Path(tmp) / "plan.json"
        plan = build_catalog_db_export_plan(row_dir=row_dir, sql_output=sql_output, output=output)
        sql = sql_output.read_text(encoding="utf-8")
        assert output.exists()
        assert sql.count("\\copy") == len(ROW_FILES)
        assert "FROM component c" in sql
        assert "FROM manifest_import_record" in sql
        assert plan["ok"]
        assert plan["row_family_count"] == len(ROW_FILES)
        assert plan["export_sql_coverage"]["copy_statement_count"] == len(ROW_FILES)
        assert not plan["export_sql_coverage"]["issues"]
        assert plan["rows"]["components"].endswith("components.jsonl")
        assert plan["integrity_report"].endswith("catalog-row-integrity-report.json")
        assert any(command["step"] == "validate_exported_row_integrity" for command in plan["commands"])
    print(json.dumps({"ok": True, "self_test": "catalog_db_export_plan"}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan database row exports for catalog manifests.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--row-dir", type=Path, default=DEFAULT_ROW_DIR)
    parser.add_argument("--sql-output", type=Path, default=DEFAULT_SQL)
    parser.add_argument("--output", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--integrity-report", type=Path)
    parser.add_argument("--database-url-env", default=DEFAULT_DATABASE_URL_ENV)
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    plan = build_catalog_db_export_plan(
        row_dir=args.row_dir,
        sql_output=args.sql_output,
        output=args.output,
        integrity_report=args.integrity_report,
        database_url_env=args.database_url_env,
    )
    print(json.dumps(plan, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
