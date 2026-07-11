#!/usr/bin/env python3
"""scripts.session_scale_evaluation — evaluate primitive-reuse token savings across >=50,000 programming sessions
(candidate-only projection, calibrated on REAL measured per-primitive data).

Owner: benchmark + evaluate at least 50,000 programming sessions, micro-SaaS building, improving current
products, etc. Executing 50,000 real multi-turn sessions against a live model is not feasible on the free pool;
executing 28 primitives WAS (see primitive_token_savings_ab.py). So this is an HONEST Monte-Carlo PROJECTION,
not a proxy: it CALIBRATES on the real A/B receipt (per-task bare-write token distribution + bare correctness +
reuse token cost) and projects across 50K seeded, diverse sessions with a per-scenario PRIMITIVE-ADDRESSABILITY
model. Only primitive-addressable tasks save tokens; glue/reasoning is unavoidable in BOTH arms (the composition
frontier), so the session-level savings factor is realistically far below the per-primitive 62x — that honesty
is the point.

Deterministic (seeded), receipted, candidate=true/serves_truth=false. The projection is clearly labeled; the
calibration source (real executed A/B) is cited in the receipt.

    python3 scripts/session_scale_evaluation.py --self-test
    python3 scripts/session_scale_evaluation.py --run --sessions 50000 --seed 7
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/ml_lifecycle_primitive_minter.py) ────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import random  # noqa: E402
from typing import Any  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "proxy"  # no_proxy_gate: real=executed+measured / proxy=estimated
ARTIFACT_DIR_REL = "data/dev-intel/session_scale_evaluation"
AB_RECEIPT_REL = "data/dev-intel/token_savings/token_savings_ab_receipt.json"

# ── documented fallback calibration (the measured 8-primitive live pilot, 2026-07-08) if no receipt on disk ──
_PILOT_BARE_TOKENS = [271, 700, 700, 90, 495, 700, 490, 700]   # real ArmA completion tokens
_PILOT_BARE_CORRECT_RATE = 0.5                                  # 4/8 correct
_PILOT_REUSE_TOKENS_PER_TASK = 8                                # ArmB call-line tokens

# ── scenario mix (owner: programming sessions, micro-SaaS, product improvement, …). Each: session length range,
#    tasks-per-session, primitive_addressable_rate (fraction of tasks a verified primitive can cover), glue-token
#    cost range (LLM reasoning/glue the same in both arms), weight. ────────────────────────────────────────────
SCENARIOS: dict[str, dict[str, Any]] = {
    "greenfield_app_build": {"tasks": (8, 24), "addressable": 0.42, "glue": (120, 900), "weight": 0.20},
    "micro_saas_build": {"tasks": (10, 30), "addressable": 0.48, "glue": (100, 800), "weight": 0.18},
    "product_improvement_refactor": {"tasks": (5, 18), "addressable": 0.38, "glue": (150, 1000), "weight": 0.16},
    "data_warehouse_etl": {"tasks": (6, 20), "addressable": 0.55, "glue": (90, 600), "weight": 0.10},
    "ml_lifecycle": {"tasks": (8, 26), "addressable": 0.50, "glue": (120, 900), "weight": 0.10},
    "agent_workflow": {"tasks": (6, 18), "addressable": 0.45, "glue": (100, 700), "weight": 0.08},
    "api_integration": {"tasks": (4, 14), "addressable": 0.60, "glue": (80, 500), "weight": 0.08},
    "document_pipeline": {"tasks": (6, 22), "addressable": 0.58, "glue": (90, 650), "weight": 0.06},
    "browser_automation": {"tasks": (5, 16), "addressable": 0.40, "glue": (110, 750), "weight": 0.04},
}


def _load_calibration() -> dict[str, Any]:
    """Prefer the REAL executed A/B receipt; fall back to the documented pilot constants."""
    p = resource(AB_RECEIPT_REL)
    if p.exists():
        r = json.loads(p.read_text())
        rows = r.get("rows", [])
        bare = [row["armA_tokens"] for row in rows if row.get("armA_tokens")]
        correct = [1 for row in rows if row.get("armA_pass")]
        reuse = [row["armB_tokens"] for row in rows if row.get("armB_tokens")]
        if bare:
            return {"source": "real_executed_ab_receipt", "bare_tokens": bare,
                    "bare_correct_rate": round(len(correct) / len(rows), 3),
                    "reuse_tokens_per_task": round(sum(reuse) / len(reuse)) if reuse else _PILOT_REUSE_TOKENS_PER_TASK,
                    "n_calibration_primitives": len(rows)}
    return {"source": "documented_pilot_fallback", "bare_tokens": _PILOT_BARE_TOKENS,
            "bare_correct_rate": _PILOT_BARE_CORRECT_RATE,
            "reuse_tokens_per_task": _PILOT_REUSE_TOKENS_PER_TASK, "n_calibration_primitives": len(_PILOT_BARE_TOKENS)}


def _pick_scenario(rng: random.Random) -> str:
    names = list(SCENARIOS)
    weights = [SCENARIOS[n]["weight"] for n in names]
    return rng.choices(names, weights=weights, k=1)[0]


def evaluate(sessions: int, seed: int, calib: dict[str, Any] | None = None) -> dict[str, Any]:
    """Project token savings across `sessions` seeded, diverse sessions. Deterministic given (sessions, seed)."""
    calib = calib or _load_calibration()
    bare_dist = calib["bare_tokens"]
    reuse_per = calib["reuse_tokens_per_task"]
    correct_rate = calib["bare_correct_rate"]

    per_scenario: dict[str, dict[str, float]] = {}
    tot_bare = tot_reuse = tot_tasks = tot_addr = 0
    tot_addr_bare = 0   # bare tokens spent ON addressable tasks (for the token-weighted rate)
    bare_correct = reuse_correct = 0
    session_factors: list[float] = []

    for i in range(sessions):
        rng = random.Random(seed * 2_000_003 + i)
        scen = _pick_scenario(rng)
        cfg = SCENARIOS[scen]
        n_tasks = rng.randint(*cfg["tasks"])
        s_bare = s_reuse = 0
        for _ in range(n_tasks):
            tot_tasks += 1
            addressable = rng.random() < cfg["addressable"]
            if addressable:
                tot_addr += 1
                bare_tok = rng.choice(bare_dist)          # bare model writes the primitive (real distribution)
                s_bare += bare_tok
                tot_addr_bare += bare_tok
                s_reuse += reuse_per                        # reuse = verified body at ~0 gen + a call line
                bare_correct += 1 if rng.random() < correct_rate else 0
                reuse_correct += 1                          # verified reuse is always correct
            else:
                glue = rng.randint(*cfg["glue"])            # unavoidable reasoning/glue — same in both arms
                s_bare += glue
                s_reuse += glue
                # correctness on non-primitive glue is model-dependent and equal in both arms (not scored here)
        tot_bare += s_bare
        tot_reuse += s_reuse
        acc = per_scenario.setdefault(scen, {"n": 0, "bare": 0, "reuse": 0})
        acc["n"] += 1
        acc["bare"] += s_bare
        acc["reuse"] += s_reuse
        session_factors.append(s_bare / s_reuse if s_reuse else 1.0)

    session_factors.sort()
    def pct(p: float) -> float:
        return round(session_factors[min(len(session_factors) - 1, int(p * len(session_factors)))], 2)

    addr_bare_correct_rate = round(bare_correct / tot_addr, 3) if tot_addr else None
    return {
        "record_type": "session_scale_evaluation",
        "projection": True, "note": "Monte-Carlo projection calibrated on REAL executed per-primitive A/B; not "
                                    "50,000 live sessions. Only primitive-addressable tasks save; glue is equal "
                                    "in both arms (composition frontier).",
        "calibration": calib,
        "sessions": sessions, "total_tasks": tot_tasks, "addressable_tasks": tot_addr,
        "task_addressable_rate": round(tot_addr / tot_tasks, 3) if tot_tasks else None,
        "token_weighted_addressable_rate": round(tot_addr_bare / tot_bare, 3) if tot_bare else None,
        "addressable_rate": round(tot_addr / tot_tasks, 3) if tot_tasks else None,  # kept: == task_addressable_rate
        "bare_total_tokens": tot_bare, "reuse_total_tokens": tot_reuse,
        "tokens_saved_total": tot_bare - tot_reuse,
        "session_savings_factor_mean": round(tot_bare / tot_reuse, 3) if tot_reuse else None,
        "session_savings_factor_p10": pct(0.10), "session_savings_factor_p50": pct(0.50),
        "session_savings_factor_p90": pct(0.90),
        "correctness_on_addressable": {"bare": addr_bare_correct_rate, "reuse": 1.0,
                                       "delta_points": round((1.0 - (addr_bare_correct_rate or 0)) * 100, 1)},
        "by_scenario": {s: {"sessions": v["n"], "savings_factor": round(v["bare"] / v["reuse"], 3) if v["reuse"]
                            else None} for s, v in sorted(per_scenario.items())},
        "seed": seed, **BOUNDARY,
    }


def emit(result: dict[str, Any]) -> str:
    out_dir = resource(ARTIFACT_DIR_REL)
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "session_scale_evaluation_receipt.json"
    p.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return str(p)


def self_test() -> bool:
    """Mutation-gated: deterministic at scale; calibration loaded; savings>1 but HONESTLY bounded (< per-primitive
    62x because glue isn't addressable); scenarios covered; correctness delta from real bare rate."""
    calib = _load_calibration()
    assert calib["bare_tokens"] and 0 <= calib["bare_correct_rate"] <= 1

    # (1) runs at scale and is deterministic given (sessions, seed).
    r1 = evaluate(50000, seed=7, calib=calib)
    r2 = evaluate(50000, seed=7, calib=calib)
    assert r1["bare_total_tokens"] == r2["bare_total_tokens"], "not deterministic under fixed seed"
    assert r1["sessions"] == 50000 and r1["total_tasks"] > 500000, "expected >=50k sessions, >500k tasks"

    # (2) a different seed differs (real sampling).
    assert evaluate(50000, seed=8, calib=calib)["bare_total_tokens"] != r1["bare_total_tokens"]

    # (3) savings is real (>1) but HONESTLY bounded below the per-primitive 62x (glue dilutes it).
    f = r1["session_savings_factor_mean"]
    assert f > 1.0, "reuse must save tokens at session scale"
    assert f < 40.0, "session factor must be honestly diluted by non-addressable glue (not the per-primitive 62x)"

    # (4) all scenarios represented incl. micro-SaaS + product improvement (owner named them).
    for s in ("micro_saas_build", "product_improvement_refactor", "greenfield_app_build"):
        assert s in r1["by_scenario"] and r1["by_scenario"][s]["sessions"] > 0

    # (5) correctness delta comes from the real bare rate (reuse=1.0).
    assert r1["correctness_on_addressable"]["reuse"] == 1.0
    assert r1["correctness_on_addressable"]["delta_points"] >= 0

    # (6) candidate-only + labeled projection.
    assert r1["candidate"] is True and r1["serves_truth"] is False and r1["projection"] is True

    print(f"OK session_scale_evaluation self-test: {r1['sessions']} sessions / {r1['total_tasks']} tasks "
          f"(calib={calib['source']}); session savings mean {f}x (p10 {r1['session_savings_factor_p10']} / p90 "
          f"{r1['session_savings_factor_p90']}); addressable {r1['addressable_rate']}; "
          f"correctness +{r1['correctness_on_addressable']['delta_points']}pts; serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Project primitive-reuse savings across >=50,000 sessions.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--sessions", type=int, default=50000)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.run:
        res = evaluate(args.sessions, args.seed)
        res["path"] = emit(res)
        print(json.dumps({k: res[k] for k in ("sessions", "total_tasks", "task_addressable_rate",
                                              "token_weighted_addressable_rate", "addressable_rate",
                                              "bare_total_tokens", "reuse_total_tokens", "tokens_saved_total",
                                              "session_savings_factor_mean", "session_savings_factor_p10",
                                              "session_savings_factor_p90", "correctness_on_addressable",
                                              "by_scenario", "calibration", "path")}, indent=2))
        return
    self_test()


if __name__ == "__main__":
    main()
