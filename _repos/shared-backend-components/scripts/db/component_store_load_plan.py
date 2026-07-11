#!/usr/bin/env python3
"""Export component-store candidates as CSV plus a psql load script."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import csv
import json
import tempfile
import time
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
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


def _json(value: Any, default: Any) -> str:
    return json.dumps(value if value is not None else default, sort_keys=True, ensure_ascii=False)


def _str(value: Any) -> str:
    return "" if value is None else str(value)


COMPONENT_COLUMNS = [
    "component_candidate_id", "source_object_id", "component_type", "name",
    "component_layer", "control_flow_kind", "trust_tier", "privacy_boundary",
    "review_status", "quality_status", "content_hash", "promotion_state", "body",
]
SUBCOMPONENT_COLUMNS = [
    "subcomponent_candidate_id", "component_candidate_id", "parent_object_id",
    "subcomponent_type", "name", "review_status", "content_hash", "body",
]
SOURCE_LINK_COLUMNS = [
    "source_record_id", "component_candidate_id", "publisher", "license",
    "trust_tier", "privacy_boundary", "content_hash",
]


def _component_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "component_candidate_id": _str(row.get("component_candidate_id")),
        "source_object_id": _str(row.get("source_object_id")),
        "component_type": _str(row.get("component_type")),
        "name": _str(row.get("name")),
        "component_layer": _str(row.get("component_layer")),
        "control_flow_kind": _str(row.get("control_flow_kind")),
        "trust_tier": _str(row.get("trust_tier")),
        "privacy_boundary": _str(row.get("privacy_boundary")),
        "review_status": _str(row.get("review_status")),
        "quality_status": _str(row.get("quality_status")),
        "content_hash": _str(row.get("content_hash")),
        "promotion_state": _str(row.get("promotion_state") or "candidate"),
        "body": _json(row.get("body"), {}),
    }


def _subcomponent_row(row: dict[str, Any], component_by_object: dict[str, str]) -> dict[str, str]:
    parent_object_id = _str(row.get("parent_object_id"))
    return {
        "subcomponent_candidate_id": _str(row.get("subcomponent_candidate_id")),
        "component_candidate_id": component_by_object.get(parent_object_id, ""),
        "parent_object_id": parent_object_id,
        "subcomponent_type": _str(row.get("subcomponent_type")),
        "name": _str(row.get("name")),
        "review_status": _str(row.get("review_status")),
        "content_hash": _str(row.get("content_hash")),
        "body": _json(row.get("body"), {}),
    }


def _source_link_rows(
    source_rows: list[dict[str, Any]],
    object_rows: list[dict[str, Any]],
    components: list[dict[str, Any]],
) -> list[dict[str, str]]:
    source_by_id = {
        _str(row.get("source_record_id")): row
        for row in source_rows
        if row.get("source_record_id")
    }
    source_by_object_id = {
        _str(row.get("object_id")): _str(row.get("source_record_id"))
        for row in object_rows
        if row.get("object_id") and row.get("source_record_id")
    }
    out: list[dict[str, str]] = []
    for component in components:
        body = component.get("body") if isinstance(component.get("body"), dict) else {}
        source_id = _str(body.get("source_record_id")) or source_by_object_id.get(_str(component.get("source_object_id")), "")
        source = source_by_id.get(source_id, {})
        if not source_id:
            continue
        out.append({
            "source_record_id": source_id,
            "component_candidate_id": _str(component.get("component_candidate_id")),
            "publisher": _str(source.get("publisher")),
            "license": _str(source.get("license")),
            "trust_tier": _str(source.get("trust_tier")),
            "privacy_boundary": _str(source.get("privacy_boundary")),
            "content_hash": _str(source.get("content_hash")),
        })
    return out


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _load_sql(component_csv: Path, subcomponent_csv: Path, source_link_csv: Path) -> str:
    return f"""BEGIN;

CREATE TEMP TABLE stage_component_candidate (
  component_candidate_id text,
  source_object_id text,
  component_type text,
  name text,
  component_layer text,
  control_flow_kind text,
  trust_tier text,
  privacy_boundary text,
  review_status text,
  quality_status text,
  content_hash text,
  promotion_state text,
  body jsonb
);

