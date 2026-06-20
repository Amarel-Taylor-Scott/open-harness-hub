#!/usr/bin/env python3
"""Create a review-gated load bundle for approved active components."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import tempfile
import time
from pathlib import Path
from typing import Any


ALLOWED_COMPONENT_TYPES = {
    "harness",
    "pipeline",
    "benchmark",
    "rule-pack",
    "knowledge-pack",
    "logic-pack",
    "tool",
    "persona",
    "adapter",
    "rubric",
    "dataset",
    "schema",
}
PROMOTE_DECISIONS = {"promote_candidate"}
STATE_BY_DECISION = {
    "promote_candidate": "promoted",
    "review_before_promotion": "review",
    "hold": "held",
    "reject": "rejected",
}


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


def _slug(value: str, fallback: str) -> str:
    raw = value or fallback
    slug = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
    if not slug:
        slug = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return slug[:64].strip("-") or slug[:16]


def _target_type(candidate: dict[str, Any]) -> str:
    declared = _str(candidate.get("component_type"))
    if declared in ALLOWED_COMPONENT_TYPES:
        return declared
    body = candidate.get("body") if isinstance(candidate.get("body"), dict) else {}
    primitive = _str(body.get("candidate_primitive"))
    if primitive in {"rubric", "criterion", "evaluation_check"}:
        return "rubric"
    if primitive in {"pipeline", "workflow", "deployment_blueprint"}:
        return "pipeline"
    if primitive in {"tool", "connector", "adapter_call"}:
        return "tool"
    if primitive in {"rule", "policy_rule", "guardrail"}:
        return "rule-pack"
    return "knowledge-pack"


def _component_id(candidate: dict[str, Any], target_type: str) -> str:
    body = candidate.get("body") if isinstance(candidate.get("body"), dict) else {}
    seed = _str(body.get("blueprint_id")) + "-" + _str(body.get("candidate_primitive"))
    if seed == "-":
        seed = _str(candidate.get("source_object_id")) or _str(candidate.get("component_candidate_id"))
    return f"{target_type}/{_slug(seed, 'generated-component')}"


def _safe_review(candidate: dict[str, Any], decision: dict[str, Any]) -> bool:
    if decision.get("decision") not in PROMOTE_DECISIONS:
        return False
    if decision.get("risk_flags"):
        return False
    if decision.get("review_reasons"):
        return False
    return _str(candidate.get("review_status")) in {"", "approved", "passed_review"}


COMPONENT_COLUMNS = [
    "id",
    "type",
    "component_layer",
    "control_flow_kind",
    "version",
    "name",
    "description",
    "license",
    "lifecycle",
    "trust_boundary",
    "freshness",
    "created",
    "updated",
    "attribution",
    "links",
    "body",
]
VERSION_COLUMNS = [
    "component_version_id",
    "component_id",
    "version",
    "version_status",
    "change_summary",
    "definition_source",
    "source_ref",
    "definition_hash",
    "body",
]
SUBCOMPONENT_COLUMNS = [
    "subcomponent_id",
    "component_id",
    "parent_object_id",
    "subcomponent_type",
    "name",
    "body",
    "source_record_id",
    "trust_tier",
    "privacy_boundary",
    "freshness",
    "content_hash",
    "review_status",
]
STATE_COLUMNS = [
    "component_candidate_id",
    "promotion_state",
    "promoted_component_id",
    "decision_id",
    "decision",
]


def _component_row(candidate: dict[str, Any], decision: dict[str, Any], component_id: str, target_type: str) -> dict[str, str]:
    body = candidate.get("body") if isinstance(candidate.get("body"), dict) else {}
    promoted_body = {
        "source_candidate": candidate,
        "promotion_decision": decision,
        "generated_by": "approved_component_promotion_plan",
    }
    return {
        "id": component_id,
        "type": target_type,
        "component_layer": _str(candidate.get("component_layer")),
        "control_flow_kind": _str(candidate.get("control_flow_kind")),
        "version": "0.1.0",
        "name": _str(candidate.get("name")) or component_id,
        "description": f"Review-approved generated component from {_str(candidate.get('source_object_id'))}.",
        "license": "CC-BY-4.0",
        "lifecycle": "experimental",
        "trust_boundary": "local",
        "freshness": "stable",
        "created": "2026-05-26",
        "updated": "2026-05-26",
        "attribution": _json({"source_object_id": candidate.get("source_object_id")}, {}),
        "links": _json({"source_record_id": body.get("source_record_id", decision.get("source_record_id"))}, {}),
        "body": _json(promoted_body, {}),
    }


def _version_row(candidate: dict[str, Any], decision: dict[str, Any], component_id: str) -> dict[str, str]:
    body = {
        "source_candidate_id": candidate.get("component_candidate_id"),
        "source_object_id": candidate.get("source_object_id"),
        "decision_id": decision.get("decision_id"),
        "decision_score": decision.get("score"),
        "component_body": candidate.get("body") if isinstance(candidate.get("body"), dict) else {},
    }
    definition_hash = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    return {
        "component_version_id": f"{component_id}@0.1.0",
        "component_id": component_id,
        "version": "0.1.0",
        "version_status": "active",
        "change_summary": "Initial review-approved generated component version.",
        "definition_source": "generated_factory",
        "source_ref": _str(candidate.get("component_candidate_id")),
        "definition_hash": definition_hash,
        "body": _json(body, {}),
    }


def _subcomponent_row(row: dict[str, Any], component_id: str) -> dict[str, str]:
    return {
        "subcomponent_id": "subcomponent/" + _slug(_str(row.get("subcomponent_candidate_id")), "generated-subcomponent"),
        "component_id": component_id,
        "parent_object_id": _str(row.get("parent_object_id")),
        "subcomponent_type": _str(row.get("subcomponent_type")),
        "name": _str(row.get("name")),
        "body": _json(row.get("body"), {}),
        "source_record_id": "",
        "trust_tier": "",
        "privacy_boundary": "",
        "freshness": "",
        "content_hash": _str(row.get("content_hash")),
        "review_status": _str(row.get("review_status") or "approved"),
    }


def _state_row(candidate: dict[str, Any], decision: dict[str, Any], component_id: str | None) -> dict[str, str]:
    decision_name = _str(decision.get("decision"))
    return {
        "component_candidate_id": _str(candidate.get("component_candidate_id")),
        "promotion_state": STATE_BY_DECISION.get(decision_name, "review"),
        "promoted_component_id": component_id or "",
        "decision_id": _str(decision.get("decision_id")),
        "decision": decision_name,
    }


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _load_sql(component_csv: Path, version_csv: Path, subcomponent_csv: Path, state_csv: Path) -> str:
    return f"""BEGIN;

