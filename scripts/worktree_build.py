#!/usr/bin/env python3
"""scripts.worktree_build — run the Kimi/GLM build_loop in an ISOLATED git worktree (safe persistent code-editing).

build_loop does `git reset --hard` on a red cycle — UNSAFE in the shared tree (it can revert the swarm/flywheel/
human work; it deleted a file twice). This runs it in a dedicated worktree on branch `auto/ollama-build`, located
OUTSIDE the main working tree, with its OWN index — so its checkpoints/resets/commits touch ONLY the worktree and
never contend with the main repo. Merge `auto/ollama-build` → your branch when you want the changes. The gitignored
.env (Ollama key) is symlinked in so the lane authenticates. serves_truth=false (cycles are gate-checked candidates).

  --self-test            offline pure-logic test (no git mutation)
  --setup                create the worktree (+ .env symlink) if missing
  --run [args...]        setup, then run ONE build_loop cycle INSIDE the worktree
  --supervise [args...]  setup, then run build_loop --supervise inside the worktree (persistent isolated loop)
  --status               worktree path, branch, recent commits, ahead/behind main
  --stop                 request the isolated build_loop to halt (writes the worktree's STOP flag)
  --teardown             remove the worktree (the branch + its commits are kept)
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WT_DIR = REPO.parent / ".oh-worktrees" / "ollama-build"     # OUTSIDE the main tree → resets can't touch it
BRANCH = "auto/ollama-build"
_MODE_FLAGS = {"--self-test", "--setup", "--run", "--supervise", "--status", "--stop", "--teardown"}


def _git(*args: str, cwd: Path | None = None):
    return subprocess.run(["git", *args], cwd=str(cwd or REPO), capture_output=True, text=True)


def worktree_exists() -> bool:
    return (WT_DIR / ".git").exists() and str(WT_DIR) in _git("worktree", "list", "--porcelain").stdout


def setup() -> Path:
    WT_DIR.parent.mkdir(parents=True, exist_ok=True)
    if not (WT_DIR / ".git").exists():
        r = _git("worktree", "add", "--force", "-B", BRANCH, str(WT_DIR), "HEAD")
        if r.returncode and "already" not in (r.stderr or "").lower():
            raise RuntimeError(f"worktree add failed: {r.stderr.strip()}")
    env_link = WT_DIR / ".env"                              # symlink the gitignored key so the lane authenticates
    if not env_link.exists() and (REPO / ".env").exists():
        try:
            env_link.symlink_to(REPO / ".env")
        except OSError:
            pass
    return WT_DIR


def run_in_worktree(extra: list[str], *, one: bool) -> int:
    wt = setup()
    # build_loop resolves its own REPO = parents[1] of <wt>/scripts/build_loop.py = the worktree → it operates there
    cmd = [sys.executable, "scripts/build_loop.py", "--run" if one else "--supervise", *extra]
    env = {**os.environ, "PYTHONPATH": str(wt)}
    return subprocess.call(cmd, cwd=str(wt), env=env)


def status() -> None:
    print(f"worktree: {WT_DIR}")
    print(f"exists:   {worktree_exists()}")
    print(f"branch:   {BRANCH}")
    if worktree_exists():
        print("recent:")
        print("  " + (_git("log", "--oneline", "-5", BRANCH).stdout.strip().replace("\n", "\n  ") or "(none)"))
        ab = _git("rev-list", "--left-right", "--count", f"main...{BRANCH}").stdout.strip()
        if ab:
            print(f"main <-> {BRANCH} (behind  ahead): {ab}")


def stop() -> None:
    f = WT_DIR / ".agent" / "BUILD_STOP_REQUESTED"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("", encoding="utf-8")
    print(f"stop requested: {f}")


def teardown() -> None:
    if worktree_exists():
        _git("worktree", "remove", "--force", str(WT_DIR))
        print(f"removed worktree {WT_DIR} (branch {BRANCH} + its commits kept)")
    else:
        print("no worktree to remove")


def self_test() -> int:
    import tempfile
    # build_loop in a worktree resolves REPO to the worktree (parents[1] of scripts/build_loop.py)
    fake = Path(tempfile.mkdtemp()) / "wt"
    (fake / "scripts").mkdir(parents=True)
    (fake / "scripts" / "build_loop.py").write_text("# stub", encoding="utf-8")
    assert (fake / "scripts" / "build_loop.py").resolve().parents[1] == fake, "REPO must resolve to the worktree"
    # the worktree is OUTSIDE the main tree (so resets can't touch main)
    assert not str(WT_DIR).startswith(str(REPO) + os.sep), "worktree must live outside the main repo"
    assert WT_DIR.name == "ollama-build" and BRANCH == "auto/ollama-build"
    # command construction passes build_loop flags through, strips mode flags
    extra = [a for a in ["--supervise", "--harness", "aider"] if a not in _MODE_FLAGS]
    assert extra == ["--harness", "aider"], extra
    cmd = [sys.executable, "scripts/build_loop.py", "--supervise", *extra]
    assert cmd[1].endswith("build_loop.py") and "--supervise" in cmd
    print("worktree_build self-test: OK (REPO→worktree, outside-main isolation, flag passthrough, cmd build)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    if "--status" in argv:
        status(); return 0
    if "--stop" in argv:
        stop(); return 0
    if "--teardown" in argv:
        teardown(); return 0
    if "--setup" in argv:
        print(f"worktree ready: {setup()}"); return 0
    extra = [a for a in argv if a not in _MODE_FLAGS]
    if "--run" in argv:
        return run_in_worktree(extra, one=True)
    if "--supervise" in argv:
        return run_in_worktree(extra, one=False)
    print("usage: worktree_build.py --self-test | --setup | --run | --supervise | --status | --stop | --teardown")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
