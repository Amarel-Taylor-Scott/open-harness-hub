"""src.baltor.workers.policy_recommender — turn TELEMETRY into POLICY RECOMMENDATIONS (C-FLEET-2).

Reads the telemetry bundle (and a few live signals) and recommends ramp-up/ramp-down changes:
keep workers warmer when SLA is missed, colder when idle burn is high, bigger batches when fills are
high, fallbacks/circuit-open when a provider fails a lot, more/fewer workers as the queue ages. Pure +
deterministic — it only RECOMMENDS; a human/policy owner applies. It never serves truth or mutates the
ledger, and it never recommends an unsafe truth path (no "auto-promote", no "skip verification").
"""
from __future__ import annotations

# named thresholds — single source, each with a rationale
SLA_MISS_HIGH = 3                 # SLA misses in the window before we keep workers warmer / shrink max_wait
IDLE_BURN_HIGH_MS = 300_000       # 5 min of idle burn before we cool a warm pool down
TASKS_PER_START_GOOD = 3.0        # a cold_start worker reused this much would be cheaper kept warm
BATCH_FILL_HIGH = 0.9             # batches consistently this full ⇒ raise batch_min
PROVIDER_FAILURE_HIGH = 0.5       # a provider failing this often ⇒ open circuit + add fallback
QUEUE_AGE_HIGH_S = 120            # queue oldest-age over this ⇒ raise max_workers


def _rec(kind: str, reason: str, **extra) -> dict:
    return {"recommendation": kind, "reason": reason, **extra}


def recommend(telemetry: dict, *, current_lifecycle_policy_id: str,
              sla_miss_count: int = 0, idle_burn_ms: int = 0) -> list[dict]:
    """Return an ordered list of policy recommendations (most impactful first). Empty = steady state."""
    recs: list[dict] = []
    cost = telemetry.get("worker_cost_metrics", {})
    queue = telemetry.get("worker_queue_metrics", {})
    providers = telemetry.get("worker_provider_metrics", [])
    cur = current_lifecycle_policy_id

    # ── ramp-up: missing SLA ──
    if sla_miss_count >= SLA_MISS_HIGH:
        if cur in ("cold_start_each_task", "burst_keepalive"):
            recs.append(_rec("switch_lifecycle_policy", f"{sla_miss_count} SLA misses ≥ {SLA_MISS_HIGH}: keep workers warmer",
                             from_policy=cur, to_policy="warm_pool"))
        recs.append(_rec("lower_max_wait", f"{sla_miss_count} SLA misses ≥ {SLA_MISS_HIGH}: dispatch batches sooner"))

    # ── reuse economics: cold_start worker is being reused a lot ──
    if cur == "cold_start_each_task" and cost.get("tasks_per_worker_start", 0) >= TASKS_PER_START_GOOD:
        recs.append(_rec("switch_lifecycle_policy",
                         f"tasks_per_worker_start={cost.get('tasks_per_worker_start')} ≥ {TASKS_PER_START_GOOD}: keep alive to amortize cold start",
                         from_policy=cur, to_policy="burst_keepalive"))

    # ── ramp-down: idle burn too high on a warm/hot pool ──
    if idle_burn_ms >= IDLE_BURN_HIGH_MS and cur in ("warm_pool", "hot_pool"):
        recs.append(_rec("switch_lifecycle_policy", f"idle_burn_ms={idle_burn_ms} ≥ {IDLE_BURN_HIGH_MS}: cool down",
                         from_policy=cur, to_policy="burst_keepalive"))
        recs.append(_rec("reduce_max_workers", f"idle_burn_ms={idle_burn_ms} ≥ {IDLE_BURN_HIGH_MS}: shrink the pool"))

    # ── batch tuning ──
    if queue.get("batch_fill_ratio", 0) >= BATCH_FILL_HIGH:
        recs.append(_rec("increase_batch_min", f"batch_fill_ratio={queue.get('batch_fill_ratio')} ≥ {BATCH_FILL_HIGH}: bigger batches are efficient"))

    # ── queue aging despite capacity ──
    if queue.get("oldest_task_age_s", 0) >= QUEUE_AGE_HIGH_S:
        recs.append(_rec("increase_max_workers", f"oldest_task_age_s={queue.get('oldest_task_age_s')} ≥ {QUEUE_AGE_HIGH_S}: add capacity"))

    # ── provider health ──
    for p in providers:
        if p.get("failure_rate", 0) >= PROVIDER_FAILURE_HIGH and (p["successes"] + p["failures"]) >= 4:
            recs.append(_rec("open_circuit_and_add_fallback",
                             f"provider {p['provider_id']} failure_rate={p['failure_rate']} ≥ {PROVIDER_FAILURE_HIGH}",
                             provider_id=p["provider_id"]))
    return recs


__all__ = ["recommend"]
