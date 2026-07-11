"""Shared queue priority policy for Baltor context workers.

The policy is deliberately small and deterministic. Model-backed workers can add
signals, but queue routing should stay explainable and reproducible.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any


LANE_VERIFY = "verify"
LANE_REFRESH = "refresh"
LANE_RESEARCH = "research"
LANE_ARCHIVE = "archive"
LANE_REVIEW = "review"

PRIORITY_BACKGROUND = "background"
PRIORITY_LOW = "low"
PRIORITY_NORMAL = "normal"
PRIORITY_HIGH = "high"
PRIORITY_URGENT = "urgent"
PRIORITY_BLOCKED = "blocked"

TASK_SECOND_SOURCE = "verify.second_source.find"
TASK_OFFICIAL_SOURCE = "verify.official_source.find"
TASK_RECONCILE = "context.reconcile.claims"
TASK_TRUST_SCORE = "source.trust.score"
TASK_ARCHIVE = "source.archive.submit"
TASK_ADVERSARIAL_REVIEW = "openclaw.adversarial.review"

BUDGET_ALLOW = "allow"
BUDGET_BATCH = "batch"
BUDGET_REQUIRE_APPROVAL = "require_approval"
BUDGET_BLOCK = "block"

TASK_COST_TABLE_USD = {
    TASK_SECOND_SOURCE: 0.035,
    TASK_OFFICIAL_SOURCE: 0.045,
    TASK_RECONCILE: 0.020,
    TASK_TRUST_SCORE: 0.025,
    TASK_ARCHIVE: 0.004,
    TASK_ADVERSARIAL_REVIEW: 0.080,
    "hermes.procedure.discover": 0.160,
    "web.price.check": 0.025,
    "web.statute.read": 0.055,
    "web.site.search": 0.045,
    "web.business.address.find": 0.030,
    "web.business.hierarchy.find": 0.090,
    "web.news.mna.scan": 0.050,
    "docs.capability.lookup": 0.025,
}


@dataclass(frozen=True)
class PriorityDecision:
    lane: str
    priority: str
    priority_score: float
    task_type: str
    reason_codes: tuple[str, ...]

    def as_queue_policy(self) -> dict[str, Any]:
        return {
            "lane": self.lane,
            "priority": self.priority,
            "priority_score": round(self.priority_score, 3),
            "reason_codes": list(self.reason_codes),
            "max_attempts": 3,
            "backoff": "exponential",
        }


def task_dedupe_key(*, tenant_id: str, task_type: str, fact_id: str = "", source_id: str = "", target_url: str = "") -> str:
    parts = [tenant_id or "local", task_type or "unknown", fact_id or "-", source_id or "-", target_url or "-"]
    return "|".join(parts)


def task_id_from_dedupe_key(dedupe_key: str) -> str:
    return "rt-" + sha256(dedupe_key.encode("utf-8")).hexdigest()[:16]


def estimate_task_cost(task_type: str, *, priority: str = PRIORITY_NORMAL, signals: dict[str, Any] | None = None) -> dict[str, Any]:
    signals = signals or {}
    base = float(TASK_COST_TABLE_USD.get(task_type, 0.030))
    failed_attempts = int(signals.get("failed_attempts") or 0)
    usage_factor = min(float(signals.get("agent_usage") or 0.0) / 100.0, 1.0)
    priority_factor = {
        PRIORITY_BACKGROUND: 0.70,
        PRIORITY_LOW: 0.85,
        PRIORITY_NORMAL: 1.00,
        PRIORITY_HIGH: 1.15,
        PRIORITY_URGENT: 1.35,
        PRIORITY_BLOCKED: 1.10,
    }.get(priority, 1.0)
    retry_factor = 1.0 + min(failed_attempts, 3) * 0.15
    estimate = round(base * priority_factor * retry_factor * (1.0 + usage_factor * 0.10), 4)
    search_calls = 0 if task_type == TASK_ARCHIVE else 1
    if task_type in {"hermes.procedure.discover", TASK_ADVERSARIAL_REVIEW, "web.business.hierarchy.find"}:
        search_calls = 2
    return {
        "currency": "USD",
        "estimate_kind": "task_planning",
        "estimated_total_usd": estimate,
        "estimated_floor_usd": round(estimate * 0.65, 4),
        "estimated_ceiling_usd": round(estimate * 1.8, 4),
        "estimated_search_calls": search_calls,
        "estimated_browser_seconds": 45 if search_calls else 0,
        "estimated_worker_seconds": 20 if task_type != TASK_ARCHIVE else 5,
        "estimated_gpu_seconds": 0,
        "line_items": [
            {
                "key": "worker_lane",
                "label": "Worker lane execution",
                "amount_usd": round(estimate * 0.35, 4),
                "basis": f"{task_type} queue worker",
            },
            {
                "key": "search_or_model",
                "label": "Search/model/tool allowance",
                "amount_usd": round(estimate * 0.65, 4),
                "basis": f"{search_calls} planned search/tool call(s)",
            },
        ],
    }


def decide_budget_policy(
    cost_estimate: dict[str, Any],
    *,
    tenant_budget_remaining_usd: float | None = None,
    task_budget_ceiling_usd: float = 0.25,
    monthly_budget_ceiling_usd: float | None = None,
    expensive_lane: bool = False,
) -> dict[str, Any]:
    estimated = float(cost_estimate.get("estimated_total_usd") or 0.0)
    remaining = float(tenant_budget_remaining_usd) if tenant_budget_remaining_usd is not None else None
    reasons: list[str] = []
    action = BUDGET_ALLOW
    if estimated > task_budget_ceiling_usd:
        action = BUDGET_REQUIRE_APPROVAL
        reasons.append("task_estimate_exceeds_ceiling")
    elif expensive_lane:
        action = BUDGET_BATCH
        reasons.append("expensive_lane_batch_when_possible")
    if remaining is not None and estimated > remaining:
        action = BUDGET_BLOCK
        reasons.append("tenant_budget_remaining_too_low")
    if not reasons:
        reasons.append("within_budget")
    budget_used_pct = round((estimated / task_budget_ceiling_usd) * 100, 2) if task_budget_ceiling_usd else 0.0
    policy = {
        "task_budget_ceiling_usd": round(task_budget_ceiling_usd, 4),
        "budget_used_pct": budget_used_pct,
        "action": action,
        "reason_codes": reasons,
    }
    if remaining is not None:
        policy["tenant_budget_remaining_usd"] = round(remaining, 4)
    if monthly_budget_ceiling_usd is not None:
        policy["monthly_budget_ceiling_usd"] = round(float(monthly_budget_ceiling_usd), 4)
    return policy


def _band(score: float, *, blocked: bool = False) -> str:
    if blocked:
        return PRIORITY_BLOCKED
    if score >= 0.85:
        return PRIORITY_URGENT
    if score >= 0.60:
        return PRIORITY_HIGH
    if score >= 0.30:
        return PRIORITY_NORMAL
    if score >= 0.10:
        return PRIORITY_LOW
    return PRIORITY_BACKGROUND


def decide_followup_for_fact(fact: dict[str, Any]) -> PriorityDecision:
    """Return the next task for a fact-like record.

    Expected inputs are intentionally generic so uploaded-corpus facts, external
    search findings, and manually curated facts can use the same policy.
    """
    state = str(fact.get("state") or fact.get("fact_state") or "candidate_detected")
    source_count = int(fact.get("independent_source_count") or fact.get("source_count") or 0)
    authoritative_count = int(fact.get("authoritative_source_count") or 0)
    signals = fact.get("priority_signals") if isinstance(fact.get("priority_signals"), dict) else {}
    risk = float(signals.get("risk") or 0.0)
    impact = float(signals.get("customer_impact") or 0.0)
    usage = min(float(signals.get("agent_usage") or 0.0) / 25.0, 1.0)
    age = min(float(signals.get("freshness_age_hours") or 0.0) / 168.0, 1.0)
    injection = float(signals.get("injection_risk") or 0.0)
    failed_attempts = int(signals.get("failed_attempts") or 0)

    score = (0.30 * risk) + (0.25 * impact) + (0.20 * usage) + (0.15 * age) + (0.10 * injection)
    reasons: list[str] = []

    if injection >= 0.70 or state == "needs_trust_review":
        reasons.append("source_trust_or_injection_risk")
        return PriorityDecision(LANE_REVIEW, _band(score, blocked=True), score, TASK_ADVERSARIAL_REVIEW, tuple(reasons))
    if state == "needs_reconciliation":
        reasons.append("source_disagreement_or_scope_mismatch")
        return PriorityDecision(LANE_VERIFY, _band(max(score, 0.65)), max(score, 0.65), TASK_RECONCILE, tuple(reasons))
    if authoritative_count >= 1 and state in {"authoritative_source_found", "ready_for_adoption"}:
        reasons.append("authoritative_source_available")
        return PriorityDecision(LANE_ARCHIVE, _band(max(score, 0.35)), max(score, 0.35), TASK_ARCHIVE, tuple(reasons))
    if source_count == 1 or state in {"one_source_found", "needs_second_source"}:
        reasons.append("needs_second_independent_source")
        if failed_attempts >= 3:
            reasons.append("repeated_search_failures_route_to_hermes")
            return PriorityDecision(LANE_RESEARCH, _band(max(score, 0.50)), max(score, 0.50), "hermes.procedure.discover", tuple(reasons))
        return PriorityDecision(LANE_RESEARCH, _band(max(score, 0.45)), max(score, 0.45), TASK_SECOND_SOURCE, tuple(reasons))
    if source_count == 0:
        reasons.append("needs_official_or_primary_source")
        return PriorityDecision(LANE_RESEARCH, _band(max(score, 0.35)), max(score, 0.35), TASK_OFFICIAL_SOURCE, tuple(reasons))
    if source_count >= 2:
        reasons.append("enough_sources_archive_before_adoption")
        return PriorityDecision(LANE_ARCHIVE, _band(max(score, 0.30)), max(score, 0.30), TASK_ARCHIVE, tuple(reasons))

    reasons.append("background_refresh")
    return PriorityDecision(LANE_REFRESH, _band(score), score, TASK_SECOND_SOURCE, tuple(reasons))


def make_research_task(*, run_id: str, tenant_id: str, fact: dict[str, Any]) -> dict[str, Any]:
    decision = decide_followup_for_fact(fact)
    fact_id = str(fact.get("fact_id") or fact.get("id") or "")
    source_id = str(fact.get("source_record_id") or fact.get("source_id") or "")
    target_url = str(fact.get("target_url") or fact.get("url") or "")
    queue_policy = decision.as_queue_policy()
    signals = fact.get("priority_signals") if isinstance(fact.get("priority_signals"), dict) else {}
    cost_estimate = estimate_task_cost(decision.task_type, priority=decision.priority, signals=signals)
    budget_policy = decide_budget_policy(
        cost_estimate,
        tenant_budget_remaining_usd=fact.get("tenant_budget_remaining_usd"),
        task_budget_ceiling_usd=float(fact.get("task_budget_ceiling_usd") or 0.25),
        monthly_budget_ceiling_usd=fact.get("monthly_budget_ceiling_usd"),
        expensive_lane=decision.task_type in {"hermes.procedure.discover", TASK_ADVERSARIAL_REVIEW},
    )
    queue_policy["dedupe_key"] = task_dedupe_key(
        tenant_id=tenant_id,
        task_type=decision.task_type,
        fact_id=fact_id,
        source_id=source_id,
        target_url=target_url,
    )
    task_id = task_id_from_dedupe_key(str(queue_policy["dedupe_key"]))
    queue_policy["cost_estimate"] = cost_estimate
    queue_policy["budget_policy"] = budget_policy
    return {
        "task_id": task_id,
        "task": "context.search.verify",
        "task_type": decision.task_type,
        "state": "queued",
        "lane": decision.lane,
        "priority": decision.priority,
        "run_id": run_id,
        "tenant_id": tenant_id,
        "fact_id": fact_id,
        "source_record_id": source_id,
        "cost_estimate": cost_estimate,
        "budget_policy": budget_policy,
        "payload": {
            "fact_id": fact_id,
            "query": f"{fact.get('target') or fact.get('subject') or 'claim'} authoritative verification source",
            "priority": decision.priority,
            "queue_policy": queue_policy,
            "cost_estimate": cost_estimate,
            "budget_policy": budget_policy,
        },
        "queue_policy": queue_policy,
    }
