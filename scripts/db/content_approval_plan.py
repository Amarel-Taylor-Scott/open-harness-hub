#!/usr/bin/env python3
"""Plan content approval decisions after dedupe resolution."""
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


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def _json(value: Any, default: Any) -> str:
    return json.dumps(value if value is not None else default, sort_keys=True, ensure_ascii=False)


def _str(value: Any) -> str:
    return "" if value is None else str(value)


def _sql_path(path: Path) -> str:
    return str(path).replace("'", "''")


def _body(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("body")
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value]
    return []


def _criteria(candidate: dict[str, Any], obj: dict[str, Any], resolution: dict[str, Any] | None) -> dict[str, float]:
    body = _body(candidate) or _body(obj)
    stages = _list(body.get("required_stages"))
    labels = _list(body.get("label_paths"))
    source_patterns = _list(body.get("source_patterns"))
    review_triggers = _list(body.get("review_triggers"))
    resolution_confidence = float((resolution or {}).get("confidence") or 0.0)
    return {
        "dedupe_confidence": round(resolution_confidence, 3),
        "source_publicness": 1.0 if candidate.get("trust_tier") == "public" and candidate.get("privacy_boundary") == "public" else 0.0,
        "stage_completeness": round(min(1.0, len(stages) / 8.0), 3),
        "label_coverage": round(min(1.0, len(labels) / 3.0), 3),
        "source_pattern_coverage": round(min(1.0, len(source_patterns) / 3.0), 3),
        "review_risk": round(min(1.0, len(review_triggers) / 2.0), 3),
    }


def _approval_for_candidate(
    candidate: dict[str, Any],
    obj: dict[str, Any],
    resolution: dict[str, Any] | None,
) -> dict[str, Any]:
    object_id = _str(candidate.get("source_object_id"))
    body = _body(candidate)
    criteria = _criteria(candidate, obj, resolution)
    risk_flags: list[str] = []
    review_reasons: list[str] = []

    if not resolution:
        risk_flags.append("missing_dedupe_resolution")
        review_reasons.append("Candidate has no dedupe resolution row.")
    elif resolution.get("resolution_action") != "mark_singleton_resolved":
        risk_flags.append("dedupe_not_clear")
        review_reasons.append("Dedupe resolution does not clear this candidate for content review.")
    if candidate.get("privacy_boundary") != "public":
        risk_flags.append("privacy_review")
        review_reasons.append("Privacy boundary must be reviewed before promotion.")
    if candidate.get("trust_tier") != "public":
        risk_flags.append("trust_tier_review")
        review_reasons.append("Trust tier is not public.")
    if "insurance" in _list(body.get("excluded_scopes")):
        # This is an exclusion control, not a promotion blocker.
        pass
    if _str(candidate.get("review_status")) not in {"approved", "passed_review", "dedupe_resolved_content_review_required"}:
        risk_flags.append("content_review_required")
        review_reasons.append("Content has not been explicitly approved.")

    confidence = round(
        0.2 * criteria["dedupe_confidence"]
        + 0.2 * criteria["source_publicness"]
        + 0.2 * criteria["stage_completeness"]
        + 0.15 * criteria["label_coverage"]
        + 0.15 * criteria["source_pattern_coverage"]
        + 0.1 * (1.0 - criteria["review_risk"]),
        3,
    )
    if not risk_flags and confidence >= 0.72:
        decision = "approve_for_promotion"
    elif confidence >= 0.55:
        decision = "review_before_promotion"
    elif confidence >= 0.35:
        decision = "hold"
    else:
        decision = "reject"

    promotion_decision = "promote_candidate" if decision == "approve_for_promotion" else decision
    approval_id = "content-approval/" + object_id.replace("/", "-")
    promotion_decision_id = "promotion/content-approval/" + object_id.replace("/", "-")
    return {
        "approval_id": approval_id,
        "object_id": object_id,
        "component_candidate_id": _str(candidate.get("component_candidate_id")),
        "dedupe_resolution_id": _str((resolution or {}).get("resolution_id")),
        "decision": decision,
        "confidence": confidence,
        "criteria": criteria,
        "risk_flags": sorted(set(risk_flags)),
        "review_reasons": review_reasons,
        "promotion_decision_id": promotion_decision_id,
        "promotion_decision": {
            "decision_id": promotion_decision_id,
            "object_id": object_id,
            "source_record_id": _str(obj.get("source_record_id")),
            "score": round(confidence * 100, 2),
            "max_score": 100.0,
            "decision": promotion_decision,
            "criteria": criteria,
            "risk_flags": sorted(set(risk_flags)),
            "review_reasons": review_reasons,
            "recommended_outputs": ["component_candidate", "subcomponent_candidate", "index_record", "review_ticket"],
            "created_at": _utc_now(),
        },
        "created_at": _utc_now(),
    }


