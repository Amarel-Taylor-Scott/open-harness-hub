"""Model cascade policy for context trust workers.

The cascade is risk-driven, not brand-driven. Cheap/open-weight models handle
volume; larger or frontier routes are selected only when task risk, confidence,
conflict, or user-facing impact requires escalation.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_CASCADE_POLICY: dict[str, Any] = {
    "version": "model-cascade-policy",
    "tiers": [
        {
            "tier": 0,
            "id": "deterministic",
            "lane": "deterministic",
            "model_policy": {"capability": "none", "lane": "deterministic"},
            "trainable": False,
            "examples": ["schema validation", "regex extraction", "date normalization", "ontology checks"],
        },
        {
            "tier": 1,
            "id": "small_open_weight",
            "lane": "local_efficient",
            "model_policy": {"capability": "structured_json", "lane": "local_efficient"},
            "trainable": True,
            "examples": ["Gemma 4 efficient", "small Qwen", "small Llama/Mistral"],
            "fine_tune_targets": ["classification", "claim extraction", "fragility tagging", "ambiguity detection"],
        },
        {
            "tier": 2,
            "id": "mid_open_weight",
            "lane": "open_weight_medium",
            "model_policy": {"capability": "structured_review", "lane": "open_weight_medium"},
            "trainable": True,
            "examples": ["Gemma 4 larger", "Qwen 3.6 mid", "medium open-weight reviewer"],
            "fine_tune_targets": ["edge extraction", "evidence review", "summary verification", "contradiction candidates"],
        },
        {
            "tier": 3,
            "id": "large_open_weight",
            "lane": "open_weight_large",
            "model_policy": {"capability": "hard_reasoning", "lane": "open_weight_large"},
            "trainable": False,
            "examples": ["large Qwen", "large Llama", "Mistral Large", "DeepSeek-class"],
        },
        {
            "tier": 4,
            "id": "ensemble_review",
            "lane": "open_weight_large",
            "model_policy": {"capability": "ensemble_review", "lane": "open_weight_large"},
            "trainable": False,
            "examples": ["independent judges for support, conflict, fragility, ambiguity"],
        },
        {
            "tier": 5,
            "id": "frontier_adjudication",
            "lane": "frontier_controlled",
            "model_policy": {"capability": "audit_review", "lane": "frontier_controlled"},
            "trainable": False,
            "requires_approval": True,
            "examples": ["high-stakes appeals court", "teacher labels", "user-facing high-risk summaries"],
        },
        {
            "tier": 6,
            "id": "human_review",
            "lane": "human_review",
            "model_policy": {"capability": "human_review", "lane": "human_review"},
            "trainable": False,
            "requires_approval": True,
            "examples": ["legal", "medical", "financial", "security", "reputational", "unresolved conflict"],
        },
    ],
    "task_defaults": {
        "llm.claim.review": {"start_tier": 1, "max_tier": 3, "training_task": "claim_review"},
        "llm.graph.enrich": {"start_tier": 2, "max_tier": 4, "training_task": "graph_enrichment"},
        "llm.context.summarize": {"start_tier": 1, "max_tier": 4, "training_task": "safe_summary"},
        "llm.conflict.review": {"start_tier": 2, "max_tier": 5, "training_task": "conflict_review"},
        "llm.audit.review": {"start_tier": 5, "max_tier": 6, "training_task": "audit_review"},
    },
    "escalation_rules": {
        "confidence_below": 0.75,
        "evidence_directness_below": 0.80,
        "source_quality_below": 0.60,
        "entity_resolution_below": 0.75,
        "escalate_on_conflict": True,
        "escalate_on_high_fragility": True,
        "escalate_on_ambiguity": True,
        "escalate_on_high_stakes": True,
        "escalate_on_user_facing": True,
        "escalate_on_model_disagreement": True,
    },
    "fine_tuning": {
        "capture_examples": True,
        "capture_bad_outputs": True,
        "capture_corrected_outputs": True,
        "do_not_train_changing_facts_into_weights": True,
        "preferred_methods": ["LoRA", "QLoRA", "PEFT", "TRL", "Axolotl", "LLaMA-Factory", "Unsloth"],
    },
}


def load_cascade_policy(path: str | None = None) -> dict[str, Any]:
    raw_path = path or os.environ.get("MODEL_CASCADE_POLICY_PATH")
    if not raw_path:
        return DEFAULT_CASCADE_POLICY
    policy_path = Path(raw_path)
    if not policy_path.exists():
        return DEFAULT_CASCADE_POLICY
    data = json.loads(policy_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return DEFAULT_CASCADE_POLICY
    return data


def tier_by_id(policy: dict[str, Any], tier_id: str) -> dict[str, Any]:
    for tier in policy.get("tiers", []):
        if isinstance(tier, dict) and tier.get("id") == tier_id:
            return tier
    return {}


def tier_by_number(policy: dict[str, Any], tier_number: int) -> dict[str, Any]:
    for tier in policy.get("tiers", []):
        if isinstance(tier, dict) and int(tier.get("tier", -1)) == int(tier_number):
            return tier
    return {}


def risk_signals(payload: dict[str, Any]) -> dict[str, Any]:
    claims = payload.get("claim_risk_records") if isinstance(payload.get("claim_risk_records"), list) else payload.get("claims", [])
    context_concerns = payload.get("context_concerns") if isinstance(payload.get("context_concerns"), list) else []
    conflicts = payload.get("conflict_candidates") if isinstance(payload.get("conflict_candidates"), list) else []
    fragile = [
        claim for claim in claims
        if isinstance(claim, dict) and (
            ((claim.get("freshness") or {}).get("volatile"))
            or "volatile_fact" in ((claim.get("context_serving") or {}).get("risk_reasons") or [])
        )
    ]
    user_facing = bool(payload.get("user_facing") or payload.get("publish_context_pack"))
    high_stakes = bool(payload.get("high_stakes")) or str(payload.get("domain") or "").lower() in {"legal", "medical", "financial", "security", "reputational"}
    return {
        "claim_count": len(claims) if isinstance(claims, list) else 0,
        "conflict_count": len(conflicts),
        "ambiguous_count": len(context_concerns),
        "fragile_count": len(fragile),
        "user_facing": user_facing,
        "high_stakes": high_stakes,
        "model_disagreement": bool(payload.get("model_disagreement")),
        "low_confidence": float(payload.get("confidence", 1.0)) < 0.75,
    }


def choose_cascade_tiers(task_name: str, payload: dict[str, Any], policy: dict[str, Any] | None = None) -> dict[str, Any]:
    policy = policy or load_cascade_policy()
    defaults = policy.get("task_defaults", {}).get(task_name, {"start_tier": 1, "max_tier": 4, "training_task": task_name})
    start_tier = int(defaults.get("start_tier", 1))
    max_tier = int(defaults.get("max_tier", 4))
    signals = risk_signals(payload)
    rules = policy.get("escalation_rules", {})
    target_tier = start_tier
    reasons: list[str] = []
    if rules.get("escalate_on_conflict") and signals["conflict_count"]:
        target_tier = max(target_tier, min(max_tier, 3))
        reasons.append("conflict_candidates")
    if rules.get("escalate_on_high_fragility") and signals["fragile_count"]:
        target_tier = max(target_tier, min(max_tier, 2))
        reasons.append("fragile_facts")
    if rules.get("escalate_on_ambiguity") and signals["ambiguous_count"]:
        target_tier = max(target_tier, min(max_tier, 2))
        reasons.append("ambiguous_context")
    if rules.get("escalate_on_user_facing") and signals["user_facing"]:
        target_tier = max(target_tier, min(max_tier, 3))
        reasons.append("user_facing_context")
    if rules.get("escalate_on_high_stakes") and signals["high_stakes"]:
        target_tier = max(target_tier, min(max_tier, 5))
        reasons.append("high_stakes_domain")
    if rules.get("escalate_on_model_disagreement") and signals["model_disagreement"]:
        target_tier = max(target_tier, min(max_tier, 4))
        reasons.append("model_disagreement")
    if signals["low_confidence"]:
        target_tier = max(target_tier, min(max_tier, 3))
        reasons.append("low_confidence")
    tiers = [
        tier for tier in policy.get("tiers", [])
        if isinstance(tier, dict) and start_tier <= int(tier.get("tier", -1)) <= target_tier
    ]
    return {
        "policy_version": policy.get("version"),
        "task_name": task_name,
        "training_task": defaults.get("training_task", task_name),
        "start_tier": start_tier,
        "target_tier": target_tier,
        "max_tier": max_tier,
        "selected_tiers": tiers,
        "risk_signals": signals,
        "escalation_reasons": reasons or ["default_start_tier"],
    }
