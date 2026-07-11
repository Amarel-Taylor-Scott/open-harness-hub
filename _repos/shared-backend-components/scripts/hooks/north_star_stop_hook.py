#!/usr/bin/env python3
"""_repos/shared-backend-components/scripts/hooks/north_star_stop_hook.py — Claude Code STOP hook: in-session forever-continuation of the loop.

Wired in .claude/settings.json under hooks.Stop. At each turn end Claude Code runs this; it decides whether the
agent stops or continues. To CONTINUE we emit {"decision":"block","reason": <the self-generated next-cycle prompt>}
so the agent immediately starts the next loop cycle without the human re-pasting anything. The prompt itself comes
from scripts.loop_prompt_builder (generated from .agent/next-action.json — the loop is self-prompting).

THREE SAFETY RAILS (this hook is OFF and harmless by default):
  1. OPT-IN  — does nothing unless .agent/LOOP_ACTIVE exists. With no LOOP_ACTIVE the hook exits 0 (the agent
               stops normally), so a normal interactive session in this repo is never trapped.
  2. STOP    — if .agent/STOP_REQUESTED exists, it allows the stop (owner's kill switch), even mid-loop.
  3. CAP     — a per-run iteration counter (.agent/loop/hook_iterations) bounds continuations to
               NORTH_STAR_LOOP_MAX_ITERS (default 200); at the cap it allows the stop. rm the counter to reset.
FAIL-OPEN: any error (bad stdin, builder failure, fs error) ALLOWS the stop — the hook never traps a session it
shouldn't. ANTI-SLOP (stop-slop spirit): the continuation prompt carries the no-fake-completion / no-soft-stop gate.

Owner controls:  touch .agent/LOOP_ACTIVE  (start)   ·  touch .agent/STOP_REQUESTED  (stop)
                 rm .agent/loop/hook_iterations       (reset the cap)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/aidevobserver_hook.py) ───────────────────────────────
# A Stop hook is launched by the harness from an ARBITRARY cwd — resolve the dir that holds the `scripts`
# package and install every code root BEFORE any `from scripts.*` import (this file previously imported
# scripts._repo_paths first and crashed ModuleNotFoundError on every stop).
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[2])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource as _resource  # noqa: E402

_install_code_roots()

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2])
# sentinel dir defaults to the real .agent; NORTH_STAR_LOOP_AGENT_DIR overrides it so the proof can exercise
# every guard path in a TEMP dir without ever touching (and accidentally arming) the real .agent/LOOP_ACTIVE.
_AGENT = Path(os.environ.get("NORTH_STAR_LOOP_AGENT_DIR") or ((_REPO / ".agent")))
_LOOP_ACTIVE = _AGENT / "LOOP_ACTIVE"
_STOP = _AGENT / "STOP_REQUESTED"
_COUNTER = _AGENT / "loop" / "hook_iterations"
_MAX = int(os.environ.get("NORTH_STAR_LOOP_MAX_ITERS", "200"))


def _allow_stop(note: str = "") -> None:
    """Let the agent stop normally: emit no block, exit 0. (Note -> stderr, shown in Claude Code's hook debug.)"""
    if note:
        sys.stderr.write(f"[north-star-loop-stop-hook] {note}\n")
    raise SystemExit(0)


def _continue(prompt: str) -> None:
    """Continue the loop: block the stop and feed the next-cycle prompt back to the agent."""
    print(json.dumps({"decision": "block", "reason": prompt}))
    raise SystemExit(0)


def main() -> None:
    # read (and ignore-on-error) the hook payload; we never crash-block on bad input
    try:
        raw = sys.stdin.read()
        _ = json.loads(raw) if raw.strip() else {}
    except Exception:
        _allow_stop("unreadable hook input -> allowing stop (fail-open)")

    # rail 1: OFF unless the owner opted in
    if not _LOOP_ACTIVE.exists():
        _allow_stop("LOOP_ACTIVE absent -> hook inert; allowing stop")
    # rail 2: owner stop switch
    if _STOP.exists():
        _allow_stop("STOP_REQUESTED present -> allowing stop")
    # rail 3: bounded continuations
    try:
        n = int(_COUNTER.read_text()) if _COUNTER.exists() else 0
    except Exception:
        n = 0
    if n >= _MAX:
        _allow_stop(f"iteration cap {_MAX} reached -> allowing stop (rm {_COUNTER} or raise NORTH_STAR_LOOP_MAX_ITERS to resume)")

    # continue: generate the next-cycle prompt from state, increment the counter, block the stop
    try:
        if str(_REPO) not in sys.path:
            sys.path.insert(0, str(_REPO))
        from scripts.loop_prompt_builder import emit
        prompt = emit()
    except Exception as e:  # builder failure -> fail open, never trap the session
        _allow_stop(f"prompt builder error ({type(e).__name__}: {e}) -> allowing stop (fail-open)")
    try:
        _COUNTER.parent.mkdir(parents=True, exist_ok=True)
        _COUNTER.write_text(str(n + 1))
    except Exception:
        pass
    _continue(prompt)


if __name__ == "__main__":
    main()
