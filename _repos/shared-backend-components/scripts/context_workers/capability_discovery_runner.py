#!/usr/bin/env python3
"""scripts.context_workers.capability_discovery_runner — the SIDE RUNNER that turns discovered capabilities into
governed, descent-walked seeds, continuously and resumably.

Pipeline (one pass = run_once): DISCOVER -> SEED -> WALK -> STAGE -> remember.
  * DISCOVER — pull capability candidates from discovery SOURCES. Two source kinds, behind one port:
      - FeedFileSource (default, offline, CI-safe): read discovered-feed JSON files a research agent / the owner
        dropped into the feeds dir (each row = a capability found in a public skills/tools/MCP/plugin source).
      - live discovery (search repos / scrape the web / read skills databases) is a DOCUMENTED SEAM, OFF by
        default: it is a Teleon capability that emits candidate rows (evidence), never truth, and never runs in CI
        or without --allow-live. Same governance as every other live-fetch in this repo.
  * SEED + WALK — hand each candidate to scripts.capability_seeder: normalize -> gap/lift SCREEN (rejects retained)
    -> walk the evolution graph from the non-deterministic root to the most-deterministic runner it can support.
  * STAGE + remember — write staged candidates to JSONL staging and record processed content_hashes in a resumable
    state file, so re-running is IDEMPOTENT (already-seen capabilities are skipped) and the loop can resume.

Long runs are OWNER-LAUNCHED and stop ONLY via the stop file (.agent/STOP_REQUESTED) — the repo's durable-runner
contract. Deterministic + offline for CI (a fixed `now` and an injectable sleep keep the self-test hermetic).
Reads/writes shared DATA only; Teleon-layer logic via the seeder/evolution — never imports src.baltor.

CLI:
    python3 _repos/shared-backend-components/scripts/context_workers/capability_discovery_runner.py --self-test
    python3 _repos/shared-backend-components/scripts/context_workers/capability_discovery_runner.py --once
    python3 _repos/shared-backend-components/scripts/context_workers/capability_discovery_runner.py --loop --interval 900   # owner-launched
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

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

from scripts.capability_seeder import normalize_candidate, screen, walk_candidate, SeederError

_REPO = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_FEEDS_DIR = _resource("data") / "capability-candidates"
_STATE_PATH = _FEEDS_DIR / "runner-state.json"
_STAGED_PATH = _FEEDS_DIR / "staged-candidates.jsonl"
_STOP_FILE = _resource(".agent") / "STOP_REQUESTED"

STATE_VERSION = "CapabilityDiscoveryRunnerState"


class LiveDiscoveryDisabled(RuntimeError):
    """Raised if live discovery (search/scrape) is requested without --allow-live + a configured discovery
    capability. Live fetch is a governed seam — never on by default, never in CI."""


def discover_feed_files(feeds_dir: Path) -> list[Path]:
    """FeedFileSource: every *.json in the feeds dir that parses to a discovered feed (a dict with a 'candidates'
    list, or a bare list). Deterministic order (sorted)."""
    out = []
    for p in sorted(feeds_dir.glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if (isinstance(d, dict) and isinstance(d.get("candidates"), list)) or isinstance(d, list):
            out.append(p)
    return out


def _rows_from_feed(path: Path) -> list[dict]:
    d = json.loads(path.read_text(encoding="utf-8"))
    return d.get("candidates", []) if isinstance(d, dict) else list(d)


def discover(feeds_dir: Path = _FEEDS_DIR, *, allow_live: bool = False) -> list[dict]:
    """Gather raw candidate rows from all discovery sources. Live discovery (search/scrape) is OFF unless
    allow_live AND a discovery capability is configured — otherwise it fails loud rather than silently doing
    nothing or scraping unsafely."""
    rows: list[dict] = []
    for p in discover_feed_files(feeds_dir):
        rows.extend(_rows_from_feed(p))
    if allow_live:
        # The live seam: a Teleon capability (search-repos / scrape-web / read-skills-db) would emit rows here.
        # It is intentionally not wired to a network call in this repo — discovery feeds are produced by an
        # owner-launched research agent and dropped into the feeds dir. Fail loud so "live" is never a silent no-op.
        raise LiveDiscoveryDisabled(
            "live discovery is a governed seam: run an owner-launched research agent to produce a discovered-feed "
            "JSON in the feeds dir, then run the runner offline over it (see module docstring).")
    return rows


def _load_state(state_path: Path) -> dict:
    if state_path.exists():
        return json.loads(state_path.read_text(encoding="utf-8"))
    return {"state_version": STATE_VERSION, "processed_hashes": [], "runs": 0,
            "total_accepted": 0, "total_rejected": 0, "by_category": {}}


def _save_state(state_path: Path, state: dict) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = state_path.with_suffix(state_path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(state_path)  # atomic


def run_once(*, feeds_dir: Path = _FEEDS_DIR, state_path: Path = _STATE_PATH, staged_path: Path = _STAGED_PATH,
             allow_live: bool = False, now: str | None = None) -> dict:
    """One governed pass: discover -> normalize+screen each candidate -> walk NEW ones (idempotent by
    content_hash) -> append to JSONL staging -> persist state. Returns a run report. Nothing serves truth; every
    seeded row stays a candidate."""
    state = _load_state(state_path)
    seen = set(state.get("processed_hashes", []))
    _prior_seen = len(seen)  # to report how many NEW candidates entered the resumable cursor this run
    new_accepted, new_rejected, walked = [], [], []
    for raw in discover(feeds_dir, allow_live=allow_live):
        try:
            cand = normalize_candidate(raw)
        except SeederError as e:
            new_rejected.append({"reasons": [f"normalize: {e}"]})
            continue
        if cand["content_hash"] in seen:
            continue  # IDEMPOTENT: already processed in a prior run
        seen.add(cand["content_hash"])
        verdict = screen(cand)
        if not verdict["accepted"]:
            new_rejected.append({"capability_slot": cand["capability_slot"], "reasons": verdict["reasons"]})
            continue
        cand["descent"] = walk_candidate(cand)  # walk non-det -> most-det on the evolution-graph engine
        new_accepted.append(cand)
        walked.append(cand["descent"])

    # append the new accepted candidates to JSONL staging (candidate staging, never active publication)
    if new_accepted:
        staged_path.parent.mkdir(parents=True, exist_ok=True)
        with staged_path.open("a", encoding="utf-8") as fh:
            for c in new_accepted:
                fh.write(json.dumps(c, sort_keys=True, ensure_ascii=False) + "\n")

    by_cat = dict(state.get("by_category", {}))
    for c in new_accepted:
        by_cat[c["category"]] = by_cat.get(c["category"], 0) + 1
    state.update({"state_version": STATE_VERSION, "processed_hashes": sorted(seen), "runs": state.get("runs", 0) + 1,
                  "total_accepted": state.get("total_accepted", 0) + len(new_accepted),
                  "total_rejected": state.get("total_rejected", 0) + len(new_rejected), "by_category": by_cat})
    if now is not None:
        state["last_run"] = now
    _save_state(state_path, state)
    return {"new_accepted": len(new_accepted), "new_rejected": len(new_rejected),
            "processed": len(seen) - _prior_seen,  # candidates that entered the cursor this run (accepted + screened-out)
            "walked": len(walked), "total_accepted": state["total_accepted"],
            "by_category": by_cat, "serves_truth": False,
            "sample": [{"capability_slot": c["capability_slot"],
                        "most_deterministic_runner": c["descent"]["most_deterministic_runner"]}
                       for c in new_accepted[:5]]}


def run_loop(*, feeds_dir: Path = _FEEDS_DIR, state_path: Path = _STATE_PATH, staged_path: Path = _STAGED_PATH,
             interval_s: float = 900.0, stop_file: Path = _STOP_FILE, max_iterations: int | None = None,
             allow_live: bool = False, sleep_fn=time.sleep, now: str | None = None) -> dict:
    """Owner-launched continuous loop: run_once, then sleep interval_s, repeat — UNTIL the stop file exists (the
    durable-runner contract) or max_iterations is reached. Idempotent per iteration. ``sleep_fn`` is injectable so
    the self-test is hermetic. Returns the aggregate report."""
    iterations, total_new = 0, 0
    while True:
        if stop_file.exists():
            break
        if max_iterations is not None and iterations >= max_iterations:
            break
        report = run_once(feeds_dir=feeds_dir, state_path=state_path, staged_path=staged_path,
                          allow_live=allow_live, now=now)
        total_new += report["new_accepted"]
        iterations += 1
        if stop_file.exists() or (max_iterations is not None and iterations >= max_iterations):
            break
        sleep_fn(interval_s)
    return {"iterations": iterations, "total_new_accepted": total_new,
            "stopped_by": "stop_file" if stop_file.exists() else "max_iterations", "serves_truth": False}


def _self_test() -> int:
    import tempfile

    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    feed = _FEEDS_DIR / "discovered-feed-2026-06-19.json"
    ck("the committed discovered feed is present as a discovery source", feed.exists())
    ck("discover_feed_files finds the feed (FeedFileSource)", feed in set(discover_feed_files(_FEEDS_DIR)))

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        state_path, staged_path = tdp / "runner-state.json", tdp / "staged.jsonl"

        # FIRST pass: discovers + seeds the real feed.
        r1 = run_once(feeds_dir=_FEEDS_DIR, state_path=state_path, staged_path=staged_path, now="t0")
        ck("first pass seeds many governed candidates and walks each non-det -> most-det",
           r1["new_accepted"] >= 30 and r1["walked"] == r1["new_accepted"] and r1["serves_truth"] is False, str(r1)[:140])
        ck("staging JSONL is written (candidate staging, not active publication)",
           staged_path.exists() and sum(1 for _ in staged_path.open()) == r1["new_accepted"])
        ck("the named categories are covered in one pass",
           {"federal-register", "regulation", "legal-statute", "financial-data", "scraping", "email", "research"}
           <= set(r1["by_category"]), str(sorted(r1["by_category"])))
        ck("state persists the resumable cursor (every processed candidate, accepted + screened-out) + last_run",
           state_path.exists() and len(_load_state(state_path)["processed_hashes"]) == r1["processed"]
           and r1["processed"] >= r1["new_accepted"] and _load_state(state_path)["last_run"] == "t0")

        # SECOND pass: IDEMPOTENT — nothing new (already processed).
        r2 = run_once(feeds_dir=_FEEDS_DIR, state_path=state_path, staged_path=staged_path, now="t1")
        ck("second pass is IDEMPOTENT (0 new — already-seen capabilities are skipped)", r2["new_accepted"] == 0)
        ck("staging is not duplicated on the idempotent re-run",
           sum(1 for _ in staged_path.open()) == r1["new_accepted"])

        # LOOP honors max_iterations with a hermetic sleep.
        state2 = tdp / "loop-state.json"
        loop = run_loop(feeds_dir=_FEEDS_DIR, state_path=state2, staged_path=tdp / "loop-staged.jsonl",
                        stop_file=tdp / "no-stop-file", max_iterations=3, sleep_fn=lambda _s: None, now="t0")
        ck("the loop runs run_once each iteration and stops at max_iterations",
           loop["iterations"] == 3 and loop["stopped_by"] == "max_iterations")

        # LOOP honors the STOP file (the durable-runner contract): present -> 0 iterations.
        stop = tdp / "STOP_REQUESTED"
        stop.write_text("stop", encoding="utf-8")
        stopped = run_loop(feeds_dir=_FEEDS_DIR, state_path=tdp / "s3.json", stop_file=stop,
                           max_iterations=10, sleep_fn=lambda _s: None)
        ck("the loop stops immediately when the stop file exists (.agent/STOP_REQUESTED contract)",
           stopped["iterations"] == 0 and stopped["stopped_by"] == "stop_file")

    # live discovery is a governed seam: OFF by default, fails loud rather than scraping silently.
    raised = False
    try:
        discover(_FEEDS_DIR, allow_live=True)
    except LiveDiscoveryDisabled:
        raised = True
    ck("live discovery (search/scrape) is OFF by default and fails loud when requested unconfigured", raised)

    print("\n" + ("PASS - capability_discovery_runner: a resumable side runner discovers capability candidates "
                  "(feed-file source; live search/scrape a governed off-by-default seam), seeds + screens them, "
                  "walks each non-deterministic -> most-deterministic on the evolution-graph engine, stages to "
                  "JSONL, and remembers processed hashes so re-runs are idempotent. The loop is owner-launched and "
                  "stops only via the stop file. Nothing serves truth; every row stays a candidate."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Side runner: discover -> seed -> walk capability candidates (governed).")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--once", action="store_true", help="run a single governed pass")
    p.add_argument("--loop", action="store_true", help="owner-launched continuous loop (stop via .agent/STOP_REQUESTED)")
    p.add_argument("--interval", type=float, default=900.0, help="seconds between loop passes")
    p.add_argument("--allow-live", action="store_true", help="enable the live search/scrape seam (governed; off by default)")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    if a.once:
        print(json.dumps(run_once(allow_live=a.allow_live), indent=2))
        return 0
    if a.loop:
        print(json.dumps(run_loop(interval_s=a.interval, allow_live=a.allow_live), indent=2))
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
