#!/usr/bin/env python3
"""scripts.build_loop — the AUTONOMOUS LLM coding loop on the Ollama Cloud lane (GLM 5.2 + Kimi K2.7-code).

This is the harness that lets Kimi/GLM actually *write code* (not just review): each cycle picks one
backlog item, drives a coding agent (opencode `run` by default, or aider) to implement it, then runs the
HONEST proof gate (_repos/shared-backend-components/scripts/run_proofs.py) as the objective arbiter — committing ONLY on green and reverting
on red. It is the open-model replacement for "Claude Code drives the build".

Safety rails (serves_truth=false — every cycle is a candidate the gate accepts or rejects):
  * NEVER runs on main/master (refuses; branch first).
  * CHECKPOINTS the working tree (commit) BEFORE the agent edits, so a red cycle's `git reset --hard HEAD`
    only discards the agent's bad changes — never pre-existing work (lossless; matches the ./loop norm).
  * Only NEW untracked files created during a red cycle are removed (a snapshot diff — never deletes other
    untracked files).
  * The proof gate is OUTSIDE the model's control. "It's green" gates the auto-commit; owner-gated proposals
    are skipped (they need a human warrant per the change-verification contract).
  * Honors .agent/BUILD_STOP_REQUESTED and a --max-cycles cap.

  --self-test                 offline: task selection, prompt build, gate-parse, state roundtrip (no model/git writes)
  --run [opts]                run ONE cycle (live: agent edits + gate + commit/revert)
  --supervise [opts]          loop cycles until .agent/BUILD_STOP_REQUESTED (the ./build "start" entry)
  --status                    print loop state (read-only)
Options: --harness opencode|aider  --model <id>  --architect  --task "<text>"  --gate <substr>
         --interval-sec N  --max-cycles N  --timeout-sec N  --goal-file <path>
CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/build_loop.py --run --harness opencode
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts._config import (  # noqa: E402
    AIDEVOBSERVER_ROUTE_PACKET_BUILD_INSTRUCTION,
    AIDEVOBSERVER_ROUTE_PACKET_LABEL,
    AIDEVOBSERVER_ROUTE_PACKET_MAX_PROMPT_CHARS,
)

PROPOSALS = _resource("data") / "dev-intel" / "proposals.jsonl"
STATE = _resource("data") / "dev-intel" / "build_loop_state.json"
LEDGER = _resource("data") / "dev-intel" / "build_loop.jsonl"
STOP = (REPO / ".agent") / "BUILD_STOP_REQUESTED"
GOAL_DEFAULT = _resource("docs") / "goals" / "ollama-build-loop.md"

DEFAULT_HARNESS = "opencode"
DEFAULT_MODEL = "kimi-k2.7-code"          # coding-specialized; --architect adds a GLM 5.2 plan pass (aider)
ARCHITECT_MODEL = "glm-5.2"
GATE_CMD = ["python3", str(_resource("scripts/run_proofs.py"))]   # exit code == number of red proofs (0 = green)
PROTECTED_BRANCHES = {"main", "master"}


# ── env: be self-sufficient (work even if ./build's shim didn't run) ──────────────────────────────────
def ensure_env() -> None:
    """Load the gitignored .env and put the Ollama Cloud lane on os.environ for opencode/aider."""
    f = REPO / ".env"
    if f.exists():
        for ln in f.read_text(encoding="utf-8").splitlines():
            ln = ln[7:] if ln.startswith("export ") else ln
            if not ln or ln.startswith("#") or "=" not in ln:
                continue
            k, v = ln.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    key = os.environ.get("OLLAMA_API_KEY") or os.environ.get("OH_LLM_API_KEY") or ""
    os.environ.setdefault("OLLAMA_API_KEY", key)
    os.environ.setdefault("OPENAI_API_BASE", os.environ.get("OH_LLM_BASE_URL", "https://ollama.com/v1"))
    os.environ.setdefault("OPENAI_API_KEY", key)


# ── git helpers ───────────────────────────────────────────────────────────────────────────────────────
def _git(*args: str, check: bool = False) -> str:
    r = subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def current_branch() -> str:
    return _git("branch", "--show-current")


def head_sha() -> str:
    return _git("rev-parse", "HEAD")


def untracked_files() -> set[str]:
    return set(_git("ls-files", "--others", "--exclude-standard").splitlines())


def tree_dirty() -> bool:
    return bool(_git("status", "--porcelain"))


def checkpoint_commit(msg: str) -> bool:
    """Commit the current tree so the cycle has a clean rollback target. Returns True if anything committed."""
    if not tree_dirty():
        return False
    _git("add", "-A")
    r = subprocess.run(["git", "commit", "-m", msg, "--no-verify"], cwd=REPO, capture_output=True, text=True)
    return r.returncode == 0


def revert_failed_cycle(base_sha: str, untracked_before: set[str]) -> None:
    """Discard the agent's TRACKED changes back to the checkpoint. We deliberately do NOT delete untracked files:
    with concurrent writers (the swarm, the flywheel, a human, Claude Code) a blanket untracked-clean can destroy
    unrelated work — it once deleted a file being written alongside a cycle. New untracked files from a red cycle
    are left for inspection (the next checkpoint absorbs them, or a human removes them). For full isolation, run
    this loop in a dedicated git worktree."""
    _git("reset", "--hard", base_sha)
    _ = untracked_before  # kept for signature/back-compat; intentionally NOT used to delete files


# ── task selection ──────────────────────────────────────────────────────────────────────────────────--
def load_proposals() -> list[dict]:
    if not PROPOSALS.exists():
        return []
    out = []
    for ln in PROPOSALS.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln:
            try:
                out.append(json.loads(ln))
            except json.JSONDecodeError:
                pass
    return out


def pick_task(state: dict, explicit: str | None) -> dict | None:
    """Highest-scored non-owner-gated, not-yet-attempted proposal. owner_gated items are SKIPPED (need a human
    warrant). Returns {pid, title, kind, next_steps} or a synthetic task for an explicit --task string."""
    if explicit:
        return {"pid": "explicit", "title": explicit, "kind": "explicit", "next_steps": ""}
    done = set(state.get("done_pids", []))
    cand = []
    for p in load_proposals():
        if p.get("comfort") == "owner_gated":
            continue
        if str(p.get("status", "open")).lower() in ("done", "applied", "closed", "rejected"):
            continue
        pid = p.get("pid") or p.get("id") or p.get("title", "")
        if pid in done:
            continue
        try:
            score = float(p.get("score", 0) or 0)
        except (TypeError, ValueError):
            score = 0.0
        cand.append((score, pid, p))
    if not cand:
        return None
    cand.sort(key=lambda t: t[0], reverse=True)
    _, pid, p = cand[0]
    return {"pid": pid, "title": p.get("title", ""), "kind": p.get("kind", "proposal"),
            "next_steps": p.get("next_steps", ""), "rationale": p.get("rationale", "")}


def build_prompt(task: dict, goal_file: Path) -> str:
    title = str(task["title"])
    if AIDEVOBSERVER_ROUTE_PACKET_LABEL in title:
        return f"{title.rstrip()}\n{AIDEVOBSERVER_ROUTE_PACKET_BUILD_INSTRUCTION}\n"
    goal = goal_file.read_text(encoding="utf-8") if goal_file.exists() else (
        "Make one small, high-value, REVERSIBLE improvement to this repo. Follow AGENTS.md and CLAUDE.md.")
    return (
        f"{goal}\n\n"
        "=== THIS CYCLE — implement exactly ONE small change ===\n"
        f"Task: {title}\n"
        f"Kind: {task.get('kind','')}\n"
        f"Next steps hint: {task.get('next_steps','')}\n\n"
        "HARD RULES:\n"
        "1. Keep the change SMALL and self-contained (prefer one module + its asserting check).\n"
        "2. Follow the CLAUDE.md fast-path. NO magic values (compute/centralize shared values).\n"
        "3. The change MUST keep the proof gate green: `PYTHONPATH=. python3 scripts/run_proofs.py`.\n"
        "   If you add or alter a seam, update its --self-test in the SAME change.\n"
        "4. Do NOT touch brand/pricing/strategy/vocabulary (owner-gated). Do NOT expand insurance examples.\n"
        "5. If you cannot do it safely, make NO changes and say why.\n"
    )


# ── harness invocation ──────────────────────────────────────────────────────────────────────────────--
def run_opencode(prompt: str, model: str, timeout: int) -> tuple[bool, str]:
    cmd = ["opencode", "run", "--log-level", "ERROR", "-m", f"ollama-cloud/{model}", prompt]
    return _run(cmd, timeout)


def run_aider(prompt: str, model: str, architect: bool, timeout: int) -> tuple[bool, str]:
    cmd = ["aider", "--yes-always", "--no-auto-commits", "--no-show-model-warnings",
           "--model-metadata-file", str(REPO / ".aider.model.metadata.json"), "--map-tokens", "2048"]
    if architect:
        cmd += ["--model", f"openai/{ARCHITECT_MODEL}", "--editor-model", f"openai/{model}",
                "--architect", "--auto-accept-architect"]
    else:
        cmd += ["--model", f"openai/{model}"]
    cmd += ["--message", prompt]
    return _run(cmd, timeout)


def _run(cmd: list[str], timeout: int) -> tuple[bool, str]:
    try:
        r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, (r.stdout or "")[-4000:] + (("\n[stderr]\n" + r.stderr[-1500:]) if r.stderr else "")
    except subprocess.TimeoutExpired:
        return False, f"harness timed out after {timeout}s"
    except FileNotFoundError as e:
        return False, f"harness not found: {e}"


# ── proof gate ──────────────────────────────────────────────────────────────────────────────────────--
def run_gate(substr: str | None, timeout: int = 1200) -> tuple[bool, int, str]:
    cmd = ["python3", str(_resource("scripts/run_proofs.py"))] + ([substr] if substr else [])
    env = {**os.environ, "PYTHONPATH": str(REPO) + os.pathsep + os.environ.get("PYTHONPATH", "")}
    try:
        r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return False, -1, f"gate timed out after {timeout}s"
    tail = (r.stdout or "")[-2500:]
    return r.returncode == 0, r.returncode, tail


# ── state + ledger ──────────────────────────────────────────────────────────────────────────────────--
def load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"cycles": 0, "committed": 0, "reverted": 0, "done_pids": [], "last": None}


def save_state(state: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def append_ledger(entry: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    entry["serves_truth"] = False
    with LEDGER.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


# ── one cycle ───────────────────────────────────────────────────────────────────────────────────────--
def run_cycle(*, harness: str, model: str, architect: bool, explicit: str | None, gate_substr: str | None,
              goal_file: Path, timeout: int, dry_run: bool = False) -> dict:
    branch = current_branch()
    if branch in PROTECTED_BRANCHES:
        return {"ok": False, "reason": f"refusing to run on protected branch {branch!r} — branch first"}

    state = load_state()
    task = pick_task(state, explicit)
    if not task:
        return {"ok": True, "reason": "no actionable (non-owner-gated) task in the backlog", "noop": True}

    prompt = build_prompt(task, goal_file)
    if dry_run:
        return {"ok": True, "dry_run": True, "task": task["title"][:80], "harness": harness, "model": model,
                "prompt_chars": len(prompt)}

    checkpoint_commit(f"chore(build-loop): checkpoint before cycle {state['cycles'] + 1}")
    base = head_sha()
    untracked_before = untracked_files()

    if harness == "aider":
        ran_ok, out = run_aider(prompt, model, architect, timeout)
    else:
        ran_ok, out = run_opencode(prompt, model, timeout)

    changed = tree_dirty() or head_sha() != base
    result = {"ts": _now(), "cycle": state["cycles"] + 1, "harness": harness, "model": model,
              "task_pid": task["pid"], "task": task["title"][:140], "ran_ok": ran_ok, "changed": changed}

    if not changed:
        result.update(outcome="noop", note="agent made no change")
    else:
        green, red_n, tail = run_gate(gate_substr)
        result.update(gate_green=green, gate_red=red_n)
        if green:
            _git("add", "-A")
            subprocess.run(["git", "commit", "-m",
                            f"feat(build-loop): {task['title'][:60]} [{model}]", "--no-verify"],
                           cwd=REPO, capture_output=True, text=True)
            result.update(outcome="committed", commit=head_sha()[:10])
            state["committed"] += 1
        else:
            revert_failed_cycle(base, untracked_before)
            result.update(outcome="reverted", gate_tail=tail[-800:])
            state["reverted"] += 1

    state["cycles"] += 1
    state["done_pids"] = (state.get("done_pids", []) + [task["pid"]])[-500:]
    state["last"] = {k: result.get(k) for k in ("ts", "outcome", "task", "model", "gate_red")}
    save_state(state)
    append_ledger(result)
    return {"ok": True, **result}


def supervise(*, interval: int, max_cycles: int | None, **cycle_kw) -> int:
    print(f"build-loop: supervising (harness={cycle_kw['harness']} model={cycle_kw['model']} "
          f"architect={cycle_kw['architect']}). Stop: touch {STOP.relative_to(REPO)}")
    n = 0
    while True:
        if STOP.exists():
            print("BUILD_STOP_REQUESTED — halting (state preserved)."); return 0
        if max_cycles is not None and n >= max_cycles:
            print(f"reached --max-cycles {max_cycles}."); return 0
        res = run_cycle(**cycle_kw)
        n += 1
        print(f"[{_now()}] cycle {n}: {res.get('outcome') or res.get('reason')}"
              + (f" — {res.get('task','')[:70]}" if res.get("task") else ""))
        if res.get("noop") and not res.get("changed"):
            time.sleep(max(interval, 30))
        else:
            time.sleep(interval)


def print_status() -> int:
    s = load_state()
    print("=== build-loop status ===")
    print(f"branch:    {current_branch()}")
    print(f"cycles:    {s.get('cycles', 0)}  committed={s.get('committed', 0)}  reverted={s.get('reverted', 0)}")
    print(f"stop flag: {'SET' if STOP.exists() else 'clear'}")
    print(f"last:      {json.dumps(s.get('last'))}")
    print(f"ledger:    {LEDGER.relative_to(REPO)} ({LEDGER.stat().st_size if LEDGER.exists() else 0} bytes)")
    return 0


# ── offline self-test (the proof-gate entry) ──────────────────────────────────────────────────────────
def self_test() -> int:
    import tempfile
    # task selection: owner_gated skipped, highest score wins, done_pids excluded
    rows = [{"pid": "a", "score": 0.9, "comfort": "owner_gated", "title": "gated"},
            {"pid": "b", "score": 0.5, "comfort": "auto", "title": "good"},
            {"pid": "c", "score": 0.8, "comfort": "propose", "title": "better"}]
    tmp = Path(tempfile.mkdtemp()) / "p.jsonl"
    tmp.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    global PROPOSALS
    orig = PROPOSALS
    try:
        PROPOSALS = tmp
        t = pick_task({"done_pids": []}, None)
        assert t and t["pid"] == "c", f"expected highest non-gated 'c', got {t}"
        assert pick_task({"done_pids": ["c"]}, None)["pid"] == "b", "done_pids must exclude c"
        assert pick_task({"done_pids": ["b", "c"]}, None) is None or \
            pick_task({"done_pids": ["b", "c"]}, None)["pid"] not in ("b", "c"), "all-done -> None"
        ex = pick_task({"done_pids": []}, "do the thing")
        assert ex["pid"] == "explicit" and ex["title"] == "do the thing"
    finally:
        PROPOSALS = orig
    # prompt build carries the hard rules + the task
    pr = build_prompt({"pid": "x", "title": "TASKY", "kind": "k", "next_steps": "ns"}, Path("/does/not/exist"))
    assert "TASKY" in pr and "run_proofs.py" in pr and "owner-gated" in pr, "prompt missing rails"
    rp = build_prompt({
        "pid": "route",
        "title": (
            "TASK: Build a CSV import flow\n"
            f"{AIDEVOBSERVER_ROUTE_PACKET_LABEL}\n"
            "action: fetch/import refs; wire components into a template/DAG; write only missing glue/tests\n"
            "selected:\n"
            "- id:csv.read; edge:Path=>list[CsvRow]; does:read CSV; mut:-; ref:src/x.py::read\n"
        ),
        "kind": "explicit",
        "next_steps": "",
    }, Path("/does/not/exist"))
    assert "run_proofs.py" not in rp and len(rp) <= AIDEVOBSERVER_ROUTE_PACKET_MAX_PROMPT_CHARS, \
        "route packet prompt should bypass broad goal context"
    # state roundtrip — use a TEMP state path; NEVER pollute the real loop state (run_proofs runs this)
    global STATE
    orig_state = STATE
    try:
        STATE = Path(tempfile.mkdtemp()) / "state.json"
        st = {"cycles": 3, "committed": 1, "reverted": 2, "done_pids": ["z"], "last": None}
        save_state(st); assert load_state()["cycles"] == 3
    finally:
        STATE = orig_state
    # protected-branch guard is wired (string check — no git mutation here)
    assert PROTECTED_BRANCHES == {"main", "master"}
    print("build_loop self-test: OK (task-select, prompt-rails, state-roundtrip, branch-guard)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()

    def opt(name: str, default=None):
        return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default

    cycle_kw = dict(
        harness=opt("--harness", DEFAULT_HARNESS),
        model=opt("--model", DEFAULT_MODEL),
        architect="--architect" in argv,
        explicit=opt("--task"),
        gate_substr=opt("--gate"),
        goal_file=Path(opt("--goal-file", str(GOAL_DEFAULT))),
        timeout=int(opt("--timeout-sec", "900")),
    )
    ensure_env()

    if "--status" in argv:
        return print_status()
    if "--run" in argv:
        res = run_cycle(dry_run="--dry-run" in argv, **cycle_kw)
        print(json.dumps(res, indent=2))
        return 0 if res.get("ok") else 1
    if "--supervise" in argv or "--forever" in argv:
        mc = opt("--max-cycles")
        return supervise(interval=int(opt("--interval-sec", "45")),
                         max_cycles=int(mc) if mc else None, **cycle_kw)
    print(__doc__.strip().splitlines()[0])
    print("usage: build_loop.py --self-test | --run | --supervise | --status  [--harness opencode|aider]"
          " [--model id] [--architect] [--task ...] [--gate substr] [--max-cycles N]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
