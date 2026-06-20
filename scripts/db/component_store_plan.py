#!/usr/bin/env python3
"""Plan database-backed component and subcomponent rows from factory JSONL."""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import time
from pathlib import Path
from typing import Any


ROW_FILES = {
    "source_record": "source-records.jsonl",
    "normalized_object": "normalized-objects.jsonl",
    "canonical_entity": "canonical-entities.jsonl",
    "object_entity_ref": "object-entity-refs.jsonl",
    "dedupe_cluster": "dedupe-clusters.jsonl",
    "label_assignment": "label-assignments.jsonl",
    "dimension_value": "dimension-values.jsonl",
    "object_embedding": "object-embeddings.jsonl",
    "index_record": "index-records.jsonl",
    "review_ticket": "review-tickets.jsonl",
}


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


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


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _object_id(row: dict[str, Any]) -> str:
    return str(row.get("object_id") or row.get("id") or row.get("subject_id") or "")


def _source_id(row: dict[str, Any]) -> str:
    return str(row.get("source_record_id") or row.get("id") or "")


def plan_component_store(
    *,
    row_dir: str | Path,
    output_dir: str | Path | None = None,
    run_id: str = "component-store-plan",
) -> dict[str, Any]:
    base = Path(row_dir)
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-component-store-"))
    rows = {name: _read_jsonl(base / filename) for name, filename in ROW_FILES.items()}

    component_candidates: list[dict[str, Any]] = []
    for row in rows["normalized_object"]:
        oid = _object_id(row)
        component_candidates.append({
            "component_candidate_id": f"component-candidate/{oid}",
            "source_object_id": oid,
            "component_type": row.get("object_type", "knowledge_object"),
            "name": row.get("title") or oid,
            "trust_tier": row.get("trust_tier"),
            "privacy_boundary": row.get("privacy_boundary"),
            "review_status": row.get("review_status"),
            "quality_status": row.get("quality_status"),
            "content_hash": row.get("content_hash") or _hash(row.get("body", row)),
            "promotion_state": "candidate",
            "body": row.get("body", row),
        })

    subcomponent_candidates: list[dict[str, Any]] = []
    type_map = {
        "label_assignment": "label",
        "dimension_value": "dimension",
        "object_entity_ref": "entity_ref",
        "index_record": "index_record",
        "object_embedding": "embedding_work_item",
        "review_ticket": "review_route",
    }
    for family, sub_type in type_map.items():
        for row in rows[family]:
            subject_id = str(row.get("subject_id") or row.get("object_id") or row.get("source_object_id") or "")
            row_id = str(row.get("label_id") or row.get("dimension_id") or row.get("index_record_id") or row.get("embedding_id") or row.get("review_ticket_id") or _hash(row))
            subcomponent_candidates.append({
                "subcomponent_candidate_id": f"subcomponent-candidate/{sub_type}/{row_id}",
                "parent_object_id": subject_id,
                "subcomponent_type": sub_type,
                "name": row.get("label") or row.get("name") or row.get("review_type") or sub_type,
                "review_status": row.get("review_status") or row.get("status"),
                "content_hash": row.get("content_hash") or row.get("text_hash") or _hash(row),
                "body": row,
            })

    source_component_links = [{
        "source_record_id": _source_id(row),
        "publisher": row.get("publisher"),
        "license": row.get("license"),
        "trust_tier": row.get("trust_tier"),
        "privacy_boundary": row.get("privacy_boundary"),
        "content_hash": row.get("content_hash"),
    } for row in rows["source_record"]]

    _write_jsonl(out / "component-candidates.jsonl", component_candidates)
    _write_jsonl(out / "subcomponent-candidates.jsonl", subcomponent_candidates)
    _write_jsonl(out / "source-component-links.jsonl", source_component_links)
    summary = {
        "ok": True,
        "run_id": run_id,
        "generated_at": _utc_now(),
        "row_dir": str(base),
        "component_candidate_count": len(component_candidates),
        "subcomponent_candidate_count": len(subcomponent_candidates),
        "source_component_link_count": len(source_component_links),
        "input_row_counts": {name: len(value) for name, value in rows.items()},
        "files": {
            "component_candidates": str(out / "component-candidates.jsonl"),
            "subcomponent_candidates": str(out / "subcomponent-candidates.jsonl"),
            "source_component_links": str(out / "source-component-links.jsonl"),
            "summary": str(out / "component-store-plan.json"),
        },
        "safety_notes": [
            "This planner does not mutate Postgres.",
            "Repository files remain seed/export definitions; the planned target is database-backed components and subcomponents.",
            "Private or sensitive rows must pass source governance and review routing before promotion.",
        ],
    }
    _write_json(out / "component-store-plan.json", summary)
    return summary


def _self_test() -> int:
    source = Path("dist/source-surface-scan-partitions/seed/rows")
    if not source.exists():
        raise FileNotFoundError("dist/source-surface-scan-partitions/seed/rows is required")
    with tempfile.TemporaryDirectory() as tmp:
        report = plan_component_store(row_dir=source, output_dir=tmp)
        assert report["component_candidate_count"] > 0
        assert report["subcomponent_candidate_count"] > report["component_candidate_count"]
        assert Path(report["files"]["summary"]).exists()
    print(json.dumps({
        "ok": True,
        "component_candidate_count": report["component_candidate_count"],
        "subcomponent_candidate_count": report["subcomponent_candidate_count"],
    }, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan database-backed component and subcomponent rows from factory JSONL.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--row-dir")
    parser.add_argument("--output-dir")
    parser.add_argument("--run-id", default="component-store-plan")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.row_dir:
        parser.error("--row-dir is required unless --self-test is used")
    result = plan_component_store(row_dir=args.row_dir, output_dir=args.output_dir, run_id=args.run_id)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
