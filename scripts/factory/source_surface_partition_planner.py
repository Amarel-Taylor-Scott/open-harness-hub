from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_ACCESS_METHODS = ["official_web_page"]
DEFAULT_REQUIRED_STAGES = [
    "source_governance",
    "source_discovery",
    "source_snapshot",
    "page_to_markdown",
    "source_ingest",
    "entity_linking",
    "fuzzy_dedupe",
    "dedupe_index",
    "publish_review",
]


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if isinstance(value, dict):
                rows.append(value)
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _safe_slug(value: str, *, limit: int = 72) -> str:
    out: list[str] = []
    for char in value.lower():
        if char.isalnum():
            out.append(char)
        elif out and out[-1] != "-":
            out.append("-")
    return "".join(out).strip("-")[:limit] or "unknown"


def _hash_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _list(value: Any, default: list[str] | None = None) -> list[str]:
    if value is None:
        return list(default or [])
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return list(default or [])


def _int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(parsed, 1)


def _priority(surface: dict[str, Any]) -> float:
    score = surface.get("priority_score")
    if isinstance(score, (int, float)):
        return float(score)
    factors = surface.get("priority_factors") or {}
    if not isinstance(factors, dict):
        return 1.0
    product = 1.0
    for key in [
        "usefulness",
        "demand",
        "complexity",
        "time_savings",
        "frequency_of_deployment",
        "not_solved_by_out_of_box_llms",
        "cost_savings",
        "deployment_management_value",
        "model_swap_value",
    ]:
        product *= max(float(factors.get(key, 1.0)), 0.1)
    return round(product, 4)


def _partition_count(surface: dict[str, Any], max_sources_per_partition: int) -> int:
    source_patterns = _list(surface.get("source_patterns") or surface.get("source_surfaces"))
    primitives = _list(surface.get("candidate_primitives") or surface.get("expected_objects"), ["candidate_primitive"])
    access_methods = _list(surface.get("access_methods"), DEFAULT_ACCESS_METHODS)
    rough_units = max(len(source_patterns), 1) * max(len(primitives), 1) * max(len(access_methods), 1)
    requested = _int(surface.get("partition_count"), 0)
    estimated = max(1, (rough_units + max_sources_per_partition - 1) // max_sources_per_partition)
    return min(max(requested, estimated), _int(surface.get("max_partitions"), 24))


def _partition(surface: dict[str, Any], *, index: int, count: int, run_id: str, max_records: int) -> dict[str, Any]:
    surface_id = str(surface.get("id") or surface.get("slug") or "source-surface")
    vertical = str(surface.get("vertical") or surface.get("domain") or "cross_domain")
    partition_seed = {
        "surface_id": surface_id,
        "index": index,
        "count": count,
        "source_patterns": _list(surface.get("source_patterns") or surface.get("source_surfaces")),
        "candidate_primitives": _list(surface.get("candidate_primitives") or surface.get("expected_objects")),
    }
    partition_id = f"partition/source-surface/{_safe_slug(surface_id)}/{index:03d}-of-{count:03d}"
    return {
        "partition_id": partition_id,
        "surface_id": surface_id,
        "run_id": run_id,
        "status": "queued",
        "vertical": vertical,
        "title": surface.get("title", surface_id),
        "partition_index": index,
        "partition_count": count,
        "cursor": {
            "strategy": surface.get("cursor_strategy", "deterministic_hash_bucket"),
            "bucket": index,
            "bucket_count": count,
            "resume_after": "",
        },
        "source_patterns": _list(surface.get("source_patterns") or surface.get("source_surfaces")),
        "publisher_classes": _list(surface.get("publisher_classes"), ["public_publisher"]),
        "access_methods": _list(surface.get("access_methods"), DEFAULT_ACCESS_METHODS),
        "expected_objects": _list(surface.get("candidate_primitives") or surface.get("expected_objects"), ["candidate_primitive"]),
        "label_paths": sorted(set(_list(surface.get("label_paths")) + [f"vertical.{vertical}"])),
        "required_stages": _list(surface.get("required_stages"), DEFAULT_REQUIRED_STAGES),
        "review_triggers": _list(surface.get("review_triggers")),
        "risk_tier": surface.get("risk_tier", "medium"),
        "priority_score": _priority(surface),
        "max_records": max_records,
        "content_hash": _hash_json(partition_seed),
        "policy": {
            "privacy_boundary": surface.get("privacy_boundary", "public"),
            "license_policy": surface.get("license_posture", "metadata_and_citation_first"),
            "trust_tier": surface.get("trust_tier", "public"),
            "excluded_scopes": sorted(set(_list(surface.get("excluded_scope")) + ["insurance"])),
            "do_not_store_raw_private_data": True,
            "do_not_republish_source_body_without_license": True,
        },
    }


def _blueprint_from_partition(partition: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": partition["partition_id"].replace("partition/source-surface/", "").replace("/", "-"),
        "title": partition["title"],
        "vertical": partition["vertical"],
        "publisher_classes": partition["publisher_classes"],
        "access_methods": partition["access_methods"],
        "source_patterns": partition["source_patterns"],
        "expected_objects": partition["expected_objects"],
        "label_paths": partition["label_paths"],
        "required_stages": partition["required_stages"],
        "review_triggers": partition["review_triggers"],
        "risk_tier": partition["risk_tier"],
        "privacy_boundary": partition["policy"]["privacy_boundary"],
        "license_posture": partition["policy"]["license_policy"],
        "trust_tier": partition["policy"]["trust_tier"],
        "excluded_scope": partition["policy"]["excluded_scopes"],
        "resume_cursor": partition["cursor"],
        "source_partition_id": partition["partition_id"],
    }


def plan_source_surface_partitions(
    source_surfaces: list[dict[str, Any]],
    *,
    output_dir: str | Path | None = None,
    run_id: str | None = None,
    max_sources_per_partition: int = 4,
    max_records_per_partition: int = 250,
) -> dict[str, Any]:
    run_id = run_id or f"run/{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-source-surface-partitions-"))
    partitions: list[dict[str, Any]] = []
    for surface in sorted(source_surfaces, key=lambda row: (-_priority(row), str(row.get("id", "")))):
        count = _partition_count(surface, max_sources_per_partition)
        max_records = _int(surface.get("max_records_per_partition"), max_records_per_partition)
        for index in range(1, count + 1):
            partitions.append(_partition(surface, index=index, count=count, run_id=run_id, max_records=max_records))
    blueprints = [_blueprint_from_partition(partition) for partition in partitions]
    summary_rows = [
        {
            "surface_id": str(surface.get("id") or "source-surface"),
            "vertical": str(surface.get("vertical") or surface.get("domain") or "cross_domain"),
            "priority_score": _priority(surface),
            "partition_count": _partition_count(surface, max_sources_per_partition),
            "expected_objects": _list(surface.get("candidate_primitives") or surface.get("expected_objects")),
            "risk_tier": surface.get("risk_tier", "medium"),
        }
        for surface in source_surfaces
    ]
    _write_jsonl(out_dir / "source-surface-scan-partitions.jsonl", partitions)
    _write_jsonl(out_dir / "public-source-blueprints.jsonl", blueprints)
    _write_jsonl(out_dir / "source-surface-schedule-summary.jsonl", summary_rows)
    return {
        "output_dir": str(out_dir),
        "run_id": run_id,
        "source_surface_count": len(source_surfaces),
        "partition_count": len(partitions),
        "blueprint_count": len(blueprints),
        "files": [
            "source-surface-scan-partitions.jsonl",
            "public-source-blueprints.jsonl",
            "source-surface-schedule-summary.jsonl",
        ],
        "partition_counts_by_risk": {
            risk: sum(1 for partition in partitions if partition.get("risk_tier") == risk)
            for risk in sorted({str(partition.get("risk_tier")) for partition in partitions})
        },
        "warnings": ["Partitions contain source metadata and cursors only; workers must store raw captures outside the public catalog."],
    }


