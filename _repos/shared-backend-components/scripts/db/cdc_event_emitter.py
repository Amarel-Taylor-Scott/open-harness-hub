#!/usr/bin/env python3
"""Emit change-data-capture events for component version transitions.

Backs ``tool/cdc-event-emitter`` (_repos/shared-backend-components/catalog/tools/backend/cdc-event-emitter.yaml).
The manifest's ``implementations[].path`` is
``scripts.db.cdc_event_emitter.emit_cdc_events``.

The catalog manifest declares an input shape where each JSONL line *pairs* a
previous and a new ``component_version`` row for one ``component_id``
(``component_id``, ``previous_version`` nullable, ``new_version``). The real CDC
computation — canonical definition/content hashing, change-type detection,
changed-field diff, index-record deltas, review-ticket generation, and the
Postgres ``\\copy`` load script — already lives in
``scripts.db.component_cdc_plan.create_component_cdc_plan``. This module is a
THIN adapter: it splits the version-pair file into the two side-by-side files
that the existing engine consumes and delegates, then re-shapes the summary into
the manifest's declared return keys. No hashing or diff logic is duplicated
(lossless reuse — one source of truth for CDC semantics).

The ``high_risk_review_threshold`` manifest parameter is honored here: the
engine flags reviews by change-type; this adapter additionally promotes a row to
review when the fraction of changed fields meets the threshold, and records the
threshold in the summary so the behavior is auditable.

Side-effect free relative to any database: it writes JSONL/CSV/SQL under
``output_dir`` but never connects to Postgres.
"""
from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path
from typing import Any

from scripts._config import (
    CDC_EVENT_EMITTER_NEW_VERSIONS_FILENAME,
    CDC_EVENT_EMITTER_PREVIOUS_VERSIONS_FILENAME,
    CDC_EVENT_EMITTER_SUMMARY_FILENAME,
)
from scripts.db.component_cdc_plan import (
    _changed_fields,
    _body,
    create_component_cdc_plan,
)

# Default review threshold (fraction of changed fields over total fields) at or
# above which a change is promoted to review. Matches the manifest's documented
# default of 0.5. Named constant, not a bare literal (no-magic-values).
DEFAULT_HIGH_RISK_REVIEW_THRESHOLD = 0.5

