#!/usr/bin/env python3
"""Shared loader for database-shaped catalog row sets.

The files loaded here are produced by the manifest bridge or by exporting the
Postgres catalog tables. Consumers should use this module when they need a
portable row-backed read path instead of walking catalog YAML directly.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts._config import DEFAULT_CATALOG_ROW_DIR, OH_CATALOG_ROW_DIR_ENV


@dataclass(frozen=True)
class CatalogRowComponent:
    id: str
    type: str
    manifest: dict[str, Any]
    source_path: str
    refs: list[tuple[str, str]] = field(default_factory=list)
    database_refs: list[dict[str, str]] = field(default_factory=list)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no}: invalid JSONL row: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no}: expected JSON object row")
        rows.append(value)
    return rows


def read_json_report(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else None


def has_component_rows(row_dir: Path) -> bool:
    return (row_dir / "components.jsonl").exists()


def default_smoke_dir_for_row_dir(row_dir: Path) -> Path:
    # The standard generated layout is dist/catalog-*-rows*/ plus
    # dist/catalog-migration-smoke/. Keep this as metadata discovery only; the
    # row loader itself must not depend on smoke artifacts being present.
    if row_dir.parent.name == "dist":
        return row_dir.parent / "catalog-migration-smoke"
    return row_dir.parent / "catalog-migration-smoke"


def row_source_status(row_dir: Path, *, smoke_dir: Path | None = None) -> dict[str, Any]:
    """Return non-blocking metadata about a database-shaped row source.

    Consumers use this to expose whether they are reading seed-bridge rows,
    database-exported rows, or an unknown row snapshot. The status is advisory:
    it never reads catalog YAML and it never raises on missing reports.
    """
    manifest_plan = read_json_report(row_dir / "manifest-import-plan.json")
    export_plan = read_json_report(row_dir / "catalog-db-export-plan.json")
    integrity = read_json_report(row_dir / "catalog-row-integrity-report.json")
    row_kind = "database_export" if export_plan else "seed_bridge" if manifest_plan else "row_snapshot"
    smoke_root = smoke_dir or default_smoke_dir_for_row_dir(row_dir)
    readiness = read_json_report(smoke_root / "catalog-database-promotion-readiness.json")
    staleness = read_json_report(smoke_root / "catalog-db-export-staleness-gate.json")
    return {
        "row_dir": str(row_dir),
        "kind": row_kind,
        "component_rows_present": has_component_rows(row_dir),
        "integrity_ok": bool(integrity.get("ok")) if isinstance(integrity, dict) else None,
        "integrity_warning_count": (
            int(integrity.get("severity_counts", {}).get("warning") or 0)
            if isinstance(integrity, dict) and isinstance(integrity.get("severity_counts"), dict)
            else 0
        ),
        "seed_load_sql_coverage_ok": (
            bool(manifest_plan.get("load_sql_coverage", {}).get("ok"))
            if isinstance(manifest_plan, dict) and isinstance(manifest_plan.get("load_sql_coverage"), dict)
            else None
        ),
        "database_export_sql_coverage_ok": (
            bool(export_plan.get("export_sql_coverage", {}).get("ok"))
            if isinstance(export_plan, dict) and isinstance(export_plan.get("export_sql_coverage"), dict)
            else None
        ),
        "promotion_ready": (
            bool(readiness.get("would_pass"))
            if isinstance(readiness, dict)
            else None
        ),
        "promotion_status": (
            str(readiness.get("status"))
            if isinstance(readiness, dict) and readiness.get("status") is not None
            else None
        ),
        "staleness_status": (
            str(staleness.get("status"))
            if isinstance(staleness, dict) and staleness.get("status") is not None
            else None
        ),
        "staleness_would_pass": (
            bool(staleness.get("would_pass"))
            if isinstance(staleness, dict)
            else None
        ),
        "report_paths": {
            "manifest_plan": str(row_dir / "manifest-import-plan.json"),
            "database_export_plan": str(row_dir / "catalog-db-export-plan.json"),
            "integrity": str(row_dir / "catalog-row-integrity-report.json"),
            "promotion_readiness": str(smoke_root / "catalog-database-promotion-readiness.json"),
            "staleness_gate": str(smoke_root / "catalog-db-export-staleness-gate.json"),
        },
    }


def resolve_catalog_row_dir(
    row_dir: Path | str | None = None,
    *,
    require_existing: bool = True,
) -> Path | None:
    """Resolve the preferred database-shaped catalog row directory.

    Explicit caller input wins, then OH_CATALOG_ROW_DIR, then the default bridge
    export directory. When `require_existing` is true, the returned directory
    must contain components.jsonl; otherwise callers should use their documented
    seed/export fallback.
    """
    candidate = row_dir or os.environ.get(OH_CATALOG_ROW_DIR_ENV)
    path = Path(candidate) if candidate else DEFAULT_CATALOG_ROW_DIR
    if require_existing and not has_component_rows(path):
        return None
    return path


def axis_values_by_component(row_dir: Path, filename: str, value_key: str) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    for row in read_jsonl(row_dir / filename):
        component_id = row.get("component_id")
        value = row.get(value_key)
        if not isinstance(component_id, str) or not isinstance(value, str):
            continue
        bucket = values.setdefault(component_id, [])
        if value not in bucket:
            bucket.append(value)
    return values


def refs_by_component(row_dir: Path) -> dict[str, list[tuple[str, str]]]:
    refs: dict[str, list[tuple[str, str]]] = {}
    for row in read_jsonl(row_dir / "component_refs.jsonl"):
        component_id = row.get("component_id") or row.get("src_id")
        role = row.get("relation") or row.get("role")
        target_id = row.get("target_id") or row.get("dst_id")
        if not all(isinstance(value, str) for value in [component_id, role, target_id]):
            continue
        refs.setdefault(component_id, []).append((role, target_id))
    return refs


def database_refs_by_component(row_dir: Path) -> dict[str, list[dict[str, str]]]:
    refs: dict[str, list[dict[str, str]]] = {}
    for component_id, values in refs_by_component(row_dir).items():
        refs[component_id] = [
            {
                "role": role,
                "target_id": target_id,
            }
            for role, target_id in values
        ]
    return refs


def component_manifest_from_row(
    row: dict[str, Any],
    industries: dict[str, list[str]],
    capabilities: dict[str, list[str]],
    modalities: dict[str, list[str]],
    tags: dict[str, list[str]],
) -> dict[str, Any] | None:
    component_id = row.get("id")
    component_type = row.get("type")
    if not isinstance(component_id, str) or not isinstance(component_type, str):
        return None

    body = row.get("body")
    if not isinstance(body, dict):
        body = {}
    manifest: dict[str, Any] = dict(body)
    manifest.setdefault("id", component_id)
    manifest.setdefault("type", component_type)
    manifest.setdefault("version", row.get("version"))
    manifest.setdefault("name", row.get("name") or component_id)
    manifest.setdefault("description", row.get("description") or "")
    manifest.setdefault("license", row.get("license"))
    manifest.setdefault("lifecycle", row.get("lifecycle") or "unknown")
    manifest.setdefault("trust_boundary", row.get("trust_boundary"))
    manifest["industry"] = industries.get(component_id, manifest.get("industry") or [])
    manifest["capability"] = capabilities.get(component_id, manifest.get("capability") or [])
    manifest["modality"] = modalities.get(component_id, manifest.get("modality") or [])
    manifest["tags"] = tags.get(component_id, manifest.get("tags") or [])
    return manifest


def source_path_from_row(row: dict[str, Any], component_id: str) -> str:
    seed = row.get("seed")
    if isinstance(seed, dict) and isinstance(seed.get("path"), str):
        return seed["path"]
    if isinstance(row.get("source_ref"), str):
        return row["source_ref"]
    return f"db://component/{component_id}"


def iter_components_from_rows(row_dir: Path) -> list[CatalogRowComponent]:
    industries = axis_values_by_component(row_dir, "component_industries.jsonl", "industry")
    capabilities = axis_values_by_component(row_dir, "component_capabilities.jsonl", "capability")
    modalities = axis_values_by_component(row_dir, "component_modalities.jsonl", "modality")
    tags = axis_values_by_component(row_dir, "component_tags.jsonl", "tag")
    refs = refs_by_component(row_dir)
    database_refs = database_refs_by_component(row_dir)

    components: list[CatalogRowComponent] = []
    for row in read_jsonl(row_dir / "components.jsonl"):
        component_id = row.get("id")
        component_type = row.get("type")
        if not isinstance(component_id, str) or not isinstance(component_type, str):
            continue
        manifest = component_manifest_from_row(row, industries, capabilities, modalities, tags)
        if manifest is None:
            continue
        components.append(
            CatalogRowComponent(
                id=component_id,
                type=component_type,
                manifest=manifest,
                source_path=source_path_from_row(row, component_id),
                refs=refs.get(component_id, []),
                database_refs=database_refs.get(component_id, []),
            )
        )
    return components


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Summarize database-shaped catalog row sets.")
    parser.add_argument("row_dir", type=Path)
    args = parser.parse_args()
    components = iter_components_from_rows(args.row_dir)
    print(json.dumps({"row_dir": str(args.row_dir), "components": len(components)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
