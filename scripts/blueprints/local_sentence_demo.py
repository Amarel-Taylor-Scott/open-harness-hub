from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from scripts.blueprints.cost_route_matrix import build_route_matrix, plan_ab_test


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_sentence(prompt: str) -> dict[str, Any]:
    text = prompt.lower()
    modalities = ["text"]
    if any(term in text for term in ["photo", "image", "picture", "screenshot"]):
        modalities.append("image")
    if any(term in text for term in ["audio", "voice", "call recording"]):
        modalities.append("audio")
    if any(term in text for term in ["video", "clip"]):
        modalities.append("video")

    risk_tier = "standard"
    if any(term in text for term in ["exploitation", "trafficking", "csam", "child safety", "abuse"]):
        risk_tier = "high"
    elif any(term in text for term in ["aml", "sanctions", "fraud", "overcharging", "employment agency fee"]):
        risk_tier = "regulated"
    elif any(term in text for term in ["water quality", "food quality", "disaster", "public health"]):
        risk_tier = "public_safety"

    task_type = "general_pipeline_blueprint"
    if "overcharging" in text or "placement fee" in text or "ofw" in text:
        task_type = "verified_fact_policy_triage"
    elif "aml" in text or "alert" in text:
        task_type = "analyst_alert_review"
    elif "exploitation" in text or "trafficking" in text:
        task_type = "image_text_safety_triage" if "image" in modalities else "safety_triage"

    return {
        "task_type": task_type,
        "objective": prompt.strip(),
        "modalities": modalities,
        "risk_tier": risk_tier,
        "budget_preference": "cheap" if "cheap" in text or "cheapest" in text else "balanced",
        "requires_verified_facts": any(term in text for term in ["rules", "fees", "government", "verified", "cdc"]),
    }


