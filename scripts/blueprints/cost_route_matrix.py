from __future__ import annotations

import argparse
import json
from typing import Any


DEFAULT_METRICS = [
    "precision_at_review",
    "false_negative_sample_rate",
    "cost_per_1000_items",
    "latency_p95_ms",
]


def _risk_guardrails(risk_tier: str, modalities: list[str]) -> list[str]:
    guardrails = ["structured output schema", "audit trace"]
    if "image" in modalities:
        guardrails.append("image safety screen before classification")
    if risk_tier in {"high", "regulated", "public_safety"}:
        guardrails.extend(
            [
                "privacy redaction before external model calls",
                "human review for positive or uncertain cases",
                "evidence spans required for generated conclusions",
            ]
        )
    return guardrails


def build_route_matrix(
    task_parse: dict[str, Any],
    model_routes: list[dict[str, Any]] | dict[str, Any] | None = None,
    pricing_snapshots: list[dict[str, Any]] | None = None,
    runtime_constraints: dict[str, Any] | None = None,
) -> dict[str, Any]:
    modalities = list(task_parse.get("modalities") or ["text"])
    risk_tier = str(task_parse.get("risk_tier") or "standard")
    objective = str(task_parse.get("objective") or task_parse.get("task_type") or "pipeline request")
    runtime_constraints = runtime_constraints or {}
    pricing_snapshots = pricing_snapshots or []
    guardrails = _risk_guardrails(risk_tier, modalities)

    base = {
        "objective": objective,
        "modalities": modalities,
        "risk_tier": risk_tier,
        "pricing_snapshot_ids": [
            item.get("snapshot_id") for item in pricing_snapshots if isinstance(item, dict) and item.get("snapshot_id")
        ],
    }
    options = [
        {
            **base,
            "name": "cheap",
            "route": ["deterministic gates", "local or low-cost model", "human review escalation"],
            "trust_boundary": runtime_constraints.get("cheap_trust_boundary", "local"),
            "estimated_cost": {"currency": "USD", "amount": None, "mode": "simulated_until_live_pricing"},
            "model_swap_points": ["classifier", "reranker", "judge"],
        },
        {
            **base,
            "name": "balanced",
            "route": ["cheap preprocessing", "RAG retrieval", "small model", "selective specialist fallback"],
            "trust_boundary": runtime_constraints.get("balanced_trust_boundary", "mixed"),
            "estimated_cost": {"currency": "USD", "amount": None, "mode": "simulated_until_live_pricing"},
            "model_swap_points": ["captioner", "extractor", "verifier"],
        },
        {
            **base,
            "name": "quality_first",
            "route": ["best available model", "cross-check", "rubric evaluation", "human review"],
            "trust_boundary": runtime_constraints.get("quality_trust_boundary", "mixed"),
            "estimated_cost": {"currency": "USD", "amount": None, "mode": "simulated_until_live_pricing"},
            "model_swap_points": ["primary model", "judge", "appeal reviewer"],
        },
    ]
    if runtime_constraints.get("allow_local_first", True):
        options.append(
            {
                **base,
                "name": "local_first",
                "route": ["local parsing", "local embeddings", "local model", "external call only by approval"],
                "trust_boundary": "local",
                "estimated_cost": {"currency": "USD", "amount": 0, "mode": "compute_not_included"},
                "model_swap_points": ["local model runtime", "embedding model"],
            }
        )

    return {
        "matrix_id": "route-matrix-simulated",
        "options": options,
        "required_guardrails": guardrails,
        "review_queues": ["human_reviewer"] if len(guardrails) > 2 else [],
        "assumptions": [
            "Live provider and runtime pricing must be refreshed before production deployment.",
            "Simulated estimates do not include storage, staff review, legal review, or incident response costs.",
        ],
    }


def plan_ab_test(
    route_matrix: dict[str, Any],
    eval_requirements: dict[str, Any] | None = None,
    cost_policy: dict[str, Any] | None = None,
    promotion_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cost_policy = cost_policy or {}
    options = route_matrix.get("options", [])
    max_cost = cost_policy.get("max_usd_per_1000_items")
    arms = [{"name": option.get("name"), "max_usd_per_1000_items": max_cost} for option in options]
    return {
        "experiment_id": "ab-cost-quality-simulated",
        "arms": arms,
        "metrics": list(DEFAULT_METRICS),
        "stop_rules": ["Stop any arm that exceeds a configured cost ceiling without approval."],
        "promotion_criteria": ["Promote the lowest-cost arm that clears risk-tier quality and safety gates."],
    }


def _self_test() -> None:
    matrix = build_route_matrix(
        {
            "task_type": "image_text_triage",
            "modalities": ["image", "text"],
            "risk_tier": "high",
            "objective": "flag likely exploitation content for review",
        },
        runtime_constraints={"allow_local_first": True},
    )
    assert len(matrix["options"]) == 4
    assert "human review for positive or uncertain cases" in matrix["required_guardrails"]
    plan = plan_ab_test(matrix, cost_policy={"max_usd_per_1000_items": 5.0})
    assert len(plan["arms"]) == 4
    assert "cost_per_1000_items" in plan["metrics"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a simulated blueprint route matrix.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--task-json", help="Task parse JSON object.")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        print("ok")
        return 0
    task_parse = json.loads(args.task_json) if args.task_json else {"task_type": "demo", "modalities": ["text"]}
    matrix = build_route_matrix(task_parse)
    print(json.dumps({"route_matrix": matrix, "ab_plan": plan_ab_test(matrix)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
