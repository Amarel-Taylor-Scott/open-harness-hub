#!/usr/bin/env python3
"""Export promotion decisions, review tickets, and index records as CSV plus SQL."""
from __future__ import annotations

import argparse
import csv
import json
import tempfile
import time
from pathlib import Path
from typing import Any


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


def _json(value: Any, default: Any) -> str:
    return json.dumps(value if value is not None else default, sort_keys=True, ensure_ascii=False)


def _str(value: Any) -> str:
    return "" if value is None else str(value)


def _sql_path(path: Path) -> str:
    return str(path).replace("'", "''")


PROMOTION_COLUMNS = [
    "decision_id", "object_id", "source_record_id", "score", "max_score",
    "decision", "criteria", "risk_flags", "review_reasons",
    "recommended_outputs", "created_at",
]
INDEX_COLUMNS = [
    "index_record_id", "index_kind", "subject_id", "subject_type",
    "text", "metadata", "embedding_model", "embedding_ref", "graph_edges",
]
REVIEW_COLUMNS = [
    "review_ticket_id", "object_id", "source_record_id",
    "review_type", "reason", "status", "created_at",
]


def _promotion_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "decision_id": _str(row.get("decision_id")),
        "object_id": _str(row.get("object_id")),
        "source_record_id": _str(row.get("source_record_id")),
        "score": _str(row.get("score")),
        "max_score": _str(row.get("max_score") or 100),
        "decision": _str(row.get("decision")),
        "criteria": _json(row.get("criteria"), {}),
        "risk_flags": _json(row.get("risk_flags"), []),
        "review_reasons": _json(row.get("review_reasons"), []),
        "recommended_outputs": _json(row.get("recommended_outputs"), []),
        "created_at": _str(row.get("created_at")),
    }


def _index_row(row: dict[str, Any]) -> dict[str, str]:
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


def _review_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "review_ticket_id": _str(row.get("review_ticket_id")),
        "object_id": _str(row.get("object_id")),
        "source_record_id": _str(row.get("source_record_id")),
        "review_type": _str(row.get("review_type") or "quality"),
        "reason": _str(row.get("reason") or "Promotion decision requires review."),
        "status": _str(row.get("status") or "open"),
        "created_at": _str(row.get("created_at")),
    }


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _load_sql(promotion_csv: Path, index_csv: Path, review_csv: Path) -> str:
    return f"""BEGIN;

CREATE TEMP TABLE stage_promotion_decision (
  decision_id text,
  object_id text,
  source_record_id text,
  score numeric,
  max_score numeric,
  decision text,
  criteria jsonb,
  risk_flags jsonb,
  review_reasons jsonb,
  recommended_outputs jsonb,
  created_at timestamptz
);

CREATE TEMP TABLE stage_index_record (
  index_record_id text,
  index_kind text,
  subject_id text,
  subject_type text,
  text text,
  metadata jsonb,
  embedding_model text,
  embedding_ref text,
  graph_edges jsonb
);

CREATE TEMP TABLE stage_review_ticket (
  review_ticket_id text,
  object_id text,
  source_record_id text,
  review_type text,
  reason text,
  status text,
  created_at timestamptz
);

\\copy stage_promotion_decision FROM '{_sql_path(promotion_csv)}' WITH (FORMAT csv, HEADER true)
\\copy stage_index_record FROM '{_sql_path(index_csv)}' WITH (FORMAT csv, HEADER true)
\\copy stage_review_ticket FROM '{_sql_path(review_csv)}' WITH (FORMAT csv, HEADER true)

INSERT INTO promotion_decision (
  decision_id, object_id, source_record_id, score, max_score, decision,
  criteria, risk_flags, review_reasons, recommended_outputs, created_at
)
SELECT
  decision_id,
  CASE WHEN object_id <> '' AND EXISTS (SELECT 1 FROM normalized_object n WHERE n.object_id = stage_promotion_decision.object_id) THEN object_id ELSE NULL END,
  CASE WHEN source_record_id <> '' AND EXISTS (SELECT 1 FROM source_record s WHERE s.source_record_id = stage_promotion_decision.source_record_id) THEN source_record_id ELSE NULL END,
  score,
  COALESCE(max_score, 100),
  decision,
  COALESCE(criteria, '{{}}'::jsonb),
  COALESCE(risk_flags, '[]'::jsonb),
  COALESCE(review_reasons, '[]'::jsonb),
  COALESCE(recommended_outputs, '[]'::jsonb),
  COALESCE(created_at, now())
FROM stage_promotion_decision
WHERE decision_id <> ''
ON CONFLICT (decision_id) DO UPDATE SET
  object_id=EXCLUDED.object_id,
  source_record_id=EXCLUDED.source_record_id,
  score=EXCLUDED.score,
  max_score=EXCLUDED.max_score,
  decision=EXCLUDED.decision,
  criteria=EXCLUDED.criteria,
  risk_flags=EXCLUDED.risk_flags,
  review_reasons=EXCLUDED.review_reasons,
  recommended_outputs=EXCLUDED.recommended_outputs;

INSERT INTO index_record (
  index_record_id, index_kind, subject_id, subject_type, text, metadata,
  embedding_model, embedding_ref, graph_edges
)
SELECT
  index_record_id,
  index_kind,
  subject_id,
  NULLIF(subject_type, ''),
  text,
  COALESCE(metadata, '{{}}'::jsonb),
  NULLIF(embedding_model, ''),
  NULLIF(embedding_ref, ''),
  COALESCE(graph_edges, '[]'::jsonb)
FROM stage_index_record
WHERE index_record_id <> ''
ON CONFLICT (index_record_id) DO UPDATE SET
  index_kind=EXCLUDED.index_kind,
  subject_id=EXCLUDED.subject_id,
  subject_type=EXCLUDED.subject_type,
  text=EXCLUDED.text,
  metadata=EXCLUDED.metadata,
  embedding_model=EXCLUDED.embedding_model,
  embedding_ref=EXCLUDED.embedding_ref,
  graph_edges=EXCLUDED.graph_edges,
  updated_at=now();

INSERT INTO review_ticket (
  review_ticket_id, object_id, source_record_id, review_type, reason, status, created_at
)
SELECT
  review_ticket_id,
  CASE WHEN object_id <> '' AND EXISTS (SELECT 1 FROM normalized_object n WHERE n.object_id = stage_review_ticket.object_id) THEN object_id ELSE NULL END,
  CASE WHEN source_record_id <> '' AND EXISTS (SELECT 1 FROM source_record s WHERE s.source_record_id = stage_review_ticket.source_record_id) THEN source_record_id ELSE NULL END,
  review_type,
  reason,
  status,
  COALESCE(created_at, now())
FROM stage_review_ticket
WHERE review_ticket_id <> ''
ON CONFLICT (review_ticket_id) DO UPDATE SET
  object_id=EXCLUDED.object_id,
  source_record_id=EXCLUDED.source_record_id,
  review_type=EXCLUDED.review_type,
  reason=EXCLUDED.reason,
  status=EXCLUDED.status;

COMMIT;
"""


