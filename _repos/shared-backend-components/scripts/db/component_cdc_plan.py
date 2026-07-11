#!/usr/bin/env python3
"""Plan component version CDC rows from old/new component definitions."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import tempfile
import time
from pathlib import Path
from typing import Any


EVENT_COLUMNS = [
    "change_event_id",
    "component_id",
    "previous_component_version_id",
    "new_component_version_id",
    "change_type",
    "previous_definition_hash",
    "new_definition_hash",
    "previous_content_hash",
    "new_content_hash",
    "changed_fields",
    "source_record_id",
    "actor_type",
    "actor_ref",
    "signature_ref",
    "event_body",
    "created_at",
]

INDEX_COLUMNS = [
    "index_record_id",
    "index_kind",
    "subject_id",
    "subject_type",
    "text",
    "metadata",
    "embedding_model",
    "embedding_ref",
    "graph_edges",
]

REVIEW_COLUMNS = [
    "review_ticket_id",
    "object_id",
    "source_record_id",
    "review_type",
    "reason",
    "status",
    "created_at",
]


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
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n" for row in rows), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def canonical_hash(value: Any) -> str:
    """Return a stable sha256 over canonical JSON."""
    return "sha256:" + hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _str(value: Any) -> str:
    return "" if value is None else str(value)


def _json(value: Any, default: Any) -> str:
    return json.dumps(value if value is not None else default, sort_keys=True, ensure_ascii=True)


def _body(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("body")
    return value if isinstance(value, dict) else {}


def _component_id(row: dict[str, Any]) -> str:
    return _str(row.get("component_id") or row.get("id"))


def _version_id(row: dict[str, Any]) -> str:
    existing = _str(row.get("component_version_id"))
    if existing:
        return existing
    component_id = _component_id(row)
    version = _str(row.get("version") or "0.0.0")
    return "component-version/" + component_id.replace("/", "-") + "/" + version.replace("/", "-")


def _definition_hash(row: dict[str, Any]) -> str:
    existing = _str(row.get("definition_hash"))
    if existing:
        return existing
    return canonical_hash(_body(row) or row)


def _content_hash(row: dict[str, Any]) -> str:
    existing = _str(row.get("content_hash"))
    if existing:
        return existing
    body = _body(row)
    content = body.get("content") or body.get("text") or body or row
    return canonical_hash(content)


def _changed_fields(previous: dict[str, Any] | None, new: dict[str, Any]) -> list[str]:
    if previous is None:
        return sorted(new.keys())
    fields = sorted(set(previous.keys()) | set(new.keys()))
    return [field for field in fields if previous.get(field) != new.get(field)]


def _change_type(previous: dict[str, Any] | None, new: dict[str, Any], previous_hash: str, new_hash: str) -> str:
    if previous is None:
        return "created"
    if previous_hash == new_hash and _content_hash(previous) != _content_hash(new):
        return "source_refreshed"
    old_status = _str(previous.get("version_status") or previous.get("lifecycle"))
    new_status = _str(new.get("version_status") or new.get("lifecycle"))
    if new_status == "deprecated" and old_status != "deprecated":
        return "deprecated"
    if new_status == "superseded" and old_status != "superseded":
        return "superseded"
    return "updated" if previous_hash != new_hash else "hash_recomputed"


def _event_id(component_id: str, new_version_id: str, new_hash: str) -> str:
    seed = canonical_hash({"component_id": component_id, "version": new_version_id, "hash": new_hash}).split(":", 1)[1][:16]
    return "component-change/" + component_id.replace("/", "-") + "/" + seed


def create_component_cdc_plan(
    previous_versions_path: Path,
    new_versions_path: Path,
    output_dir: Path,
    actor_type: str = "worker",
    actor_ref: str = "component-cdc-planner",
) -> dict[str, Any]:
    previous_rows = _read_jsonl(previous_versions_path)
    new_rows = _read_jsonl(new_versions_path)
    previous_by_component = {_component_id(row): row for row in previous_rows if _component_id(row)}

    events: list[dict[str, Any]] = []
    index_rows: list[dict[str, Any]] = []
    review_rows: list[dict[str, Any]] = []
    now = _utc_now()

    for new in new_rows:
        component_id = _component_id(new)
        if not component_id:
            continue
        previous = previous_by_component.get(component_id)
        previous_hash = _definition_hash(previous) if previous else ""
        new_hash = _definition_hash(new)
        previous_content_hash = _content_hash(previous) if previous else ""
        new_content_hash = _content_hash(new)
        changed_fields = _changed_fields(previous, new)
        change_type = _change_type(previous, new, previous_hash, new_hash)
        source_record_id = _str(new.get("source_record_id") or (previous or {}).get("source_record_id"))
        event_body = {
            "version": _str(new.get("version")),
            "version_status": _str(new.get("version_status") or new.get("lifecycle")),
            "source_ref": _str(new.get("source_ref") or new.get("source_url")),
            "change_summary": _str(new.get("change_summary")),
            "requires_review": change_type in {"updated", "source_refreshed", "publisher_signed"},
        }
        event = {
            "change_event_id": _event_id(component_id, _version_id(new), new_hash),
            "component_id": component_id,
            "previous_component_version_id": _version_id(previous) if previous else "",
            "new_component_version_id": _version_id(new),
            "change_type": change_type,
            "previous_definition_hash": previous_hash,
            "new_definition_hash": new_hash,
            "previous_content_hash": previous_content_hash,
            "new_content_hash": new_content_hash,
            "changed_fields": changed_fields,
            "source_record_id": source_record_id,
            "actor_type": actor_type,
            "actor_ref": actor_ref,
            "signature_ref": _str(new.get("signature_ref")),
            "event_body": event_body,
            "created_at": now,
        }
        events.append(event)
        index_rows.append(
            {
                "index_record_id": "index/" + event["change_event_id"].replace("/", "-"),
                "index_kind": "freshness",
                "subject_id": component_id,
                "subject_type": "component",
                "text": f"{component_id} {change_type} {new_hash} fields {' '.join(changed_fields[:12])}",
                "metadata": {
                    "change_event_id": event["change_event_id"],
                    "change_type": change_type,
                    "definition_hash": new_hash,
                    "content_hash": new_content_hash,
                    "changed_fields": changed_fields,
                },
                "embedding_model": "",
                "embedding_ref": "",
                "graph_edges": [{"from": component_id, "to": event["change_event_id"], "role": "has_change_event"}],
            }
        )
        if event_body["requires_review"]:
            review_rows.append(
                {
                    "review_ticket_id": "review/" + event["change_event_id"].replace("/", "-"),
                    "object_id": "",
                    "source_record_id": source_record_id,
                    "review_type": "component_change_review",
                    "reason": f"Review {change_type} for {component_id}; changed fields: {', '.join(changed_fields[:12])}",
                    "status": "open",
                    "created_at": now,
                }
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    events_jsonl = output_dir / "component-change-events.jsonl"
    index_jsonl = output_dir / "component-change-index-records.jsonl"
    review_jsonl = output_dir / "component-change-review-tickets.jsonl"
    events_csv = output_dir / "component-change-events.csv"
    index_csv = output_dir / "component-change-index-records.csv"
    review_csv = output_dir / "component-change-review-tickets.csv"
    load_sql = output_dir / "load-component-change-events.sql"

    _write_jsonl(events_jsonl, events)
    _write_jsonl(index_jsonl, index_rows)
    _write_jsonl(review_jsonl, review_rows)
    _write_csv(events_csv, [_event_csv_row(row) for row in events], EVENT_COLUMNS)
    _write_csv(index_csv, [_index_csv_row(row) for row in index_rows], INDEX_COLUMNS)
    _write_csv(review_csv, review_rows, REVIEW_COLUMNS)
    load_sql.write_text(_load_sql(events_csv, index_csv, review_csv), encoding="utf-8")

    summary = {
        "ok": True,
        "previous_version_count": len(previous_rows),
        "new_version_count": len(new_rows),
        "change_event_count": len(events),
        "index_record_count": len(index_rows),
        "review_ticket_count": len(review_rows),
        "change_type_counts": _counts(row["change_type"] for row in events),
        "generated_at": now,
        "output_dir": str(output_dir),
        "files": {
            "component_change_events_jsonl": str(events_jsonl),
            "component_change_events_csv": str(events_csv),
            "component_change_index_records_jsonl": str(index_jsonl),
            "component_change_index_records_csv": str(index_csv),
            "component_change_review_tickets_jsonl": str(review_jsonl),
            "component_change_review_tickets_csv": str(review_csv),
            "load_sql": str(load_sql),
        },
    }
    _write_json(output_dir / "component-cdc-plan.json", summary)
    return summary


def _counts(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[_str(value)] = counts.get(_str(value), 0) + 1
    return dict(sorted(counts.items()))


def _event_csv_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "change_event_id": _str(row.get("change_event_id")),
        "component_id": _str(row.get("component_id")),
        "previous_component_version_id": _str(row.get("previous_component_version_id")),
        "new_component_version_id": _str(row.get("new_component_version_id")),
        "change_type": _str(row.get("change_type")),
        "previous_definition_hash": _str(row.get("previous_definition_hash")),
        "new_definition_hash": _str(row.get("new_definition_hash")),
        "previous_content_hash": _str(row.get("previous_content_hash")),
        "new_content_hash": _str(row.get("new_content_hash")),
        "changed_fields": _json(row.get("changed_fields"), []),
        "source_record_id": _str(row.get("source_record_id")),
        "actor_type": _str(row.get("actor_type")),
        "actor_ref": _str(row.get("actor_ref")),
        "signature_ref": _str(row.get("signature_ref")),
        "event_body": _json(row.get("event_body"), {}),
        "created_at": _str(row.get("created_at")),
    }


def _index_csv_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "index_record_id": _str(row.get("index_record_id")),
        "index_kind": _str(row.get("index_kind")),
        "subject_id": _str(row.get("subject_id")),
        "subject_type": _str(row.get("subject_type")),
        "text": _str(row.get("text")),
        "metadata": _json(row.get("metadata"), {}),
        "embedding_model": _str(row.get("embedding_model")),
        "embedding_ref": _str(row.get("embedding_ref")),
        "graph_edges": _json(row.get("graph_edges"), []),
    }


def _sql_path(path: Path) -> str:
    return str(path).replace("'", "''")


def _load_sql(events_csv: Path, index_csv: Path, review_csv: Path) -> str:
    return f"""BEGIN;

