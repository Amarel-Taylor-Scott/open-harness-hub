#!/usr/bin/env python3
"""Bridge approved component version outputs into component CDC planning."""
from __future__ import annotations

import argparse
import csv
import json
import tempfile
from pathlib import Path
from typing import Any

from scripts.db.component_cdc_plan import create_component_cdc_plan


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n" for row in rows), encoding="utf-8")


def _json_loads(value: str, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def _version_row_from_csv(row: dict[str, str]) -> dict[str, Any]:
    body = _json_loads(row.get("body", ""), {})
    source_record_id = ""
    if isinstance(body, dict):
        candidate_body = body.get("component_body")
        if isinstance(candidate_body, dict):
            source_record_id = str(candidate_body.get("source_record_id") or "")
    return {
        "component_version_id": row.get("component_version_id", ""),
        "component_id": row.get("component_id", ""),
        "version": row.get("version", ""),
        "version_status": row.get("version_status", ""),
        "change_summary": row.get("change_summary", ""),
        "definition_source": row.get("definition_source", ""),
        "source_ref": row.get("source_ref", ""),
        "definition_hash": row.get("definition_hash", ""),
        "source_record_id": source_record_id,
        "body": body,
    }


def create_promotion_cdc_bridge_plan(
    *,
    approved_component_versions_csv: str | Path,
    previous_component_versions_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    actor_type: str = "worker",
    actor_ref: str = "promotion-cdc-bridge-planner",
) -> dict[str, Any]:
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-promotion-cdc-bridge-"))
    out.mkdir(parents=True, exist_ok=True)
    csv_rows = _read_csv(Path(approved_component_versions_csv))
    new_rows = [_version_row_from_csv(row) for row in csv_rows if row.get("component_id")]

    previous_path = Path(previous_component_versions_path) if previous_component_versions_path else out / "previous-component-versions.jsonl"
    if not previous_path.exists():
        _write_jsonl(previous_path, [])

    new_path = out / "new-component-versions.jsonl"
    _write_jsonl(new_path, new_rows)
    cdc_dir = out / "component-cdc"
    cdc_summary = create_component_cdc_plan(
        previous_versions_path=previous_path,
        new_versions_path=new_path,
        output_dir=cdc_dir,
        actor_type=actor_type,
        actor_ref=actor_ref,
    )
    summary = {
        "ok": True,
        "approved_component_version_count": len(csv_rows),
        "new_component_version_count": len(new_rows),
        "previous_component_versions_path": str(previous_path),
        "new_component_versions_path": str(new_path),
        "cdc": cdc_summary,
        "files": {
            "new_component_versions_jsonl": str(new_path),
            "component_cdc_plan": str(cdc_dir / "component-cdc-plan.json"),
            "component_change_events_jsonl": cdc_summary["files"]["component_change_events_jsonl"],
            "component_change_index_records_jsonl": cdc_summary["files"]["component_change_index_records_jsonl"],
            "component_change_review_tickets_jsonl": cdc_summary["files"]["component_change_review_tickets_jsonl"],
            "load_sql": cdc_summary["files"]["load_sql"],
            "summary": str(out / "promotion-cdc-bridge-plan.json"),
        },
    }
    _write_json(out / "promotion-cdc-bridge-plan.json", summary)
    return summary


def _self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        csv_path = root / "component-versions.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "component_version_id",
                    "component_id",
                    "version",
                    "version_status",
                    "change_summary",
                    "definition_source",
                    "source_ref",
                    "definition_hash",
                    "body",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "component_version_id": "knowledge-pack/test@0.1.0",
                    "component_id": "knowledge-pack/test",
                    "version": "0.1.0",
                    "version_status": "active",
                    "change_summary": "Initial approved component version.",
                    "definition_source": "generated_factory",
                    "source_ref": "component-candidate/test",
                    "definition_hash": "",
                    "body": json.dumps({"component_body": {"source_record_id": "source/test"}, "value": "ok"}, sort_keys=True),
                }
            )
        result = create_promotion_cdc_bridge_plan(approved_component_versions_csv=csv_path, output_dir=root / "out")
        assert result["new_component_version_count"] == 1, result
        assert result["cdc"]["change_event_count"] == 1, result
        print(json.dumps({"ok": True, "change_event_count": 1}, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--approved-component-versions-csv")
    parser.add_argument("--previous-component-versions-path")
    parser.add_argument("--output-dir")
    parser.add_argument("--actor-type", default="worker")
    parser.add_argument("--actor-ref", default="promotion-cdc-bridge-planner")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.approved_component_versions_csv:
        parser.error("--approved-component-versions-csv is required unless --self-test is used")
    result = create_promotion_cdc_bridge_plan(
        approved_component_versions_csv=args.approved_component_versions_csv,
        previous_component_versions_path=args.previous_component_versions_path,
        output_dir=args.output_dir,
        actor_type=args.actor_type,
        actor_ref=args.actor_ref,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