def create_promotion_decision_load_plan(
    *,
    promotion_decisions_path: str | Path,
    index_records_path: str | Path | None = None,
    review_tickets_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    load_sql_name: str = "load-promotion-decisions.sql",
) -> dict[str, Any]:
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-promotion-load-"))
    promotion_rows = [_promotion_row(row) for row in _read_jsonl(Path(promotion_decisions_path))]
    index_rows = [_index_row(row) for row in _read_jsonl(Path(index_records_path))] if index_records_path else []
    review_rows = [_review_row(row) for row in _read_jsonl(Path(review_tickets_path))] if review_tickets_path else []

    promotion_csv = out / "promotion-decisions.csv"
    index_csv = out / "promotion-index-records.csv"
    review_csv = out / "promotion-review-tickets.csv"
    load_sql = out / load_sql_name
    _write_csv(promotion_csv, PROMOTION_COLUMNS, promotion_rows)
    _write_csv(index_csv, INDEX_COLUMNS, index_rows)
    _write_csv(review_csv, REVIEW_COLUMNS, review_rows)
    load_sql.write_text(_load_sql(promotion_csv, index_csv, review_csv), encoding="utf-8")

    report = {
        "ok": True,
        "generated_at": _utc_now(),
        "promotion_decision_count": len(promotion_rows),
        "index_record_count": len(index_rows),
        "review_ticket_count": len(review_rows),
        "output_dir": str(out),
        "input_files": {
            "promotion_decisions": str(promotion_decisions_path),
            "index_records": str(index_records_path) if index_records_path else "",
            "review_tickets": str(review_tickets_path) if review_tickets_path else "",
        },
        "files": {
            "promotion_decisions_csv": str(promotion_csv),
            "promotion_index_records_csv": str(index_csv),
            "promotion_review_tickets_csv": str(review_csv),
            "load_sql": str(load_sql),
            "summary": str(out / "promotion-decision-load-plan.json"),
        },
        "safety_notes": [
            "This planner writes CSV and SQL only; it does not connect to Postgres.",
            "Promotion decisions are operational review signals, not automatic publication.",
            "Unresolved source or object references are loaded as nullable links while preserving ids in JSON/index rows.",
        ],
    }
    _write_json(out / "promotion-decision-load-plan.json", report)
    return report


def _self_test() -> int:
    source = Path("catalog/knowledge-packs/data/candidate-primitive-promotion-patterns/promotion-decisions.jsonl")
    if not source.exists():
        raise FileNotFoundError(source)
    with tempfile.TemporaryDirectory() as tmp:
        report = create_promotion_decision_load_plan(promotion_decisions_path=source, output_dir=tmp)
        assert report["promotion_decision_count"] > 0
        assert Path(report["files"]["load_sql"]).exists()
    print(json.dumps({
        "ok": True,
        "promotion_decision_count": report["promotion_decision_count"],
    }, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create CSV and psql load script for promotion decisions.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--promotion-decisions-path")
    parser.add_argument("--index-records-path")
    parser.add_argument("--review-tickets-path")
    parser.add_argument("--output-dir")
    parser.add_argument("--load-sql-name", default="load-promotion-decisions.sql")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.promotion_decisions_path:
        parser.error("--promotion-decisions-path is required unless --self-test is used")
    result = create_promotion_decision_load_plan(
        promotion_decisions_path=args.promotion_decisions_path,
        index_records_path=args.index_records_path,
        review_tickets_path=args.review_tickets_path,
        output_dir=args.output_dir,
        load_sql_name=args.load_sql_name,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