APPROVAL_COLUMNS = [
    "approval_id",
    "object_id",
    "component_candidate_id",
    "dedupe_resolution_id",
    "decision",
    "confidence",
    "criteria",
    "risk_flags",
    "review_reasons",
    "promotion_decision_id",
    "created_at",
]
PROMOTION_COLUMNS = [
    "decision_id",
    "object_id",
    "source_record_id",
    "score",
    "max_score",
    "decision",
    "criteria",
    "risk_flags",
    "review_reasons",
    "recommended_outputs",
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


def _approval_csv_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "approval_id": _str(row.get("approval_id")),
        "object_id": _str(row.get("object_id")),
        "component_candidate_id": _str(row.get("component_candidate_id")),
        "dedupe_resolution_id": _str(row.get("dedupe_resolution_id")),
        "decision": _str(row.get("decision")),
        "confidence": _str(row.get("confidence")),
        "criteria": _json(row.get("criteria"), {}),
        "risk_flags": _json(row.get("risk_flags"), []),
        "review_reasons": _json(row.get("review_reasons"), []),
        "promotion_decision_id": _str(row.get("promotion_decision_id")),
        "created_at": _str(row.get("created_at")),
    }


def _promotion_csv_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "decision_id": _str(row.get("decision_id")),
        "object_id": _str(row.get("object_id")),
        "source_record_id": _str(row.get("source_record_id")),
        "score": _str(row.get("score")),
        "max_score": _str(row.get("max_score") or 100.0),
        "decision": _str(row.get("decision")),
        "criteria": _json(row.get("criteria"), {}),
        "risk_flags": _json(row.get("risk_flags"), []),
        "review_reasons": _json(row.get("review_reasons"), []),
        "recommended_outputs": _json(row.get("recommended_outputs"), []),
        "created_at": _str(row.get("created_at")),
    }


def _index_row(approval: dict[str, Any]) -> dict[str, str]:
    text = " ".join([
        _str(approval.get("object_id")),
        _str(approval.get("decision")),
        " ".join(approval.get("risk_flags") or []),
        " ".join(approval.get("review_reasons") or []),
    ])
    return {
        "index_record_id": "index/content-approval/" + _str(approval.get("object_id")).replace("/", "-"),
        "index_kind": "quality",
        "subject_id": _str(approval.get("object_id")),
        "subject_type": "content_approval_decision",
        "text": text,
        "metadata": _json({
            "approval_id": approval.get("approval_id"),
            "decision": approval.get("decision"),
            "confidence": approval.get("confidence"),
            "risk_flags": approval.get("risk_flags", []),
            "promotion_decision_id": approval.get("promotion_decision_id"),
        }, {}),
        "embedding_model": "",
        "embedding_ref": "",
        "graph_edges": _json([], []),
    }


