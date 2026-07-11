#!/usr/bin/env python3
"""Score showcase pipeline templates against generated component candidates."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROLE_KEYWORDS = {
    "source_governance": ["source_governance", "source_record", "governance", "source"],
    "sensitive_gate": ["sensitive", "privacy", "pii", "gate", "review_ticket"],
    "entity_linking": ["entity_linking", "entity", "link", "canonical"],
    "retrieval": ["retrieval", "index_record", "embedding", "search", "rag"],
    "model_route": ["model", "route", "llm", "cost", "capability"],
    "cost_check": ["cost", "pricing", "estimate", "budget"],
    "review_gate": ["review_ticket", "review", "human_review", "gate"],
    "blueprint_emit": ["blueprint", "pipeline_step", "output", "template"],
}

DOMAIN_ALIASES = {
    "labor_migration.fee_overcharge": ["social_media_moderation", "government_services", "public_procurement"],
    "platform_safety.child_safety": ["social_media_moderation", "social_media_community", "game_content_safety"],
    "water_quality.public_notice": ["water_quality", "utilities_water"],
    "food_quality.hold_release": ["food_quality", "food_service", "manufacturing_quality"],
    "automotive.used_cars": ["automotive_used_cars", "marketplace_seller_ops"],
    "cybersecurity.soc": ["cybersecurity_soc", "software_devops"],
    "finance.aml": ["finance_aml"],
    "humanitarian.response": ["humanitarian_response", "government_services"],
    "public_procurement": ["public_procurement", "government_services"],
    "content_creation.brand_safety": ["content_creation", "creative_media"],
    "animal_hospital.discharge": ["animal_hospital", "veterinary_specialty"],
    "environmental.review.public_comment": ["environmental_review"],
}


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
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_no}: expected JSON object")
        rows.append(row)
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def _tokens(value: Any) -> set[str]:
    text = json.dumps(value, sort_keys=True, ensure_ascii=False) if not isinstance(value, str) else value
    return {part for part in re.split(r"[^a-zA-Z0-9]+", text.lower()) if len(part) > 2}


def _domain_keys(domain: str) -> set[str]:
    normalized = domain.replace(".", "_").replace("-", "_")
    keys = {normalized}
    keys.update(DOMAIN_ALIASES.get(domain, []))
    keys.update(DOMAIN_ALIASES.get(normalized, []))
    parts = normalized.split("_")
    for size in range(1, min(3, len(parts)) + 1):
        keys.add("_".join(parts[:size]))
    return keys


def _candidate_search_text(candidate: dict[str, Any]) -> str:
    body = candidate.get("body") if isinstance(candidate.get("body"), dict) else {}
    parts = [
        candidate.get("object_id", ""),
        candidate.get("title", ""),
        body.get("domain", ""),
        body.get("task", ""),
        body.get("risk_tier", ""),
        " ".join(str(item) for item in body.get("inputs", []) or []),
        " ".join(str(item) for item in body.get("outputs", []) or []),
        " ".join(str(item) for item in body.get("required_stages", []) or []),
        " ".join(str(item) for item in body.get("label_paths", []) or []),
    ]
    return " ".join(str(part) for part in parts if part).lower()


def _score_candidate(template: dict[str, Any], step: dict[str, Any], candidate: dict[str, Any]) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    body = candidate.get("body") if isinstance(candidate.get("body"), dict) else {}
    search_text = _candidate_search_text(candidate)
    candidate_domain = str(body.get("domain", ""))
    template_domain = str(template.get("domain", ""))
    role = str((step.get("body") or {}).get("showcase_role") or step.get("id") or "")

    if candidate_domain in _domain_keys(template_domain):
        score += 6
        reasons.append("domain_match")
    elif _tokens(candidate_domain) & _tokens(template_domain):
        score += 3
        reasons.append("domain_token_overlap")

    for industry in template.get("industry", []) or []:
        if str(industry).replace(".", "_").lower() in search_text:
            score += 2
            reasons.append("industry_match")
            break

    role_hits = 0
    for keyword in ROLE_KEYWORDS.get(role, []):
        if keyword.lower() in search_text:
            role_hits += 1
    if role_hits:
        score += min(6, role_hits * 2)
        reasons.append(f"role_keyword_hits:{role_hits}")

    if template.get("risk_tier") and template.get("risk_tier") == body.get("risk_tier"):
        score += 1
        reasons.append("risk_tier_match")

    if "pipeline_step" in search_text:
        score += 1
        reasons.append("pipeline_step_candidate")

    return score, reasons


def _coverage_status(best_score: int) -> str:
    if best_score >= 8:
        return "covered"
    if best_score >= 4:
        return "partial"
    return "missing"


def _missing_request(template: dict[str, Any], step: dict[str, Any], status: str, best_score: int) -> dict[str, Any]:
    role = str((step.get("body") or {}).get("showcase_role") or step.get("id") or "unknown")
    return {
        "request_id": f"missing/{template['template_id']}/{role}".replace(" ", "-"),
        "template_id": template["template_id"],
        "template_name": template.get("name"),
        "step_id": step.get("id"),
        "showcase_role": role,
        "status": status,
        "best_score": best_score,
        "needed_domain": template.get("domain"),
        "needed_risk_tier": template.get("risk_tier"),
        "needed_cost_profile": template.get("cost_profile"),
        "needed_deployment_target": template.get("deployment_target"),
        "suggested_outputs": [role, "pipeline_step", "review_ticket" if "review" in role else "index_record"],
        "suggested_label_paths": [
            f"vertical.{template.get('domain')}",
            f"showcase_role.{role}",
            f"cost_profile.{template.get('cost_profile')}",
            f"deployment.{template.get('deployment_target')}",
        ],
        "review_status": "generated_gap_request",
    }


def build_showcase_coverage(
    *,
    template_dir: str | Path,
    normalized_objects: str | Path,
    output_dir: str | Path,
    top_k: int = 5,
) -> dict[str, Any]:
    template_paths = sorted(Path(template_dir).glob("*.json"))
    if not template_paths:
        raise FileNotFoundError(f"no template JSON files found in {template_dir}")
    candidates = _read_jsonl(Path(normalized_objects))
    out = Path(output_dir)

    coverage_rows: list[dict[str, Any]] = []
    missing_rows: list[dict[str, Any]] = []
    template_summaries: list[dict[str, Any]] = []

    for template_path in template_paths:
        template = _read_json(template_path)
        step_statuses: list[str] = []
        for step in template.get("steps", []) or []:
            scored: list[dict[str, Any]] = []
            for candidate in candidates:
                score, reasons = _score_candidate(template, step, candidate)
                if score > 0:
                    scored.append({
                        "object_id": candidate.get("object_id"),
                        "title": candidate.get("title"),
                        "score": score,
                        "reasons": reasons,
                        "review_status": candidate.get("review_status"),
                    })
            scored.sort(key=lambda row: (-int(row["score"]), str(row["object_id"])))
            best_score = int(scored[0]["score"]) if scored else 0
            status = _coverage_status(best_score)
            step_statuses.append(status)
            row = {
                "template_id": template.get("template_id"),
                "template_name": template.get("name"),
                "template_domain": template.get("domain"),
                "step_id": step.get("id"),
                "showcase_role": (step.get("body") or {}).get("showcase_role"),
                "component_layer": step.get("component_layer"),
                "coverage_status": status,
                "best_score": best_score,
                "top_candidates": scored[:top_k],
            }
            coverage_rows.append(row)
            if status != "covered":
                missing_rows.append(_missing_request(template, step, status, best_score))
        template_summaries.append({
            "template_id": template.get("template_id"),
            "template_name": template.get("name"),
            "steps": len(step_statuses),
            "covered_steps": sum(1 for status in step_statuses if status == "covered"),
            "partial_steps": sum(1 for status in step_statuses if status == "partial"),
            "missing_steps": sum(1 for status in step_statuses if status == "missing"),
            "ready_for_review": all(status in {"covered", "partial"} for status in step_statuses),
        })

    summary = {
        "ok": True,
        "template_count": len(template_summaries),
        "candidate_count": len(candidates),
        "step_count": len(coverage_rows),
        "covered_steps": sum(1 for row in coverage_rows if row["coverage_status"] == "covered"),
        "partial_steps": sum(1 for row in coverage_rows if row["coverage_status"] == "partial"),
        "missing_steps": sum(1 for row in coverage_rows if row["coverage_status"] == "missing"),
        "missing_request_count": len(missing_rows),
        "coverage_rows": str(out / "showcase-step-coverage.jsonl"),
        "missing_requests": str(out / "missing-component-requests.jsonl"),
        "template_summaries": template_summaries,
        "notes": [
            "Coverage is deterministic keyword/domain matching over staged candidate rows.",
            "Partial and missing rows are generation requests, not failures.",
            "This report does not require database access and does not promote candidates.",
        ],
    }
    _write_jsonl(out / "showcase-step-coverage.jsonl", coverage_rows)
    _write_jsonl(out / "missing-component-requests.jsonl", missing_rows)
    _write_json(out / "showcase-candidate-coverage-summary.json", summary)
    return summary


def _self_test() -> int:
    result = build_showcase_coverage(
        template_dir="dist/daily-showcase-pipelines/2026-05-28/templates",
        normalized_objects="dist/daily-component-batch-load-audit/2026-05-26_to_2026-05-27/merged-jsonl/normalized-objects.jsonl",
        output_dir="dist/showcase-candidate-coverage/self-test",
    )
    assert result["template_count"] >= 5
    assert result["step_count"] > 0
    assert result["candidate_count"] >= 1000
    print("ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--template-dir")
    parser.add_argument("--normalized-objects")
    parser.add_argument("--output-dir", default="dist/showcase-candidate-coverage")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.template_dir or not args.normalized_objects:
        parser.error("--template-dir and --normalized-objects are required unless --self-test is used")
    result = build_showcase_coverage(
        template_dir=args.template_dir,
        normalized_objects=args.normalized_objects,
        output_dir=args.output_dir,
        top_k=args.top_k,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
