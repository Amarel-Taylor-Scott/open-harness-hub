#!/usr/bin/env python3
"""Report duplicate primary-key collapse across staged factory row families."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Any


ROW_FILES = {
    "source_record": "source-records.jsonl",
    "normalized_object": "normalized-objects.jsonl",
    "canonical_entity": "canonical-entities.jsonl",
    "object_entity_ref": "object-entity-refs.jsonl",
    "dedupe_cluster": "dedupe-clusters.jsonl",
    "review_ticket": "review-tickets.jsonl",
    "label_assignment": "label-assignments.jsonl",
    "dimension_value": "dimension-values.jsonl",
    "object_embedding": "object-embeddings.jsonl",
    "index_record": "index-records.jsonl",
}

PRIMARY_KEYS = {
    "source_record": ("source_record_id",),
    "normalized_object": ("object_id",),
    "canonical_entity": ("entity_id",),
    "object_entity_ref": ("object_id", "entity_id", "role"),
    "dedupe_cluster": ("dedupe_cluster_id",),
    "review_ticket": ("review_ticket_id",),
    "label_assignment": ("label_id",),
    "dimension_value": ("dimension_id",),
    "object_embedding": ("embedding_id",),
    "index_record": ("index_record_id",),
}

CRITICAL_FAMILIES = {"normalized_object", "object_embedding", "index_record"}
HASH_SUFFIX_RE = re.compile(r"-[0-9a-f]{10,20}$")


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no}: expected JSON object")
        rows.append(value)
    return rows


def _write_json(path: str | Path, payload: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def _rows_dir(partition: str | Path) -> Path:
    root = Path(partition)
    candidate = root / "rows"
    return candidate if candidate.exists() else root


def _pk(table: str, row: dict[str, Any]) -> tuple[str, ...]:
    return tuple(str(row.get(field, "")) for field in PRIMARY_KEYS[table])


def _row_hash(row: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _id_source(table: str, key: tuple[str, ...]) -> str:
    joined = "|".join(key)
    if table == "source_record":
        return "shared_source_record"
    if table == "canonical_entity":
        return "shared_canonical_entity"
    if table == "object_entity_ref":
        return "shared_object_entity_ref"
    if HASH_SUFFIX_RE.search(joined):
        return "hash_suffixed_id"
    if len(joined) >= 72 and not HASH_SUFFIX_RE.search(joined):
        return "truncation_risk_id"
    if len(key) > 1:
        return "composite_key"
    return "plain_id"


def _sample(rows: list[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    return rows[:limit]


def build_duplicate_collapse_report(
    *,
    partitions: list[str | Path],
    output_dir: str | Path,
    run_id: str = "duplicate-collapse-report",
    sample_limit: int = 20,
) -> dict[str, Any]:
    out = Path(output_dir)
    generated_at = _utc_now()
    detail_rows: list[dict[str, Any]] = []
    family_reports: dict[str, dict[str, Any]] = {}

    for table, filename in ROW_FILES.items():
        grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
        raw_count = 0
        missing_files: list[str] = []
        for partition in partitions:
            path = _rows_dir(partition) / filename
            if not path.exists():
                missing_files.append(str(path))
                continue
            rows = _read_jsonl(path)
            raw_count += len(rows)
            for row in rows:
                grouped[_pk(table, row)].append(row)

        duplicate_key_groups = {key: rows for key, rows in grouped.items() if len(rows) > 1}
        duplicate_rows = sum(len(rows) - 1 for rows in duplicate_key_groups.values())
        conflicting_groups = 0
        identical_groups = 0
        id_source_counts: dict[str, int] = defaultdict(int)
        for key, rows in duplicate_key_groups.items():
            hashes = {_row_hash(row) for row in rows}
            if len(hashes) == 1:
                identical_groups += 1
            else:
                conflicting_groups += 1
            id_source_counts[_id_source(table, key)] += 1
            if len(detail_rows) < sample_limit:
                detail_rows.append({
                    "row_family": table,
                    "primary_key": list(key),
                    "duplicate_row_count": len(rows) - 1,
                    "raw_row_count": len(rows),
                    "id_source": _id_source(table, key),
                    "row_hash_count": len(hashes),
                    "conflicting": len(hashes) > 1,
                    "sample_rows": _sample(rows),
                })

        risk = "none"
        if conflicting_groups:
            risk = "high"
        elif table in CRITICAL_FAMILIES and duplicate_rows:
            risk = "medium"
        elif duplicate_rows:
            risk = "low"

        family_reports[table] = {
            "row_family": table,
            "primary_key_fields": list(PRIMARY_KEYS[table]),
            "raw_rows": raw_count,
            "unique_keys": len(grouped),
            "duplicate_rows_collapsed": duplicate_rows,
            "duplicate_key_groups": len(duplicate_key_groups),
            "identical_duplicate_groups": identical_groups,
            "conflicting_duplicate_groups": conflicting_groups,
            "id_source_counts": dict(sorted(id_source_counts.items())),
            "missing_files": missing_files,
            "risk": risk,
        }

    critical_duplicate_rows = sum(family_reports[name]["duplicate_rows_collapsed"] for name in CRITICAL_FAMILIES)
    conflicting_total = sum(row["conflicting_duplicate_groups"] for row in family_reports.values())
    duplicate_total = sum(row["duplicate_rows_collapsed"] for row in family_reports.values())
    summary_path = out / "duplicate-collapse-report.json"
    detail_path = out / "duplicate-collapse-details.jsonl"
    _write_jsonl(detail_path, detail_rows)
    status = "ok"
    if conflicting_total:
        status = "conflicting_duplicate_keys"
    elif critical_duplicate_rows:
        status = "critical_family_duplicates_present"
    elif duplicate_total:
        status = "shared_reference_duplicates_only"
    report = {
        "ok": conflicting_total == 0,
        "status": status,
        "run_id": run_id,
        "generated_at": generated_at,
        "partitions": [str(path) for path in partitions],
        "counts": {
            "duplicate_rows_collapsed": duplicate_total,
            "critical_duplicate_rows_collapsed": critical_duplicate_rows,
            "conflicting_duplicate_key_groups": conflicting_total,
            "row_families": len(family_reports),
        },
        "family_reports": family_reports,
        "files": {
            "summary": str(summary_path),
            "details": str(detail_path),
        },
        "safety_notes": [
            "This report reads staged JSONL only and does not mutate databases or generated rows.",
            "Conflicting duplicate keys should block candidate-table loading until reviewed.",
            "Duplicate source, entity, and object/entity reference rows can be normal when shared across partitions.",
            "Duplicate normalized_object, object_embedding, or index_record rows are treated as higher-risk scale regressions.",
        ],
    }
    _write_json(summary_path, report)
    return report


def _self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "rows"
        base.mkdir(parents=True)
        (base / "normalized-objects.jsonl").write_text(
            json.dumps({"object_id": "object/a", "title": "A"}) + "\n"
            + json.dumps({"object_id": "object/a", "title": "A"}) + "\n",
            encoding="utf-8",
        )
        (base / "canonical-entities.jsonl").write_text(
            json.dumps({"entity_id": "entity/shared", "canonical_name": "Shared"}) + "\n"
            + json.dumps({"entity_id": "entity/shared", "canonical_name": "Shared"}) + "\n",
            encoding="utf-8",
        )
        result = build_duplicate_collapse_report(partitions=[base], output_dir=Path(tmp) / "out", run_id="self-test")
        assert result["counts"]["duplicate_rows_collapsed"] == 2
        assert result["counts"]["critical_duplicate_rows_collapsed"] == 1
        assert result["family_reports"]["normalized_object"]["duplicate_rows_collapsed"] == 1
        assert result["family_reports"]["canonical_entity"]["duplicate_rows_collapsed"] == 1
    print(json.dumps({"ok": True}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--partition", action="append", default=[])
    parser.add_argument("--output-dir", default="dist/duplicate-collapse-report")
    parser.add_argument("--run-id", default="duplicate-collapse-report")
    parser.add_argument("--sample-limit", type=int, default=20)
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.partition:
        parser.error("--partition is required unless --self-test is used")
    result = build_duplicate_collapse_report(
        partitions=args.partition,
        output_dir=args.output_dir,
        run_id=args.run_id,
        sample_limit=args.sample_limit,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
