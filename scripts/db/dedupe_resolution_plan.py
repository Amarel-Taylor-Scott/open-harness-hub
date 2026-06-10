#!/usr/bin/env python3
"""Plan review-gated dedupe resolution rows for generated candidates."""
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


def _members(cluster: dict[str, Any]) -> list[str]:
    value = cluster.get("member_ids")
    if isinstance(value, list):
        return [_str(item) for item in value if item]
    canonical = _str(cluster.get("canonical_object_id"))
    return [canonical] if canonical else []


def _decision_for_cluster(cluster: dict[str, Any], objects_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    members = _members(cluster)
    objects = [objects_by_id[item] for item in members if item in objects_by_id]
    hashes = {_str(obj.get("content_hash")) for obj in objects if obj.get("content_hash")}
    trust_tiers = {_str(obj.get("trust_tier")) for obj in objects if obj.get("trust_tier")}
    privacy = {_str(obj.get("privacy_boundary")) for obj in objects if obj.get("privacy_boundary")}
    scores = cluster.get("scores") if isinstance(cluster.get("scores"), dict) else {}
    exact_id = bool(scores.get("exact_id"))
    fuzzy_ratio = float(scores.get("fuzzy_ratio") or 0)

    action = "route_to_curator"
    review_status = "needs_curator_review"
    confidence = 0.5
    reason = "Cluster needs curator review before candidate publication."

    if len(members) == 1 and trust_tiers <= {"public"} and privacy <= {"public"}:
        action = "mark_singleton_resolved"
        review_status = "dedupe_resolved_content_review_required"
        confidence = 0.95
        reason = "Single public member cluster; dedupe is resolved but content approval remains required."
    elif len(members) > 1 and len(hashes) == 1 and hashes:
        action = "merge_exact_duplicates"
        review_status = "merge_review_required"
        confidence = 0.9
        reason = "Multiple members share the same content hash; exact duplicate merge requires review."
    elif len(members) > 1 and exact_id and fuzzy_ratio >= 0.98:
        action = "merge_exact_duplicates"
        review_status = "merge_review_required"
        confidence = 0.85
        reason = "Multiple members have exact id and high fuzzy match; merge requires review."

    return {
        "resolution_id": "dedupe-resolution/" + _str(cluster.get("dedupe_cluster_id")).replace("/", "-"),
        "dedupe_cluster_id": _str(cluster.get("dedupe_cluster_id")),
        "canonical_object_id": _str(cluster.get("canonical_object_id")),
        "member_ids": members,
        "resolution_action": action,
        "review_status": review_status,
        "confidence": confidence,
        "reason": reason,
        "evidence": {
            "cluster_status": cluster.get("status"),
            "merge_policy": cluster.get("merge_policy"),
            "methods": cluster.get("methods", []),
            "scores": scores,
            "member_count": len(members),
            "trust_tiers": sorted(trust_tiers),
            "privacy_boundaries": sorted(privacy),
            "content_hash_count": len(hashes),
        },
        "created_at": _utc_now(),
    }


RESOLUTION_COLUMNS = [
    "resolution_id",
    "dedupe_cluster_id",
    "canonical_object_id",
    "member_ids",
    "resolution_action",
    "review_status",
    "confidence",
    "reason",
    "evidence",
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
CANDIDATE_UPDATE_COLUMNS = [
    "component_candidate_id",
    "source_object_id",
    "dedupe_review_status",
    "dedupe_cluster_id",
    "resolution_id",
]


def _resolution_csv_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "resolution_id": _str(row.get("resolution_id")),
        "dedupe_cluster_id": _str(row.get("dedupe_cluster_id")),
        "canonical_object_id": _str(row.get("canonical_object_id")),
        "member_ids": _json(row.get("member_ids"), []),
        "resolution_action": _str(row.get("resolution_action")),
        "review_status": _str(row.get("review_status")),
        "confidence": _str(row.get("confidence")),
        "reason": _str(row.get("reason")),
        "evidence": _json(row.get("evidence"), {}),
        "created_at": _str(row.get("created_at")),
    }


def _index_row(row: dict[str, Any]) -> dict[str, str]:
    subject_id = _str(row.get("dedupe_cluster_id"))
    text = f"{row.get('resolution_action')} {row.get('review_status')} {row.get('reason')} {subject_id}"
    return {
        "index_record_id": "index/dedupe-resolution/" + subject_id.replace("/", "-"),
        "index_kind": "quality",
        "subject_id": subject_id,
        "subject_type": "dedupe_cluster",
        "text": text,
        "metadata": _json({
            "resolution_id": row.get("resolution_id"),
            "resolution_action": row.get("resolution_action"),
            "review_status": row.get("review_status"),
            "confidence": row.get("confidence"),
            "member_count": (row.get("evidence") or {}).get("member_count"),
        }, {}),
        "embedding_model": "",
        "embedding_ref": "",
        "graph_edges": _json([], []),
    }


def _review_row(row: dict[str, Any], objects_by_id: dict[str, dict[str, Any]]) -> dict[str, str]:
    canonical = _str(row.get("canonical_object_id"))
    obj = objects_by_id.get(canonical, {})
    return {
        "review_ticket_id": "review/dedupe-resolution/" + _str(row.get("dedupe_cluster_id")).replace("/", "-"),
        "object_id": canonical,
        "source_record_id": _str(obj.get("source_record_id")),
        "review_type": "dedupe_resolution",
        "reason": _str(row.get("reason")),
        "status": "open" if row.get("resolution_action") != "mark_singleton_resolved" else "content_review_required",
        "created_at": _str(row.get("created_at")),
    }


def _candidate_updates(
    resolutions: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    objects_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    candidate_by_object = {_str(row.get("source_object_id")): row for row in candidates if row.get("source_object_id")}
    rows: list[dict[str, str]] = []
    for resolution in resolutions:
        for object_id in resolution.get("member_ids") or []:
            candidate = candidate_by_object.get(_str(object_id))
            if not candidate:
                continue
            obj = objects_by_id.get(_str(object_id), {})
            rows.append({
                "component_candidate_id": _str(candidate.get("component_candidate_id")),
                "source_object_id": _str(object_id),
                "dedupe_review_status": _str(resolution.get("review_status")),
                "dedupe_cluster_id": _str(obj.get("dedupe_cluster_id") or resolution.get("dedupe_cluster_id")),
                "resolution_id": _str(resolution.get("resolution_id")),
            })
    return rows


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _load_sql(resolution_csv: Path, index_csv: Path, review_csv: Path, candidate_update_csv: Path) -> str:
    return f"""BEGIN;

CREATE TEMP TABLE stage_dedupe_resolution (
  resolution_id text,
  dedupe_cluster_id text,
  canonical_object_id text,
  member_ids jsonb,
  resolution_action text,
  review_status text,
  confidence numeric,
  reason text,
  evidence jsonb,
  created_at timestamptz
);

CREATE TEMP TABLE stage_dedupe_index_record (
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

CREATE TEMP TABLE stage_dedupe_review_ticket (
  review_ticket_id text,
  object_id text,
  source_record_id text,
  review_type text,
  reason text,
  status text,
  created_at timestamptz
);

CREATE TEMP TABLE stage_candidate_dedupe_update (
  component_candidate_id text,
  source_object_id text,
  dedupe_review_status text,
  dedupe_cluster_id text,
  resolution_id text
);

\\copy stage_dedupe_resolution FROM '{_sql_path(resolution_csv)}' WITH (FORMAT csv, HEADER true)
\\copy stage_dedupe_index_record FROM '{_sql_path(index_csv)}' WITH (FORMAT csv, HEADER true)
\\copy stage_dedupe_review_ticket FROM '{_sql_path(review_csv)}' WITH (FORMAT csv, HEADER true)
\\copy stage_candidate_dedupe_update FROM '{_sql_path(candidate_update_csv)}' WITH (FORMAT csv, HEADER true)

INSERT INTO dedupe_resolution (
  resolution_id, dedupe_cluster_id, canonical_object_id, member_ids,
  resolution_action, review_status, confidence, reason, evidence, created_at
)
SELECT
  resolution_id,
  dedupe_cluster_id,
  CASE WHEN canonical_object_id <> '' AND EXISTS (SELECT 1 FROM normalized_object n WHERE n.object_id = stage_dedupe_resolution.canonical_object_id) THEN canonical_object_id ELSE NULL END,
  COALESCE(member_ids, '[]'::jsonb),
  resolution_action,
  review_status,
  confidence,
  reason,
  COALESCE(evidence, '{{}}'::jsonb),
  COALESCE(created_at, now())
FROM stage_dedupe_resolution
WHERE resolution_id <> ''
ON CONFLICT (resolution_id) DO UPDATE SET
  dedupe_cluster_id=EXCLUDED.dedupe_cluster_id,
  canonical_object_id=EXCLUDED.canonical_object_id,
  member_ids=EXCLUDED.member_ids,
  resolution_action=EXCLUDED.resolution_action,
  review_status=EXCLUDED.review_status,
  confidence=EXCLUDED.confidence,
  reason=EXCLUDED.reason,
  evidence=EXCLUDED.evidence;

UPDATE dedupe_cluster c
SET status = CASE
  WHEN r.resolution_action = 'mark_singleton_resolved' THEN 'resolved_singleton'
  WHEN r.resolution_action = 'merge_exact_duplicates' THEN 'merge_review'
  WHEN r.resolution_action = 'reject_cluster' THEN 'rejected'
  ELSE 'review_required'
END
FROM stage_dedupe_resolution r
WHERE c.dedupe_cluster_id = r.dedupe_cluster_id;

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
FROM stage_dedupe_index_record
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
  CASE WHEN object_id <> '' AND EXISTS (SELECT 1 FROM normalized_object n WHERE n.object_id = stage_dedupe_review_ticket.object_id) THEN object_id ELSE NULL END,
  CASE WHEN source_record_id <> '' AND EXISTS (SELECT 1 FROM source_record s WHERE s.source_record_id = stage_dedupe_review_ticket.source_record_id) THEN source_record_id ELSE NULL END,
  review_type,
  reason,
  status,
  COALESCE(created_at, now())
FROM stage_dedupe_review_ticket
WHERE review_ticket_id <> ''
ON CONFLICT (review_ticket_id) DO UPDATE SET
  object_id=EXCLUDED.object_id,
  source_record_id=EXCLUDED.source_record_id,
  review_type=EXCLUDED.review_type,
  reason=EXCLUDED.reason,
  status=EXCLUDED.status;

UPDATE normalized_object n
SET review_status = s.dedupe_review_status
FROM stage_candidate_dedupe_update s
WHERE n.object_id = s.source_object_id
  AND s.dedupe_review_status <> '';

UPDATE component_candidate c
SET review_status = s.dedupe_review_status,
    body = jsonb_set(
      jsonb_set(COALESCE(c.body, '{{}}'::jsonb), '{{dedupe_cluster_id}}', to_jsonb(s.dedupe_cluster_id), true),
      '{{dedupe_resolution_id}}',
      to_jsonb(s.resolution_id),
      true
    )
FROM stage_candidate_dedupe_update s
WHERE c.component_candidate_id = s.component_candidate_id
  AND s.dedupe_review_status <> '';

COMMIT;
"""


def create_dedupe_resolution_plan(
    *,
    dedupe_clusters_path: str | Path,
    normalized_objects_path: str | Path,
    component_candidates_path: str | Path,
    output_dir: str | Path | None = None,
    load_sql_name: str = "load-dedupe-resolutions.sql",
) -> dict[str, Any]:
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-dedupe-resolution-"))
    clusters = _read_jsonl(Path(dedupe_clusters_path))
    objects = _read_jsonl(Path(normalized_objects_path))
    candidates = _read_jsonl(Path(component_candidates_path))
    objects_by_id = {_str(row.get("object_id")): row for row in objects if row.get("object_id")}

    resolutions = [_decision_for_cluster(cluster, objects_by_id) for cluster in clusters]
    indexes = [_index_row(row) for row in resolutions]
    reviews = [_review_row(row, objects_by_id) for row in resolutions]
    updates = _candidate_updates(resolutions, candidates, objects_by_id)

    action_counts: dict[str, int] = {}
    for row in resolutions:
        action = _str(row.get("resolution_action"))
        action_counts[action] = action_counts.get(action, 0) + 1

    resolution_jsonl = out / "dedupe-resolutions.jsonl"
    resolution_csv = out / "dedupe-resolutions.csv"
    index_csv = out / "dedupe-index-records.csv"
    review_csv = out / "dedupe-review-tickets.csv"
    candidate_update_csv = out / "candidate-dedupe-review-updates.csv"
    load_sql = out / load_sql_name

    _write_jsonl(resolution_jsonl, resolutions)
    _write_csv(resolution_csv, RESOLUTION_COLUMNS, [_resolution_csv_row(row) for row in resolutions])
    _write_csv(index_csv, INDEX_COLUMNS, indexes)
    _write_csv(review_csv, REVIEW_COLUMNS, reviews)
    _write_csv(candidate_update_csv, CANDIDATE_UPDATE_COLUMNS, updates)
    load_sql.write_text(_load_sql(resolution_csv, index_csv, review_csv, candidate_update_csv), encoding="utf-8")

    report = {
        "ok": True,
        "generated_at": _utc_now(),
        "dedupe_cluster_count": len(clusters),
        "normalized_object_count": len(objects),
        "component_candidate_count": len(candidates),
        "dedupe_resolution_count": len(resolutions),
        "index_record_count": len(indexes),
        "review_ticket_count": len(reviews),
        "candidate_dedupe_update_count": len(updates),
        "action_counts": action_counts,
        "output_dir": str(out),
        "files": {
            "dedupe_resolutions_jsonl": str(resolution_jsonl),
            "dedupe_resolutions_csv": str(resolution_csv),
            "dedupe_index_records_csv": str(index_csv),
            "dedupe_review_tickets_csv": str(review_csv),
            "candidate_dedupe_review_updates_csv": str(candidate_update_csv),
            "load_sql": str(load_sql),
            "summary": str(out / "dedupe-resolution-plan.json"),
        },
        "safety_notes": [
            "Singleton public clusters can be marked dedupe-resolved, but content approval remains separate.",
            "No row is promoted to active components by this planner.",
            "Planning emits files only; database execution is separate.",
        ],
    }
    _write_json(out / "dedupe-resolution-plan.json", report)
    return report


def _self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        clusters = base / "clusters.jsonl"
        objects = base / "objects.jsonl"
        candidates = base / "candidates.jsonl"
        clusters.write_text(json.dumps({
            "dedupe_cluster_id": "dedupe/test/1",
            "canonical_object_id": "object/test/1",
            "member_ids": ["object/test/1"],
            "status": "review_required",
            "scores": {"exact_id": True, "fuzzy_ratio": 1.0},
        }) + "\n", encoding="utf-8")
        objects.write_text(json.dumps({
            "object_id": "object/test/1",
            "dedupe_cluster_id": "dedupe/test/1",
            "content_hash": "abc",
            "trust_tier": "public",
            "privacy_boundary": "public",
            "source_record_id": "source/test/1",
        }) + "\n", encoding="utf-8")
        candidates.write_text(json.dumps({
            "component_candidate_id": "component-candidate/object/test/1",
            "source_object_id": "object/test/1",
        }) + "\n", encoding="utf-8")
        report = create_dedupe_resolution_plan(
            dedupe_clusters_path=clusters,
            normalized_objects_path=objects,
            component_candidates_path=candidates,
            output_dir=base / "out",
        )
        assert report["dedupe_resolution_count"] == 1
        assert report["candidate_dedupe_update_count"] == 1
        assert report["action_counts"]["mark_singleton_resolved"] == 1
        assert Path(report["files"]["load_sql"]).exists()
    print(json.dumps({"ok": True, "dedupe_resolution_count": report["dedupe_resolution_count"]}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create CSV and SQL load bundle for dedupe resolution decisions.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--dedupe-clusters-path")
    parser.add_argument("--normalized-objects-path")
    parser.add_argument("--component-candidates-path")
    parser.add_argument("--output-dir")
    parser.add_argument("--load-sql-name", default="load-dedupe-resolutions.sql")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.dedupe_clusters_path:
        parser.error("--dedupe-clusters-path is required unless --self-test is used")
    if not args.normalized_objects_path:
        parser.error("--normalized-objects-path is required unless --self-test is used")
    if not args.component_candidates_path:
        parser.error("--component-candidates-path is required unless --self-test is used")
    result = create_dedupe_resolution_plan(
        dedupe_clusters_path=args.dedupe_clusters_path,
        normalized_objects_path=args.normalized_objects_path,
        component_candidates_path=args.component_candidates_path,
        output_dir=args.output_dir,
        load_sql_name=args.load_sql_name,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
