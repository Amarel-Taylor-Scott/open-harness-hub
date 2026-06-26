#!/usr/bin/env python3
"""scripts.context_workers.distillation_runner — the scheduled DISTILLATION pass: turn discovered capabilities
into deterministic forks, cheapest-first, and let the meta-learner make it cheaper over time.

One pass (run_once): read the discovered/staged candidates -> for each not-yet-distilled capability at/above a
determinism-ceiling threshold, the meta-learner recommends the strategy, the distiller produces the deterministic
FORK + a DistillationRecord (within the org's confines), the record feeds the meta-learner, and state persists so
re-runs are IDEMPOTENT and learning ACCUMULATES across runs. Start at ceiling 1.0 (pure API/compute capabilities —
the cheapest, most-complete distillations) and lower the threshold on later scheduled runs.

Deterministic + offline + FREE (no model calls, no agents) — safe to schedule on a cron. The token-costing
discovery-AGENT waves stay owner-triggered. Long runs are owner-launched and stop only via .agent/STOP_REQUESTED.
Teleon-layer logic via src.teleon.evolution; reads/writes shared DATA only; never imports src.baltor.

CLI:
    python3 scripts/context_workers/distillation_runner.py --self-test
    python3 scripts/context_workers/distillation_runner.py --once --min-ceiling 0.99
    python3 scripts/context_workers/distillation_runner.py --loop --interval 3600   # owner-launched
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

from scripts.capability_seeder import normalize_candidate, screen, SeederError
from scripts.context_workers.capability_discovery_runner import discover
from src.teleon.evolution import DistillationMetaLearner, distill

_REPO = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_FEEDS_DIR = _REPO / "data" / "capability-candidates"
_STATE_PATH = _FEEDS_DIR / "distillation-state.json"
_STOP_FILE = _REPO / ".agent" / "STOP_REQUESTED"
_DEFAULT_MIN_CEILING = 0.99  # start with the pure-deterministic capabilities; lower on later scheduled runs

STATE_VERSION = "DistillationState"


def _load_state(state_path: Path) -> dict:
    if state_path.exists():
        return json.loads(state_path.read_text(encoding="utf-8"))
    return {"state_version": STATE_VERSION, "distilled_slots": [], "records": [], "runs": 0}


def _save_state(state_path: Path, state: dict) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = state_path.with_suffix(state_path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(state_path)


def _accepted_candidates(feeds_dir: Path) -> list[dict]:
    """Normalized + screened candidates from all discovered feeds (dedup by content_hash)."""
    out, seen = [], set()
    for raw in discover(feeds_dir):
        try:
            cand = normalize_candidate(raw)
        except SeederError:
            continue
        if cand["content_hash"] in seen or not screen(cand)["accepted"]:
            continue
        seen.add(cand["content_hash"])
        out.append(cand)
    return out


def run_once(*, feeds_dir: Path = _FEEDS_DIR, state_path: Path = _STATE_PATH,
             min_ceiling: float = _DEFAULT_MIN_CEILING, policy=None, now: str | None = None) -> dict:
    """One distillation pass. Distills every accepted candidate at/above ``min_ceiling`` not already distilled;
    the meta-learner (rebuilt from prior records) recommends each strategy; new records accumulate into state."""
    state = _load_state(state_path)
    done = set(state.get("distilled_slots", []))
    ml = DistillationMetaLearner()
    for r in state.get("records", []):
        try:
            ml.record(r)
        except ValueError:
            pass

    distilled, total_saving = [], 0.0
    for cand in sorted(_accepted_candidates(feeds_dir), key=lambda c: c["capability_slot"]):
        if cand["capability_slot"] in done or cand["determinism_ceiling"] < min_ceiling:
            continue
        strategy = ml.recommend_strategy(cand["category"], cand["determinism_ceiling"])["strategy"]
        result = distill(cand["capability_slot"], category=cand["category"],
                         determinism_ceiling=cand["determinism_ceiling"],
                         deterministic_coverage_estimate=cand["deterministic_coverage_estimate"],
                         strategy=strategy, policy=policy)
        rec = result["record"]
        ml.record(rec)
        state["records"].append(rec)
        if rec["applied"]:
            done.add(cand["capability_slot"])
            distilled.append(rec)
            total_saving += rec["coverage"] * (rec["per_call_cost_before"] - rec["per_call_cost_after"])

    state.update({"state_version": STATE_VERSION, "distilled_slots": sorted(done),
                  "runs": state.get("runs", 0) + 1})
    if now is not None:
        state["last_run"] = now
    _save_state(state_path, state)
    by_strategy: dict = {}
    for r in distilled:
        by_strategy[r["strategy"]] = by_strategy.get(r["strategy"], 0) + 1
    return {"newly_distilled": len(distilled), "total_distilled": len(done), "by_strategy": by_strategy,
            "per_call_cost_saving_added": round(total_saving, 6),
            "mean_coverage": round(sum(r["coverage"] for r in distilled) / len(distilled), 4) if distilled else 0.0,
            "meta_learner": ml.efficiency_summary(), "serves_truth": False}


def run_loop(*, feeds_dir: Path = _FEEDS_DIR, state_path: Path = _STATE_PATH, min_ceiling: float = _DEFAULT_MIN_CEILING,
             interval_s: float = 3600.0, stop_file: Path = _STOP_FILE, max_iterations: int | None = None,
             policy=None, sleep_fn=time.sleep, now: str | None = None) -> dict:
    """Owner-launched continuous distillation: run_once, sleep, repeat — until the stop file or max_iterations."""
    iters, total_new = 0, 0
    while True:
        if stop_file.exists() or (max_iterations is not None and iters >= max_iterations):
            break
        rep = run_once(feeds_dir=feeds_dir, state_path=state_path, min_ceiling=min_ceiling, policy=policy, now=now)
        total_new += rep["newly_distilled"]
        iters += 1
        if stop_file.exists() or (max_iterations is not None and iters >= max_iterations):
            break
        sleep_fn(interval_s)
    return {"iterations": iters, "total_newly_distilled": total_new,
            "stopped_by": "stop_file" if stop_file.exists() else "max_iterations", "serves_truth": False}


def _self_test() -> int:
    import tempfile

    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    with tempfile.TemporaryDirectory() as td:
        state = Path(td) / "distill-state.json"

        # FIRST pass over the real corpus at ceiling 1.0 -> distill the pure-deterministic capabilities.
        r1 = run_once(feeds_dir=_FEEDS_DIR, state_path=state, min_ceiling=0.99, now="t0")
        ck("distills the ceiling-1.0 capabilities into deterministic forks (>=8)",
           r1["newly_distilled"] >= 8 and r1["serves_truth"] is False, str(r1["newly_distilled"]))
        ck("every ceiling-1.0 distillation uses the cheap direct_api_rule strategy",
           set(r1["by_strategy"]) == {"direct_api_rule"}, str(r1["by_strategy"]))
        ck("the deterministic forks recover near-full coverage at a real per-call saving",
           r1["mean_coverage"] >= 0.9 and r1["per_call_cost_saving_added"] > 0)
        ck("state persists the distilled set + the accumulated records (resumable)",
           state.exists() and len(_load_state(state)["distilled_slots"]) == r1["total_distilled"]
           and len(_load_state(state)["records"]) >= r1["newly_distilled"])

        # SECOND pass at the same threshold is IDEMPOTENT — nothing re-distilled.
        r2 = run_once(feeds_dir=_FEEDS_DIR, state_path=state, min_ceiling=0.99, now="t1")
        ck("re-running at the same threshold is idempotent (0 newly distilled)", r2["newly_distilled"] == 0)

        # LOWERING the threshold distills MORE (the scheduled descent picks up lower-ceiling capabilities).
        r3 = run_once(feeds_dir=_FEEDS_DIR, state_path=state, min_ceiling=0.8, now="t2")
        ck("lowering the ceiling threshold distills additional (lower-determinism) capabilities",
           r3["newly_distilled"] > 0 and r3["total_distilled"] > r1["total_distilled"], str(r3["newly_distilled"]))
        ck("the meta-learner has learned at least one class by now (the factory is improving)",
           r3["meta_learner"]["classes_learned"] >= 1, str(r3["meta_learner"]["classes_learned"]))

        # LOOP honors max_iterations + the stop file (durable-runner contract), hermetic sleep.
        loop = run_loop(feeds_dir=_FEEDS_DIR, state_path=Path(td) / "loop.json", min_ceiling=0.99,
                        stop_file=Path(td) / "no-stop-file", max_iterations=2, sleep_fn=lambda _s: None, now="t0")
        ck("the loop runs distillation passes and stops at max_iterations",
           loop["iterations"] == 2 and loop["stopped_by"] == "max_iterations")
        stop = Path(td) / "STOP"
        stop.write_text("x", encoding="utf-8")
        stopped = run_loop(feeds_dir=_FEEDS_DIR, state_path=Path(td) / "l2.json", stop_file=stop,
                           max_iterations=9, sleep_fn=lambda _s: None)
        ck("the loop stops immediately when the stop file exists", stopped["iterations"] == 0)

    print("\n" + ("PASS - distillation_runner: a scheduled, resumable pass distills the corpus's pure-deterministic "
                  "(ceiling-1.0) capabilities into deterministic forks via the cheap direct_api_rule strategy "
                  "(near-full coverage, real per-call saving, lossless, within confines); re-runs are idempotent, "
                  "lowering the threshold distills more, and the meta-learner accumulates across runs so distilling "
                  "gets cheaper. Free + offline (cron-safe); the loop stops via .agent/STOP_REQUESTED. Never truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Scheduled distillation pass: deterministic forks + meta-learning.")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--once", action="store_true")
    p.add_argument("--loop", action="store_true", help="owner-launched continuous loop (stop via .agent/STOP_REQUESTED)")
    p.add_argument("--min-ceiling", type=float, default=_DEFAULT_MIN_CEILING)
    p.add_argument("--interval", type=float, default=3600.0)
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    if a.once:
        print(json.dumps(run_once(min_ceiling=a.min_ceiling), indent=2))
        return 0
    if a.loop:
        print(json.dumps(run_loop(min_ceiling=a.min_ceiling, interval_s=a.interval), indent=2))
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
