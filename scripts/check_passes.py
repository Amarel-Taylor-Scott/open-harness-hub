#!/usr/bin/env python3
"""check_passes — System 8/9: the PassManager (LLVM for cognition) with legality + cost gates.

Proves: CSE merges duplicate nodes (mechanical); deterministic-replacement swaps an llm node for a cheaper deterministic
one (the descent) AND only fires when it (a) re-verifies and (b) lowers cost — an illegal (type-breaking) rewrite is
rejected, and a cost-worsening rewrite is rejected. serves_truth=false.

  python3 scripts/check_passes.py --self-test
"""
from __future__ import annotations

import uuid

from src.teleon.economics import observation_store as OBS
from src.teleon.synthesis import passes as P
from src.teleon.inference.preference_profile import cost_first


def _seed(cost):
    rid = f"test.pass.{uuid.uuid4().hex[:10]}"
    OBS.record_observation(rid, source="test", cost=cost, latency_ms=10)
    return rid


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    r = _seed(0.001)
    # CSE: two identical embedding nodes (same component, plane, no preds) -> merged to one
    dup = {"nodes": [{"step": "a", "component": r, "plane": "embedding"}, {"step": "b", "component": r, "plane": "embedding"}], "edges": []}
    res = P.run_passes(dup, passes=["cse"])
    ck("CSE merges duplicate nodes (2 identical -> 1)", len(res["dag"]["nodes"]) == 1 and res["applied"][0]["applied"])

    # deterministic-replacement: ocr -> llm(expensive); replace llm with a cheaper deterministic field_parser
    r_ocr, r_llm_exp, r_det_cheap = _seed(0.001), _seed(0.050), _seed(0.001)
    dag = {"nodes": [{"step": "x", "component": r_ocr, "plane": "ocr"}, {"step": "y", "component": r_llm_exp, "plane": "llm"}], "edges": [["x", "y"]]}
    sub_ok = {"y": {"component": r_det_cheap, "plane": "field_parsing"}}
    res2 = P.run_passes(dag, passes=["deterministic_replacement"], substitutions=sub_ok)
    yplane = next(n["plane"] for n in res2["dag"]["nodes"] if n["step"] == "y")
    ck("deterministic-replacement swaps llm -> deterministic (the descent) when it re-verifies + lowers cost",
       res2["applied"][0]["applied"] and yplane == "field_parsing" and res2["savings"] > 0, str(res2["savings"]))

    # cost gate: replacing a CHEAP llm with an EXPENSIVE deterministic is rejected (would worsen the objective)
    r_llm_cheap, r_det_exp = _seed(0.001), _seed(0.050)
    dag_c = {"nodes": [{"step": "x", "component": r_ocr, "plane": "ocr"}, {"step": "y", "component": r_llm_cheap, "plane": "llm"}], "edges": [["x", "y"]]}
    res3 = P.run_passes(dag_c, passes=["deterministic_replacement"], substitutions={"y": {"component": r_det_exp, "plane": "field_parsing"}})
    ck("cost gate REJECTS a rewrite that would worsen the objective", not res3["applied"][0]["applied"] and "worsen" in res3["applied"][0]["reason"])

    # legality gate: a type-breaking replacement (llm -> asr: consumes audio, but ocr upstream produces text) is rejected
    res4 = P.run_passes(dag, passes=["deterministic_replacement"], substitutions={"y": {"component": r_det_cheap, "plane": "asr"}})
    ck("legality gate REJECTS an illegal (type-breaking) rewrite via re-verification",
       not res4["applied"][0]["applied"] and "re-verify" in res4["applied"][0]["reason"])
    ck("serves_truth=false", res2["serves_truth"] is False)

    print("\n" + ("PASS - check_passes: PassManager with CSE + deterministic-replacement, each gated by re-verification "
                  "(legality) and a cost gate (never worsen the objective)." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