CREATE TEMP TABLE component_change_event_stage (
  change_event_id TEXT,
  component_id TEXT,
  previous_component_version_id TEXT,
  new_component_version_id TEXT,
  change_type TEXT,
  previous_definition_hash TEXT,
  new_definition_hash TEXT,
  previous_content_hash TEXT,
  new_content_hash TEXT,
  changed_fields TEXT,
  source_record_id TEXT,
  actor_type TEXT,
  actor_ref TEXT,
  signature_ref TEXT,
  event_body TEXT,
  created_at TEXT
);

CREATE TEMP TABLE review_ticket_stage (
  review_ticket_id TEXT,
  object_id TEXT,
  source_record_id TEXT,
  review_type TEXT,
  reason TEXT,
  status TEXT,
  created_at TEXT
);

\\copy component_change_event_stage ({", ".join(EVENT_COLUMNS)}) FROM '{_sql_path(events_csv)}' WITH (FORMAT csv, HEADER true)
\\copy index_record ({", ".join(INDEX_COLUMNS)}) FROM '{_sql_path(index_csv)}' WITH (FORMAT csv, HEADER true)
\\copy review_ticket_stage ({", ".join(REVIEW_COLUMNS)}) FROM '{_sql_path(review_csv)}' WITH (FORMAT csv, HEADER true)

