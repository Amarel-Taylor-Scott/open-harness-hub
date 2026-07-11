"""enrichment_loop — a dedicated, long-running ENRICHMENT loop across the WHOLE project surface.

Owner ask (2026-06-24): a loop to run for ~3 days, iterating every ~30 minutes, filling gaps and generating records /
metadata / embeddings / tools / descriptions / use-cases for ALL surfaces — Baltor, Teleon, the Open*Hubs, and the new
Observer/Spotter supervisor/monitor/session-review tool.

This is a CADENCE SCHEDULER over the real worker scripts (it does not reimplement them): each cycle it picks the
most-overdue enrichment task by its own cadence, runs it as a subprocess, records the result, periodically runs the
full proof gate to stay honest, and checkpoints state so a restart resumes. It is separate from ./loop (the YC/sweep
flywheel daemon) and uses its OWN stop flag, so both can run at once.

Governance: every task is an existing GOVERNED script (serves_truth=false, candidate-only, no-magic-values, lossless);
this loop adds no new truth — it just schedules generation + verification. Network tasks honor --offline and fail
honest. The loop never crashes on a task error or a red gate; it records and continues for YOU to review.

  python3 _repos/shared-backend-components/scripts/enrichment_loop.py --supervise               # the 3-day loop (every 30 min); ./enrich start wraps this
  python3 _repos/shared-backend-components/scripts/enrichment_loop.py --run                     # one cycle (foreground)
  python3 _repos/shared-backend-components/scripts/enrichment_loop.py --status                  # read-only monitor
  python3 _repos/shared-backend-components/scripts/enrichment_loop.py --supervise --days 3 --interval-min 30 --offline
  python3 _repos/shared-backend-components/scripts/enrichment_loop.py --self-test               # offline wiring check (no subprocess)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
_STATE = _resource("data") / "dev-intel" / "enrichment_loop_state.json"
_LOG = _resource("data") / "dev-intel" / "enrichment_loop.log"
_STOP = (_REPO / ".agent") / "ENRICHMENT_STOP_REQUESTED"

#: the enrichment task set — one per (surface, kind of generation). cadence = run roughly every N cycles. argv runs the
#: REAL worker in its BUILD/generate form (not --self-test). network tasks are skipped under --offline (honest).
#: ORDERED interleaved by surface so the cold-start (never-run drain) is surface-diverse; steady state is cadence-driven.
TASKS: list[dict] = [
    # Teleon — the registry federation: refresh (discover->depgraph->records+ENRICHMENT->mvp + population)
    {"id": "teleon_refresh", "surface": "Teleon", "cadence": 1, "network": False,
     "argv": ["scripts/registry_loop.py", "--run", "--with-population"]},
    # Hubs — rebuild every Open*Hub site from the registries
    {"id": "hubs_sites", "surface": "Hubs", "cadence": 2, "network": False,
     "argv": ["scripts/build_hub_sites.py", "--all"]},
    # Observer/Spotter — rebuild the demoable surface (taxonomy + live review, computed counts)
    {"id": "observer_surface", "surface": "Observer", "cadence": 2, "network": False,
     "argv": ["scripts/build_spotter_surface.py"]},
    # Baltor — one applied-context flywheel cycle
    {"id": "baltor_cycle", "surface": "Baltor", "cadence": 3, "network": False,
     "argv": ["scripts/baltor_flywheel.py", "--once"]},
    # Discovery — grow the staged tool registry from the forges (NETWORK; honest rate-limit stop)
    {"id": "discover_tools", "surface": "Discovery", "cadence": 3, "network": True,
     "argv": ["scripts/harvest_tools.py", "--run"]},
    # Teleon — scale records via governed variation mutation (industry x geo x season x ...)
    {"id": "teleon_scale_records", "surface": "Teleon", "cadence": 3, "network": False,
     "argv": ["scripts/build_million_records.py"]},
    # Observer/Spotter — dogfood the code genome over our own source
    {"id": "observer_genome", "surface": "Observer", "cadence": 3, "network": False,
     "argv": ["scripts/build_code_genome_index.py"]},
    # Hubs — rebuild the browse-everything hub table
    {"id": "hubs_browser", "surface": "Hubs", "cadence": 4, "network": False,
     "argv": ["scripts/build_hub_browser.py"]},
    # Teleon — distill mined Kaggle kernels -> candidate registry entries (population)
    {"id": "teleon_kaggle_distill", "surface": "Teleon", "cadence": 4, "network": False,
     "argv": ["scripts/distill_kaggle_kernels.py"]},
    # Teleon — refresh the capability MVP showcase from the registries
    {"id": "teleon_capability_mvp", "surface": "Teleon", "cadence": 5, "network": False,
     "argv": ["scripts/build_capability_mvp.py"]},
]

_SURFACES = {"Teleon", "Hubs", "Observer", "Baltor", "Discovery"}
_TASK_TIMEOUT_S = 1500   # a single task is capped below the 30-min interval so it can't overrun the cycle
_GATE_TIMEOUT_S = 1500
_DEFAULT_INTERVAL_MIN = 30
_DEFAULT_DAYS = 3
_DEFAULT_GATE_EVERY = 4   # run the full proof gate every N cycles (≈ every 2h at 30-min cadence)
_HISTORY_KEEP = 60


def _now() -> float:
    return time.time()


def _new_state() -> dict:
    return {"version": "0.1.0", "serves_truth": False, "cycle": 0, "runs": 0,
            "last": {}, "last_gate": None, "history": [], "started_at": None}


def load_state() -> dict:
    if _STATE.exists():
        try:
            s = json.loads(_STATE.read_text())
            for k, v in _new_state().items():
                s.setdefault(k, v)
            return s
        except json.JSONDecodeError:
            pass
    return _new_state()


def save_state(state: dict) -> None:
    _STATE.parent.mkdir(parents=True, exist_ok=True)
    _STATE.write_text(json.dumps(state, indent=2) + "\n")


def _enabled_tasks(offline: bool) -> list[dict]:
    return [t for t in TASKS if not (offline and t["network"])]


def _due_score(task: dict, state: dict, cyc: int) -> float:
    """Overdue ratio: (cycles since last run) / cadence. A never-run task is maximally due."""
    last = state["last"].get(task["id"])
    if last is None:
        return float("inf")
    return (cyc - last) / max(1, task["cadence"])


def pick_task(state: dict, offline: bool) -> dict:
    """The most-overdue enabled task by its cadence (ties broken by TASKS order = a stable rotation)."""
    cyc = state["cycle"]
    cands = _enabled_tasks(offline)
    return max(cands, key=lambda t: (_due_score(t, state, cyc), -TASKS.index(t)))


def _run_subprocess(argv: list[str], timeout: int) -> dict:
    """Run a worker script with repo cwd + PYTHONPATH. Never raises — returns rc + a tail of output."""
    import os
    env = dict(os.environ)
    env["PYTHONPATH"] = str(_REPO) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    t0 = _now()
    try:
        p = subprocess.run([sys.executable, *argv], cwd=str(_REPO), env=env, capture_output=True, text=True,
                           timeout=timeout)
        out = (p.stdout or "") + (p.stderr or "")
        return {"rc": p.returncode, "secs": round(_now() - t0, 1), "tail": out.strip().splitlines()[-1:] and
                out.strip().splitlines()[-1][:300] or ""}
    except subprocess.TimeoutExpired:
        return {"rc": -1, "secs": round(_now() - t0, 1), "tail": f"TIMEOUT after {timeout}s"}
    except Exception as e:  # never let a worker crash the loop
        return {"rc": -2, "secs": round(_now() - t0, 1), "tail": f"ERROR {type(e).__name__}: {e}"[:300]}


def _run_gate() -> dict:
    res = _run_subprocess(["scripts/run_proofs.py"], _GATE_TIMEOUT_S)
    green = total = None
    tail = res["tail"]
    # parse "proofs: X/Y green"
    import re
    m = re.search(r"proofs:\s*(\d+)/(\d+)\s*green", tail)
    if m:
        green, total = int(m.group(1)), int(m.group(2))
    return {"green": green, "total": total, "tail": tail, "secs": res["secs"]}


def _log(msg: str) -> None:
    _LOG.parent.mkdir(parents=True, exist_ok=True)
    with _LOG.open("a") as f:
        f.write(msg + "\n")
    print(msg)


def run_once(state: dict, offline: bool, gate_every: int) -> dict:
    state["cycle"] += 1
    cyc = state["cycle"]
    if state["started_at"] is None:
        state["started_at"] = _now()
    task = pick_task(state, offline)
    _log(f"[enrich cycle {cyc}] {task['surface']}/{task['id']} -> {' '.join(task['argv'])}")
    res = _run_subprocess(task["argv"], _TASK_TIMEOUT_S)
    state["last"][task["id"]] = cyc
    state["runs"] += 1
    entry = {"cycle": cyc, "task": task["id"], "surface": task["surface"], "rc": res["rc"],
             "secs": res["secs"], "tail": res["tail"]}
    _log(f"  rc={res['rc']} {res['secs']}s :: {res['tail']}")

    if gate_every and cyc % gate_every == 0:
        g = _run_gate()
        state["last_gate"] = {"cycle": cyc, "green": g["green"], "total": g["total"]}
        entry["gate"] = state["last_gate"]
        _log(f"  [gate] {g['green']}/{g['total']} green ({g['secs']}s)" + (
            "  <-- RED, review" if g["green"] is not None and g["green"] != g["total"] else ""))

    state["history"] = (state["history"] + [entry])[-_HISTORY_KEEP:]
    save_state(state)
    return entry


def _should_continue(state: dict, deadline: float, now: float) -> bool:
    return now < deadline and not _STOP.exists()


def supervise(interval_min: float, days: float, offline: bool, gate_every: int) -> int:
    state = load_state()
    if state["started_at"] is None:
        state["started_at"] = _now()
    deadline = state["started_at"] + days * 86400
    interval = interval_min * 60
    _log(f"[enrichment_loop] supervising: every {interval_min}min for {days}d "
         f"(~{int(days * 24 * 60 / max(1, interval_min))} cycles), offline={offline}, gate every {gate_every}. "
         f"stop: ./enrich stop (or touch {_STOP.relative_to(_REPO)})")
    while _should_continue(state, deadline, _now()):
        run_once(state, offline, gate_every)
        if not _should_continue(state, deadline, _now()):
            break
        time.sleep(interval)
    reason = "STOP requested" if _STOP.exists() else "duration reached"
    _log(f"[enrichment_loop] halted ({reason}) after {state['runs']} runs / {state['cycle']} cycles.")
    return 0


def status(state: dict) -> None:
    print(f"enrichment_loop: cycle {state['cycle']}, {state['runs']} runs"
          + (f", last gate {state['last_gate']['green']}/{state['last_gate']['total']}" if state["last_gate"] else ""))
    by_surface: dict[str, int] = {}
    for t in TASKS:
        s = t["surface"]
        by_surface[s] = by_surface.get(s, 0)
    for e in state["history"]:
        by_surface[e["surface"]] = by_surface.get(e["surface"], 0) + 1
    print("  runs by surface:", ", ".join(f"{k}={v}" for k, v in sorted(by_surface.items())))
    print("  recent:")
    for e in state["history"][-8:]:
        g = f" gate={e['gate']['green']}/{e['gate']['total']}" if e.get("gate") else ""
        print(f"    c{e['cycle']:<4} {e['surface']:9} {e['task']:22} rc={e['rc']} {e['secs']}s{g}")


def _self_test() -> int:
    fails, checks = [], 0

    def ck(name, ok, detail=""):
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(name)
            print(f"  [XX] {name}{(' — ' + detail) if detail else ''}")

    # wiring: every task points at a real worker script + valid shape
    ck("all task scripts exist on disk", all((_resource(t["argv"][0])).exists() for t in TASKS),
       str([t["argv"][0] for t in TASKS if not (_resource(t["argv"][0])).exists()]))
    ck("task ids unique", len({t["id"] for t in TASKS}) == len(TASKS))
    ck("all cadences >= 1", all(t["cadence"] >= 1 for t in TASKS))
    ck("surfaces are the known set", {t["surface"] for t in TASKS} <= _SURFACES)
    ck("ALL surfaces covered (Baltor/Teleon/Hubs/Observer/Discovery)", {t["surface"] for t in TASKS} == _SURFACES)

    # scheduler: a never-run task is maximally due; after running it, a different task becomes most-due (rotation)
    st = _new_state()
    first = pick_task(st, offline=False)
    ck("a fresh loop picks a never-run task", _due_score(first, st, st["cycle"]) == float("inf"))
    st["cycle"] = 1
    st["last"][first["id"]] = 1
    second = pick_task(st, offline=False)
    ck("scheduler rotates (next pick differs from the just-run task)", second["id"] != first["id"])

    # offline skips network tasks
    ck("offline excludes network tasks", all(not t["network"] for t in _enabled_tasks(offline=True)))
    ck("network tasks exist for online mode", any(t["network"] for t in TASKS))

    # duration / stop math (pure)
    st2 = _new_state()
    st2["started_at"] = 1000.0
    ck("runs while within the window + no stop", _should_continue(st2, deadline=2000.0, now=1500.0))
    ck("stops at the deadline", not _should_continue(st2, deadline=2000.0, now=2001.0))
    ck("cycle count math (~3d @ 30min ≈ 144)", int(3 * 24 * 60 / 30) == 144)
    ck("serves_truth false", _new_state()["serves_truth"] is False)

    if fails:
        print(f"\nFAIL - enrichment_loop: {len(fails)} of {checks} failed")
        return 1
    print(f"PASS - enrichment_loop: cadence scheduler over {len(TASKS)} governed enrichment tasks across all "
          f"{len(_SURFACES)} surfaces (Baltor/Teleon/Hubs/Observer/Discovery); rotation + offline + duration/stop "
          f"logic verified; {checks} assertions; serves_truth=false (schedules generation+gating, adds no truth).")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--supervise", action="store_true", help="run the long loop (every --interval-min for --days)")
    ap.add_argument("--run", action="store_true", help="run exactly one cycle in the foreground")
    ap.add_argument("--status", action="store_true", help="print the read-only monitor")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--interval-min", type=float, default=_DEFAULT_INTERVAL_MIN)
    ap.add_argument("--days", type=float, default=_DEFAULT_DAYS)
    ap.add_argument("--gate-every", type=int, default=_DEFAULT_GATE_EVERY)
    ap.add_argument("--offline", action="store_true", help="skip network tasks (Discovery), fail honest")
    args = ap.parse_args()

    if args.self_test:
        return _self_test()
    if args.status:
        status(load_state())
        return 0
    if args.run:
        run_once(load_state(), args.offline, args.gate_every)
        return 0
    if args.supervise:
        return supervise(args.interval_min, args.days, args.offline, args.gate_every)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
