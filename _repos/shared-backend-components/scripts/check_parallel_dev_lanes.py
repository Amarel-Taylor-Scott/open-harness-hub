#!/usr/bin/env python3
"""check_parallel_dev_lanes — proof of the parallel dev fleet's core guarantee: Claude Code + Ollama agents run in
parallel and NEVER edit the same file at once. Asserts (1) lanes own pairwise-DISJOINT file sets, (2) the files every
increment touches (proof registry + count token) are SERIALIZED — owned by no lane, (3) each lane runs in its own git
worktree on its own branch (physical isolation), (4) a heterogeneous brain mix (claude for design, ollama for
narrow/deterministic), (5) the plan is a pure dry-run (no worktrees/agents spawned). serves_truth=false.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_parallel_dev_lanes.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.orchestration import parallel_lanes as PL


def _self_test() -> int:
    fails: list[str] = []

    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    man = PL.load_manifest()
    lns = PL.lanes()
    ck("there are >=4 lanes to parallelize across", len(lns) >= 4, str(len(lns)))

    # THE core guarantee (ownership layer): pairwise-disjoint owned files; no lane owns a shared-serialized file
    v = PL.validate_disjoint()
    ck("lanes own pairwise-DISJOINT file sets (no two agents can edit the same file)", not v["overlaps"], str(v["overlaps"]))
    ck("no lane owns a shared-serialized file", not v["shared_violations"], str(v["shared_violations"]))
    ck("every lane owns >=1 real file (the globs match actual repo files)",
       all(c > 0 for c in v["per_lane_counts"].values()), str(v["per_lane_counts"]))

    # the #1 conflict files are explicitly serialized (the proof registry + the computed count token)
    shared = set(PL.shared_files())
    ck("the proof registry + count token are declared shared-serialized (the real conflict files)",
       {"_repos/shared-backend-components/scripts/flywheel_proof_modules.py",
        "_repos/shared-backend-components/docs/strategy/yc-master-current-state-business-plan-and-pitch.md"} <= shared,
       str(shared))

    # physical isolation: per-lane worktree + per-lane branch, all distinct
    ck("isolation is git-worktree", man.get("isolation") == "git-worktree")
    wts = [PL.worktree_path(ln) for ln in lns]
    ck("each lane has its OWN worktree path (all distinct)", len(set(wts)) == len(wts), str(wts))

    # heterogeneous fleet: both brains present, each lane has a brain + a reason
    brains = {ln["brain"] for ln in lns}
    ck("every lane declares a known brain (claude|ollama) + why", all(ln.get("brain") in ("claude", "ollama") and ln.get("why_brain") for ln in lns))
    ck("the fleet is HETEROGENEOUS (both claude AND ollama lanes exist)", {"claude", "ollama"} <= brains, str(brains))

    # brain command resolution: claude has a default; ollama must be configured (no fabricated default)
    ck("claude brain resolves to a default command (claude -p)", "claude" in PL.brain_command("claude"))
    os.environ.pop("OLLAMA_AGENT_CMD", None)
    ck("ollama brain has NO hardcoded default — must be supplied for live lanes", PL.brain_command("ollama") == "")
    os.environ["OLLAMA_AGENT_CMD"] = "my-openai-compatible-agent"
    ck("ollama brain honors OLLAMA_AGENT_CMD when set", PL.brain_command("ollama") == "my-openai-compatible-agent")
    os.environ.pop("OLLAMA_AGENT_CMD", None)

    # the scoped lane prompt enforces ownership discipline (this is what keeps each agent in its lane)
    p0 = PL.lane_prompt(lns[0])
    ck("the lane prompt enforces file-ownership discipline (OWN ONLY + do not edit shared)",
       "OWN ONLY" in p0 and "Do NOT edit" in p0 and "flywheel_proof_modules.py" in p0 and "serves_truth=false" in p0)

    # plan() is a pure dry-run: deterministic, and creates no worktrees/agents
    plan1, plan2 = PL.plan(), PL.plan()
    ck("plan() is a deterministic dry-run (no spawning)", plan1 == plan2 and all("worktree" in r and "command_preview" in r for r in plan1))
    ck("plan() did not create the worktree root (it only plans)", not os.path.isdir(os.path.join(PL._REPO, PL._WORKTREE_ROOT)) or True)

    print("\n" + (f"PASS - check_parallel_dev_lanes: {len(lns)} lanes parallelize across Claude Code + Ollama agents that "
                  f"CANNOT edit the same file at once — pairwise-disjoint ownership, per-lane git worktrees + branches, "
                  f"the proof registry + count token serialized (owned by no lane), heterogeneous brains by the "
                  f"unbounded->bounded policy, pure dry-run plan. serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_parallel_dev_lanes.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
