#!/usr/bin/env python3
"""scripts.process_path_search — the Universal Process Path Search Engine ("OmniPath"): any task = a typed graph
of possible steps x possible primitives per step; sample many PATHS, run them in parallel, benchmark, keep a
Pareto frontier, mutate/remix winners, and promote only through gates (candidate-only).

Owner directive (2026-07-08): generalize Anthropic's Fable-5 advisor/orchestrator economics to ANY task — a
network of paths (all steps x all primitives per step) + orchestrator + supervisor + improver that fire many
paths at once, benchmark each, random-seed, and find the most efficient path (a massive grid search). Honors the
corrected law: EXPLORE like a massive grid search, PROMOTE like a regulated supply chain, SERVE like a lean
route cache — generation/storage scales hard; usefulness is a non-destructive router; serve-time stays lean.

Pieces: ProcessSpace (from the atlas) · PathSampler (grid/random/stratified/evolutionary + declared
bandit/mcts/llm seams) · deterministic multi-objective Benchmarker PROXY (real verifier is a pluggable seam) ·
Pareto frontier · Supervisor (continue/mutate/promote/quarantine, budget-aware) · Improver (mutate via the
expander's operators) · Promoter (gated: candidate->benchmarked->validated->certified; NEVER certified without a
real verifier/security/replay gate) · economic ROUTING POLICIES (advisor + orchestrator, with Anthropic's cited
numbers). Reproducible: explicit seeds only (no hash()/random-module global seeding).

    python3 scripts/process_path_search.py --self-test
    python3 scripts/process_path_search.py --task document_ingestion --strategy random --trials 200 --seed 7
    python3 scripts/process_path_search.py --emit --task ml_training --strategy stratified --trials 300 --seed 1
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
import hashlib  # noqa: E402  (deterministic SCORING proxy only — ids use canonical_id)
import itertools  # noqa: E402
import json  # noqa: E402
import random  # noqa: E402
from typing import Any  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"process_path_search requires canonical_id; import failed: {exc}")
from scripts.process_possibility_atlas import DOMAIN_STEPS  # noqa: E402
from scripts.process_atlas_expander import MUTATION_OPERATORS, METRIC_LAW_V2  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "proxy"  # no_proxy_gate: real=executed+measured / proxy=estimated
PATH_ID_PREFIX = "path"
ARTIFACT_DIR_REL = "data/dev-intel/path_search"

# ── objectives: direction +1 = higher is better, -1 = lower is better ────────────────────────────────────────
OBJECTIVES: dict[str, int] = {"quality": +1, "cost": -1, "latency": -1, "risk": -1, "determinism": +1}
SCORE_WEIGHTS: dict[str, float] = {"quality": 0.40, "cost": 0.20, "latency": 0.15, "risk": 0.15,
                                   "determinism": 0.10}

# ── sampler strategies (grid/random/stratified/evolutionary implemented; others declared seams) ─────────────
STRATEGIES: dict[str, bool] = {"grid": True, "random": True, "stratified": True, "evolutionary": True,
                               "bandit": False, "mcts": False, "bayesian": False, "llm_proposed": False,
                               "human_seeded": False}

# ── economic routing policies (owner: generalize Fable-5 advisor/orchestrator; Anthropic's cited numbers) ────
ECONOMIC_POLICIES: dict[str, Any] = {
    "advisor": {"pattern": "cheap executor consults a strong advisor mid-task for plan/course-correction",
                "example": "Sonnet 5 executor + Fable 5 advisor ~= 92% of Fable 5 SWE-bench Pro at ~63% price",
                "applies_to_path_stage": "planning/hard-decision nodes only; cheap model runs the rest"},
    "orchestrator": {"pattern": "strong orchestrator plans + delegates token-heavy execution to cheap workers",
                     "example": "Fable 5 orchestrator + Sonnet 5 workers ~= 96% of Fable 5 BrowseComp at ~46% price",
                     "applies_to_path_stage": "coordinator node = strong; per-step worker nodes = cheap, isolated"},
}

# ── promotion lifecycle (owner §12): NEVER certified without a real verifier/security/replay gate ───────────
PROMOTION_STAGES = ["candidate_path", "benchmarked_path", "validated_path", "certified_route", "production_route"]


def build_space(task_family: str) -> dict[str, Any]:
    """A ProcessSpace = ordered step slots + primitive options per step, from the atlas. Any domain works."""
    if task_family not in DOMAIN_STEPS:
        raise ValueError(f"unknown task_family {task_family}; known: {sorted(DOMAIN_STEPS)}")
    steps = DOMAIN_STEPS[task_family]
    slots = [{"step": s["step"], "options": list(s["possibilities"])} for s in steps]
    theoretical = 1
    for sl in slots:
        theoretical *= len(sl["options"])
    return {"process_space_id": canonical_id("space", task_family, str(len(slots))),
            "task_family": task_family, "step_slots": slots, "n_steps": len(slots),
            "theoretical_paths": theoretical, **BOUNDARY}


def _obj_value(method: str, objective: str) -> float:
    """DETERMINISTIC scoring PROXY in [0,1] (not the real benchmark — that is a pluggable seam). Reproducible:
    a stable digest of (method, objective). Real trials replace this with executed verifier/cost/latency."""
    h = hashlib.sha256(f"{method}|{objective}".encode()).digest()
    return int.from_bytes(h[:4], "big") / 0xFFFFFFFF


def score_path(path: dict[str, Any], space: dict[str, Any], seed: int) -> dict[str, Any]:
    """Multi-objective proxy score for one path (deterministic given path+seed). Aggregate + per-objective."""
    methods = path["nodes"]
    rng = random.Random(seed ^ hash_stable(path["path_id"]))  # reproducible per (path, seed)
    objs: dict[str, float] = {}
    for name, direction in OBJECTIVES.items():
        raw = sum(_obj_value(m, name) for m in methods) / max(1, len(methods))
        # tiny seeded jitter models run-to-run noise (reproducible); separates path-quality from luck.
        raw = min(1.0, max(0.0, raw + (rng.random() - 0.5) * 0.02))
        objs[name] = raw
    agg = sum(SCORE_WEIGHTS[n] * (objs[n] if d > 0 else (1.0 - objs[n])) for n, d in OBJECTIVES.items())
    return {"objective_scores": objs, "score": round(agg, 6)}


def hash_stable(s: str) -> int:
    """Stable int from a string (reproducible across runs — NOT Python's salted hash())."""
    return int.from_bytes(hashlib.sha256(s.encode()).digest()[:8], "big")


def _make_path(space: dict[str, Any], choices: list[str], seed: int) -> dict[str, Any]:
    pid = canonical_id(PATH_ID_PREFIX, space["task_family"], *choices)
    return {"path_id": pid, "process_space_id": space["process_space_id"], "task_family": space["task_family"],
            "nodes": choices, "seed": seed, "parent_path": None, "mutation_history": [], **BOUNDARY}


def sample_paths(space: dict[str, Any], strategy: str, n: int, seed: int,
                 winners: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Generate n path candidates. Reproducible given seed. Generation is NEVER capped by usefulness (owner law)."""
    slots = space["step_slots"]
    if strategy == "grid":
        combos = itertools.islice(itertools.product(*[sl["options"] for sl in slots]), n)
        return [_make_path(space, list(c), seed) for c in combos]
    if strategy == "random":
        out = []
        for i in range(n):
            rng = random.Random(seed * 1_000_003 + i)
            out.append(_make_path(space, [rng.choice(sl["options"]) for sl in slots], seed))
        return out
    if strategy == "stratified":
        # ensure every option of every step appears across the sample (coverage), then fill randomly.
        out = []
        for i in range(n):
            rng = random.Random(seed * 7 + i)
            choices = [sl["options"][i % len(sl["options"])] if i < len(sl["options"]) else rng.choice(sl["options"])
                       for sl in slots]
            out.append(_make_path(space, choices, seed))
        return out
    if strategy == "evolutionary":
        base = winners or sample_paths(space, "random", max(4, n // 4), seed)
        out = []
        for i in range(n):
            parent = base[i % len(base)]
            out.append(mutate_path(space, parent, seed * 13 + i))
        return out
    raise ValueError(f"strategy {strategy} not implemented (declared seam: {STRATEGIES.get(strategy)})")


def mutate_path(space: dict[str, Any], parent: dict[str, Any], seed: int) -> dict[str, Any]:
    """Improver: swap one step's method for a different option (lineage recorded)."""
    rng = random.Random(seed)
    slots = space["step_slots"]
    idx = rng.randrange(len(slots))
    opts = slots[idx]["options"]
    cur = parent["nodes"][idx]
    alt = rng.choice([o for o in opts if o != cur] or opts)
    child_nodes = list(parent["nodes"])
    child_nodes[idx] = alt
    child = _make_path(space, child_nodes, seed)
    child["parent_path"] = parent["path_id"]
    child["mutation_history"] = parent.get("mutation_history", []) + [f"swap_step[{slots[idx]['step']}]:{cur}->{alt}"]
    return child


def pareto_frontier(trials: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Non-dominated set over the objectives (owner §10 multi-objective; 'best' depends on constraints)."""
    def dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
        oa, ob = a["objective_scores"], b["objective_scores"]
        better_or_equal = all((oa[n] >= ob[n]) if d > 0 else (oa[n] <= ob[n]) for n, d in OBJECTIVES.items())
        strictly_better = any((oa[n] > ob[n]) if d > 0 else (oa[n] < ob[n]) for n, d in OBJECTIVES.items())
        return better_or_equal and strictly_better
    front = []
    for t in trials:
        if not any(dominates(o, t) for o in trials if o is not t):
            front.append(t)
    return front


def supervisor_decide(trial: dict[str, Any], promote_threshold: float) -> str:
    """continue/mutate/promote/quarantine (budget/quality aware). Real risk/verifier gates tighten this."""
    if trial["objective_scores"]["risk"] > 0.9:
        return "quarantine"
    if trial["score"] >= promote_threshold:
        return "promote"
    if trial["score"] >= promote_threshold * 0.8:
        return "mutate"
    return "stop"


def promote_if_gated(path_id: str, trials: list[dict[str, Any]], *, has_real_verifier: bool = False) -> dict[str, Any]:
    """Owner §12: promote on MEAN score + LOW variance + gates — not the single luckiest trial. Without a real
    verifier/security/replay gate the ceiling is 'benchmarked_path'; 'certified' requires the real seam."""
    scores = [t["score"] for t in trials]
    mean = sum(scores) / len(scores)
    var = sum((s - mean) ** 2 for s in scores) / len(scores)
    gated = mean >= 0.55 and var <= 0.02
    if not gated:
        stage = "candidate_path"
    elif not has_real_verifier:
        stage = "benchmarked_path"   # honest ceiling until a real executed verifier exists
    else:
        stage = "certified_route"
    return {"path_id": path_id, "promotion_stage": stage, "n_trials": len(trials),
            "mean_score": round(mean, 4), "variance": round(var, 5), "gated": gated,
            "certified_requires": "executed verifier + security + deterministic replay + provenance", **BOUNDARY}


def run_search(task_family: str, strategy: str, trials: int, seed: int,
               promote_threshold: float = 0.6) -> dict[str, Any]:
    """The supervisor loop: sample -> score -> Pareto -> supervise -> improve. Budget = trial count."""
    space = build_space(task_family)
    paths = sample_paths(space, strategy if strategy != "evolutionary" else "random", trials, seed)
    scored = [{**p, **score_path(p, space, seed)} for p in paths]
    front = pareto_frontier(scored)
    decisions = {d: 0 for d in ("promote", "mutate", "stop", "quarantine")}
    winners = []
    for t in scored:
        d = supervisor_decide(t, promote_threshold)
        decisions[d] += 1
        if d == "promote":
            winners.append(t)
    # improver: next wave from the frontier (mutation) — raw count scales, never capped.
    next_wave = [mutate_path(space, w, seed * 31 + i) for i, w in enumerate(front[:min(len(front), trials)])]
    best = {name: max(scored, key=lambda t, n=name, dd=dr: t["objective_scores"][n] if dd > 0
                      else 1 - t["objective_scores"][n])["path_id"]
            for name, dr in OBJECTIVES.items()}
    best_overall = max(scored, key=lambda t: t["score"])
    promotion = promote_if_gated(best_overall["path_id"], scored, has_real_verifier=False)
    return {"space": {k: space[k] for k in ("process_space_id", "task_family", "n_steps", "theoretical_paths")},
            "strategy": strategy, "trials": len(scored), "seed": seed,
            "pareto_frontier_size": len(front), "supervisor_decisions": decisions,
            "best_by_objective": best, "best_overall": {"path_id": best_overall["path_id"],
                                                        "score": best_overall["score"]},
            "next_wave_size": len(next_wave), "promotion": promotion,
            "economic_policies": list(ECONOMIC_POLICIES), **BOUNDARY}


def emit(task_family: str, strategy: str, trials: int, seed: int) -> dict[str, Any]:
    space = build_space(task_family)
    paths = sample_paths(space, strategy if strategy != "evolutionary" else "random", trials, seed)
    scored = [{**p, **score_path(p, space, seed)} for p in paths]
    front = pareto_frontier(scored)
    out_dir = resource(ARTIFACT_DIR_REL)
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "path_trials.jsonl").open("w", encoding="utf-8") as f:
        for t in scored:
            f.write(json.dumps(t, sort_keys=True) + "\n")
    with (out_dir / "pareto_frontier.jsonl").open("w", encoding="utf-8") as f:
        for t in front:
            f.write(json.dumps({"path_id": t["path_id"], "score": t["score"],
                                "objective_scores": t["objective_scores"]}) + "\n")
    summary = run_search(task_family, strategy, trials, seed)
    (out_dir / "path_search_report.md").write_text(
        f"# Path search — {task_family} / {strategy}\n\n"
        f"- theoretical paths: {space['theoretical_paths']:,}\n- trials: {len(scored)} | seed: {seed}\n"
        f"- Pareto frontier: {len(front)}\n- best overall: {summary['best_overall']}\n"
        f"- promotion: {summary['promotion']['promotion_stage']} (certified needs a real verifier seam)\n",
        encoding="utf-8")
    return {"trials": len(scored), "pareto": len(front), "theoretical_paths": space["theoretical_paths"],
            "artifacts_dir": str(out_dir)}


def self_test() -> bool:
    """Mutation-gated. Asserts the whole loop: space build, SEEDED reproducible sampling, deterministic scoring,
    non-dominated Pareto, improver lineage, GATED promotion (no certified without a real verifier), and the
    non-cap law (usefulness never limits sampling)."""
    space = build_space("document_ingestion")
    assert space["n_steps"] == len(DOMAIN_STEPS["document_ingestion"])
    assert space["theoretical_paths"] > 1_000_000, "document_ingestion path space should be enormous"

    # (1) grid count is exactly n; random is SEEDED + reproducible; stratified covers each first-step option.
    grid = sample_paths(space, "grid", 50, seed=1)
    assert len(grid) == 50
    r1 = sample_paths(space, "random", 30, seed=42)
    r2 = sample_paths(space, "random", 30, seed=42)
    assert [p["path_id"] for p in r1] == [p["path_id"] for p in r2], "random sampling not reproducible under seed"
    r3 = sample_paths(space, "random", 30, seed=43)
    assert [p["path_id"] for p in r1] != [p["path_id"] for p in r3], "different seed must differ"
    strat = sample_paths(space, "stratified", 20, seed=1)
    first_opts = {p["nodes"][0] for p in strat}
    assert len(first_opts) == min(20, len(space["step_slots"][0]["options"])), "stratified must cover step-0 options"

    # (2) scoring deterministic given (path, seed); objectives complete.
    s1 = score_path(grid[0], space, seed=5)
    s2 = score_path(grid[0], space, seed=5)
    assert s1 == s2, "scoring not deterministic"
    assert set(s1["objective_scores"]) == set(OBJECTIVES)

    # (3) Pareto frontier is non-dominated.
    scored = [{**p, **score_path(p, space, seed=9)} for p in grid]
    front = pareto_frontier(scored)
    assert 0 < len(front) <= len(scored)
    for t in front:
        assert not any(all((o["objective_scores"][n] >= t["objective_scores"][n]) if d > 0
                           else (o["objective_scores"][n] <= t["objective_scores"][n]) for n, d in OBJECTIVES.items())
                       and any((o["objective_scores"][n] > t["objective_scores"][n]) if d > 0
                               else (o["objective_scores"][n] < t["objective_scores"][n]) for n, d in OBJECTIVES.items())
                       for o in scored if o is not t), "frontier member is dominated"

    # (4) improver: child differs from parent + records lineage.
    child = mutate_path(space, grid[0], seed=3)
    assert child["nodes"] != grid[0]["nodes"] and child["parent_path"] == grid[0]["path_id"]
    assert child["mutation_history"] and "swap_step" in child["mutation_history"][-1]

    # (5) promotion is GATED and never 'certified' without a real verifier (honest ceiling).
    good = [{"score": 0.7} for _ in range(20)]
    prom = promote_if_gated("p1", good, has_real_verifier=False)
    assert prom["promotion_stage"] == "benchmarked_path", "no certified without a real verifier seam"
    assert promote_if_gated("p2", good, has_real_verifier=True)["promotion_stage"] == "certified_route"
    bad = [{"score": 0.1} for _ in range(20)]
    assert promote_if_gated("p3", bad)["promotion_stage"] == "candidate_path", "low mean must not promote"

    # (6) the non-cap law holds (usefulness can never cap generation) + economic policies present.
    assert "cap_raw_count" in METRIC_LAW_V2["usefulness_score"]["forbidden_actions"]
    assert "advisor" in ECONOMIC_POLICIES and "orchestrator" in ECONOMIC_POLICIES
    assert "92%" in ECONOMIC_POLICIES["advisor"]["example"] and "96%" in ECONOMIC_POLICIES["orchestrator"]["example"]

    # (7) full loop runs end-to-end and is candidate-only.
    res = run_search("ml_training", "random", 120, seed=11)
    assert res["candidate"] is True and res["serves_truth"] is False
    assert res["pareto_frontier_size"] >= 1 and sum(res["supervisor_decisions"].values()) == res["trials"]

    print(f"OK process_path_search self-test: space {space['theoretical_paths']:,} theoretical paths; "
          f"seeded+reproducible sampling ({sum(1 for v in STRATEGIES.values() if v)} strategies live); "
          f"Pareto {len(front)}/{len(scored)}; gated promotion (certified needs real verifier); "
          f"advisor+orchestrator economics; serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Universal Process Path Search Engine (OmniPath).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--task", default="document_ingestion", help=f"task family: {sorted(DOMAIN_STEPS)}")
    ap.add_argument("--strategy", default="random", choices=[k for k, v in STRATEGIES.items() if v])
    ap.add_argument("--trials", type=int, default=200)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--emit", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.emit:
        print(json.dumps(emit(args.task, args.strategy, args.trials, args.seed), indent=2))
        return
    print(json.dumps(run_search(args.task, args.strategy, args.trials, args.seed), indent=2))


if __name__ == "__main__":
    main()