INSERT INTO component_change_event (
  change_event_id,
  component_id,
  previous_component_version_id,
  new_component_version_id,
  change_type,
  previous_definition_hash,
  new_definition_hash,
  previous_content_hash,
  new_content_hash,
  changed_fields,
  source_record_id,
  actor_type,
  actor_ref,
  signature_ref,
  event_body,
  created_at
)
SELECT
  change_event_id,
  component_id,
  NULLIF(previous_component_version_id, ''),
  NULLIF(new_component_version_id, ''),
  change_type,
  NULLIF(previous_definition_hash, ''),
  NULLIF(new_definition_hash, ''),
  NULLIF(previous_content_hash, ''),
  NULLIF(new_content_hash, ''),
  changed_fields::jsonb,
  NULLIF(source_record_id, ''),
  NULLIF(actor_type, ''),
  NULLIF(actor_ref, ''),
  NULLIF(signature_ref, ''),
  event_body::jsonb,
  created_at::timestamptz
FROM component_change_event_stage;

INSERT INTO review_ticket (
  review_ticket_id,
  object_id,
  source_record_id,
  review_type,
  reason,
  status,
  created_at
)
SELECT
  review_ticket_id,
  NULLIF(object_id, ''),
  NULLIF(source_record_id, ''),
  review_type,
  reason,
  status,
  created_at::timestamptz
FROM review_ticket_stage;

COMMIT;
"""


def _self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        previous = root / "previous.jsonl"
        new = root / "new.jsonl"
        previous.write_text(
            json.dumps(
                {
                    "component_id": "knowledge-pack/example",
                    "component_version_id": "component-version/example/0.1.0",
                    "version": "0.1.0",
                    "version_status": "active",
                    "body": {"facts": [{"id": "a", "value": "old"}]},
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        new.write_text(
            json.dumps(
                {
                    "component_id": "knowledge-pack/example",
                    "component_version_id": "component-version/example/0.1.1",
                    "version": "0.1.1",
                    "version_status": "review",
                    "body": {"facts": [{"id": "a", "value": "new"}]},
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        summary = create_component_cdc_plan(previous, new, root / "out")
        assert summary["change_event_count"] == 1, summary
        assert summary["review_ticket_count"] == 1, summary
        assert summary["change_type_counts"] == {"updated": 1}, summary
        print(json.dumps({"ok": True, "change_event_count": 1}, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous-versions-path", type=Path, required=False)
    parser.add_argument("--new-versions-path", type=Path, required=False)
    parser.add_argument("--output-dir", type=Path, required=False)
    parser.add_argument("--actor-type", default="worker")
    parser.add_argument("--actor-ref", default="component-cdc-planner")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        return
    if not args.previous_versions_path or not args.new_versions_path or not args.output_dir:
        parser.error("--previous-versions-path, --new-versions-path, and --output-dir are required unless --self-test is used")
    summary = create_component_cdc_plan(
        args.previous_versions_path,
        args.new_versions_path,
        args.output_dir,
        actor_type=args.actor_type,
        actor_ref=args.actor_ref,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