def _review_row(approval: dict[str, Any], obj: dict[str, Any]) -> dict[str, str] | None:
    if approval.get("decision") == "approve_for_promotion":
        return None
    return {
        "review_ticket_id": "review/content-approval/" + _str(approval.get("object_id")).replace("/", "-"),
        "object_id": _str(approval.get("object_id")),
        "source_record_id": _str(obj.get("source_record_id")),
        "review_type": "content_approval",
        "reason": " ".join(approval.get("review_reasons") or ["Content approval requires curator review."]),
        "status": "open",
        "created_at": _str(approval.get("created_at")),
    }


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _load_sql(approval_csv: Path, promotion_csv: Path, index_csv: Path, review_csv: Path) -> str:
    return f"""BEGIN;

CREATE TEMP TABLE stage_content_approval_decision (
  approval_id text,
  object_id text,
  component_candidate_id text,
  dedupe_resolution_id text,
  decision text,
  confidence numeric,
  criteria jsonb,
  risk_flags jsonb,
  review_reasons jsonb,
  promotion_decision_id text,
  created_at timestamptz
);

CREATE TEMP TABLE stage_content_promotion_decision (
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

CREATE TEMP TABLE stage_content_index_record (
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

CREATE TEMP TABLE stage_content_review_ticket (
  review_ticket_id text,
  object_id text,
  source_record_id text,
  review_type text,
  reason text,
  status text,
  created_at timestamptz
);

\\copy stage_content_approval_decision FROM '{_sql_path(approval_csv)}' WITH (FORMAT csv, HEADER true)
\\copy stage_content_promotion_decision FROM '{_sql_path(promotion_csv)}' WITH (FORMAT csv, HEADER true)
\\copy stage_content_index_record FROM '{_sql_path(index_csv)}' WITH (FORMAT csv, HEADER true)
\\copy stage_content_review_ticket FROM '{_sql_path(review_csv)}' WITH (FORMAT csv, HEADER true)

INSERT INTO promotion_decision (
  decision_id, object_id, source_record_id, score, max_score, decision,
  criteria, risk_flags, review_reasons, recommended_outputs, created_at
)
SELECT
  decision_id,
  CASE WHEN object_id <> '' AND EXISTS (SELECT 1 FROM normalized_object n WHERE n.object_id = stage_content_promotion_decision.object_id) THEN object_id ELSE NULL END,
  CASE WHEN source_record_id <> '' AND EXISTS (SELECT 1 FROM source_record s WHERE s.source_record_id = stage_content_promotion_decision.source_record_id) THEN source_record_id ELSE NULL END,
  score,
  COALESCE(max_score, 100),
  decision,
  COALESCE(criteria, '{{}}'::jsonb),
  COALESCE(risk_flags, '[]'::jsonb),
  COALESCE(review_reasons, '[]'::jsonb),
  COALESCE(recommended_outputs, '[]'::jsonb),
  COALESCE(created_at, now())
FROM stage_content_promotion_decision
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

INSERT INTO content_approval_decision (
  approval_id, object_id, component_candidate_id, dedupe_resolution_id,
  decision, confidence, criteria, risk_flags, review_reasons,
  promotion_decision_id, created_at
)
SELECT
  approval_id,
  CASE WHEN object_id <> '' AND EXISTS (SELECT 1 FROM normalized_object n WHERE n.object_id = stage_content_approval_decision.object_id) THEN object_id ELSE NULL END,
  CASE WHEN component_candidate_id <> '' AND EXISTS (SELECT 1 FROM component_candidate c WHERE c.component_candidate_id = stage_content_approval_decision.component_candidate_id) THEN component_candidate_id ELSE NULL END,
  CASE WHEN dedupe_resolution_id <> '' AND EXISTS (SELECT 1 FROM dedupe_resolution d WHERE d.resolution_id = stage_content_approval_decision.dedupe_resolution_id) THEN dedupe_resolution_id ELSE NULL END,
  decision,
  confidence,
  COALESCE(criteria, '{{}}'::jsonb),
  COALESCE(risk_flags, '[]'::jsonb),
  COALESCE(review_reasons, '[]'::jsonb),
  CASE WHEN promotion_decision_id <> '' AND EXISTS (SELECT 1 FROM promotion_decision p WHERE p.decision_id = stage_content_approval_decision.promotion_decision_id) THEN promotion_decision_id ELSE NULL END,
  COALESCE(created_at, now())
FROM stage_content_approval_decision
WHERE approval_id <> ''
ON CONFLICT (approval_id) DO UPDATE SET
  object_id=EXCLUDED.object_id,
  component_candidate_id=EXCLUDED.component_candidate_id,
  dedupe_resolution_id=EXCLUDED.dedupe_resolution_id,
  decision=EXCLUDED.decision,
  confidence=EXCLUDED.confidence,
  criteria=EXCLUDED.criteria,
  risk_flags=EXCLUDED.risk_flags,
  review_reasons=EXCLUDED.review_reasons,
  promotion_decision_id=EXCLUDED.promotion_decision_id;

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
FROM stage_content_index_record
WHERE index_record_id <> ''
ON CONFLICT (index_record_id) DO UPDATE SET
  index_kind=EXCLUDED.index_kind,
  subject_id=EXCLUDED.subject_id,
  subject_type=EXCLUDED.subject_type,
  text=EXCLUDED.text,
  metadata=EXCLUDED.metadata,
  updated_at=now();

INSERT INTO review_ticket (
  review_ticket_id, object_id, source_record_id, review_type, reason, status, created_at
)
SELECT
  review_ticket_id,
  CASE WHEN object_id <> '' AND EXISTS (SELECT 1 FROM normalized_object n WHERE n.object_id = stage_content_review_ticket.object_id) THEN object_id ELSE NULL END,
  CASE WHEN source_record_id <> '' AND EXISTS (SELECT 1 FROM source_record s WHERE s.source_record_id = stage_content_review_ticket.source_record_id) THEN source_record_id ELSE NULL END,
  review_type,
  reason,
  status,
  COALESCE(created_at, now())
FROM stage_content_review_ticket
WHERE review_ticket_id <> ''
ON CONFLICT (review_ticket_id) DO UPDATE SET
  object_id=EXCLUDED.object_id,
  source_record_id=EXCLUDED.source_record_id,
  review_type=EXCLUDED.review_type,
  reason=EXCLUDED.reason,
  status=EXCLUDED.status;

UPDATE component_candidate c
SET review_status = CASE
    WHEN a.decision = 'approve_for_promotion' THEN 'approved'
    WHEN a.decision = 'review_before_promotion' THEN 'content_review_required'
    ELSE a.decision
  END,
  promotion_state = CASE
    WHEN a.decision = 'approve_for_promotion' THEN 'review'
    WHEN a.decision = 'reject' THEN 'rejected'
    ELSE c.promotion_state
  END
FROM stage_content_approval_decision a
WHERE c.component_candidate_id = a.component_candidate_id;

COMMIT;
"""


