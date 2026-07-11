#!/usr/bin/env python3
"""Report manifest counts separately from generated object counts.

This script intentionally works without a live database so CI and local runs can
summarize staged JSONL shards. Hosted deployments should pair it with
db/postgres/object_count_report.sql for canonical Postgres row counts.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_CATALOG_ID_INDEX = _resource("dist/catalog-component-ids.json")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _count_jsonl(path: Path) -> int:
    count = 0
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no}: expected JSON object")
        count += 1
    return count


def _component_count(path: Path) -> int | None:
    if not path.exists():
        return None
    payload = _read_json(path)
    if isinstance(payload, dict):
        ids = payload.get("component_ids") or payload.get("ids")
        if isinstance(ids, list):
            return len(ids)
        count = payload.get("component_count")
        if isinstance(count, int):
            return count
    if isinstance(payload, list):
        return len(payload)
    return None


def build_report(
    *,
    jsonl_inputs: dict[str, list[str]],
    catalog_id_index: str | None = str(DEFAULT_CATALOG_ID_INDEX),
    output: str | None = None,
    run_id: str = "local-count-report",
) -> dict[str, Any]:
    object_counts: dict[str, int] = {}
    inputs: dict[str, list[str]] = {}
    for object_type, raw_paths in sorted(jsonl_inputs.items()):
        paths = [Path(raw_path) for raw_path in raw_paths]
        object_counts[object_type] = sum(_count_jsonl(path) for path in paths)
        inputs[object_type] = [str(path) for path in paths]

    component_count = _component_count(Path(catalog_id_index)) if catalog_id_index else None
    report = {
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "catalog": {
            "component_id_index": catalog_id_index,
            "manifest_count": component_count,
            "meaning": "curated catalog manifests, not total generated objects",
        },
        "generated_objects": {
            "total_staged_rows": sum(object_counts.values()),
            "counts_by_type": object_counts,
            "inputs": inputs,
            "meaning": "staged JSONL rows awaiting or mirroring canonical Postgres storage",
        },
        "canonical_store": {
            "recommended": "postgres+pgvector",
            "count_sql": "db/postgres/object_count_report.sql",
        },
    }
    if output:
        out = Path(output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _parse_jsonl_arg(values: list[str]) -> dict[str, list[str]]:
    parsed: dict[str, list[str]] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"--jsonl expects type=path, got {value!r}")
        object_type, path = value.split("=", 1)
        object_type = object_type.strip()
        if not object_type:
            raise ValueError(f"--jsonl object type is empty in {value!r}")
        parsed.setdefault(object_type, []).append(path)
    return parsed


def _self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        staged = base / "objects.jsonl"
        staged.write_text(
            json.dumps({"object_id": "object/demo/1"}) + "\n"
            + json.dumps({"object_id": "object/demo/2"}) + "\n",
            encoding="utf-8",
        )
        ids = base / "catalog-component-ids.json"
        ids.write_text(json.dumps({"component_ids": ["tool/a", "pipeline/b"]}), encoding="utf-8")
        out = base / "report.json"
        report = build_report(
            jsonl_inputs={"normalized_object": [str(staged)]},
            catalog_id_index=str(ids),
            output=str(out),
            run_id="self-test",
        )
        assert report["catalog"]["manifest_count"] == 2
        assert report["generated_objects"]["total_staged_rows"] == 2
        assert out.exists()
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report catalog manifest counts separately from generated object counts.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--jsonl", action="append", default=[], help="Count a staged JSONL shard as type=path. Repeatable.")
    parser.add_argument("--catalog-id-index", default=str(DEFAULT_CATALOG_ID_INDEX))
    parser.add_argument("--output")
    parser.add_argument("--run-id", default="local-count-report")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    report = build_report(
        jsonl_inputs=_parse_jsonl_arg(args.jsonl),
        catalog_id_index=args.catalog_id_index,
        output=args.output,
        run_id=args.run_id,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