CREATE TEMP TABLE stage_subcomponent_candidate (
  subcomponent_candidate_id text,
  component_candidate_id text,
  parent_object_id text,
  subcomponent_type text,
  name text,
  review_status text,
  content_hash text,
  body jsonb
);

CREATE TEMP TABLE stage_source_component_link (
  source_record_id text,
  component_candidate_id text,
  publisher text,
  license text,
  trust_tier text,
  privacy_boundary text,
  content_hash text
);

\\copy stage_component_candidate FROM '{component_csv}' WITH (FORMAT csv, HEADER true)
\\copy stage_subcomponent_candidate FROM '{subcomponent_csv}' WITH (FORMAT csv, HEADER true)
\\copy stage_source_component_link FROM '{source_link_csv}' WITH (FORMAT csv, HEADER true)

INSERT INTO component_candidate (
  component_candidate_id, source_object_id, component_type, name, trust_tier,
  privacy_boundary, review_status, quality_status, content_hash,
  promotion_state, body, component_layer, control_flow_kind
)
SELECT
  component_candidate_id,
  NULLIF(source_object_id, ''),
  component_type,
  name,
  NULLIF(trust_tier, ''),
  NULLIF(privacy_boundary, ''),
  NULLIF(review_status, ''),
  NULLIF(quality_status, ''),
  NULLIF(content_hash, ''),
  COALESCE(NULLIF(promotion_state, ''), 'candidate'),
  COALESCE(body, '{{}}'::jsonb),
  NULLIF(component_layer, ''),
  NULLIF(control_flow_kind, '')
FROM stage_component_candidate
ON CONFLICT (component_candidate_id) DO UPDATE SET
  source_object_id=EXCLUDED.source_object_id,
  component_type=EXCLUDED.component_type,
  name=EXCLUDED.name,
  component_layer=EXCLUDED.component_layer,
  control_flow_kind=EXCLUDED.control_flow_kind,
  trust_tier=EXCLUDED.trust_tier,
  privacy_boundary=EXCLUDED.privacy_boundary,
  review_status=EXCLUDED.review_status,
  quality_status=EXCLUDED.quality_status,
  content_hash=EXCLUDED.content_hash,
  promotion_state=EXCLUDED.promotion_state,
  body=EXCLUDED.body;

INSERT INTO subcomponent_candidate (
  subcomponent_candidate_id, component_candidate_id, parent_object_id,
  subcomponent_type, name, review_status, content_hash, body
)
SELECT
  subcomponent_candidate_id,
  NULLIF(component_candidate_id, ''),
  NULLIF(parent_object_id, ''),
  subcomponent_type,
  NULLIF(name, ''),
  NULLIF(review_status, ''),
  NULLIF(content_hash, ''),
  COALESCE(body, '{{}}'::jsonb)
FROM stage_subcomponent_candidate
ON CONFLICT (subcomponent_candidate_id) DO UPDATE SET
  component_candidate_id=EXCLUDED.component_candidate_id,
  parent_object_id=EXCLUDED.parent_object_id,
  subcomponent_type=EXCLUDED.subcomponent_type,
  name=EXCLUDED.name,
  review_status=EXCLUDED.review_status,
  content_hash=EXCLUDED.content_hash,
  body=EXCLUDED.body;

INSERT INTO source_component_link (
  source_record_id, component_candidate_id, publisher, license,
  trust_tier, privacy_boundary, content_hash
)
SELECT
  source_record_id,
  component_candidate_id,
  NULLIF(publisher, ''),
  NULLIF(license, ''),
  NULLIF(trust_tier, ''),
  NULLIF(privacy_boundary, ''),
  NULLIF(content_hash, '')
FROM stage_source_component_link
WHERE source_record_id <> '' AND component_candidate_id <> ''
ON CONFLICT (source_record_id, component_candidate_id) DO UPDATE SET
  publisher=EXCLUDED.publisher,
  license=EXCLUDED.license,
  trust_tier=EXCLUDED.trust_tier,
  privacy_boundary=EXCLUDED.privacy_boundary,
  content_hash=EXCLUDED.content_hash;

