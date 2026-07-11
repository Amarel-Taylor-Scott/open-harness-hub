#!/usr/bin/env python3
"""Run the dry-run catalog database migration checklist.

This script does not connect to Postgres, start Docker, or move catalog files.
It verifies the seed/export side of the database-backed catalog flow:

1. YAML seed manifests can be mapped into database-shaped rows.
2. The migration gate passes with explicit current allowances.
3. Row integrity passes for bridge rows.
4. The Postgres load execution plan is ready and points to DB export planning.
5. The database export plan includes row integrity validation.
6. The catalog operational dashboard views are declared in canonical schema.
7. Existing database-exported smoke rows, when present, pass integrity.
8. Row-backed consumers can search, render docs, and build SQLite snapshots.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
from collections.abc import Callable
import json
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parent.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.build_catalog_db import main as build_catalog_db_main
from scripts.build_catalog_index import main as build_catalog_index_main
from scripts.build_catalog_pages import main as build_catalog_pages_main
from scripts.db.build_vector_index import main as build_vector_index_main
from scripts.db.build_vector_store import build as build_vector_store
from scripts.db.catalog_db_export_plan import build_catalog_db_export_plan
from scripts.db.catalog_db_export_smoke_refresh_plan import build_refresh_plan as build_db_export_refresh_plan
from scripts.db.catalog_db_export_staleness_gate import build_staleness_gate_report
from scripts.db.catalog_database_promotion_readiness import build_promotion_readiness_report
from scripts.db.catalog_manifest_bridge import build_bridge_plan
from scripts.db.catalog_manifest_export_plan import build_export_plan as build_manifest_export_plan
from scripts.db.catalog_manifest_migration_gate import build_migration_gate_report
from scripts.db.catalog_operational_view_probe import probe_catalog_operational_views
from scripts.db.catalog_row_integrity import build_integrity_report
from scripts.db.catalog_row_schema_coverage import build_schema_coverage_report
from scripts.db.catalog_row_source_compare import compare_row_sources
from scripts.db.catalog_yaml_reader_audit import audit_paths, default_paths
from scripts.db.postgres_load_execution_plan import build_postgres_load_execution_plan
from scripts.emit._lib import load_catalog as load_emit_catalog
from scripts.factory.capability_gap_scout import existing_pack_summary
from scripts.factory.capability_lift_gate import run_gate as run_capability_lift_gate
from scripts.factory.processor_loader import list_processors, resolve_callable
from scripts.foundry.standardize import sample_manifest_for_schema_validation, schema_valid
from scripts.oh_hub import load_catalog as load_oh_hub_catalog
from scripts.processors.catalog_search import run as catalog_search_run
from scripts.run_pipeline import load_catalog as load_pipeline_catalog
from scripts.run_pipeline import run_pipeline


DEFAULT_BRIDGE_DIR = _resource("dist") / "catalog-manifest-bridge"
DEFAULT_DB_ROW_DIR = _resource("dist") / "catalog-db-export-rows-smoke"
DEFAULT_OUTPUT = _resource("dist") / "catalog-migration-smoke" / "catalog-database-migration-smoke.json"
DEFAULT_MANIFEST_EXPORT_DIR = _resource("dist") / "catalog-migration-smoke" / "manifest-export-from-seed-rows"
DEFAULT_PAGES_DIR = _resource("dist") / "catalog-migration-smoke" / "pages-from-db-rows"
DEFAULT_SQLITE = _resource("dist") / "catalog-migration-smoke" / "catalog-from-db-rows.sqlite"
DEFAULT_BROWSER_INDEX = _resource("dist") / "catalog-migration-smoke" / "index-from-db-rows.json"
DEFAULT_VECTOR_INDEX_DIR = _resource("dist") / "catalog-migration-smoke" / "vector-index-from-db-rows"
DEFAULT_VECTOR_STORE = _resource("dist") / "catalog-migration-smoke" / "vector-store-from-db-rows.sqlite"


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def step(name: str, fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    started = time.time()
    try:
        details = fn()
        ok = bool(details.pop("ok", True))
        status = "passed" if ok else "failed"
        return {
            "name": name,
            "status": status,
            "ok": ok,
            "duration_ms": int((time.time() - started) * 1000),
            "details": details,
        }
    except Exception as exc:
        return {
            "name": name,
            "status": "failed",
            "ok": False,
            "duration_ms": int((time.time() - started) * 1000),
            "details": {
                "error": type(exc).__name__,
                "message": str(exc),
            },
        }


def sqlite_counts(path: Path) -> dict[str, int]:
    conn = sqlite3.connect(path)
    try:
        return {
            "components": int(conn.execute("select count(*) from components").fetchone()[0]),
            "components_fts": int(conn.execute("select count(*) from components_fts").fetchone()[0]),
            "edges": int(conn.execute("select count(*) from edges").fetchone()[0]),
            "catalog_snapshot_metadata": int(conn.execute("select count(*) from catalog_snapshot_metadata").fetchone()[0]),
        }
    finally:
        conn.close()


def build_smoke_report(
    *,
    bridge_dir: Path = DEFAULT_BRIDGE_DIR,
    db_row_dir: Path = DEFAULT_DB_ROW_DIR,
    output: Path = DEFAULT_OUTPUT,
    manifest_export_dir: Path = DEFAULT_MANIFEST_EXPORT_DIR,
    pages_dir: Path = DEFAULT_PAGES_DIR,
    sqlite_output: Path = DEFAULT_SQLITE,
    browser_index_output: Path = DEFAULT_BROWSER_INDEX,
    vector_index_dir: Path = DEFAULT_VECTOR_INDEX_DIR,
    vector_store_output: Path = DEFAULT_VECTOR_STORE,
    allow_hold_count: int = 4,
    allow_review_count: int = 743,
    allow_archive_seed_count: int = 0,
) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []

    steps.append(step("build_manifest_bridge_rows", lambda: {
        **build_bridge_plan(output_dir=bridge_dir),
        "ok": True,
    }))

    steps.append(step("audit_direct_catalog_yaml_readers", lambda: {
        **audit_paths(default_paths()),
    }))

    steps.append(step("run_manifest_migration_gate", lambda: {
        **build_migration_gate_report(
            row_dir=bridge_dir,
            output=bridge_dir / "migration-gate-report.json",
            allow_hold_count=allow_hold_count,
            allow_review_count=allow_review_count,
            allow_archive_seed_count=allow_archive_seed_count,
        ),
    }))

    steps.append(step("validate_bridge_row_integrity", lambda: {
        **build_integrity_report(
            row_dir=bridge_dir,
            output=bridge_dir / "catalog-row-integrity-report.json",
        ),
    }))

    steps.append(step("validate_bridge_row_schema_coverage", lambda: {
        **build_schema_coverage_report(
            row_dir=bridge_dir,
            output=bridge_dir / "catalog-row-schema-coverage.json",
        ),
    }))

    steps.append(step("export_manifest_review_artifacts_from_seed_rows", lambda: {
        **build_manifest_export_plan(
            row_dir=bridge_dir,
            output_dir=manifest_export_dir,
        ),
    }))

    steps.append(step("probe_catalog_operational_views_schema", lambda: {
        **probe_catalog_operational_views(),
    }))

    steps.append(step("plan_postgres_load_execution", lambda: {
        **build_postgres_load_execution_plan(
            load_plan_manifest=bridge_dir / "manifest-import-plan.json",
            migration_gate_report=bridge_dir / "migration-gate-report.json",
            output=bridge_dir / "postgres-load-execution-plan.json",
        ),
    }))

    steps.append(step("plan_database_row_export", lambda: {
        **build_catalog_db_export_plan(
            row_dir=db_row_dir,
            sql_output=db_row_dir / "export-catalog-db-rows.sql",
            output=db_row_dir / "catalog-db-export-plan.json",
            integrity_report=db_row_dir / "catalog-row-integrity-report.json",
        ),
    }))

    if db_row_dir.exists():
        steps.append(step("validate_database_export_row_integrity", lambda: {
            **build_integrity_report(
                row_dir=db_row_dir,
                output=db_row_dir / "catalog-row-integrity-report.json",
            ),
        }))
        steps.append(step("compare_seed_and_database_row_search", lambda: {
            **compare_row_sources(
                seed_row_dir=bridge_dir,
                db_row_dir=db_row_dir,
                output=db_row_dir / "catalog-row-source-compare.json",
            ),
        }))
        steps.append(step("plan_database_export_smoke_refresh", lambda: {
            **build_db_export_refresh_plan(
                bridge_dir=bridge_dir,
                db_row_dir=db_row_dir,
                output=output.parent / "catalog-db-export-smoke-refresh-plan.json",
                parity_report_path=output.parent / "catalog-row-roundtrip-parity.json",
            ),
        }))
        steps.append(step("gate_database_export_snapshot_freshness_advisory", lambda: {
            **build_staleness_gate_report(
                seed_row_dir=bridge_dir,
                db_row_dir=db_row_dir,
                parity_report_path=output.parent / "catalog-row-roundtrip-parity.json",
                output=output.parent / "catalog-db-export-staleness-gate.json",
                advisory=True,
            ),
        }))
        steps.append(step("summarize_database_promotion_readiness_advisory", lambda: {
            **build_promotion_readiness_report(
                bridge_dir=bridge_dir,
                db_row_dir=db_row_dir,
                smoke_dir=output.parent,
                output=output.parent / "catalog-database-promotion-readiness.json",
                advisory=True,
            ),
        }))
        steps.append(step("search_database_rows", lambda: {
            "ok": True,
            "result": catalog_search_run(
                "governance rubrics for context objects and fragile information",
                top_k=3,
                row_dir=db_row_dir,
            ),
        }))
        steps.append(step("render_database_row_pages", lambda: {
            "ok": build_catalog_pages_main([
                "--row-dir", str(db_row_dir),
                "--output-dir", str(pages_dir),
            ]) == 0,
            "page_count": len(list(pages_dir.glob("*.md"))) if pages_dir.exists() else 0,
            "output_dir": str(pages_dir),
        }))
        steps.append(step("build_database_row_browser_index", lambda: {
            "ok": build_catalog_index_main([
                "--row-dir", str(db_row_dir),
                "--output", str(browser_index_output),
            ]) == 0,
            "output": str(browser_index_output),
            "row_count": int(json.loads(browser_index_output.read_text(encoding="utf-8"))["_meta"]["total"]) if browser_index_output.exists() else 0,
        }))
        steps.append(step("load_oh_hub_database_rows", lambda: {
            "ok": True,
            "component_count": len(load_oh_hub_catalog(row_dir=db_row_dir)),
        }))
        def run_database_row_pipeline_smoke() -> dict[str, Any]:
            catalog = load_pipeline_catalog(row_dir=db_row_dir)
            pipeline_id = "pipeline/recommend-pipeline-from-prompt"
            pipeline = catalog[pipeline_id]
            result = run_pipeline(pipeline, {}, simulate=True, catalog=catalog)
            return {
                "ok": result.get("catalog_source") == "database_rows",
                "pipeline_id": pipeline_id,
                "catalog_source": result.get("catalog_source"),
                "trace_count": len(result.get("trace") or []),
            }

        steps.append(step("run_pipeline_database_rows", run_database_row_pipeline_smoke))
        def load_processor_database_rows_smoke() -> dict[str, Any]:
            rows = list_processors(row_dir=db_row_dir)
            fn = resolve_callable("processor/catalog-search", row_dir=db_row_dir)
            return {
                "ok": bool(rows) and fn is not None,
                "processor_count": len(rows),
                "catalog_source": rows[0].get("catalog_source") if rows else None,
                "resolved_processor_id": "processor/catalog-search",
                "resolved_module": getattr(fn, "__module__", None),
                "resolved_callable": getattr(fn, "__qualname__", None),
            }

        steps.append(step("load_processor_database_rows", load_processor_database_rows_smoke))
        steps.append(step("capability_lift_gate_database_rows", lambda: {
            **{
                key: value
                for key, value in run_capability_lift_gate(_resource("catalog"), row_dir=db_row_dir).items()
                if key != "decisions"
            },
            "ok": True,
        }))
        def capability_gap_scout_database_row_smoke() -> dict[str, Any]:
            summary = existing_pack_summary(row_dir=db_row_dir)
            return {
                **summary,
                "ok": summary.get("catalog_source") == "database_rows",
            }

        steps.append(step("capability_gap_scout_database_rows", capability_gap_scout_database_row_smoke))
        def foundry_standardize_database_row_smoke() -> dict[str, Any]:
            sample_path, manifest, source = sample_manifest_for_schema_validation(row_dir=db_row_dir)
            if manifest is None:
                return {
                    "ok": False,
                    "catalog_source": source,
                    "message": "no manifest available for schema validation",
                }
            ok, errors = schema_valid(manifest)
            return {
                "ok": ok and source == "database_rows",
                "catalog_source": source,
                "sample": str(sample_path),
                "sample_id": manifest.get("id"),
                "sample_type": manifest.get("type"),
                "errors": errors,
            }

        steps.append(step("foundry_standardize_database_rows", foundry_standardize_database_row_smoke))
        steps.append(step("load_emit_database_rows", lambda: {
            "ok": True,
            "component_count": len(load_emit_catalog(row_dir=db_row_dir)),
        }))
        steps.append(step("build_vector_index_database_rows", lambda: {
            "ok": build_vector_index_main([
                "--row-dir", str(db_row_dir),
                "--embedder", "hash",
                "--output-dir", str(vector_index_dir),
            ]) == 0,
            "output_dir": str(vector_index_dir),
            "catalog_row_count": sum(1 for _ in (vector_index_dir / "oh_catalog.jsonl").read_text(encoding="utf-8").splitlines()) if (vector_index_dir / "oh_catalog.jsonl").exists() else 0,
        }))
        steps.append(step("build_vector_store_database_rows", lambda: {
            **build_vector_store(
                store=vector_store_output,
                model="hash-bow-v1",
                limit=400,
                row_dir=db_row_dir,
            ),
            "ok": True,
        }))
        steps.append(step("build_database_row_sqlite_snapshot", lambda: {
            "ok": build_catalog_db_main([
                "--row-dir", str(db_row_dir),
                "--output", str(sqlite_output),
            ]) == 0,
            "sqlite_output": str(sqlite_output),
            "counts": sqlite_counts(sqlite_output) if sqlite_output.exists() else {},
        }))
    else:
        steps.append({
            "name": "database_export_row_smokes",
            "status": "skipped",
            "ok": True,
            "duration_ms": 0,
            "details": {
                "reason": "database-exported row directory is not present",
                "db_row_dir": str(db_row_dir),
            },
        })

    failures = [item for item in steps if not item["ok"]]
    report = {
        "ok": not failures,
        "generated_at": utc_now(),
        "bridge_dir": str(bridge_dir),
        "db_row_dir": str(db_row_dir),
        "output": str(output),
        "allowances": {
            "hold": allow_hold_count,
            "review": allow_review_count,
            "archive_seed": allow_archive_seed_count,
        },
        "step_count": len(steps),
        "failure_count": len(failures),
        "steps": steps,
        "notes": [
            "This smoke is side-effect free with respect to Postgres and catalog files.",
            "It regenerates dist row/report artifacts and row-backed consumer outputs.",
            "It does not prove a live database has been loaded; use the generated execution/export plans for that.",
        ],
    }
    write_json(output, report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run dry-run catalog database migration smoke checks.")
    parser.add_argument("--bridge-dir", type=Path, default=DEFAULT_BRIDGE_DIR)
    parser.add_argument("--db-row-dir", type=Path, default=DEFAULT_DB_ROW_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--pages-dir", type=Path, default=DEFAULT_PAGES_DIR)
    parser.add_argument("--sqlite-output", type=Path, default=DEFAULT_SQLITE)
    parser.add_argument("--browser-index-output", type=Path, default=DEFAULT_BROWSER_INDEX)
    parser.add_argument("--vector-index-dir", type=Path, default=DEFAULT_VECTOR_INDEX_DIR)
    parser.add_argument("--vector-store-output", type=Path, default=DEFAULT_VECTOR_STORE)
    parser.add_argument("--allow-hold-count", type=int, default=4)
    parser.add_argument("--allow-review-count", type=int, default=743)
    parser.add_argument("--allow-archive-seed-count", type=int, default=0)
    args = parser.parse_args(argv)
    report = build_smoke_report(
        bridge_dir=args.bridge_dir,
        db_row_dir=args.db_row_dir,
        output=args.output,
        pages_dir=args.pages_dir,
        sqlite_output=args.sqlite_output,
        browser_index_output=args.browser_index_output,
        vector_index_dir=args.vector_index_dir,
        vector_store_output=args.vector_store_output,
        allow_hold_count=args.allow_hold_count,
        allow_review_count=args.allow_review_count,
        allow_archive_seed_count=args.allow_archive_seed_count,
    )
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
