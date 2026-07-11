#!/usr/bin/env python3
"""check_teleon_descent_axes — proof for the canonical descent axes, the robustness/freshness axis, and the
cost+speed measurement harness.

  * CANONICAL AXES — determinism / cost / latency(speed) / llm_usage / freshness are a single-source vocabulary
    with directions; improves() respects each direction (lower-better for cost/latency/llm, higher for det/fresh).
  * FRESHNESS (anti-fragility) — a capability on FRAGILE, changing facts (regulations that change monthly) descends
    via freshness_sync: bound to an authoritative source with a sync cadence matched to its volatility + a CDC
    re-heal, an always-current deterministic lookup; stale answers held out. Within the org's confines.
  * MEASUREMENT HARNESS — measure_descent aggregates per-axis impact across records (total per-call COST saved +
    how many capabilities improved on each axis incl. freshness) and, with a RunLedger, the OBSERVED cost+latency
    (SPEED) from real runs; cost_speed_report names the cheapest + fastest runner. The moat measured, not asserted.

CLI: python3 _repos/shared-backend-components/scripts/check_teleon_descent_axes.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.evolution import (
    DESCENT_AXES,
    cost_speed_report,
    distill,
    distill_robustness,
    freshness_policy,
    improves,
    measure_descent,
)
from src.teleon.governance import load_policy
from src.teleon.objectives import RunLedger, RunObservation


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # CANONICAL AXES: cost + latency(speed) + freshness are first-class, with correct directions.
    ck("the canonical axes include determinism/cost/latency(speed)/llm_usage/freshness",
       {"determinism", "cost", "latency", "llm_usage", "freshness"} <= set(DESCENT_AXES))
    ck("cost & latency are lower-is-better; determinism & freshness are higher-is-better",
       DESCENT_AXES["cost"]["direction"] == "lower" and DESCENT_AXES["latency"]["direction"] == "lower"
       and DESCENT_AXES["determinism"]["direction"] == "higher" and DESCENT_AXES["freshness"]["direction"] == "higher")
    ck("improves() respects axis direction (cost 0.07->0.01 improves; latency 100->300 does not; freshness 0.5->0.9 improves)",
       improves("cost", 0.07, 0.01) and not improves("latency", 100, 300) and improves("freshness", 0.5, 0.9))

    # FRESHNESS POLICY: cadence matched to volatility (monthly-changing regulations -> monthly).
    ck("freshness policy maps volatility -> sync cadence (low->monthly, realtime->continuous, high->daily)",
       freshness_policy("low")["sync_cadence"] == "monthly" and freshness_policy("realtime")["sync_cadence"] == "continuous"
       and freshness_policy("high")["sync_cadence"] == "daily")
    ck("freshness policy requires an authoritative source + a CDC re-heal + holds out stale answers",
       freshness_policy("low")["cdc_reheal"] is True and freshness_policy("low")["authoritative_source_required"] is True
       and freshness_policy("low")["stale_behavior"] == "hold_out")

    # ROBUSTNESS descent: a fragile, monthly-changing regulation -> synced authoritative lookup.
    rob = distill_robustness("reg-e-error-resolution-deadline", category="regulation", volatility_class="low",
                             authoritative_source="ecfr://12/1005.11", source_coverage=0.95)
    rec = rob["record"]
    ck("freshness_sync binds to the authoritative source on a volatility-matched cadence (monthly) + CDC",
       rob["authoritative_source"] == "ecfr://12/1005.11" and rob["freshness_policy"]["sync_cadence"] == "monthly"
       and rob["freshness_policy"]["cdc_reheal"] is True)
    ck("the synced fork is an always-current DETERMINISTIC lookup (improves freshness + determinism + cost)",
       any(r["kind"] == "synced_source" and r["determinism"] == 1.0 for r in rob["graph"]["runners"])
       and set(rec["improvement_axes"]) == {"freshness", "determinism", "cost"})
    ck("the fragile parent is preserved + residual routed (lossless); never serves truth",
       any(r["kind"] == "model" for r in rob["graph"]["runners"]) and rec["lossless"] is True
       and rob["serves_truth"] is False)
    # within confines: a deterministic-only org ACCEPTS the synced (deterministic) fork.
    ck("a deterministic-only org accepts the synced fork (it is deterministic + current)",
       distill_robustness("x", volatility_class="low", authoritative_source="s", policy=load_policy("deterministic-audit"))["applied"] is True)

    # MEASUREMENT HARNESS: aggregate per-axis impact across the three descent kinds.
    records = [
        distill("stock-quote", category="financial-data", determinism_ceiling=1.0, deterministic_coverage_estimate=1.0)["record"],
        distill("open-writer", category="other", determinism_ceiling=0.25, deterministic_coverage_estimate=0.4)["record"],
        rec,  # the freshness_sync record
    ]
    m = measure_descent(records)
    ck("measure_descent captures total per-call COST saved across the descended capabilities",
       m["per_call_cost_saved"] > 0 and m["capabilities_descended"] == 3)
    ck("it counts capabilities improved on each axis — including the new FRESHNESS axis",
       m["improved_by_axis"]["cost"] >= 2 and m["improved_by_axis"]["freshness"] == 1
       and m["improved_by_axis"]["determinism"] >= 2 and set(m["improved_by_axis"]) == set(DESCENT_AXES))
    ck("the measurement never serves truth", m["serves_truth"] is False)

    # OBSERVED cost + speed from real runs (the RunLedger as the measurement harness).
    led = RunLedger()
    for _ in range(3):
        led.record(RunObservation("cheap_fast_rule", cost=0.0, latency_ms=15, llm_calls=0, passed=True, output_key="a"))
        led.record(RunObservation("expensive_slow_model", cost=0.07, latency_ms=1500, llm_calls=1, passed=True, output_key="b"))
    rep = cost_speed_report(led)
    ck("cost_speed_report names the cheapest + fastest runner from OBSERVED runs",
       rep["cheapest"] == "cheap_fast_rule" and rep["fastest"] == "cheap_fast_rule" and len(rep["runners"]) == 2)
    m_obs = measure_descent(records, ledger=led)
    ck("measure_descent with a ledger reports OBSERVED mean cost + latency (the cost+speed measurement)",
       "observed_mean_cost" in m_obs and "observed_mean_latency_ms" in m_obs and m_obs["observed_mean_latency_ms"] > 0)

    # deterministic
    ck("the harness is deterministic (same records -> same measurement)", measure_descent(records) == m)

    print("\n" + ("PASS - check_teleon_descent_axes: descent has canonical axes (determinism/cost/latency-speed/"
                  "llm_usage/freshness) with directions; the FRESHNESS axis binds a fragile changing-fact capability "
                  "to an authoritative source on a volatility-matched cadence + CDC re-heal (always-current "
                  "deterministic lookup, stale held out, within confines); and the measurement harness captures "
                  "per-call cost saved + per-axis improvement + OBSERVED cost/speed from real runs. Never truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