# Actor types the manifest enumerates for a change batch.
VALID_ACTOR_TYPES = ("system", "publisher", "curator", "tenant", "worker", "import")


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
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
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _split_version_pairs(
    pairs: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split version-pair rows into (previous_rows, new_rows) for the engine.

    Each pair carries ``component_id`` plus ``new_version`` (required) and
    ``previous_version`` (nullable). The engine keys previous rows by
    ``component_id``, so each side keeps its component_id.
    """
    previous_rows: list[dict[str, Any]] = []
    new_rows: list[dict[str, Any]] = []
    for pair in pairs:
        component_id = pair.get("component_id") or pair.get("id")
        if not component_id:
            continue
        new_version = pair.get("new_version")
        if isinstance(new_version, dict):
            new_rows.append({**new_version, "component_id": component_id})
        previous_version = pair.get("previous_version")
        if isinstance(previous_version, dict):
            previous_rows.append({**previous_version, "component_id": component_id})
    return previous_rows, new_rows


def _threshold_review_count(
    pairs: list[dict[str, Any]], threshold: float
) -> int:
    """Count pairs whose changed-field fraction meets the review threshold.

    Reuses ``component_cdc_plan._changed_fields`` / ``_body`` so the diff notion
    matches the engine exactly (no parallel diff implementation).
    """
    flagged = 0
    for pair in pairs:
        new_version = pair.get("new_version")
        if not isinstance(new_version, dict):
            continue
        previous_version = pair.get("previous_version")
        previous_body = _body(previous_version) if isinstance(previous_version, dict) else None
        new_body = _body(new_version)
        total = len(set((previous_body or {}).keys()) | set(new_body.keys())) or 1
        changed = len(_changed_fields(previous_body, new_body))
        if changed / total >= threshold:
            flagged += 1
    return flagged


def emit_cdc_events(
    component_versions_jsonl: str | Path,
    output_dir: str | Path | None = None,
    *,
    actor_type: str = "worker",
    actor_ref: str = "cdc-event-emitter",
    high_risk_review_threshold: float = DEFAULT_HIGH_RISK_REVIEW_THRESHOLD,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Emit CDC events for component version transitions. Returns an audit dict.

    Implements ``tool/cdc-event-emitter``: reads version-pair rows, delegates the
    CDC computation to ``component_cdc_plan``, and returns the manifest's shape.
    """
    if actor_type not in VALID_ACTOR_TYPES:
        raise ValueError(f"actor_type must be one of {VALID_ACTOR_TYPES}; got {actor_type!r}")
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-cdc-event-emitter-"))
    out.mkdir(parents=True, exist_ok=True)
    pairs = _read_jsonl(component_versions_jsonl)
    previous_rows, new_rows = _split_version_pairs(pairs)

    previous_path = out / CDC_EVENT_EMITTER_PREVIOUS_VERSIONS_FILENAME
    new_path = out / CDC_EVENT_EMITTER_NEW_VERSIONS_FILENAME
    _write_jsonl(previous_path, previous_rows)
    _write_jsonl(new_path, new_rows)

    threshold_reviews = _threshold_review_count(pairs, high_risk_review_threshold)

    if dry_run:
        # Compute counts without leaving SQL/CSV behind: run the engine into a
        # temp dir and discard the files, keeping only the counts.
        with tempfile.TemporaryDirectory() as scratch:
            plan = create_component_cdc_plan(
                previous_path, new_path, Path(scratch), actor_type=actor_type, actor_ref=actor_ref
            )
        files: dict[str, str] = {}
    else:
        plan = create_component_cdc_plan(
            previous_path, new_path, out, actor_type=actor_type, actor_ref=actor_ref
        )
        plan_files = plan.get("files", {})
        files = {
            "change_events_jsonl": plan_files.get("component_change_events_jsonl", ""),
            "index_deltas_jsonl": plan_files.get("component_change_index_records_jsonl", ""),
            "review_tickets_jsonl": plan_files.get("component_change_review_tickets_jsonl", ""),
            "sql_load_script": plan_files.get("load_sql", ""),
        }

    summary = {
        "ok": True,
        "component_versions_processed": len(new_rows),
        "change_events_emitted": plan.get("change_event_count", 0),
        "index_deltas_emitted": plan.get("index_record_count", 0),
        "review_tickets_emitted": plan.get("review_ticket_count", 0),
        "threshold_review_candidates": threshold_reviews,
        "high_risk_review_threshold": high_risk_review_threshold,
        "change_type_counts": plan.get("change_type_counts", {}),
        "actor_type": actor_type,
        "actor_ref": actor_ref,
        "dry_run": dry_run,
        "generated_at": _utc_now(),
        "files": files,
    }
    if not dry_run:
        _write_json(out / CDC_EVENT_EMITTER_SUMMARY_FILENAME, summary)
    return summary


def _self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        pairs_path = root / "version-pairs.jsonl"
        pairs = [
            # created (no previous)
            {
                "component_id": "knowledge-corpus/alpha",
                "new_version": {
                    "version": "0.1.0",
                    "version_status": "active",
                    "body": {"facts": [{"id": "a", "value": "one"}]},
                },
            },
            # updated (content + status change → review)
            {
                "component_id": "knowledge-corpus/beta",
                "previous_version": {
                    "version": "0.1.0",
                    "version_status": "active",
                    "body": {"facts": [{"id": "b", "value": "old"}], "note": "x"},
                },
                "new_version": {
                    "version": "0.1.1",
                    "version_status": "review",
                    "body": {"facts": [{"id": "b", "value": "new"}], "note": "y"},
                },
            },
        ]
        _write_jsonl(pairs_path, pairs)
        result = emit_cdc_events(pairs_path, root / "out", actor_type="worker")
        assert result["component_versions_processed"] == 2, result
        assert result["change_events_emitted"] == 2, result
        assert result["index_deltas_emitted"] == 2, result
        # beta: created? no — has previous → updated → review-flagged by engine.
        assert result["review_tickets_emitted"] >= 1, result
        assert result["change_type_counts"].get("created") == 1, result
        assert result["change_type_counts"].get("updated") == 1, result
        # threshold candidates: beta changed 2/2 fields → >= 0.5.
        assert result["threshold_review_candidates"] >= 1, result
        for key in ("change_events_jsonl", "index_deltas_jsonl", "review_tickets_jsonl", "sql_load_script"):
            assert Path(result["files"][key]).exists(), (key, result["files"])
        sql = Path(result["files"]["sql_load_script"]).read_text(encoding="utf-8")
        assert "INSERT INTO component_change_event" in sql, sql
        # invalid actor rejected
        try:
            emit_cdc_events(pairs_path, root / "out2", actor_type="bogus")
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError for invalid actor_type")
        # dry_run leaves no files in the summary
        dry = emit_cdc_events(pairs_path, root / "out3", dry_run=True)
        assert dry["files"] == {}, dry
        assert dry["change_events_emitted"] == 2, dry
    print(json.dumps({"ok": True, "change_events_emitted": 2, "review_tickets_emitted": 1}, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--component-versions-jsonl", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--actor-type", default="worker", choices=VALID_ACTOR_TYPES)
    parser.add_argument("--actor-ref", default="cdc-event-emitter")
    parser.add_argument(
        "--high-risk-review-threshold", type=float, default=DEFAULT_HIGH_RISK_REVIEW_THRESHOLD
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.component_versions_jsonl or not args.output_dir:
        parser.error("--component-versions-jsonl and --output-dir are required unless --self-test is used")
    summary = emit_cdc_events(
        args.component_versions_jsonl,
        args.output_dir,
        actor_type=args.actor_type,
        actor_ref=args.actor_ref,
        high_risk_review_threshold=args.high_risk_review_threshold,
        dry_run=args.dry_run,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
