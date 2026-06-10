#!/usr/bin/env python3
"""Create a synthetic approved-promotion smoke run through component CDC."""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

from scripts.db.approved_component_promotion_plan import create_approved_component_promotion_plan
from scripts.db.promotion_cdc_bridge_plan import create_promotion_cdc_bridge_plan


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n" for row in rows), encoding="utf-8")


def _approved_candidate_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    candidate_id = "component-candidate/smoke/approved-procedure-question"
    object_id = "object/smoke/approved-procedure-question"
    source_record_id = "source/smoke/public-procedure"
    component_id = "knowledge-pack/approved-smoke-procedure-question"
    candidates = [
        {
            "component_candidate_id": candidate_id,
            "source_object_id": object_id,
            "component_type": "candidate_primitive",
            "component_layer": "data",
            "name": "Approved smoke procedure question",
            "trust_tier": "public",
            "privacy_boundary": "public",
            "review_status": "approved",
            "quality_status": "passed_review",
            "content_hash": "sha256:smoke-approved-procedure-question",
            "promotion_state": "candidate",
            "body": {
                "blueprint_id": "approved-smoke",
                "candidate_primitive": "procedure_question",
                "source_record_id": source_record_id,
                "required_stages": [
                    "source_governance",
                    "normalized_object_schema",
                    "entity_linking",
                    "dedupe",
                    "index_record_emission",
                    "review_ticket_routing",
                ],
                "label_paths": ["factory.smoke", "procedure.question", "approval.approved"],
                "source_patterns": ["public_procedure", "synthetic_fixture"],
                "review_triggers": [],
                "question": "Does the source-backed procedure require evidence before the pipeline takes action?",
            },
        }
    ]
    subcomponents = [
        {
            "subcomponent_candidate_id": "subcomponent-candidate/smoke/approved-procedure-question/evidence-check",
            "component_candidate_id": candidate_id,
            "parent_object_id": object_id,
            "subcomponent_type": "question",
            "name": "Evidence check question",
            "content_hash": "sha256:smoke-evidence-check-question",
            "review_status": "approved",
            "body": {
                "question": "What public source evidence supports this procedure step?",
                "evidence_required": ["source_url", "retrieved_at", "content_hash"],
            },
        }
    ]
    decisions = [
        {
            "decision_id": "promotion/smoke/approved-procedure-question",
            "object_id": object_id,
            "source_record_id": source_record_id,
            "score": 96,
            "max_score": 100,
            "decision": "promote_candidate",
            "criteria": {
                "content_approved": 1.0,
                "dedupe_cleared": 1.0,
                "privacy_public": 1.0,
                "source_governance": 1.0,
            },
            "risk_flags": [],
            "review_reasons": [],
            "recommended_outputs": ["component", "component_version", "subcomponent", "component_change_event", "index_record"],
        }
    ]
    previous_versions = [
        {
            "component_version_id": f"{component_id}@0.0.9",
            "component_id": component_id,
            "version": "0.0.9",
            "version_status": "active",
            "change_summary": "Prior synthetic baseline for smoke testing update CDC.",
            "definition_source": "generated_factory",
            "source_ref": "component-candidate/smoke/previous",
            "definition_hash": "sha256:previous-smoke-definition",
            "source_record_id": source_record_id,
            "body": {
                "component_body": {
                    "source_record_id": source_record_id,
                    "question": "Prior smoke question text.",
                }
            },
        }
    ]
    return candidates, subcomponents, decisions, previous_versions


def create_approved_promotion_smoke_plan(output_dir: str | Path | None = None) -> dict[str, Any]:
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-approved-promotion-smoke-"))
    input_dir = out / "inputs"
    promotion_dir = out / "approved-component-promotion"
    bridge_dir = out / "promotion-cdc-bridge"
    candidates, subcomponents, decisions, previous_versions = _approved_candidate_rows()

    component_candidates_path = input_dir / "component-candidates.jsonl"
    subcomponent_candidates_path = input_dir / "subcomponent-candidates.jsonl"
    promotion_decisions_path = input_dir / "promotion-decisions.jsonl"
    previous_versions_path = input_dir / "previous-component-versions.jsonl"
    _write_jsonl(component_candidates_path, candidates)
    _write_jsonl(subcomponent_candidates_path, subcomponents)
    _write_jsonl(promotion_decisions_path, decisions)
    _write_jsonl(previous_versions_path, previous_versions)

    promotion = create_approved_component_promotion_plan(
        component_candidates_path=component_candidates_path,
        subcomponent_candidates_path=subcomponent_candidates_path,
        promotion_decisions_path=promotion_decisions_path,
        output_dir=promotion_dir,
    )
    bridge = create_promotion_cdc_bridge_plan(
        approved_component_versions_csv=promotion["files"]["component_versions_csv"],
        previous_component_versions_path=previous_versions_path,
        output_dir=bridge_dir,
        actor_type="worker",
        actor_ref="approved-promotion-smoke",
    )
    ok = (
        promotion["approved_component_count"] == 1
        and promotion["approved_component_version_count"] == 1
        and promotion["approved_subcomponent_count"] == 1
        and bridge["cdc"]["change_event_count"] == 1
        and bridge["cdc"]["index_record_count"] == 1
        and bridge["cdc"]["review_ticket_count"] == 1
    )
    summary = {
        "ok": ok,
        "promotion": promotion,
        "bridge": bridge,
        "output_dir": str(out),
        "files": {
            "component_candidates_jsonl": str(component_candidates_path),
            "subcomponent_candidates_jsonl": str(subcomponent_candidates_path),
            "promotion_decisions_jsonl": str(promotion_decisions_path),
            "previous_component_versions_jsonl": str(previous_versions_path),
            "approved_component_promotion_summary": promotion["files"]["summary"],
            "promotion_cdc_bridge_summary": bridge["files"]["summary"],
            "summary": str(out / "approved-promotion-smoke-plan.json"),
        },
    }
    _write_json(out / "approved-promotion-smoke-plan.json", summary)
    return summary


def _self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        result = create_approved_promotion_smoke_plan(Path(tmp) / "out")
        assert result["ok"], result
        assert result["promotion"]["approved_component_count"] == 1, result
        assert result["bridge"]["cdc"]["review_ticket_count"] == 1, result
        print(json.dumps({"ok": True, "change_event_count": 1, "review_ticket_count": 1}, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output-dir")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    result = create_approved_promotion_smoke_plan(args.output_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
