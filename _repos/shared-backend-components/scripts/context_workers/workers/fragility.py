"""Claim verification priority worker."""
from __future__ import annotations

from typing import Any

from scripts.context_workers.common import DATE_OR_NUMBER_RE, FRAGILE_RE
from scripts.context_workers.priority import decide_followup_for_fact
from scripts.context_workers.registry import TaskContext, TaskResult, registry


@registry.register(
    "context.fragility.scan",
    lane="verify",
    description="Flag claims that need verification, reconciliation, or freshness refresh.",
    emits=("fragile_facts", "updates"),
    capabilities=("fact_risk_scoring", "review_prioritization"),
    task_types=("fact.review_prioritize", "fact.refresh_candidate.detect"),
    image="baltor-worker-audit",
    output_contract="fact_review_queue",
)
def fragility_scan(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    claims = payload.get("claims") or []
    by_subject: dict[str, set[str]] = {}
    for claim in claims:
        by_subject.setdefault(str(claim.get("subject", "")).lower(), set()).add(str(claim.get("polarity", "neutral")))
    fragile = []
    updates = []
    for claim in claims:
        reasons = []
        polarities = by_subject.get(str(claim.get("subject", "")).lower(), set())
        text = str(claim.get("claim", ""))
        needs_reconciliation = {"positive", "negative"}.issubset(polarities)
        if needs_reconciliation:
            reasons.append("reconcile with nearby claims before promotion")
        if FRAGILE_RE.search(text) or DATE_OR_NUMBER_RE.search(text):
            reasons.append("refreshable via search/tool worker")
        if reasons:
            priority_signals = {
                "risk": 0.70 if needs_reconciliation else 0.35,
                "customer_impact": 0.50,
                "source_count": 1,
                "freshness_age_hours": 24 if FRAGILE_RE.search(text) else 0,
            }
            fact_record = {
                "fact_id": claim["id"],
                "claim": text,
                "subject": claim.get("subject", "claim"),
                "source_chunk": claim.get("source_chunk"),
                "state": "needs_reconciliation" if needs_reconciliation else "needs_second_source",
                "independent_source_count": 1,
                "authoritative_source_count": 0,
                "priority_signals": priority_signals,
                "reasons": reasons,
            }
            decision = decide_followup_for_fact(fact_record)
            fragile.append({
                **fact_record,
                "priority": decision.priority,
                "queue_policy": decision.as_queue_policy(),
            })
            updates.append({
                "fact_id": claim["id"],
                "target": claim.get("subject", "claim"),
                "worker": decision.task_type,
                "priority": decision.priority,
                "priority_signals": priority_signals,
                "queue_policy": decision.as_queue_policy(),
                "state": fact_record["state"],
            })
    return TaskResult.success({"fragile_facts": fragile, "updates": updates})
