#!/usr/bin/env python3
"""Create a load and promotion audit plan for specialized model-card rows."""
from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path
from typing import Any

from scripts.db.factory_jsonl_bulk_copy import export_bulk
from scripts.db.factory_jsonl_relationship_preflight import preflight
from scripts.factory.candidate_promotion_scorer import score_candidates


ROW_FILES = {
    "source_records": "source-records.jsonl",
    "normalized_objects": "normalized-objects.jsonl",
    "canonical_entities": "canonical-entities.jsonl",
    "object_entity_refs": "object-entity-refs.jsonl",
    "dedupe_clusters": "dedupe-clusters.jsonl",
    "review_tickets": "review-tickets.jsonl",
    "label_assignments": "label-assignments.jsonl",
    "dimension_values": "dimension-values.jsonl",
    "object_embeddings": "object-embeddings.jsonl",
    "index_records": "index-records.jsonl",
}


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _path(row_dir: Path, key: str) -> str:
    path = row_dir / ROW_FILES[key]
    if not path.exists():
        raise FileNotFoundError(path)
    return str(path)


def create_model_card_load_plan(
    *,
    row_dir: str | Path,
    output_dir: str | Path | None = None,
    load_sql_name: str = "load.sql",
) -> dict[str, Any]:
    row_dir = Path(row_dir)
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-model-card-load-plan-"))
    out.mkdir(parents=True, exist_ok=True)
    promotion_dir = out / "promotion"
    bulk_dir = out / "bulk"

    row_paths = {key: _path(row_dir, key) for key in ROW_FILES}
    preflight_report = preflight(
        source_records=[row_paths["source_records"]],
        normalized_objects=[row_paths["normalized_objects"]],
        canonical_entities=[row_paths["canonical_entities"]],
        object_entity_refs=[row_paths["object_entity_refs"]],
        dedupe_clusters=[row_paths["dedupe_clusters"]],
        review_tickets=[row_paths["review_tickets"]],
        label_assignments=[row_paths["label_assignments"]],
        dimension_values=[row_paths["dimension_values"]],
        object_embeddings=[row_paths["object_embeddings"]],
    )
    if not preflight_report["ok"]:
        manifest = {
            "ok": False,
            "created_at": _utc_now(),
            "row_dir": str(row_dir),
            "output_dir": str(out),
            "preflight_report": preflight_report,
            "error": "relationship preflight failed",
        }
        (out / "load-plan-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return manifest

    promotion_summary = score_candidates(
        input_path=row_paths["normalized_objects"],
        output_dir=str(promotion_dir),
    )
    bulk_manifest = export_bulk(
        output_dir=str(bulk_dir),
        source_records=[row_paths["source_records"]],
        normalized_objects=[row_paths["normalized_objects"]],
        promotion_decisions=[promotion_summary["paths"]["promotion_decisions"]],
        index_records=[row_paths["index_records"], promotion_summary["paths"]["index_records"]],
        canonical_entities=[row_paths["canonical_entities"]],
        object_entity_refs=[row_paths["object_entity_refs"]],
        dedupe_clusters=[row_paths["dedupe_clusters"]],
        review_tickets=[row_paths["review_tickets"], promotion_summary["paths"]["review_tickets"]],
        label_assignments=[row_paths["label_assignments"]],
        dimension_values=[row_paths["dimension_values"]],
        object_embeddings=[row_paths["object_embeddings"]],
        load_sql_name=load_sql_name,
    )
    manifest = {
        "ok": True,
        "created_at": _utc_now(),
        "row_dir": str(row_dir),
        "output_dir": str(out),
        "preflight_report": preflight_report,
        "promotion_summary": promotion_summary,
        "bulk_manifest": bulk_manifest,
        "safety_notes": [
            "Bulk load plan contains derived public model-card metadata only.",
            "Model weights and private training data are not represented in the load plan.",
            "Promotion decisions are advisory; high-impact candidates remain review-gated.",
        ],
    }
    (out / "load-plan-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _self_test() -> int:
    row_dir = Path("dist/specialized-model-card-rows/seed")
    if not row_dir.exists():
        raise FileNotFoundError("dist/specialized-model-card-rows/seed is required for this self-test")
    with tempfile.TemporaryDirectory() as tmp:
        result = create_model_card_load_plan(row_dir=row_dir, output_dir=tmp)
        assert result["ok"] is True
        assert result["preflight_report"]["issue_count"] == 0
        assert result["promotion_summary"]["promotion_decisions"] > 0
        assert Path(result["bulk_manifest"]["load_sql"]).exists()
    print("ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a bulk-load and promotion audit plan for specialized model-card row families.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--row-dir")
    parser.add_argument("--output-dir")
    parser.add_argument("--load-sql-name", default="load.sql")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.row_dir:
        parser.error("--row-dir is required unless --self-test is used")
    result = create_model_card_load_plan(
        row_dir=args.row_dir,
        output_dir=args.output_dir,
        load_sql_name=args.load_sql_name,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