def emit_blueprint_output_records(
    task_parse: dict[str, Any],
    route_matrix: dict[str, Any],
    ab_plan: dict[str, Any] | None = None,
    prompt: str = "",
    verified_fact_dependencies: list[dict[str, Any]] | None = None,
    emit_private: bool = False,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    prompt_hash = _hash_text(prompt) if prompt else ""
    normalized: list[dict[str, Any]] = []
    warnings: list[str] = []
    if prompt and not emit_private:
        warnings.append("Raw prompt text was not emitted; records carry only a prompt hash.")

    for option in route_matrix.get("options", []):
        route_name = option.get("name", "route")
        normalized.append(
            {
                "object_id": f"model-route/{prompt_hash[:12]}-{route_name}",
                "object_type": "model_route_record",
                "route_name": route_name,
                "source_prompt_hash": prompt_hash,
                "task_type": task_parse.get("task_type"),
                "modalities": task_parse.get("modalities", []),
                "risk_tier": task_parse.get("risk_tier"),
                "trust_boundary": option.get("trust_boundary"),
                "guardrails": route_matrix.get("required_guardrails", []),
                "model_swap_points": option.get("model_swap_points", []),
                "pricing_snapshot_ids": option.get("pricing_snapshot_ids", []),
                "created_at": now,
                "quality_status": "generated_candidate",
                "review_status": "pending" if route_matrix.get("review_queues") else "not_required",
            }
        )

    normalized.append(
        {
            "object_id": f"prompt-prefix-cache/{prompt_hash[:12] or 'demo'}",
            "object_type": "prompt_prefix_cache_profile",
            "source_prompt_hash": prompt_hash,
            "cacheable_sections": ["system policy", "tool registry", "output schema", "rubric"],
            "excluded_sections": ["tenant secrets", "raw user evidence", "volatile verified facts"],
            "estimated_hit_rate": None,
            "created_at": now,
            "quality_status": "generated_candidate",
        }
    )
    normalized.append(
        {
            "object_id": f"pricing-snapshot/{prompt_hash[:12] or 'demo'}",
            "object_type": "pricing_snapshot_stub",
            "source_prompt_hash": prompt_hash,
            "snapshot_mode": "simulated_until_live_lookup",
            "currency": "USD",
            "line_items": ["model calls", "embedding", "runtime", "storage", "queue", "human review"],
            "created_at": now,
            "quality_status": "needs_live_pricing",
        }
    )

    for arm in (ab_plan or {}).get("arms", []):
        normalized.append(
            {
                "object_id": f"eval-arm/{prompt_hash[:12]}-{arm.get('name', 'route')}",
                "object_type": "eval_arm",
                "source_prompt_hash": prompt_hash,
                "route_name": arm.get("name"),
                "metrics": (ab_plan or {}).get("metrics", []),
                "cost_ceiling": arm.get("max_usd_per_1000_items"),
                "stop_rules": (ab_plan or {}).get("stop_rules", []),
                "promotion_criteria": (ab_plan or {}).get("promotion_criteria", []),
                "created_at": now,
                "quality_status": "generated_candidate",
            }
        )

    for dep in verified_fact_dependencies or []:
        normalized.append(
            {
                "object_id": dep.get("object_id", f"verified-fact-dependency/{prompt_hash[:12]}-{len(normalized)}"),
                "object_type": "verified_fact_dependency",
                "source_prompt_hash": prompt_hash,
                "publisher": dep.get("publisher"),
                "jurisdiction": dep.get("jurisdiction"),
                "fact_object_id": dep.get("fact_object_id"),
                "effective_date": dep.get("effective_date"),
                "impact_action": dep.get("impact_action", "review_affected_pipeline"),
                "created_at": now,
                "quality_status": "generated_candidate",
            }
        )

    review_tickets = []
    if task_parse.get("risk_tier") in {"high", "regulated", "public_safety"}:
        review_tickets.append(
            {
                "ticket_id": f"review/{prompt_hash[:12] or 'demo'}",
                "reason": "Generated blueprint touches high-risk, regulated, or public-safety workflow.",
                "queue": "domain_safety_review",
                "source_prompt_hash": prompt_hash,
            }
        )

    return {"normalized_objects": normalized, "review_tickets": review_tickets, "warnings": warnings}


def run_sentence_to_pipeline(
    prompt: str,
    simulate: bool = True,
    cost_policy: dict[str, Any] | None = None,
    hosting_environment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    task_parse = parse_sentence(prompt)
    route_matrix = build_route_matrix(task_parse, runtime_constraints=hosting_environment or {})
    ab_plan = plan_ab_test(route_matrix, cost_policy=cost_policy or {})
    records = emit_blueprint_output_records(
        prompt=prompt,
        task_parse=task_parse,
        route_matrix=route_matrix,
        ab_plan=ab_plan,
        verified_fact_dependencies=[
            {
                "publisher": "verified publisher placeholder",
                "jurisdiction": "jurisdiction inferred at review time",
                "fact_object_id": "signed-fact/example",
                "effective_date": None,
            }
        ]
        if task_parse.get("requires_verified_facts")
        else [],
        emit_private=False,
    )
    return {
        "ok": True,
        "simulate": simulate,
        "task_parse": task_parse,
        "options": route_matrix.get("options", []),
        "route_matrix": route_matrix,
        "deployment_bundle": {"mode": "placeholder", "files": ["pipeline.yaml", "runtime.yaml", "cost-estimate.json"]},
        "eval_plan": ab_plan,
        "output_records": records,
    }


def _self_test() -> None:
    result = run_sentence_to_pipeline(
        "Build me a cheap LLM pipeline that intakes a photo plus description and classifies possible human exploitation.",
        cost_policy={"max_usd_per_1000_items": 5.0},
        hosting_environment={"allow_local_first": True},
    )
    assert result["ok"] is True
    assert "image" in result["task_parse"]["modalities"]
    assert result["task_parse"]["risk_tier"] == "high"
    object_types = {item["object_type"] for item in result["output_records"]["normalized_objects"]}
    assert "model_route_record" in object_types
    assert "prompt_prefix_cache_profile" in object_types
    assert "pricing_snapshot_stub" in object_types
    assert "eval_arm" in object_types
    assert result["output_records"]["review_tickets"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local sentence-to-pipeline simulated demo.")
    parser.add_argument("prompt", nargs="?", default="")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        print("ok")
        return 0
    if not args.prompt:
        parser.error("prompt is required unless --self-test is used")
    print(json.dumps(run_sentence_to_pipeline(args.prompt), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
