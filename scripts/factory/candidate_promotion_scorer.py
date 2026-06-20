#!/usr/bin/env python3
"""Score candidate primitives for promotion readiness.

The scorer is deterministic and stdlib-only. It uses the priority formula from
the million-object goal and applies explicit penalties for privacy, license,
dedupe, and review risk.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from scripts.eval.reason_codes import gap_durability_score


DEFAULT_WEIGHTS = {
    "usefulness": 1.2,
    "demand": 1.2,
    "complexity": 1.0,
    "time_savings": 1.1,
    "frequency_of_deployment": 1.0,
    "not_solved_by_out_of_box_llms": 1.2,
    "cost_savings": 0.9,
    "deployment_management_value": 0.9,
    "model_swap_value": 0.8,
    "verifiability": 1.0,
    "training_attention_gap": 0.8,
    "data_coverage_gap": 0.8,
    "economic_value": 1.1,
    # Durability/moat: does the gap close with more model/data/tools, or is the
    # human advantage structural (body/access/license/un-ingestible channel)?
    # High = defensible. Single source: scripts/eval/reason_codes.py — see
    # docs/concepts/capability-valleys.md.
    "durability": 1.0,
}

RISKY_PRIVACY = {"contains_pii", "unknown", "raw_listing", "external_unredacted"}
RESTRICTIVE_LICENSE_TERMS = ("unknown", "proprietary", "restricted", "no-redistribution", "terms-prohibited")


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value[:96].strip("-") or "candidate"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no}: expected JSON object")
        records.append(value)
    return records


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(json.dumps(record, sort_keys=True, ensure_ascii=False) for record in records)
    path.write_text(body + ("\n" if records else ""), encoding="utf-8")


def _body(record: dict[str, Any]) -> dict[str, Any]:
    value = record.get("body")
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value]
    return []


def _clamp(value: float, low: float = 0.0, high: float = 5.0) -> float:
    return max(low, min(high, value))


def _estimate_criteria(record: dict[str, Any]) -> dict[str, float]:
    body = _body(record)
    skills = _list(body.get("skills"))
    workflow_steps = _list(body.get("workflow_steps"))
    acceptance = _list(body.get("acceptance_criteria"))
    deliverables = _list(body.get("deliverables"))
    automation = _list(body.get("automation_opportunities"))
    risk_flags = _list(body.get("risk_flags"))
    cost_signals = body.get("cost_signals") if isinstance(body.get("cost_signals"), dict) else {}
    problem = str(body.get("problem_statement") or "")

    complexity = _clamp(1.0 + 0.35 * len(workflow_steps) + 0.25 * len(skills) + 0.15 * len(risk_flags))
    verifiability = _clamp(1.0 + 0.5 * len(acceptance) + 0.25 * len(deliverables))
    automation_value = _clamp(1.0 + 0.45 * len(automation) + 0.2 * len(workflow_steps))
    out_of_box_gap = _clamp(1.0 + 0.35 * len(workflow_steps) + 0.3 * len(acceptance) + 0.3 * len(risk_flags))
    demand = _clamp(2.0 + (0.5 if body.get("marketplace_category") or body.get("category") else 0.0))
    frequency = _clamp(2.0 + (0.35 if "support" in problem.lower() else 0.0) + (0.35 if "spreadsheet" in problem.lower() else 0.0))
    cost_savings = _clamp(1.5 + 0.4 * len(automation))
    economic_value = _clamp(2.0 + 0.5 * bool(cost_signals) + 0.2 * len(deliverables))
    deployment_value = _clamp(1.0 + 0.35 * len(["x" for x in automation if "routing" in x or "RAG" in x.upper() or "dedupe" in x]))
    # Durability of the gap this candidate addresses (0..5, high = defensible).
    # Reads explicit body signals when present; neutral default otherwise.
    durability = gap_durability_score(
        reason_codes=_list(body.get("reason_codes")) or _list(body.get("reason_code")),
        retrievability_tier=body.get("retrievability_tier"),
        adversarial=bool(body.get("adversarial")),
        mechanisms=_list(body.get("mechanisms")) or _list(body.get("mechanism")),
    )

    return {
        "usefulness": _clamp(1.5 + 0.25 * len(deliverables) + 0.25 * len(acceptance)),
        "demand": demand,
        "complexity": complexity,
        "time_savings": automation_value,
        "frequency_of_deployment": frequency,
        "not_solved_by_out_of_box_llms": out_of_box_gap,
        "cost_savings": cost_savings,
        "deployment_management_value": deployment_value,
        "model_swap_value": _clamp(1.0 + 0.2 * len(automation)),
        "verifiability": verifiability,
        "training_attention_gap": _clamp(1.0 + 0.25 * len(risk_flags)),
        "data_coverage_gap": _clamp(1.0 + 0.25 * len(risk_flags) + 0.15 * len(skills)),
        "economic_value": economic_value,
        "durability": durability,
    }


def _risk_flags(record: dict[str, Any]) -> list[str]:
    flags = list(_list(_body(record).get("risk_flags")))
    privacy = str(record.get("privacy_boundary") or "").lower()
    if privacy in RISKY_PRIVACY or "pii" in privacy and "no_pii" not in privacy:
        flags.append("privacy_boundary_review")
    license_value = str((record.get("provenance") or {}).get("license") or "").lower()
    if not license_value or any(term in license_value for term in RESTRICTIVE_LICENSE_TERMS):
        flags.append("license_review")
    if record.get("review_status") in {"review_required", "in_review"}:
        flags.append("existing_review_required")
    if record.get("dedupe_cluster_id"):
        flags.append("dedupe_review")
    return sorted(set(flags))


def score_candidate(record: dict[str, Any], weights: dict[str, float] | None = None) -> dict[str, Any]:
    criteria = _estimate_criteria(record)
    effective_weights = {**DEFAULT_WEIGHTS, **(weights or {})}
    weighted = sum(criteria[key] * effective_weights.get(key, 1.0) for key in criteria)
    max_score = sum(5.0 * effective_weights.get(key, 1.0) for key in criteria)
    risk_flags = _risk_flags(record)
    penalty = min(0.45, 0.06 * len(risk_flags))
    score = round((weighted / max_score) * 100.0 * (1.0 - penalty), 2)

    review_reasons: list[str] = []
    if "license_review" in risk_flags:
        review_reasons.append("License or marketplace terms must be reviewed before promotion.")
    if "privacy_boundary_review" in risk_flags:
        review_reasons.append("Privacy boundary is not safe enough for automatic promotion.")
    if "dedupe_review" in risk_flags:
        review_reasons.append("Candidate belongs to a dedupe cluster and needs merge review.")
    if record.get("review_status") == "review_required":
        review_reasons.append("Upstream intake marked this candidate for review.")

    if score >= 72 and not review_reasons:
        decision = "promote_candidate"
    elif score >= 45:
        decision = "review_before_promotion"
    elif score >= 25:
        decision = "hold"
    else:
        decision = "reject"

    object_id = str(record.get("object_id") or "candidate/unknown")
    return {
        "decision_id": f"promotion/{_slug(object_id)}",
        "object_id": object_id,
        "source_record_id": record.get("source_record_id", ""),
        "score": score,
        "max_score": 100.0,
        "decision": decision,
        "criteria": criteria,
        "risk_flags": risk_flags,
        "review_reasons": review_reasons,
        "recommended_outputs": _recommended_outputs(record),
        "created_at": _utc_now(),
    }


def _recommended_outputs(record: dict[str, Any]) -> list[str]:
    body = _body(record)
    outputs = ["normalized_object", "index_record", "review_ticket"]
    if _list(body.get("workflow_steps")):
        outputs.append("pipeline_candidate")
    if _list(body.get("acceptance_criteria")):
        outputs.append("rubric_candidate")
    if _list(body.get("automation_opportunities")):
        outputs.append("tool_or_harness_candidate")
    if body.get("cost_signals"):
        outputs.append("cost_model_candidate")
    return outputs


def _index_record(decision: dict[str, Any]) -> dict[str, Any]:
    text = " ".join([
        decision["object_id"],
        decision["decision"],
        " ".join(decision.get("risk_flags", [])),
        " ".join(decision.get("recommended_outputs", [])),
    ])
    return {
        "index_record_id": f"idx:{_slug(decision['decision_id'])}:quality",
        "index_kind": "quality",
        "subject_id": decision["object_id"],
        "subject_type": "promotion_decision",
        "text": text,
        "metadata": {
            "promotion_score": decision["score"],
            "decision": decision["decision"],
            "risk_flags": decision.get("risk_flags", []),
            "recommended_outputs": decision.get("recommended_outputs", []),
        },
    }


def _review_ticket(decision: dict[str, Any]) -> dict[str, Any] | None:
    if decision["decision"] == "promote_candidate":
        return None
    return {
        "review_ticket_id": f"review/{_slug(decision['decision_id'])}",
        "object_id": decision["object_id"],
        "source_record_id": decision.get("source_record_id", ""),
        "review_type": "quality",
        "reason": " ".join(decision.get("review_reasons") or ["Promotion score requires curator review."]),
        "status": "open",
        "priority": "high" if decision["score"] >= 60 else "medium",
        "created_at": _utc_now(),
        "evidence": [
            {"kind": "promotion_score", "value": decision["score"]},
            {"kind": "decision", "value": decision["decision"]},
            {"kind": "risk_flags", "value": decision.get("risk_flags", [])},
        ],
    }


def score_candidates(
    *,
    input_path: str,
    output_dir: str,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    records = _read_jsonl(Path(input_path))
    decisions = [score_candidate(record, weights) for record in records]
    index_records = [_index_record(decision) for decision in decisions]
    review_tickets = [ticket for decision in decisions if (ticket := _review_ticket(decision)) is not None]

    out = Path(output_dir)
    paths = {
        "promotion_decisions": out / "promotion-decisions.jsonl",
        "index_records": out / "promotion-index-records.jsonl",
        "review_tickets": out / "promotion-review-tickets.jsonl",
    }
    _write_jsonl(paths["promotion_decisions"], decisions)
    _write_jsonl(paths["index_records"], index_records)
    _write_jsonl(paths["review_tickets"], review_tickets)
    summary = {
        "ok": True,
        "candidates": len(records),
        "promotion_decisions": len(decisions),
        "promote_candidate": sum(1 for d in decisions if d["decision"] == "promote_candidate"),
        "review_before_promotion": sum(1 for d in decisions if d["decision"] == "review_before_promotion"),
        "hold": sum(1 for d in decisions if d["decision"] == "hold"),
        "reject": sum(1 for d in decisions if d["decision"] == "reject"),
        "index_records": len(index_records),
        "review_tickets": len(review_tickets),
        "paths": {key: str(path) for key, path in paths.items()},
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def _self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        source = base / "candidates.jsonl"
        source.write_text(
            "\n".join([
                json.dumps({
                    "object_id": "task-archetype/spreadsheet-cleanup-and-deduplication",
                    "object_type": "task",
                    "source_record_id": "source/task-marketplace/synthetic-spreadsheet-cleanup",
                    "title": "Spreadsheet cleanup and deduplication",
                    "body": {
                        "task_family": "Spreadsheet cleanup and deduplication",
                        "skills": ["spreadsheet cleanup", "deduplication", "data validation"],
                        "workflow_steps": ["Inspect columns", "Normalize formats", "Cluster duplicates", "Route ambiguous rows to review"],
                        "acceptance_criteria": ["Duplicate decisions are explainable", "Ambiguous rows are separated for review"],
                        "deliverables": ["cleaned table", "exception report"],
                        "automation_opportunities": ["schema inference", "fuzzy dedupe", "review ticket routing"],
                        "cost_signals": {"unit": "project", "low_usd": 25, "high_usd": 250},
                    },
                    "privacy_boundary": "metadata_only_no_pii",
                    "review_status": "candidate",
                    "provenance": {"license": "CC-BY-4.0"},
                    "dedupe_cluster_id": "dedupe/task-archetype/spreadsheet-cleanup-and-deduplication",
                }),
                json.dumps({
                    "object_id": "task-archetype/raw-private-listing",
                    "object_type": "task",
                    "source_record_id": "source/task-marketplace/raw-private",
                    "title": "Raw private listing",
                    "body": {
                        "task_family": "Raw private listing",
                        "skills": ["unknown"],
                        "risk_flags": ["private_message"],
                    },
                    "privacy_boundary": "external_unredacted",
                    "review_status": "review_required",
                    "provenance": {"license": "unknown"},
                }),
            ]) + "\n",
            encoding="utf-8",
        )
        result = score_candidates(input_path=str(source), output_dir=str(base / "out"))
        assert result["candidates"] == 2
        assert result["promotion_decisions"] == 2
        assert result["review_tickets"] >= 1
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score candidate primitives for promotion readiness.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--input")
    parser.add_argument("--output-dir")
    parser.add_argument("--weights-json", help="Optional JSON object overriding scoring weights.")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.input or not args.output_dir:
        parser.error("--input and --output-dir are required")
    weights = json.loads(args.weights_json) if args.weights_json else None
    if weights is not None and not isinstance(weights, dict):
        parser.error("--weights-json must decode to an object")
    result = score_candidates(input_path=args.input, output_dir=args.output_dir, weights=weights)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(_main())
