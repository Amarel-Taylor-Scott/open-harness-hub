"""vertical_proof — turn the flywheel on a real vertical. Record MEASURED economics from executions (the telemetry
write-back), then prove the OPTIMIZED (deterministic-first) pipeline is cheaper than the BASELINE (always-LLM) pipeline AT
EQUAL QUALITY — backed by telemetry, not estimates. This is the moat: measured quality you can only earn by running
things, that competitors can't replicate without your traffic. serves_truth=false (it prices/compares; truth is Baltor's).
"""
from __future__ import annotations

from src.teleon.economics import economic_graph as EG
from src.teleon.economics import provider_intel as PI
from src.teleon.economics import simulator as SIM


def record_runs(component_measurements: list) -> dict:
    """component_measurements: [{resource_id, cost, latency_ms, quality, success}] from REAL executions → the telemetry
    write-back into the live economics. Returns {recorded, cdc_emitted}."""
    return PI.ingest([{**m, "source": "measured"} for m in component_measurements])


def compare(baseline_dag: dict, optimized_dag: dict) -> dict:
    """Simulate both pipelines from the MEASURED economics and return the receipt: baseline vs optimized cost, the
    savings %, both qualities, whether quality is equal (within 5pts), and whether every node's economics is telemetry-
    backed (live observations, not config defaults)."""
    b = SIM.simulate_dag(baseline_dag["nodes"], baseline_dag.get("edges"))
    o = SIM.simulate_dag(optimized_dag["nodes"], optimized_dag.get("edges"))
    bc, oc = b["total_cost"], o["total_cost"]
    savings = (1.0 - oc / bc) if bc > 0 else 0.0
    backed = all(EG.merged_economics(n["component"]).get("live")
                 for n in (baseline_dag["nodes"] + optimized_dag["nodes"]) if n.get("component"))
    return {"baseline_cost": bc, "optimized_cost": oc, "savings_pct": round(savings * 100, 1),
            "quality_baseline": b["est_quality"], "quality_optimized": o["est_quality"],
            "equal_quality": abs(b["est_quality"] - o["est_quality"]) <= 0.05, "telemetry_backed": backed,
            "baseline_path": [n.get("step") for n in baseline_dag["nodes"]],
            "optimized_path": [n.get("step") for n in optimized_dag["nodes"]], "serves_truth": False}