COMMIT;
"""


def create_component_store_load_plan(
    *,
    component_store_plan: str | Path,
    output_dir: str | Path | None = None,
    load_sql_name: str = "load-component-store.sql",
) -> dict[str, Any]:
    plan_path = Path(component_store_plan)
    plan = _read_json(plan_path)
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-component-store-load-"))
    out.mkdir(parents=True, exist_ok=True)
    component_rows_raw = _read_jsonl(Path(plan["files"]["component_candidates"]))
    component_by_object = {
        _str(row.get("source_object_id")): _str(row.get("component_candidate_id"))
        for row in component_rows_raw
        if row.get("source_object_id")
    }
    component_rows = [_component_row(row) for row in component_rows_raw]
    subcomponent_rows = [
        _subcomponent_row(row, component_by_object)
        for row in _read_jsonl(Path(plan["files"]["subcomponent_candidates"]))
    ]
    row_dir = Path(plan["row_dir"])
    source_link_rows = _source_link_rows(
        _read_jsonl(row_dir / "source-records.jsonl"),
        _read_jsonl(row_dir / "normalized-objects.jsonl"),
        component_rows_raw,
    )

    component_csv = out / "component-candidates.csv"
    subcomponent_csv = out / "subcomponent-candidates.csv"
    source_link_csv = out / "source-component-links.csv"
    load_sql = out / load_sql_name
    _write_csv(component_csv, COMPONENT_COLUMNS, component_rows)
    _write_csv(subcomponent_csv, SUBCOMPONENT_COLUMNS, subcomponent_rows)
    _write_csv(source_link_csv, SOURCE_LINK_COLUMNS, source_link_rows)
    load_sql.write_text(_load_sql(component_csv, subcomponent_csv, source_link_csv), encoding="utf-8")

    report = {
        "ok": True,
        "generated_at": _utc_now(),
        "component_store_plan": str(plan_path),
        "component_candidate_count": len(component_rows),
        "subcomponent_candidate_count": len(subcomponent_rows),
        "source_component_link_count": len(source_link_rows),
        "output_dir": str(out),
        "files": {
            "component_candidates_csv": str(component_csv),
            "subcomponent_candidates_csv": str(subcomponent_csv),
            "source_component_links_csv": str(source_link_csv),
            "load_sql": str(load_sql),
            "summary": str(out / "component-store-load-plan.json"),
        },
        "safety_notes": [
            "This planner writes CSV and SQL only; it does not connect to Postgres.",
            "Rows load into candidate tables and remain review-gated before promotion to active components.",
            "Source links preserve license, trust, and privacy metadata for later export decisions.",
        ],
    }
    _write_json(out / "component-store-load-plan.json", report)
    return report


def _self_test() -> int:
    plan = _resource("dist/source-surface-scan-partitions/seed/component-store/component-store-plan.json")
    if not plan.exists():
        raise FileNotFoundError("component-store-plan.json is required")
    with tempfile.TemporaryDirectory() as tmp:
        report = create_component_store_load_plan(component_store_plan=plan, output_dir=tmp)
        assert report["component_candidate_count"] > 0
        assert report["subcomponent_candidate_count"] > report["component_candidate_count"]
        assert report["source_component_link_count"] > 0
        assert Path(report["files"]["load_sql"]).exists()
    print(json.dumps({
        "ok": True,
        "component_candidate_count": report["component_candidate_count"],
        "subcomponent_candidate_count": report["subcomponent_candidate_count"],
    }, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create CSV and psql load script for component-store candidates.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--component-store-plan")
    parser.add_argument("--output-dir")
    parser.add_argument("--load-sql-name", default="load-component-store.sql")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.component_store_plan:
        parser.error("--component-store-plan is required unless --self-test is used")
    result = create_component_store_load_plan(
        component_store_plan=args.component_store_plan,
        output_dir=args.output_dir,
        load_sql_name=args.load_sql_name,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