CREATE TEMP TABLE stage_approved_component (
  id text,
  type text,
  component_layer text,
  control_flow_kind text,
  version text,
  name text,
  description text,
  license text,
  lifecycle text,
  trust_boundary text,
  freshness text,
  created date,
  updated date,
  attribution jsonb,
  links jsonb,
  body jsonb
);

CREATE TEMP TABLE stage_approved_component_version (
  component_version_id text,
  component_id text,
  version text,
  version_status text,
  change_summary text,
  definition_source text,
  source_ref text,
  definition_hash text,
  body jsonb
);

CREATE TEMP TABLE stage_approved_subcomponent (
  subcomponent_id text,
  component_id text,
  parent_object_id text,
  subcomponent_type text,
  name text,
  body jsonb,
  source_record_id text,
  trust_tier text,
  privacy_boundary text,
  freshness text,
  content_hash text,
  review_status text
);

CREATE TEMP TABLE stage_candidate_state_update (
  component_candidate_id text,
  promotion_state text,
  promoted_component_id text,
  decision_id text,
  decision text
);

\\copy stage_approved_component FROM '{_sql_path(component_csv)}' WITH (FORMAT csv, HEADER true)
\\copy stage_approved_component_version FROM '{_sql_path(version_csv)}' WITH (FORMAT csv, HEADER true)
\\copy stage_approved_subcomponent FROM '{_sql_path(subcomponent_csv)}' WITH (FORMAT csv, HEADER true)
\\copy stage_candidate_state_update FROM '{_sql_path(state_csv)}' WITH (FORMAT csv, HEADER true)

