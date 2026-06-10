#!/usr/bin/env python3
"""Export database-shaped catalog rows back to manifest YAML.

This is the inverse companion to `catalog_manifest_bridge.py`. It does not
connect to Postgres and it does not overwrite the live catalog. Instead, it
reads JSONL row sets that match database tables, reconstructs portable manifest
YAML files, and writes them under an export directory for review.

The input row-set directory can be produced by:

    python3 scripts/db/catalog_manifest_bridge.py --output-dir dist/catalog-manifest-bridge

In production, the same row shape should come from database queries over
`component`, `component_*`, `rubric_dimension`, `component_ref`, and related
tables.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable

import yaml


REPO = Path(__file__).resolve().parent.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.db.catalog_row_source import row_source_status

DEFAULT_ROW_DIR = REPO / "dist" / "catalog-manifest-bridge"
DEFAULT_OUT = REPO / "dist" / "catalog-manifest-export"
COMPONENT_DIRS = {
    "harness": "harnesses",
    "pipeline": "pipelines",
    "benchmark": "benchmarks",
    "rule-pack": "rule-packs",
    "knowledge-pack": "knowledge-packs",
    "logic-pack": "logic-packs",
    "tool": "tools",
    "persona": "personas",
    "adapter": "adapters",
    "rubric": "rubrics",
    "dataset": "datasets",
    "schema": "schemas",
    "processor": "processors",
    "pattern": "patterns",
}


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no}: expected JSON object")
        rows.append(value)
    return rows


def _write_yaml(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(value, sort_keys=False, allow_unicode=True, width=1000),
        encoding="utf-8",
    )


def _component_slug(component_id: str) -> str:
    return component_id.split("/", 1)[1]


def _manifest_path(out: Path, component_id: str, component_type: str) -> Path:
    directory = COMPONENT_DIRS.get(component_type, component_type + "s")
    return out / "catalog" / directory / f"{_component_slug(component_id)}.yaml"


def _axis_by_component(rows: Iterable[dict[str, Any]], axis: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for row in rows:
        component_id = str(row.get("component_id") or "")
        value = row.get(axis)
        if component_id and isinstance(value, str):
            out.setdefault(component_id, []).append(value)
    return {key: sorted(set(values)) for key, values in out.items()}


def _refs_by_component(rows: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, str]]]:
    out: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        src_id = str(row.get("src_id") or "")
        dst_id = str(row.get("dst_id") or "")
        role = str(row.get("role") or "")
        if src_id and dst_id and role:
            out.setdefault(src_id, []).append({"role": role, "dst_id": dst_id})
    return {
        key: sorted(values, key=lambda item: (item["role"], item["dst_id"]))
        for key, values in out.items()
    }


def _dimension_sort_key(path: str) -> tuple[Any, ...]:
    parts: list[Any] = []
    for part in path.split("."):
        parts.append(int(part) if part.isdigit() else part)
    return tuple(parts)


def _rubric_dimensions_by_component(rows: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        rubric_id = str(row.get("rubric_id") or "")
        if not rubric_id:
            continue
        body = row.get("body") if isinstance(row.get("body"), dict) else {}
        dimension = {
            "id": body.get("id", row.get("dimension_path")),
            "label": body.get("label", row.get("label")),
            "weight": body.get("weight", row.get("weight")),
            "scale": body.get("scale", row.get("scale")),
        }
        evidence_required = body.get("evidence_required", row.get("evidence_required"))
        if evidence_required is not None:
            dimension["evidence_required"] = evidence_required
        for key, value in body.items():
            if key not in dimension:
                dimension[key] = value
        out.setdefault(rubric_id, []).append(dimension)
    return {
        key: sorted(values, key=lambda item: _dimension_sort_key(str(item.get("id", ""))))
        for key, values in out.items()
    }


def _base_manifest(component: dict[str, Any]) -> dict[str, Any]:
    body = component.get("body")
    manifest = dict(body) if isinstance(body, dict) else {}
    for key in [
        "id",
        "type",
        "version",
        "name",
        "description",
        "license",
        "lifecycle",
        "trust_boundary",
        "freshness",
        "created",
        "updated",
        "superseded_by",
        "deprecated_on",
        "attribution",
        "links",
    ]:
        value = component.get(key)
        if value is not None:
            manifest[key] = value
    return manifest


def build_export_plan(*, row_dir: Path = DEFAULT_ROW_DIR, output_dir: Path = DEFAULT_OUT) -> dict[str, Any]:
    components = _read_jsonl(row_dir / "components.jsonl")
    industries = _axis_by_component(_read_jsonl(row_dir / "component_industries.jsonl"), "industry")
    capabilities = _axis_by_component(_read_jsonl(row_dir / "component_capabilities.jsonl"), "capability")
    modalities = _axis_by_component(_read_jsonl(row_dir / "component_modalities.jsonl"), "modality")
    tags = _axis_by_component(_read_jsonl(row_dir / "component_tags.jsonl"), "tag")
    refs = _refs_by_component(_read_jsonl(row_dir / "component_refs.jsonl"))
    rubric_dimensions = _rubric_dimensions_by_component(_read_jsonl(row_dir / "rubric_dimensions.jsonl"))

    exported: list[dict[str, Any]] = []
    for component in components:
        component_id = str(component.get("id") or "")
        component_type = str(component.get("type") or "")
        if not component_id or not component_type:
            continue
        manifest = _base_manifest(component)
        if component_id in industries:
            manifest["industry"] = industries[component_id]
        if component_id in capabilities:
            manifest["capability"] = capabilities[component_id]
        if component_id in modalities:
            manifest["modality"] = modalities[component_id]
        if component_id in tags:
            manifest["tags"] = tags[component_id]
        if component_type == "rubric" and component_id in rubric_dimensions:
            manifest["dimensions"] = rubric_dimensions[component_id]
        if component_id in refs:
            database_export = manifest.get("database_export")
            if not isinstance(database_export, dict):
                database_export = {}
            database_export["component_refs"] = refs[component_id]
            manifest["database_export"] = database_export

        export_path = _manifest_path(output_dir, component_id, component_type)
        _write_yaml(export_path, manifest)
        rendered = yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True, width=1000)
        exported.append({
            "component_id": component_id,
            "component_type": component_type,
            "export_path": str(export_path),
            "export_hash": _sha256_text(rendered),
            "source_definition_hash": (component.get("seed") or {}).get("definition_hash"),
        })

    report = {
        "ok": True,
        "generated_at": _utc_now(),
        "row_dir": str(row_dir),
        "row_source_status": row_source_status(row_dir),
        "output_dir": str(output_dir),
        "component_count": len(components),
        "exported_count": len(exported),
        "exports": exported,
        "safety_notes": [
            "This script reads database-shaped JSONL row sets and writes a separate export directory.",
            "It does not connect to Postgres.",
            "It does not overwrite the live catalog.",
            "Use generated YAML for review, portability, static docs, or disaster recovery snapshots.",
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "manifest-export-plan.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report


def _self_test() -> int:
    sys.path.insert(0, str(REPO))
    from scripts.db.catalog_manifest_bridge import build_bridge_plan

    sample = REPO / "catalog" / "rubrics" / "baltor-business-object-governance-quality.yaml"
    if not sample.exists():
        raise FileNotFoundError(sample)
    with tempfile.TemporaryDirectory(prefix="ohh-manifest-export-") as tmp:
        tmp_path = Path(tmp)
        row_dir = tmp_path / "rows"
        export_dir = tmp_path / "exports"
        bridge_report = build_bridge_plan(paths=[sample], output_dir=row_dir)
        assert bridge_report["counts"]["components"] == 1
        report = build_export_plan(row_dir=row_dir, output_dir=export_dir)
        assert report["exported_count"] == 1
        exported_path = Path(report["exports"][0]["export_path"])
        exported = yaml.safe_load(exported_path.read_text(encoding="utf-8"))
        assert exported["id"] == "rubric/baltor-business-object-governance-quality"
        assert len(exported["dimensions"]) == bridge_report["counts"]["rubric_dimensions"]
    print(json.dumps({"ok": True, "self_test": "catalog_manifest_export_plan"}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export database-shaped catalog rows back to manifest YAML.")
    parser.add_argument("--row-dir", type=Path, default=DEFAULT_ROW_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    report = build_export_plan(row_dir=args.row_dir, output_dir=args.output_dir)
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
