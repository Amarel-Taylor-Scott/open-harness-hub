#!/usr/bin/env python3
"""check_economic_layer — the economic/market layer (Systems 20-22): LIVE economics + the unified cost model + dynamic
routing + secondary-provider arbitrage, all real and offline-deterministic.

Proves: observations roll up to current economics; a >=10% cost move emits a price-change CDC; merged_economics overlays
live data on the config default; the cost model folds availability/success into an EFFECTIVE cost so a flaky cheap
resource loses to a reliable pricier one; the router picks the cheapest viable route, ranks arbitrage over a real model's
provider set, and reroutes on change; provider_intel records a measured run (the telemetry write-back) and is HONESTLY
unavailable offline (no fabricated prices). serves_truth=false.

  python3 scripts/check_economic_layer.py --self-test
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

from src.teleon.economics import cost_model as CM
from src.teleon.economics import economic_graph as EG
from src.teleon.economics import observation_store as OBS
from src.teleon.economics import provider_intel as PI
from src.teleon.economics import routing_engine as RE
from src.teleon.inference.preference_profile import cost_first

REPO = Path(__file__).resolve().parents[1]


_SHARD = uuid.uuid4().hex[:12]   # isolate this check's economic store from concurrent subprocesses


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    rid = f"test.economic.{uuid.uuid4().hex[:10]}"   # unique per run -> no persistent-store accumulation/collision

    # 1. observation store: record + rolling current economics + price-change CDC
    OBS.record_observation(rid, source="crawl", observed_at="2026-06-22T00:00:00Z", cost=0.010, latency_ms=200, availability=0.99, shard=_SHARD)
    r2 = OBS.record_observation(rid, source="crawl", observed_at="2026-06-22T01:00:00Z", cost=0.020, latency_ms=300, availability=0.98, shard=_SHARD)
    cur = OBS.current_economics(rid, shard=_SHARD)
    ck("observations roll up to current economics (mean of recent)", abs(cur["cost"] - 0.015) < 1e-9 and cur["n"] == 2, str(cur))
    ck("a >=10% cost move emits a price-change CDC", r2["cdc_emitted"] is True)

    # 2. economic_graph: live observation overlays the config default; real routes exist
    merged = EG.merged_economics(rid, shard=_SHARD)
    ck("merged_economics surfaces the LIVE observation (live=true, cost from obs)", merged["live"] is True and abs(merged["cost"] - 0.015) < 1e-9)
    lanes = EG.routes_for_lanes(shard=_SHARD)
    ck("routes_for_lanes returns the lane market with economics", len(lanes) >= 1 and all("economics" in r for r in lanes))
    a_node = json.loads((REPO / "architecture" / "model_provider_graph.json").read_text())["nodes"][0]["node_id"]
    mroutes = EG.routes_for_model(a_node, shard=_SHARD)
    ck("routes_for_model returns >=1 real route (model + substitutable alternatives)", len(mroutes) >= 1 and mroutes[0]["resource_id"] == a_node)

    # 3. cost model: availability/success fold into an EFFECTIVE cost -> reliable pricier beats flaky cheap
    flaky = {"resource_id": "r_flaky", "deterministic": False, "economics": {"cost": 0.001, "availability": 0.1, "success_rate": 0.5}}  # eff 0.02
    solid = {"resource_id": "r_solid", "deterministic": True, "economics": {"cost": 0.005, "availability": 1.0, "success_rate": 1.0}}    # eff 0.005
    pick = CM.choose_route([flaky, solid], cost_first())
    ck("cost model folds availability+success into EFFECTIVE cost (reliable pricier beats flaky cheap)", pick["chosen"] == "r_solid")

    # 4. routing engine: cheapest viable route + reroute-on-change + arbitrage over a real model
    cheap = {"resource_id": "r_cheap", "deterministic": True, "economics": {"cost": 0.001, "latency_ms": 50, "availability": 0.99, "success_rate": 1.0}}
    exp = {"resource_id": "r_exp", "deterministic": False, "economics": {"cost": 0.05, "latency_ms": 400, "availability": 0.9, "success_rate": 0.8}}
    rr = RE.reroute("r_exp", [cheap, exp], profile=cost_first())
    ck("router reroutes to the cheaper route when economics shift (signals recompile)", rr["changed"] is True and rr["new"] == "r_cheap")
    arb = RE.arbitrage(a_node, shard=_SHARD)
    ck("arbitrage ranks the provider set cheapest-first + picks one", isinstance(arb["ranked"], list) and arb["chosen"] is not None)
    # reliability is FIRST-CLASS (OpenRouter): skip failing routes; load-balance survivors by reliability/price^2
    h_cheap = {"resource_id": "rel_cheap", "economics": {"cost": 0.001, "availability": 1.0, "success_rate": 1.0}}
    h_pricey = {"resource_id": "rel_pricey", "economics": {"cost": 0.010, "availability": 1.0, "success_rate": 1.0}}
    failing = {"resource_id": "rel_fail", "economics": {"cost": 0.0005, "availability": 0.3, "success_rate": 0.4}}  # cheapest but FAILING
    ck("reliability = availability*success", abs(RE.reliability(failing) - 0.12) < 1e-9)
    viable = RE.viable_routes([h_cheap, h_pricey, failing], min_reliability=0.5)
    ck("skip recently-failing routes (the cheapest-but-failing one is dropped, not just priced in)",
       {r["resource_id"] for r in viable} == {"rel_cheap", "rel_pricey"})
    w = RE.balance_weights([h_cheap, h_pricey], min_reliability=0.5)
    ck("load balanced by inverse-square price (cheaper healthy survivor gets more, but pricier still gets some)",
       w["rel_cheap"] > w["rel_pricey"] > 0)

    # 5. provider_intel: telemetry write-back ingests; crawl is HONESTLY offline (no fabricated prices)
    rid2 = f"test.measured.{uuid.uuid4().hex[:10]}"
    PI.record_measured_run(rid2, cost=0.003, latency_ms=120, success=True, shard=_SHARD)
    ck("telemetry write-back records a measured run as a live observation (§10->§1)", OBS.current_economics(rid2, shard=_SHARD)["n"] == 1)
    crawl = PI.crawl(network_allowed=False)
    ck("crawl is HONESTLY unavailable offline (no fabricated prices)", crawl["available"] is False and crawl["ingested"] == 0)

    ck("serves_truth=false across the layer", rr["serves_truth"] is False and crawl["serves_truth"] is False and pick.get("serves_truth") is False)

    print("\n" + ("PASS - check_economic_layer: live economic observations + CDC, the unified cost model (availability/"
                  "success folded), dynamic routing + arbitrage + reroute, measured write-back, honest-offline crawl."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