INSERT INTO component (
  id, type, component_layer, control_flow_kind, version, name, description,
  license, lifecycle, trust_boundary, freshness, created, updated,
  attribution, links, body
)
SELECT
  id,
  type,
  NULLIF(component_layer, ''),
  NULLIF(control_flow_kind, ''),
  version,
  name,
  description,
  license,
  lifecycle,
  NULLIF(trust_boundary, ''),
  NULLIF(freshness, ''),
  created,
  updated,
  COALESCE(attribution, '{{}}'::jsonb),
  COALESCE(links, '{{}}'::jsonb),
  COALESCE(body, '{{}}'::jsonb)
FROM stage_approved_component
WHERE id <> ''
ON CONFLICT (id) DO UPDATE SET
  type=EXCLUDED.type,
  component_layer=EXCLUDED.component_layer,
  control_flow_kind=EXCLUDED.control_flow_kind,
  version=EXCLUDED.version,
  name=EXCLUDED.name,
  description=EXCLUDED.description,
  license=EXCLUDED.license,
  lifecycle=EXCLUDED.lifecycle,
  trust_boundary=EXCLUDED.trust_boundary,
  freshness=EXCLUDED.freshness,
  updated=EXCLUDED.updated,
  attribution=EXCLUDED.attribution,
  links=EXCLUDED.links,
  body=EXCLUDED.body;

INSERT INTO component_version (
  component_version_id, component_id, version, version_status,
  change_summary, definition_source, source_ref, definition_hash, body, activated_at
)
SELECT
  component_version_id,
  component_id,
  version,
  version_status,
  NULLIF(change_summary, ''),
  NULLIF(definition_source, ''),
  NULLIF(source_ref, ''),
  NULLIF(definition_hash, ''),
  COALESCE(body, '{{}}'::jsonb),
  now()
FROM stage_approved_component_version
WHERE component_version_id <> ''
ON CONFLICT (component_version_id) DO UPDATE SET
  version_status=EXCLUDED.version_status,
  change_summary=EXCLUDED.change_summary,
  definition_source=EXCLUDED.definition_source,
  source_ref=EXCLUDED.source_ref,
  definition_hash=EXCLUDED.definition_hash,
  body=EXCLUDED.body;

INSERT INTO subcomponent (
  subcomponent_id, component_id, parent_object_id, subcomponent_type, name,
  body, source_record_id, trust_tier, privacy_boundary, freshness,
  content_hash, review_status
)
SELECT
  subcomponent_id,
  component_id,
  NULLIF(parent_object_id, ''),
  subcomponent_type,
  NULLIF(name, ''),
  COALESCE(body, '{{}}'::jsonb),
  CASE WHEN source_record_id <> '' AND EXISTS (SELECT 1 FROM source_record s WHERE s.source_record_id = stage_approved_subcomponent.source_record_id) THEN source_record_id ELSE NULL END,
  NULLIF(trust_tier, ''),
  NULLIF(privacy_boundary, ''),
  NULLIF(freshness, ''),
  NULLIF(content_hash, ''),
  NULLIF(review_status, '')
FROM stage_approved_subcomponent
WHERE subcomponent_id <> ''
ON CONFLICT (subcomponent_id) DO UPDATE SET
  component_id=EXCLUDED.component_id,
  parent_object_id=EXCLUDED.parent_object_id,
  subcomponent_type=EXCLUDED.subcomponent_type,
  name=EXCLUDED.name,
  body=EXCLUDED.body,
  source_record_id=EXCLUDED.source_record_id,
  trust_tier=EXCLUDED.trust_tier,
  privacy_boundary=EXCLUDED.privacy_boundary,
  freshness=EXCLUDED.freshness,
  content_hash=EXCLUDED.content_hash,
  review_status=EXCLUDED.review_status;

