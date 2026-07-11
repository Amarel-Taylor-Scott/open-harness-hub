"""src.teleon.evolution.descent_measurement — the harness that MEASURES the descent per axis (cost, speed, ...).

The moat is "distill cheaper/faster than anyone" — so it must be measured, not asserted. Given DistillationRecords
(declared before/after + improvement_axes) and optionally a RunLedger (OBSERVED cost/latency from real runs), this
aggregates per-axis impact across the corpus:
  * per_call_cost_saved — total cost eliminated (the COST axis, captured)
  * improved_by_axis — how many capabilities improved on each axis (cost / latency / llm_usage / determinism / freshness)
  * observed cost + latency per runner from the RunLedger (the SPEED + COST measurement from real runs, not estimates)

Pure + deterministic; Teleon-layer — never imports src.baltor; a measurement is evidence, never truth.
"""
from __future__ import annotations

from collections import Counter

from src.teleon.evolution.descent_axes import DESCENT_AXES


def measure_descent(records: list[dict], *, ledger=None) -> dict:
    """Aggregate descent impact per axis across applied DistillationRecords. With a RunLedger, also report the
    OBSERVED cost + latency (speed) per runner — the real measurement behind the declared estimates."""
    applied = [r for r in records if r.get("applied")]
    per_call_cost_saved = sum(float(r.get("coverage", 0.0))
                              * (float(r.get("per_call_cost_before", 0.0)) - float(r.get("per_call_cost_after", 0.0)))
                              for r in applied)
    by_axis: Counter = Counter()
    for r in applied:
        for axis in (r.get("improvement_axes") or []):
            by_axis[axis] += 1
    by_strategy = Counter(r.get("strategy", "?") for r in applied)
    out = {
        "capabilities_descended": len(applied),
        "per_call_cost_saved": round(per_call_cost_saved, 6),
        "improved_by_axis": {a: by_axis.get(a, 0) for a in DESCENT_AXES},  # every axis, in canonical order
        "by_strategy": dict(by_strategy),
        "axes": list(DESCENT_AXES),
        "serves_truth": False,
    }
    if ledger is not None:
        observed = {}
        for impl_id, mv in ledger.candidates():
            observed[impl_id] = {"observed_cost": round(mv.cost, 6), "observed_latency_ms": round(mv.latency, 3),
                                 "observed_llm_usage": round(mv.llm_usage, 3)}
        # the SPEED + COST measurement from real runs (means across the observed impls)
        if observed:
            out["observed"] = observed
            out["observed_mean_cost"] = round(sum(o["observed_cost"] for o in observed.values()) / len(observed), 6)
            out["observed_mean_latency_ms"] = round(sum(o["observed_latency_ms"] for o in observed.values()) / len(observed), 3)
    return out


def cost_speed_report(ledger) -> dict:
    """A focused COST + SPEED report from observed runs (the two axes the owner called out). Per runner: observed
    cost and latency; plus the cheapest + fastest runner seen. Empty ledger -> an explicit empty report."""
    rows = []
    for impl_id, mv in ledger.candidates():
        rows.append({"runner": impl_id, "observed_cost": round(mv.cost, 6), "observed_latency_ms": round(mv.latency, 3)})
    if not rows:
        return {"runners": [], "cheapest": None, "fastest": None, "serves_truth": False}
    cheapest = min(rows, key=lambda r: (r["observed_cost"], r["observed_latency_ms"], r["runner"]))
    fastest = min(rows, key=lambda r: (r["observed_latency_ms"], r["observed_cost"], r["runner"]))
    return {"runners": rows, "cheapest": cheapest["runner"], "fastest": fastest["runner"], "serves_truth": False}