def create_content_approval_plan(
    *,
    component_candidates_path: str | Path,
    normalized_objects_path: str | Path,
    dedupe_resolutions_path: str | Path,
    output_dir: str | Path | None = None,
    load_sql_name: str = "load-content-approvals.sql",
) -> dict[str, Any]:
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-content-approval-"))
    candidates = _read_jsonl(Path(component_candidates_path))
    objects = _read_jsonl(Path(normalized_objects_path))
    resolutions = _read_jsonl(Path(dedupe_resolutions_path))
    objects_by_id = {_str(row.get("object_id")): row for row in objects if row.get("object_id")}
    resolution_by_object: dict[str, dict[str, Any]] = {}
    for resolution in resolutions:
        for member_id in resolution.get("member_ids") or []:
            resolution_by_object[_str(member_id)] = resolution

    approvals = [
        _approval_for_candidate(candidate, objects_by_id.get(_str(candidate.get("source_object_id")), {}), resolution_by_object.get(_str(candidate.get("source_object_id"))))
        for candidate in candidates
    ]
    promotions = [approval["promotion_decision"] for approval in approvals]
    indexes = [_index_row(approval) for approval in approvals]
    reviews = [
        ticket
        for approval in approvals
        if (ticket := _review_row(approval, objects_by_id.get(_str(approval.get("object_id")), {}))) is not None
    ]

    decision_counts: dict[str, int] = {}
    for approval in approvals:
        decision = _str(approval.get("decision"))
        decision_counts[decision] = decision_counts.get(decision, 0) + 1

    approval_jsonl = out / "content-approval-decisions.jsonl"
    promotion_jsonl = out / "content-promotion-decisions.jsonl"
    approval_csv = out / "content-approval-decisions.csv"
    promotion_csv = out / "content-promotion-decisions.csv"
    index_csv = out / "content-approval-index-records.csv"
    review_csv = out / "content-approval-review-tickets.csv"
    load_sql = out / load_sql_name
    _write_jsonl(approval_jsonl, approvals)
    _write_jsonl(promotion_jsonl, promotions)
    _write_csv(approval_csv, APPROVAL_COLUMNS, [_approval_csv_row(row) for row in approvals])
    _write_csv(promotion_csv, PROMOTION_COLUMNS, [_promotion_csv_row(row) for row in promotions])
    _write_csv(index_csv, INDEX_COLUMNS, indexes)
    _write_csv(review_csv, REVIEW_COLUMNS, reviews)
    load_sql.write_text(_load_sql(approval_csv, promotion_csv, index_csv, review_csv), encoding="utf-8")

    report = {
        "ok": True,
        "generated_at": _utc_now(),
        "component_candidate_count": len(candidates),
        "normalized_object_count": len(objects),
        "dedupe_resolution_count": len(resolutions),
        "content_approval_count": len(approvals),
        "promotion_decision_count": len(promotions),
        "index_record_count": len(indexes),
        "review_ticket_count": len(reviews),
        "decision_counts": decision_counts,
        "output_dir": str(out),
        "files": {
            "content_approval_decisions_jsonl": str(approval_jsonl),
            "content_promotion_decisions_jsonl": str(promotion_jsonl),
            "content_approval_decisions_csv": str(approval_csv),
            "content_promotion_decisions_csv": str(promotion_csv),
            "content_approval_index_records_csv": str(index_csv),
            "content_approval_review_tickets_csv": str(review_csv),
            "load_sql": str(load_sql),
            "summary": str(out / "content-approval-plan.json"),
        },
        "safety_notes": [
            "Dedupe clearance is required but does not imply content approval.",
            "Only approve_for_promotion decisions emit promote_candidate promotion decisions.",
            "This planner emits files only; database execution is separate.",
        ],
    }
    _write_json(out / "content-approval-plan.json", report)
    return report


