"""State-driven requeue scanner for Baltor fact records."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.context_workers.priority import (
    TASK_ARCHIVE,
    TASK_RECONCILE,
    TASK_SECOND_SOURCE,
    TASK_TRUST_SCORE,
    decide_budget_policy,
    estimate_task_cost,
    make_research_task,
    task_dedupe_key,
    task_id_from_dedupe_key,
)


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _source_by_id(sources: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(s.get("source_record_id")): s for s in sources if s.get("source_record_id")}


def _merge_priority_signals(fact: dict[str, Any], source: dict[str, Any] | None, *, now: datetime) -> dict[str, Any]:
    signals = dict(fact.get("priority_signals") if isinstance(fact.get("priority_signals"), dict) else {})
    if source:
        source_signals = source.get("priority_signals")
        if isinstance(source_signals, dict):
            signals.update({k: v for k, v in source_signals.items() if k not in signals})
        if source.get("injection_risk") is not None:
            signals["injection_risk"] = max(float(signals.get("injection_risk") or 0.0), float(source.get("injection_risk") or 0.0))
        if source.get("trust_score") is not None:
            signals["source_authority"] = max(float(signals.get("source_authority") or 0.0), float(source.get("trust_score") or 0.0))
    last_verified = _parse_dt(fact.get("last_verified_at"))
    if last_verified:
        signals["freshness_age_hours"] = max((now - last_verified).total_seconds() / 3600.0, 0.0)
    signals.setdefault("source_count", int(fact.get("independent_source_count") or 0))
    return signals


def _fact_source(fact: dict[str, Any], sources_by_id: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    ids = fact.get("supporting_source_ids") if isinstance(fact.get("supporting_source_ids"), list) else []
    for source_id in ids:
        source = sources_by_id.get(str(source_id))
        if source:
            return source
    evidence = fact.get("evidence") if isinstance(fact.get("evidence"), list) else []
    for item in evidence:
        source = sources_by_id.get(str(item.get("source_record_id")))
        if source:
            return source
    return None


def _base_fact(fact: dict[str, Any], source: dict[str, Any] | None, *, now: datetime) -> dict[str, Any]:
    enriched = dict(fact)
    enriched["priority_signals"] = _merge_priority_signals(fact, source, now=now)
    if source:
        enriched.setdefault("source_record_id", source.get("source_record_id"))
        enriched.setdefault("target_url", source.get("source_url"))
    return enriched


def _forced_task(
    *,
    run_id: str,
    tenant_id: str,
    fact: dict[str, Any],
    task_type: str,
    lane: str,
    priority: str,
    reason_codes: list[str],
) -> dict[str, Any]:
    fact_id = str(fact.get("fact_id") or fact.get("id") or "")
    source_id = str(fact.get("source_record_id") or "")
    target_url = str(fact.get("target_url") or "")
    priority_score = 0.90 if priority == "blocked" else 0.65 if priority == "high" else 0.45
    cost_estimate = estimate_task_cost(task_type, priority=priority, signals=fact.get("priority_signals") or {})
    budget_policy = decide_budget_policy(
        cost_estimate,
        tenant_budget_remaining_usd=fact.get("tenant_budget_remaining_usd"),
        task_budget_ceiling_usd=float(fact.get("task_budget_ceiling_usd") or 0.25),
        monthly_budget_ceiling_usd=fact.get("monthly_budget_ceiling_usd"),
        expensive_lane=task_type == TASK_TRUST_SCORE,
    )
    queue_policy = {
        "lane": lane,
        "priority": priority,
        "priority_score": priority_score,
        "reason_codes": reason_codes,
        "max_attempts": 3,
        "backoff": "exponential",
        "cost_estimate": cost_estimate,
        "budget_policy": budget_policy,
        "dedupe_key": task_dedupe_key(
            tenant_id=tenant_id,
            task_type=task_type,
            fact_id=fact_id,
            source_id=source_id,
            target_url=target_url,
        ),
    }
    task_id = task_id_from_dedupe_key(str(queue_policy["dedupe_key"]))
    return {
        "task_id": task_id,
        "task": "context.search.verify",
        "task_type": task_type,
        "state": "queued",
        "lane": lane,
        "priority": priority,
        "run_id": run_id,
        "tenant_id": tenant_id,
        "fact_id": fact_id,
        "source_record_id": source_id,
        "cost_estimate": cost_estimate,
        "budget_policy": budget_policy,
        "queue_policy": queue_policy,
        "payload": {
            "fact_id": fact_id,
            "query": f"{fact.get('subject') or fact.get('claim') or 'claim'} follow-up",
            "queue_policy": queue_policy,
            "cost_estimate": cost_estimate,
            "budget_policy": budget_policy,
        },
    }


def scan_requeue(
    facts: list[dict[str, Any]],
    sources: list[dict[str, Any]] | None = None,
    *,
    run_id: str = "requeue-scan",
    tenant_id: str = "local",
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    now = now or datetime.now(timezone.utc)
    sources_by_id = _source_by_id(sources or [])
    emitted: dict[str, dict[str, Any]] = {}

    for fact in facts:
        state = str(fact.get("state") or fact.get("fact_state") or "")
        source = _fact_source(fact, sources_by_id)
        enriched = _base_fact(fact, source, now=now)
        next_refresh = _parse_dt(fact.get("next_refresh_at"))
        evidence = fact.get("evidence") if isinstance(fact.get("evidence"), list) else []
        archive_ready_state = state in {"two_sources_found", "ready_for_adoption", "authoritative_source_found"}
        archive_needed = (archive_ready_state and not evidence) or any(
            item.get("archive_status") in {"queued", "not_required", None}
            for item in evidence
        )
        injection_risk = float(enriched.get("priority_signals", {}).get("injection_risk") or 0.0)

        if state in {"superseded", "rejected", "served_current", "adopted_current", "adopted_with_history"} and not next_refresh:
            continue
        if injection_risk >= 0.70 or state == "needs_trust_review":
            task = _forced_task(
                run_id=run_id,
                tenant_id=tenant_id,
                fact=enriched,
                task_type=TASK_TRUST_SCORE,
                lane="review",
                priority="blocked",
                reason_codes=["source_trust_or_injection_risk"],
            )
        elif state == "needs_reconciliation":
            task = _forced_task(
                run_id=run_id,
                tenant_id=tenant_id,
                fact=enriched,
                task_type=TASK_RECONCILE,
                lane="verify",
                priority="high",
                reason_codes=["needs_reconciliation"],
            )
        elif archive_needed and (int(fact.get("independent_source_count") or 0) >= 2 or archive_ready_state):
            task = _forced_task(
                run_id=run_id,
                tenant_id=tenant_id,
                fact=enriched,
                task_type=TASK_ARCHIVE,
                lane="archive",
                priority="normal",
                reason_codes=["needs_archive_capture"],
            )
        elif next_refresh and next_refresh <= now:
            task = make_research_task(run_id=run_id, tenant_id=tenant_id, fact={**enriched, "state": "needs_second_source"})
            task["queue_policy"]["reason_codes"].append("refresh_due")
        elif int(fact.get("independent_source_count") or 0) == 1 or state in {"one_source_found", "needs_second_source"}:
            task = make_research_task(run_id=run_id, tenant_id=tenant_id, fact={**enriched, "state": "needs_second_source"})
        elif int(fact.get("independent_source_count") or 0) == 0 or state in {"candidate_detected", "candidate_from_upload"}:
            task = make_research_task(run_id=run_id, tenant_id=tenant_id, fact={**enriched, "state": "candidate_detected"})
        else:
            continue

        key = str(task.get("queue_policy", {}).get("dedupe_key") or task_dedupe_key(
            tenant_id=tenant_id,
            task_type=str(task.get("task_type") or TASK_SECOND_SOURCE),
            fact_id=str(task.get("fact_id") or ""),
        ))
        emitted.setdefault(key, task)

    return list(emitted.values())


def _load_records(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data, []
    if isinstance(data, dict):
        facts = data.get("facts") if isinstance(data.get("facts"), list) else []
        sources = data.get("sources") if isinstance(data.get("sources"), list) else []
        return facts, sources
    raise ValueError("expected JSON object with facts/sources or an array of facts")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan fact/source records and emit deduped follow-up tasks.")
    parser.add_argument("path", help="JSON file containing either a fact array or {'facts': [], 'sources': []}")
    parser.add_argument("--run-id", default="requeue-scan")
    parser.add_argument("--tenant-id", default="local")
    args = parser.parse_args(argv)

    facts, sources = _load_records(Path(args.path))
    tasks = scan_requeue(facts, sources, run_id=args.run_id, tenant_id=args.tenant_id)
    print(json.dumps({"tasks": tasks, "task_count": len(tasks)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
