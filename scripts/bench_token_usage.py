#!/usr/bin/env python3
"""scripts.bench_token_usage — measure TOKENS · COST · RELIABILITY of building a capability: BARE vs TELEON+HUBS.

The proof of the wedge, as a benchmark. For each scenario it runs two arms and records REAL token usage (from
_llm_client's usage field), cost (from architecture/model_index.json), and reliability (deterministic pass-check
over N trials):
  * BARE   — one strong frontier model generates everything from scratch (the "use the big model for everything").
  * TELEON — cheaper model, primed with a HUB COMPONENT scaffold (fewer generation tokens), escalating only if the
             pass-check fails (the descent). Reuse-not-regenerate + cheap-first.
Reports tokens_saved%, cost_saved%, reliability delta → data/dev-intel/benchmarks.jsonl. serves_truth=false.
Builds on scripts/eval/measured_lift_headtohead.py (the with/without A/B) + economics/cost_model.

  --self-test                                    offline (injected fake model; verifies math + governance)
  --run [--scenario id] [--trials N]             live (needs the Ollama lane) → records results + savings
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
MODEL_INDEX = REPO / "architecture" / "model_index.json"
OUT = REPO / "data" / "dev-intel" / "benchmarks.jsonl"

BARE_MODEL = "glm-5.2"            # the "strong model for everything" baseline
TELEON_CHEAP = "kimi-k2.7-code"   # cheap-first coder
TELEON_ESCALATE = "glm-5.2"       # escalate only on a failed pass-check

#: build-a-capability scenarios. pass_check is deterministic (no LLM-judge) so reliability is objective.
SCENARIOS = [
    {"id": "json_schema", "task": "Output ONLY a minimal JSON object with keys 'name','type','fields' for a user record. No prose.",
     "scaffold": '{"name":"user","type":"object","fields":[]}', "check": "json_obj"},
    {"id": "regex_email", "task": "Output ONLY a Python regex string that matches an email address. No prose, no code fences.",
     "scaffold": r"[\w.+-]+@[\w-]+\.[\w.-]+", "check": "nonempty_line"},
    {"id": "pipeline_steps", "task": "Output ONLY a JSON array of 3 stage names for a doc->schema extraction pipeline.",
     "scaffold": '["ingest","extract","validate"]', "check": "json_arr"},
]


def model_costs() -> dict:
    out = {}
    for e in json.loads(MODEL_INDEX.read_text(encoding="utf-8")).get("entries", []):
        out[e["model_id"]] = (e.get("cost_per_mtok_in", 0.0), e.get("cost_per_mtok_out", 0.0))
    return out


def cost_usd(model: str, tin: int, tout: int, costs: dict) -> float:
    ci, co = costs.get(model, (0.0, 0.0))
    return (tin * ci + tout * co) / 1_000_000.0


def passes(check: str, text: str) -> bool:
    t = (text or "").strip().strip("`")
    try:
        if check == "json_obj":
            return isinstance(json.loads(t), dict)
        if check == "json_arr":
            return isinstance(json.loads(t), list)
        if check == "nonempty_line":
            return bool(t) and "\n" not in t.strip()
    except Exception:
        return False
    return False


def _real_call(model: str, system: str, user: str) -> dict:
    from scripts._llm_client import chat, resolve_provider
    p = resolve_provider("ollama")
    if not p.get("key"):
        return {"text": "", "usage": {}, "error": "no key"}
    return chat(model, system, user, p, max_tokens=512, timeout=120)


def _usage(r: dict) -> tuple[int, int]:
    u = r.get("usage", {})
    return int(u.get("prompt_tokens", 0)), int(u.get("completion_tokens", 0))


def run_arm(scenario: dict, arm: str, costs: dict, call=_real_call) -> dict:
    """One trial of one arm. Returns tokens/cost/passed for the arm (cascade summed for teleon)."""
    if arm == "bare":
        r = call(BARE_MODEL, "You are a precise generator.", scenario["task"])
        tin, tout = _usage(r)
        return {"model": BARE_MODEL, "tin": tin, "tout": tout, "cost": cost_usd(BARE_MODEL, tin, tout, costs),
                "passed": passes(scenario["check"], r.get("text", "")), "calls": 1}
    # teleon: cheap model primed with a hub-component scaffold (fewer tokens), escalate only if it fails the check
    primed = f"Start from this hub component and complete it:\n{scenario['scaffold']}\n\nTask: {scenario['task']}"
    r = call(TELEON_CHEAP, "You compose from a provided scaffold. PUBLIC only.", primed)
    tin, tout = _usage(r)
    tot_in, tot_out, calls = tin, tout, 1
    ok = passes(scenario["check"], r.get("text", ""))
    model = TELEON_CHEAP
    if not ok:
        r2 = call(TELEON_ESCALATE, "You compose from a provided scaffold.", primed)
        a, b = _usage(r2)
        tot_in += a; tot_out += b; calls += 1; ok = passes(scenario["check"], r2.get("text", "")); model = TELEON_ESCALATE
    cost = cost_usd(TELEON_CHEAP, tin, tout, costs) + (cost_usd(TELEON_ESCALATE, tot_in - tin, tot_out - tout, costs) if calls > 1 else 0.0)
    return {"model": model, "tin": tot_in, "tout": tot_out, "cost": cost, "passed": ok, "calls": calls}


def compare(scenario: dict, trials: int, costs: dict, call=_real_call) -> dict:
    arms = {}
    for arm in ("bare", "teleon"):
        runs = [run_arm(scenario, arm, costs, call) for _ in range(trials)]
        n = len(runs)
        arms[arm] = {
            "avg_tokens": sum(r["tin"] + r["tout"] for r in runs) / n,
            "avg_cost_usd": sum(r["cost"] for r in runs) / n,
            "pass_rate": sum(r["passed"] for r in runs) / n,
            "avg_calls": sum(r["calls"] for r in runs) / n,
        }
    b, t = arms["bare"], arms["teleon"]
    pct = lambda lo, hi: round((hi - lo) / hi * 100, 1) if hi else 0.0
    return {"scenario": scenario["id"], "trials": trials, "arms": arms,
            "tokens_saved_pct": pct(t["avg_tokens"], b["avg_tokens"]),
            "cost_saved_pct": pct(t["avg_cost_usd"], b["avg_cost_usd"]),
            "reliability_delta": round(t["pass_rate"] - b["pass_rate"], 3),
            "serves_truth": False, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}


#: build-an-APP scenarios — a whole app is a SEQUENCE of capability steps; with hubs, each step reuses a component.
APPS = [
    {"id": "doc_to_schema_app", "steps": ["pipeline_steps", "json_schema", "regex_email"]},
    {"id": "log_report_app", "steps": ["json_schema", "pipeline_steps"]},
]


def build_app(app: dict, trials: int, costs: dict, call=_real_call) -> dict:
    """Build a whole app (a sequence of capability steps) WITH hubs (reuse components) vs WITHOUT (from scratch),
    summing REAL token usage across every step → the cumulative wedge for an end-to-end build. serves_truth=false."""
    by_id = {s["id"]: s for s in SCENARIOS}
    steps = [by_id[sid] for sid in app["steps"] if sid in by_id]
    arms = {"without_hubs": {"tokens": 0.0, "cost": 0.0, "passed": 0.0},
            "with_hubs": {"tokens": 0.0, "cost": 0.0, "passed": 0.0}}
    for s in steps:
        c = compare(s, trials, costs, call)
        for dst, src in (("without_hubs", "bare"), ("with_hubs", "teleon")):
            arms[dst]["tokens"] += c["arms"][src]["avg_tokens"]
            arms[dst]["cost"] += c["arms"][src]["avg_cost_usd"]
            arms[dst]["passed"] += c["arms"][src]["pass_rate"]
    n = len(steps) or 1
    for arm in arms.values():
        arm["pass_rate"] = round(arm.pop("passed") / n, 3)
        arm["cost"] = round(arm["cost"], 6)
    pct = lambda lo, hi: round((hi - lo) / hi * 100, 1) if hi else 0.0  # noqa: E731
    return {"app": app["id"], "steps": len(steps), "trials": trials, "arms": arms,
            "tokens_saved_pct": pct(arms["with_hubs"]["tokens"], arms["without_hubs"]["tokens"]),
            "cost_saved_pct": pct(arms["with_hubs"]["cost"], arms["without_hubs"]["cost"]),
            "serves_truth": False, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}


def run_apps(app_id: str | None, trials: int) -> dict:
    costs = model_costs()
    apps = [a for a in APPS if not app_id or a["id"] == app_id]
    results = [build_app(a, trials, costs) for a in apps]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("a", encoding="utf-8") as fh:
        for r in results:
            fh.write(json.dumps(r) + "\n")
    return {"apps": len(results), "results": results}


def run(scenario_id: str | None, trials: int) -> dict:
    costs = model_costs()
    scens = [s for s in SCENARIOS if not scenario_id or s["id"] == scenario_id]
    results = [compare(s, trials, costs) for s in scens]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("a", encoding="utf-8") as fh:
        for r in results:
            fh.write(json.dumps(r) + "\n")
    return {"scenarios": len(results), "results": results}


def self_test() -> int:
    costs = model_costs()
    assert costs.get(BARE_MODEL) and costs.get(TELEON_CHEAP), "model_index must carry costs for the arms"
    # injected fake model: bare returns valid JSON with big usage; teleon's cheap scaffold gives valid JSON cheaply
    def fake(model, system, user):
        if "scaffold" in system.lower() or "compose" in system.lower():
            return {"text": '{"name":"user","type":"object","fields":[]}', "usage": {"prompt_tokens": 40, "completion_tokens": 20}}
        return {"text": '{"name":"user","type":"object","fields":[]}', "usage": {"prompt_tokens": 120, "completion_tokens": 200}}
    res = compare(SCENARIOS[0], 3, costs, call=fake)
    assert res["arms"]["bare"]["avg_tokens"] == 320 and res["arms"]["teleon"]["avg_tokens"] == 60, res["arms"]
    assert res["tokens_saved_pct"] > 70, f"teleon should save tokens: {res['tokens_saved_pct']}"
    assert res["arms"]["bare"]["pass_rate"] == 1.0 and res["arms"]["teleon"]["pass_rate"] == 1.0
    assert passes("json_obj", '{"a":1}') and not passes("json_obj", "nope")
    assert res["serves_truth"] is False
    # escalation path: cheap fails the check → escalate, 2 calls counted
    def fake_fail_then_ok(model, system, user):
        if model == TELEON_CHEAP:
            return {"text": "not json", "usage": {"prompt_tokens": 30, "completion_tokens": 10}}
        return {"text": "[1,2,3]", "usage": {"prompt_tokens": 30, "completion_tokens": 10}}
    esc = run_arm(SCENARIOS[2], "teleon", costs, call=fake_fail_then_ok)
    assert esc["calls"] == 2 and esc["passed"], esc
    # build-an-app: cumulative tokens WITH hubs << WITHOUT across a whole multi-step app
    def fake_app(model, system, user):
        scaffold = "compose" in system.lower() or "scaffold" in system.lower()
        usage = {"prompt_tokens": 40, "completion_tokens": 20} if scaffold else {"prompt_tokens": 120, "completion_tokens": 200}
        text = ('["ingest","extract","validate"]' if "JSON array" in user
                else '{"name":"user","type":"object","fields":[]}' if "JSON object" in user
                else r"[\w.+-]+@[\w-]+\.[\w.-]+")
        return {"text": text, "usage": usage}
    app_res = build_app(APPS[0], 2, costs, call=fake_app)
    assert app_res["steps"] == 3, app_res["steps"]
    assert app_res["arms"]["with_hubs"]["tokens"] < app_res["arms"]["without_hubs"]["tokens"], app_res["arms"]
    assert app_res["tokens_saved_pct"] > 70 and app_res["arms"]["with_hubs"]["pass_rate"] == 1.0, app_res
    print("bench_token_usage self-test: OK (per-capability + build-an-app with/without hubs, escalation, math)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()

    def opt(name, default=None):
        return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default

    if "--run" in argv:
        res = run(opt("--scenario"), int(opt("--trials", "3")))
        for r in res["results"]:
            print(f"  [{r['scenario']}] tokens -{r['tokens_saved_pct']}% · cost -{r['cost_saved_pct']}% · "
                  f"reliability Δ{r['reliability_delta']:+}  (bare {r['arms']['bare']['avg_tokens']:.0f} tok → "
                  f"teleon {r['arms']['teleon']['avg_tokens']:.0f} tok)")
        return 0
    if "--apps" in argv:
        res = run_apps(opt("--app"), int(opt("--trials", "3")))
        for r in res["results"]:
            print(f"  [{r['app']}] {r['steps']} steps · tokens -{r['tokens_saved_pct']}% · cost -{r['cost_saved_pct']}%  "
                  f"(without-hubs {r['arms']['without_hubs']['tokens']:.0f} tok → with-hubs {r['arms']['with_hubs']['tokens']:.0f} tok)")
        return 0
    print("usage: bench_token_usage.py --self-test | --run [--scenario id] | --apps [--app id] [--trials N]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