def _self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        candidates = base / "candidates.jsonl"
        objects = base / "objects.jsonl"
        resolutions = base / "resolutions.jsonl"
        candidates.write_text(json.dumps({
            "component_candidate_id": "component-candidate/object/test/1",
            "source_object_id": "object/test/1",
            "review_status": "approved",
            "trust_tier": "public",
            "privacy_boundary": "public",
            "body": {
                "required_stages": ["source_governance", "source_discovery", "source_snapshot", "page_to_markdown", "source_ingest", "entity_linking", "fuzzy_dedupe", "publish_review"],
                "label_paths": ["object.fact", "source.public", "vertical.test"],
                "source_patterns": ["public registry", "official form", "public dataset"],
            },
        }) + "\n", encoding="utf-8")
        objects.write_text(json.dumps({
            "object_id": "object/test/1",
            "source_record_id": "source/test/1",
        }) + "\n", encoding="utf-8")
        resolutions.write_text(json.dumps({
            "resolution_id": "dedupe-resolution/test-1",
            "member_ids": ["object/test/1"],
            "resolution_action": "mark_singleton_resolved",
            "confidence": 0.95,
        }) + "\n", encoding="utf-8")
        report = create_content_approval_plan(
            component_candidates_path=candidates,
            normalized_objects_path=objects,
            dedupe_resolutions_path=resolutions,
            output_dir=base / "out",
        )
        assert report["content_approval_count"] == 1
        assert report["decision_counts"]["approve_for_promotion"] == 1
        assert Path(report["files"]["load_sql"]).exists()
    print(json.dumps({"ok": True, "content_approval_count": report["content_approval_count"]}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create CSV and SQL load bundle for content approval decisions.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--component-candidates-path")
    parser.add_argument("--normalized-objects-path")
    parser.add_argument("--dedupe-resolutions-path")
    parser.add_argument("--output-dir")
    parser.add_argument("--load-sql-name", default="load-content-approvals.sql")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.component_candidates_path:
        parser.error("--component-candidates-path is required unless --self-test is used")
    if not args.normalized_objects_path:
        parser.error("--normalized-objects-path is required unless --self-test is used")
    if not args.dedupe_resolutions_path:
        parser.error("--dedupe-resolutions-path is required unless --self-test is used")
    result = create_content_approval_plan(
        component_candidates_path=args.component_candidates_path,
        normalized_objects_path=args.normalized_objects_path,
        dedupe_resolutions_path=args.dedupe_resolutions_path,
        output_dir=args.output_dir,
        load_sql_name=args.load_sql_name,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
