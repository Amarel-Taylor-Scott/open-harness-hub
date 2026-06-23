#!/usr/bin/env python3
"""check_simulator — System 12 (SIMULATE): estimate a candidate DAG's economics WITHOUT executing, then rank candidates.

Proves: total cost is additive over nodes; latency is the CRITICAL PATH (parallel branches modelled, not summed);
estimates read the LIVE economic graph; rank_candidates orders candidate DAGs cheapest-first per the cost model — all
offline and deterministic. serves_truth=false.

  python3 scripts/check_simulator.py --self-test
"""
from __future__ import annotations

import uuid

from src.teleon.economics import observation_store as OBS
from src.teleon.economics import simulator as SIM
from src.teleon.inference.preference_profile import cost_first


_SHARD = uuid.uuid4().hex[:12]   # isolate this check's economic store from concurrent subprocesses


def _seed(cost, latency_ms):
    rid = f"test.sim.{uuid.uuid4().hex[:10]}"
    OBS.record_observation(rid, source="test", cost=cost, latency_ms=latency_ms, shard=_SHARD)
    return rid


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    ra, rb = _seed(0.010, 100), _seed(0.020, 150)
    # linear chain x->y: cost additive, latency summed (linear)
    lin = SIM.simulate_dag([{"step": "x", "resource_id": ra}, {"step": "y", "resource_id": rb}], [["x", "y"]], shard=_SHARD)
    ck("total cost is additive over nodes", abs(lin["total_cost"] - 0.030) < 1e-9, str(lin["total_cost"]))
    ck("linear chain latency = sum (100+150)", abs(lin["total_latency_ms"] - 250.0) < 1e-6, str(lin["total_latency_ms"]))
    ck("estimate reads LIVE economics (per-node live=true)", all(p["live"] for p in lin["per_node"]))

    # diamond a->b, a->c, b->d, c->d with latencies 10/50/20/5 -> critical path = 10+50+5 = 65 (NOT the 85 sum)
    a, b, c, d = _seed(0.001, 10), _seed(0.001, 50), _seed(0.001, 20), _seed(0.001, 5)
    dia = SIM.simulate_dag([{"step": "a", "resource_id": a}, {"step": "b", "resource_id": b},
                            {"step": "c", "resource_id": c}, {"step": "d", "resource_id": d}],
                           [["a", "b"], ["a", "c"], ["b", "d"], ["c", "d"]], shard=_SHARD)
    ck("latency is the CRITICAL PATH, not the sum (diamond -> 65, not 85)", abs(dia["total_latency_ms"] - 65.0) < 1e-6, str(dia["total_latency_ms"]))
    ck("diamond cost still additive over all 4 nodes", abs(dia["total_cost"] - 0.004) < 1e-9)

    # rank_candidates: a cheap DAG ranks before an expensive one (beam-search ranking, no execution)
    cheap_r, exp_r = _seed(0.001, 50), _seed(0.080, 500)
    ranked = SIM.rank_candidates([{"nodes": [{"step": "n", "resource_id": exp_r}]},
                                  {"nodes": [{"step": "n", "resource_id": cheap_r}]}], profile=cost_first(), shard=_SHARD)
    ck("rank_candidates orders DAGs cheapest-first (the expensive one is last)", ranked[0][0] == 1 and ranked[-1][0] == 0, str([r[0] for r in ranked]))
    ck("rank returns (index, estimate, score) tuples", len(ranked[0]) == 3 and "total_cost" in ranked[0][1])
    ck("serves_truth=false", lin["serves_truth"] is False)

    print("\n" + ("PASS - check_simulator: estimate a candidate DAG's cost (additive) + latency (critical path) + quality "
                  "from live economics WITHOUT executing; rank candidates cheapest-first." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