def _sample_surfaces() -> list[dict[str, Any]]:
    return [
        {
            "id": "municipal-permit-trade-checklists",
            "title": "Municipal permit and trade checklist surfaces",
            "vertical": "construction.trades",
            "publisher_classes": ["municipal_agency"],
            "access_methods": ["official_web_page", "pdf_index"],
            "source_patterns": ["permit checklist pages", "inspection correction forms"],
            "candidate_primitives": ["permit_requirement_fact", "inspection_question"],
            "priority_score": 256,
            "risk_tier": "high",
            "review_triggers": ["safety-critical inspection item"],
            "partition_count": 2,
            "excluded_scope": ["insurance"],
        }
    ]


def _self_test() -> None:
    result = plan_source_surface_partitions(_sample_surfaces(), max_sources_per_partition=2)
    assert result["source_surface_count"] == 1
    assert result["partition_count"] == 4
    partitions = _read_jsonl(Path(result["output_dir"]) / "source-surface-scan-partitions.jsonl")
    blueprints = _read_jsonl(Path(result["output_dir"]) / "public-source-blueprints.jsonl")
    assert len(partitions) == len(blueprints) == 4
    assert partitions[0]["policy"]["do_not_store_raw_private_data"] is True
    assert "insurance" in partitions[0]["policy"]["excluded_scopes"]
    assert blueprints[0]["source_partition_id"] == partitions[0]["partition_id"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan resumable source-surface scan partitions and public-source blueprints.")
    parser.add_argument("--source-surfaces-jsonl")
    parser.add_argument("--output-dir")
    parser.add_argument("--run-id")
    parser.add_argument("--max-sources-per-partition", type=int, default=4)
    parser.add_argument("--max-records-per-partition", type=int, default=250)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        print("ok")
        return 0
    if not args.source_surfaces_jsonl:
        parser.error("--source-surfaces-jsonl is required unless --self-test is used")
    print(
        json.dumps(
            plan_source_surface_partitions(
                _read_jsonl(args.source_surfaces_jsonl),
                output_dir=args.output_dir,
                run_id=args.run_id,
                max_sources_per_partition=args.max_sources_per_partition,
                max_records_per_partition=args.max_records_per_partition,
            ),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
