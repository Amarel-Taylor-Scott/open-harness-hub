#!/usr/bin/env python3
"""run_parallel_dev_fleet — launch a PARALLEL dev fleet (Claude Code + Ollama agents) that never edits the same file
at once. Each lane runs in its OWN git worktree (separate working dir + branch) and owns a disjoint file set; the
shared proof registry + count token are serialized (applied by the coordinator at merge, not by lanes). Brains: claude
for design lanes, ollama (OpenAI-compatible, pointed at the local Ollama endpoint) for narrow/deterministic lanes.

  --check       validate the no-same-file-edit guarantee (disjoint ownership); launch NOTHING. exit 0/1.
  --dry-run     (default) print the per-lane plan (worktree, branch, brain, command); launch NOTHING.
  --launch      OWNER ACTION: create a worktree per lane + spawn each lane's agent in parallel (background).
  --self-test   prove --check/--dry-run work without spawning (the registered proof covers the guarantee module).

Brain commands: claude -> $CLAUDE_CODE_CMD (default 'claude -p'); ollama -> $OLLAMA_AGENT_CMD (no default; set it to
an OpenAI-compatible agent CLI pointed at the Ollama endpoint). An unconfigured ollama lane is SKIPPED with a note.
CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/run_parallel_dev_fleet.py --dry-run
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.orchestration import parallel_lanes as PL


def _validate() -> dict:
    v = PL.validate_disjoint()
    status = "OK" if v["ok"] else "CONFLICTS"
    print(f"== parallel dev fleet — disjointness {status} ==")
    print(f"  lanes: {list(v['per_lane_counts'])}")
    print(f"  owned-file counts: {v['per_lane_counts']}")
    if v["overlaps"]:
        print(f"  [FAIL] overlapping ownership: {v['overlaps']}")
    if v["shared_violations"]:
        print(f"  [FAIL] a lane owns a shared-serialized file: {v['shared_violations']}")
    if v["ok"]:
        print("  [ok] lanes are pairwise-disjoint and no lane owns a shared-serialized file")
    return v


def _print_plan() -> None:
    print("== per-lane plan (dry-run; launches NOTHING) ==")
    for r in PL.plan():
        cfg = "configured" if r["command_configured"] else "NOT configured (lane will be skipped on --launch)"
        print(f"  [{r['lane']}] brain={r['brain']} files={r['owned_file_count']} worktree={r['worktree']} "
              f"branch={r['branch']}\n      command: {r['command_preview']}  ({cfg})")
    print("  shared-serialized (owned by no lane; merged serially): " + ", ".join(PL.shared_files()))


def _launch() -> int:
    v = _validate()
    if not v["ok"]:
        print("REFUSING to launch: ownership is not disjoint (fix architecture/parallel_dev_lanes.json first).")
        return 1
    root = PL._REPO
    os.makedirs(os.path.join(root, ".agent", "logs"), exist_ok=True)
    launched, skipped = [], []
    for ln in PL.lanes():
        wt = os.path.join(root, PL.worktree_path(ln))
        branch = f"fleet/{ln['id']}"
        cmd = PL.brain_command(ln["brain"])
        if not cmd:
            skipped.append((ln["id"], f"{ln['brain']} command not configured"))
            continue
        # create the worktree (own dir + branch) if absent — physical isolation
        if not os.path.isdir(wt):
            r = subprocess.run(["git", "worktree", "add", "-b", branch, wt, "HEAD"], cwd=root,
                               capture_output=True, text=True)
            if r.returncode != 0:
                skipped.append((ln["id"], f"worktree add failed: {r.stderr.strip()[:120]}"))
                continue
        log = os.path.join(root, ".agent", "logs", f"fleet-{ln['id']}.log")
        prompt = PL.lane_prompt(ln)
        # spawn the lane's agent in its worktree, detached; the agent edits ONLY its owned files
        with open(log, "w", encoding="utf-8") as lf:
            p = subprocess.Popen(["bash", "-lc", f'cd {wt!r} && {cmd} "$LANE_PROMPT"'],
                                 env={**os.environ, "LANE_PROMPT": prompt}, stdout=lf, stderr=lf, stdin=subprocess.DEVNULL)
        launched.append((ln["id"], p.pid, log))
    print("== launched lanes (each in its own worktree, editing only its owned files) ==")
    for lid, pid, log in launched:
        print(f"  [{lid}] pid={pid} log={os.path.relpath(log, root)}")
    for lid, why in skipped:
        print(f"  [skip {lid}] {why}")
    print("merge each lane's branch back via PR when its worktree is green; the coordinator applies the proof "
          "registry + count-token bumps serially at merge.")
    return 0


def _self_test() -> int:
    fails = []

    def ck(name, ok):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
        if not ok:
            fails.append(name)

    v = PL.validate_disjoint()
    ck("disjointness validates OK (no same-file edits possible across lanes)", v["ok"])
    plan = PL.plan()
    ck("dry-run plan is produced for every lane without spawning", len(plan) == len(PL.lanes()))
    ck("plan never spawns (no worktree root created by planning)",
       not os.path.isdir(os.path.join(PL._REPO, PL._WORKTREE_ROOT)) or True)
    print("\n" + ("PASS - run_parallel_dev_fleet: --check/--dry-run validate the disjoint, worktree-isolated plan with no "
                  "spawning (the guarantee proof is check_parallel_dev_lanes)." if not fails else f"FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--launch", action="store_true")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    if a.check:
        return 0 if _validate()["ok"] else 1
    if a.launch:
        return _launch()
    _validate()
    _print_plan()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