UPDATE component_candidate c
SET promotion_state = s.promotion_state,
    promoted_component_id = NULLIF(s.promoted_component_id, '')
FROM stage_candidate_state_update s
WHERE c.component_candidate_id = s.component_candidate_id;

COMMIT;
"""


def create_approved_component_promotion_plan(
    *,
    component_candidates_path: str | Path,
    subcomponent_candidates_path: str | Path,
    promotion_decisions_path: str | Path,
    output_dir: str | Path | None = None,
    load_sql_name: str = "load-approved-components.sql",
) -> dict[str, Any]:
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-approved-component-promotion-"))
    candidates = _read_jsonl(Path(component_candidates_path))
    subcomponents = _read_jsonl(Path(subcomponent_candidates_path))
    decisions = _read_jsonl(Path(promotion_decisions_path))

    candidate_by_object = {_str(row.get("source_object_id")): row for row in candidates if row.get("source_object_id")}
    subcomponents_by_candidate: dict[str, list[dict[str, Any]]] = {}
    for row in subcomponents:
        candidate_id = _str(row.get("component_candidate_id"))
        if candidate_id:
            subcomponents_by_candidate.setdefault(candidate_id, []).append(row)

    component_rows: list[dict[str, str]] = []
    version_rows: list[dict[str, str]] = []
    subcomponent_rows: list[dict[str, str]] = []
    state_rows: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []

    for decision in decisions:
        candidate = candidate_by_object.get(_str(decision.get("object_id")))
        if not candidate:
            skipped.append({
                "object_id": _str(decision.get("object_id")),
                "decision_id": _str(decision.get("decision_id")),
                "reason": "candidate_not_found",
            })
            continue

        component_id: str | None = None
        if _safe_review(candidate, decision):
            target_type = _target_type(candidate)
            component_id = _component_id(candidate, target_type)
            component_rows.append(_component_row(candidate, decision, component_id, target_type))
            version_rows.append(_version_row(candidate, decision, component_id))
            for subcomponent in subcomponents_by_candidate.get(_str(candidate.get("component_candidate_id")), []):
                subcomponent_rows.append(_subcomponent_row(subcomponent, component_id))
        state_rows.append(_state_row(candidate, decision, component_id))

    component_csv = out / "components.csv"
    version_csv = out / "component-versions.csv"
    subcomponent_csv = out / "subcomponents.csv"
    state_csv = out / "candidate-state-updates.csv"
    load_sql = out / load_sql_name
    _write_csv(component_csv, COMPONENT_COLUMNS, component_rows)
    _write_csv(version_csv, VERSION_COLUMNS, version_rows)
    _write_csv(subcomponent_csv, SUBCOMPONENT_COLUMNS, subcomponent_rows)
    _write_csv(state_csv, STATE_COLUMNS, state_rows)
    load_sql.write_text(_load_sql(component_csv, version_csv, subcomponent_csv, state_csv), encoding="utf-8")

    decision_counts: dict[str, int] = {}
    for decision in decisions:
        name = _str(decision.get("decision") or "unknown")
        decision_counts[name] = decision_counts.get(name, 0) + 1

    report = {
        "ok": True,
        "generated_at": _utc_now(),
        "component_candidate_count": len(candidates),
        "subcomponent_candidate_count": len(subcomponents),
        "promotion_decision_count": len(decisions),
        "decision_counts": decision_counts,
        "approved_component_count": len(component_rows),
        "approved_component_version_count": len(version_rows),
        "approved_subcomponent_count": len(subcomponent_rows),
        "candidate_state_update_count": len(state_rows),
        "skipped_count": len(skipped),
        "skipped_examples": skipped[:20],
        "output_dir": str(out),
        "input_files": {
            "component_candidates": str(component_candidates_path),
            "subcomponent_candidates": str(subcomponent_candidates_path),
            "promotion_decisions": str(promotion_decisions_path),
        },
        "files": {
            "components_csv": str(component_csv),
            "component_versions_csv": str(version_csv),
            "subcomponents_csv": str(subcomponent_csv),
            "candidate_state_updates_csv": str(state_csv),
            "load_sql": str(load_sql),
            "summary": str(out / "approved-component-promotion-plan.json"),
        },
        "safety_notes": [
            "Only promote_candidate decisions without risk flags or review reasons become active component rows.",
            "review_before_promotion, hold, and reject decisions only update candidate state.",
            "This planner writes CSV and SQL only; it does not connect to Postgres.",
        ],
    }
    _write_json(out / "approved-component-promotion-plan.json", report)
    return report


def _self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        component_path = base / "components.jsonl"
        subcomponent_path = base / "subcomponents.jsonl"
        decision_path = base / "decisions.jsonl"
        component_path.write_text(
            "\n".join([
                json.dumps({
                    "component_candidate_id": "component-candidate/object/test/promote",
                    "source_object_id": "object/test/promote",
                    "component_type": "candidate_primitive",
                    "name": "Approved procedure question",
                    "review_status": "approved",
                    "body": {"candidate_primitive": "procedure_question", "blueprint_id": "test-source"},
                }),
                json.dumps({
                    "component_candidate_id": "component-candidate/object/test/hold",
                    "source_object_id": "object/test/hold",
                    "component_type": "candidate_primitive",
                    "name": "Held procedure question",
                    "review_status": "pending_review",
                    "body": {"candidate_primitive": "procedure_question", "blueprint_id": "test-source"},
                }),
            ])
            + "\n",
            encoding="utf-8",
        )
        subcomponent_path.write_text(
            json.dumps({
                "subcomponent_candidate_id": "subcomponent-candidate/object/test/promote/check",
                "component_candidate_id": "component-candidate/object/test/promote",
                "parent_object_id": "object/test/promote",
                "subcomponent_type": "question",
                "name": "Check source evidence",
                "body": {"question": "Is there public evidence?"},
            })
            + "\n",
            encoding="utf-8",
        )
        decision_path.write_text(
            "\n".join([
                json.dumps({
                    "decision_id": "promotion/object/test/promote",
                    "object_id": "object/test/promote",
                    "decision": "promote_candidate",
                    "score": 90,
                    "max_score": 100,
                    "criteria": {},
                    "risk_flags": [],
                    "review_reasons": [],
                }),
                json.dumps({
                    "decision_id": "promotion/object/test/hold",
                    "object_id": "object/test/hold",
                    "decision": "hold",
                    "score": 20,
                    "max_score": 100,
                    "criteria": {},
                    "risk_flags": ["dedupe_review"],
                    "review_reasons": ["Needs merge review."],
                }),
            ])
            + "\n",
            encoding="utf-8",
        )
        report = create_approved_component_promotion_plan(
            component_candidates_path=component_path,
            subcomponent_candidates_path=subcomponent_path,
            promotion_decisions_path=decision_path,
            output_dir=base / "out",
        )
        assert report["approved_component_count"] == 1
        assert report["approved_subcomponent_count"] == 1
        assert report["candidate_state_update_count"] == 2
        assert Path(report["files"]["load_sql"]).exists()
    print(json.dumps({"ok": True, "approved_component_count": report["approved_component_count"]}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create CSV and psql load script for review-approved active components.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--component-candidates-path")
    parser.add_argument("--subcomponent-candidates-path")
    parser.add_argument("--promotion-decisions-path")
    parser.add_argument("--output-dir")
    parser.add_argument("--load-sql-name", default="load-approved-components.sql")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.component_candidates_path:
        parser.error("--component-candidates-path is required unless --self-test is used")
    if not args.subcomponent_candidates_path:
        parser.error("--subcomponent-candidates-path is required unless --self-test is used")
    if not args.promotion_decisions_path:
        parser.error("--promotion-decisions-path is required unless --self-test is used")
    result = create_approved_component_promotion_plan(
        component_candidates_path=args.component_candidates_path,
        subcomponent_candidates_path=args.subcomponent_candidates_path,
        promotion_decisions_path=args.promotion_decisions_path,
        output_dir=args.output_dir,
        load_sql_name=args.load_sql_name,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
