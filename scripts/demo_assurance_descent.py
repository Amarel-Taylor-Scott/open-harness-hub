#!/usr/bin/env python3
"""scripts.demo_assurance_descent — a runnable, end-to-end DEMO of the assurance/descent engine on sample skills.

For each seeded skill (data/sample-skills/sample_skills.json) under a tenant's tunable preferences, it runs the
REAL engine: token-aware A/B descent (the cheapest strategy that keeps accuracy — deterministic / cheaper model /
compressed prompt, bounded by the org policy) -> freshness binding for fragile facts (stale held out) ->
per-call cost + token measurement -> governed (serves_truth=false). Prints a readable narrative + a summary; no
mocks — every number comes from the engine. Deterministic; offline; nothing serves truth.

CLI:
    python3 scripts/demo_assurance_descent.py --run [--tenant cost-first-startup]
    python3 scripts/demo_assurance_descent.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from scripts.eval.vertical_eval_suites import eval_suite_scorer
from src.teleon.evolution import FreshnessSyncedCapability, ab_test, measure_descent
from src.teleon.governance import preferences_for

_SKILLS_PATH = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "data" / "sample-skills" / "sample_skills.json"
_DEFAULT_TENANT = "cost-first-startup"


def _load_skills() -> list[dict]:
    return json.loads(_SKILLS_PATH.read_text(encoding="utf-8"))["skills"]


def run_demo(tenant_id: str = _DEFAULT_TENANT, skills: list[dict] | None = None) -> dict:
    """Run the assurance descent on every sample skill under a tenant's preferences. Returns a structured result."""
    prefs = preferences_for(tenant_id)
    policy = prefs.to_org_policy()
    skills = skills if skills is not None else _load_skills()
    rows, records = [], []
    for s in skills:
        ab = ab_test(s, scorer=eval_suite_scorer, max_accuracy_drop=prefs.max_accuracy_drop, policy=policy)
        if ab["winning_record"] is not None:
            records.append(ab["winning_record"])
        freshness = None
        if s.get("fragile"):
            fr = FreshnessSyncedCapability(s["capability_slot"], authoritative_source=s["authoritative_source"],
                                           volatility_class=s.get("volatility_class", "low"))
            fr.sync("(current value)", now="t0", source_version="v1")
            held = fr.on_source_change({"kind": "changed", "source": s["authoritative_source"]}, now="t1")
            freshness = {"source": s["authoritative_source"], "cadence": fr.policy["sync_cadence"],
                         "on_change": held["status"], "stale_served": fr.serve(now="t2")["served"]}
        rows.append({
            "skill": s["capability_slot"], "category": s["category"], "winner": ab["winner"],
            "accuracy": ab["winner_accuracy"], "accuracy_floor": ab["accuracy_floor"], "cost": ab["winner_cost"],
            "tokens_in": ab["winner_tokens_in"], "tokens_out": ab["winner_tokens_out"],
            "tokens_saved_by_compression": ab["tokens_saved_by_compression"],
            "within_confines": ab["winner_accuracy"] >= ab["accuracy_floor"], "freshness": freshness,
            "serves_truth": ab["serves_truth"],
        })
    m = measure_descent(records)
    by_winner: dict = {}
    for r in rows:
        by_winner[r["winner"]] = by_winner.get(r["winner"], 0) + 1
    return {"tenant": tenant_id, "objective": prefs.to_objective().name,
            "hard_blockers": "MIT-only+vetted" if policy.allowed_licenses else "none",
            "max_accuracy_drop": prefs.max_accuracy_drop, "n_skills": len(rows), "rows": rows,
            "by_winner": by_winner, "per_call_cost_saved": m["per_call_cost_saved"],
            "all_within_confines": all(r["within_confines"] for r in rows), "serves_truth": False}


def _print_demo(result: dict) -> None:
    print(f"\n=== Teleon assurance descent — tenant '{result['tenant']}' "
          f"(objective={result['objective']}, hard_blockers={result['hard_blockers']}, "
          f"max_accuracy_drop={result['max_accuracy_drop']}) ===\n")
    for r in result["rows"]:
        fr = r["freshness"]
        fr_txt = (f" | freshness: bound to {fr['source']} ({fr['cadence']}); on change -> {fr['on_change']} "
                  f"(stale served={fr['stale_served']})") if fr else ""
        print(f"  {r['skill']:34} [{r['category']:14}] -> {r['winner']:22} "
              f"acc {r['accuracy']}/floor {r['accuracy_floor']}  cost {r['cost']}  "
              f"tokens {r['tokens_in']}/{r['tokens_out']} (compress saves {r['tokens_saved_by_compression']}){fr_txt}")
    print(f"\n  winners: {result['by_winner']}")
    print(f"  per-call cost saved vs always-full-model: {result['per_call_cost_saved']}")
    print(f"  all within the tenant's accuracy confines: {result['all_within_confines']}; serves_truth: {result['serves_truth']}\n")


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    res = run_demo("cost-first-startup")
    ck("the demo runs the REAL engine on every sample skill (>=6) end-to-end",
       res["n_skills"] >= 6 and len(res["rows"]) == res["n_skills"])
    ck("every skill descends WITHIN the tenant's accuracy confines (no cheap-but-wrong fork) + never serves truth",
       res["all_within_confines"] is True and res["serves_truth"] is False
       and all(r["serves_truth"] is False for r in res["rows"]))
    ck("the demo shows DIVERSE descent outcomes (rule-guided -> deterministic; open-ended -> cheaper/compressed)",
       len(res["by_winner"]) >= 2, str(res["by_winner"]))
    ck("rule-guided skills descend to a deterministic fork (tax/geocode -> cost 0, no model tokens)",
       any(r["winner"] in ("direct_api_rule", "deterministic_extract") and r["cost"] == 0.0 for r in res["rows"]))
    ck("an open-ended skill descends to a cheaper model OR a compressed prompt (not a broken deterministic fork)",
       any(r["winner"] in ("model_downgrade", "prompt_compression") for r in res["rows"]
           if r["category"] in ("document", "email")))
    ck("fragile facts are freshness-bound and HOLD STALE OUT on a change (never serve stale)",
       any(r["freshness"] and r["freshness"]["on_change"] == "held_out" and r["freshness"]["stale_served"] is None
           for r in res["rows"]))
    ck("the demo reports a real per-call cost saving vs always running the full model", res["per_call_cost_saved"] > 0)
    ck("the demo is deterministic (same tenant -> same result)", run_demo("cost-first-startup") == res)
    # a different tenant (stricter accuracy tolerance) can change the winners.
    strict = run_demo("mit-only-bank")
    ck("a stricter tenant (mit-only-bank, tighter tolerance) also runs end-to-end within confines",
       strict["all_within_confines"] is True and strict["n_skills"] == res["n_skills"])

    print("\n" + ("PASS - demo_assurance_descent: the runnable demo executes the REAL assurance engine on every "
                  "sample skill under a tenant's preferences — token-aware A/B descent (deterministic / cheaper "
                  "model / compressed prompt, within accuracy confines), freshness for fragile facts (stale held "
                  "out), cost + token measurement, governed (serves_truth=false). Diverse outcomes; deterministic; "
                  "no mocks; never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Runnable demo of the Teleon assurance/descent engine on sample skills.")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--run", action="store_true")
    p.add_argument("--tenant", default=_DEFAULT_TENANT)
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    res = run_demo(a.tenant)
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        _print_demo(res)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
