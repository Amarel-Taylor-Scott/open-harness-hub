#!/usr/bin/env python3
"""scripts.baltor_flywheel — the deterministic always-on flywheel + health supervisor.

The agentic building passes (`/baltor-goal-loop`) need a model in the loop, so they only run
when the harness wakes the agent. THIS process needs no agent: it is a plain Python watcher that
runs continuously (launch with ``--watch``, or via a background runner) and, every tick:

  * **stays-green:** re-runs every proof self-test (the shipped, deterministic contracts) and
    records pass/fail — so any regression is caught within one tick, not at the next agent pass;
  * **keeps-watching:** optionally (``--live``) re-checks the live sources (eCFR titles, OFAC SDN)
    and diffs their content hash against the previous tick (CDC) — surfacing real upstream change
    (the "current ≠ correct" freshness signal) without an agent;
  * **leaves a heartbeat:** appends one JSON line per tick to ``.agent/flywheel-health.jsonl`` and
    prints a one-line status, so a supervisor (or you, `tail -f`) can see it is alive + green.

It makes **no commits, no destructive changes, no paid calls** — only reads/runs self-tests and
(optionally) read-only public fetches. It is the safe half of "run for hours": it genuinely runs
unattended; the agentic supervisor handles new building + healing what this flags red.

This module is an operational watcher, NOT a context-producing component, so it uses wall-clock
time + subprocess (it is not required to be deterministic). Its ``--self-test`` proves ONE tick
works (all proof modules green + a health record written), offline.

CLI:
    python3 scripts/baltor_flywheel.py --self-test                 # one offline tick + assertions
    python3 scripts/baltor_flywheel.py --once                      # one tick, print + log
    python3 scripts/baltor_flywheel.py --watch --interval 600      # loop forever (offline ticks)
    python3 scripts/baltor_flywheel.py --watch --interval 900 --live  # also CDC-watch live sources
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)  # so --live can import the connectors for a STABLE freshness hash
HEALTH_LOG = os.path.join(_REPO_ROOT, ".agent", "flywheel-health.jsonl")

#: The shipped proof registry lives in its own module (data/logic split); re-exported here.
from scripts.flywheel_proof_modules import PROOF_MODULES  # noqa: E402,F401

_SELFTEST_TIMEOUT_S = 120


def _proof_env() -> dict:
    """Environment for proof subprocesses. A fresh subprocess does NOT inherit the parent's `sys.path`
    insertion — only the PYTHONPATH env var — so a proof that does `import scripts.*`/`src.*` at top level
    would fail unless the repo root is on PYTHONPATH. The flywheel KNOWS the repo root, so it injects it here.
    This makes the watcher correct regardless of how it was launched (with or without `PYTHONPATH=.`),
    preventing a false-RED when the watchdog is started bare (the exact regression seen 2026-06-06)."""
    env = dict(os.environ)
    prior = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = _REPO_ROOT + (os.pathsep + prior if prior else "")
    return env


def _run(module_args: list[str], timeout: int) -> tuple[bool, str]:
    """Run a module command; return (ok, last_line). Never raises — a watcher must not die."""
    try:
        p = subprocess.run([sys.executable, *module_args], cwd=_REPO_ROOT,
                           capture_output=True, text=True, timeout=timeout, env=_proof_env())
        out = (p.stdout or p.stderr or "").strip().splitlines()
        return p.returncode == 0, (out[-1] if out else "")
    except subprocess.TimeoutExpired:
        return False, f"TIMEOUT after {timeout}s"
    except Exception as e:  # never let the watcher crash
        return False, f"ERROR {type(e).__name__}: {e}"


def _live_freshness() -> dict:
    """CDC-watch the live sources via STABLE payload content hashes (not stdout — which carries a
    per-fetch timestamp). Imports the connectors; read-only public fetches; never raises."""
    out: dict = {}
    try:
        from scripts.ingest import ecfr_feed
        _records, lineage = ecfr_feed.load_titles()
        out["ecfr_titles"] = {"hash": lineage.content_hash, "reachable": True,
                              "titles": lineage.titles_parsed}
    except Exception as e:
        out["ecfr_titles"] = {"hash": "", "reachable": False, "error": f"{type(e).__name__}: {e}"}
    return out


def tick(*, live: bool, prev: dict | None) -> dict:
    """Run one flywheel tick: all proof self-tests (+ optional live CDC). Returns a health record."""
    results = {}
    for path, label in PROOF_MODULES:
        ok, last = _run([path, "--self-test"], _SELFTEST_TIMEOUT_S)
        results[label] = {"ok": ok, "detail": last}
    all_green = all(r["ok"] for r in results.values())

    live_rec: dict = {}
    if live:
        prev_live = (prev or {}).get("live", {}) if prev else {}
        fresh = _live_freshness()
        for label, cur in fresh.items():
            prior = prev_live.get(label, {}).get("hash")
            h = cur.get("hash", "")
            cur["changed"] = bool(prior) and bool(h) and prior != h
            live_rec[label] = cur

    return {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "all_green": all_green,
        "green_count": sum(1 for r in results.values() if r["ok"]),
        "total": len(results),
        "results": results,
        "live": live_rec,
    }


def _append_health(rec: dict) -> None:
    os.makedirs(os.path.dirname(HEALTH_LOG), exist_ok=True)
    with open(HEALTH_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")


def _heartbeat_line(rec: dict) -> str:
    flags = ""
    if rec["live"]:
        changed = [k for k, v in rec["live"].items() if v.get("changed")]
        unreach = [k for k, v in rec["live"].items() if not v.get("reachable")]
        if changed:
            flags += f"  CHANGED:{','.join(changed)}"
        if unreach:
            flags += f"  UNREACHABLE:{','.join(unreach)}"
    status = "GREEN" if rec["all_green"] else "RED"
    failed = [k for k, v in rec["results"].items() if not v["ok"]]
    return (f"[{rec['ts']}] flywheel {status} {rec['green_count']}/{rec['total']} proofs"
            + (f"  FAILED:{','.join(failed)}" if failed else "") + flags)


def _watch(interval: int, live: bool, *, sup: dict | None = None, supervisor_only: bool = False,
           max_ticks: int = 0) -> int:
    """Health-watch loop. When `sup` is set, ALSO runs one durable supervisor coordination step per tick
    so multiple --watch processes coordinate (leader/shard leases) against one DB. `supervisor_only` skips
    the heavy proof tick (for bounded multi-process tests); `max_ticks`>0 exits after N ticks."""
    prev: dict | None = None
    ticks = 0
    store = None
    sup_id = None
    supervisor_watch = None
    durable = None
    if sup is not None:
        try:
            from src.baltor.workers.supervisor_store import SupervisorStore
            from src.baltor.workers.durable_fleet_ledger import DurableFleetLedger
            from src.baltor.workers import supervisor_watch as _sw
            supervisor_watch = _sw
            store = SupervisorStore(sup["db"])
            durable = DurableFleetLedger(sup["db"])   # the LIVE dispatch source: real persisted task queue
            sup_id = sup["id"]
            store.register_instance(supervisor_id=sup_id, pid=os.getpid(),
                                    mode=("supervisor_only" if supervisor_only else "watch"))
        except Exception as e:  # coordination is best-effort — never block the health watcher
            print(f"[supervisor] coordination disabled: {e}", flush=True)
            store = None
    try:
        while True:
            rec = None
            if not supervisor_only:
                rec = tick(live=live, prev=prev)
                _append_health(rec)
                print(_heartbeat_line(rec), flush=True)
                prev = rec
            if store is not None:
                try:
                    out = supervisor_watch.step(store, supervisor_id=sup_id, leader_ttl=sup["leader_ttl"],
                                                shard_ttl=sup["shard_ttl"], max_shards=sup["max_shards"],
                                                proof_summary=rec, fleet_ledger=durable, db=sup["db"],
                                                dispatch=sup.get("dispatch", False),
                                                execution_backend=sup.get("execution_backend", False))
                    print(f"[supervisor] {sup_id} leader={out['leader']} shards={len(out['owned_shards'])}"
                          f" decisions={out['decisions']} exec_dispatched={len(out.get('execution_dispatched', []))}"
                          f" tick={out['tick_id'][:14]}", flush=True)
                except Exception as e:  # a coordination error must never kill the health tick
                    print(f"[supervisor] step error (continuing): {e}", flush=True)
            ticks += 1
            if max_ticks and ticks >= max_ticks:
                break
            time.sleep(interval if supervisor_only else max(30, interval))  # floor 30s for proof watcher
    finally:
        if store is not None:
            try:
                store.set_instance_status(sup_id, "stopped")
                store.release_leader(lease_name=supervisor_watch.LEADER_LEASE, supervisor_id=sup_id)
            except Exception:
                pass
            store.close()
    return 0


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    rec = tick(live=False, prev=None)
    check("tick ran all proof modules", rec["total"] == len(PROOF_MODULES), str(rec["total"]))
    check("all shipped proofs GREEN", rec["all_green"] is True,
          ",".join(k for k, v in rec["results"].items() if not v["ok"]))
    check("heartbeat line renders", "flywheel GREEN" in _heartbeat_line(rec))
    _append_health(rec)
    check("health record appended to log", os.path.exists(HEALTH_LOG))

    print(f"\n{'flywheel self-test passed (one green tick).' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Baltor flywheel — deterministic always-on health/freshness watcher.")
    p.add_argument("--self-test", action="store_true", help="one offline tick + assertions")
    p.add_argument("--once", action="store_true", help="one tick, print + log, then exit")
    p.add_argument("--watch", action="store_true", help="loop forever (for background running)")
    p.add_argument("--interval", type=int, default=600, help="seconds between ticks in --watch (default 600)")
    p.add_argument("--live", action="store_true", help="also CDC-watch live sources (read-only fetches)")
    # OPP-supervisor-scaling-live: durable leader/shard-lease coordination in --watch (on by default for --watch)
    p.add_argument("--no-supervisor", action="store_true", help="disable live supervisor coordination in --watch")
    p.add_argument("--supervisor-only", action="store_true",
                   help="run ONLY supervisor coordination (skip the proof tick) — for bounded multi-process tests")
    p.add_argument("--supervisor-id", default="", help="supervisor instance id (default sup-<pid>)")
    p.add_argument("--supervisor-db", default="", help="durable supervisor DB path (default the shared durable DB)")
    p.add_argument("--leader-ttl", type=int, default=30, help="leader-lease TTL seconds")
    p.add_argument("--shard-ttl", type=int, default=30, help="shard-lease TTL seconds")
    p.add_argument("--max-shards", type=int, default=16, help="max shards a supervisor claims per tick (>= shard count → a lone node owns all)")
    p.add_argument("--max-ticks", type=int, default=0, help="exit after N ticks (0=forever) — for bounded tests")
    p.add_argument("--dispatch", action="store_true",
                   help="LIVE DISPATCH: actually spawn real worker subprocesses to drain queued durable tasks (off by default — the bare watchdog only records decisions)")
    p.add_argument("--execution-backend", action="store_true",
                   help="EXECUTION-BACKEND DISPATCH: route owned-shard work through the ExecutionBackendSelector "
                        "(policy/pricebook/health/creds) → record a switchable ExecutionProviderDecision → drain via "
                        "the chosen LOCAL executor. Cloud stays deferred (falls back to local); replaces --dispatch as the drainer.")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.once:
        rec = tick(live=args.live, prev=None)
        _append_health(rec)
        print(_heartbeat_line(rec))
        return 0 if rec["all_green"] else 1
    if args.watch or args.supervisor_only:
        sup = None
        if not args.no_supervisor:
            from src.baltor.workers.supervisor_store import DEFAULT_DB
            # the lease TTL must outlive the gap between ticks (a full proof tick can take minutes), or the
            # lease would expire between renewals and churn. Floor the TTL at ~2x the interval.
            ttl_floor = max(1, args.interval) * 2
            sup = {"id": args.supervisor_id or f"sup-{os.getpid()}",
                   "db": args.supervisor_db or str(DEFAULT_DB),
                   "leader_ttl": max(args.leader_ttl, ttl_floor), "shard_ttl": max(args.shard_ttl, ttl_floor),
                   "max_shards": args.max_shards, "dispatch": args.dispatch,
                   "execution_backend": args.execution_backend}
        return _watch(args.interval, args.live, sup=sup, supervisor_only=args.supervisor_only, max_ticks=args.max_ticks)
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
