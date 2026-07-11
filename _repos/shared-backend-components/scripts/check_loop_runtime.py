#!/usr/bin/env python3
"""scripts.check_loop_runtime — PROOF: the self-prompting north-star LOOP RUNTIME (builder + Stop hook + durable
runner) runs the loop forever SAFELY — self-generating each cycle's prompt from repo state, bounded, STOP-guarded,
inert by default, and fail-open.

Three layers, each proven:
  - loop_prompt_builder.py  — generates the next cycle's /loop prompt FROM .agent/next-action.json (self-prompting).
  - _repos/shared-backend-components/scripts/hooks/north_star_stop_hook.py — Stop hook: continues the loop IN-SESSION (block+next-prompt) only when
    armed (.agent/LOOP_ACTIVE), not stopped (.agent/STOP_REQUESTED), under the per-run cap; else allows the stop.
  - _repos/shared-backend-components/scripts/run_north_star_loop.sh — durable EXTERNAL runner (claude -p) across sessions, with --check/--dry-run/
    --once/MAX_CYCLES + the STOP guard.

Asserts:
  A. BUILDER: emit() carries every standing invariant + is state-driven (next_action flows in) + deterministic.
  B. HOOK INERT BY DEFAULT: no LOOP_ACTIVE -> allow stop (empty stdout, exit 0) — a normal session is never trapped.
  C. HOOK ARMS: LOOP_ACTIVE + no STOP + under cap -> {"decision":"block","reason": <self-prompt + anti-slop gate>};
     the per-run counter increments (bounded).
  D. HOOK STOP-GUARD: LOOP_ACTIVE + STOP_REQUESTED -> allow stop (owner kill switch wins).
  E. HOOK CAP: counter at the cap -> allow stop (bounded continuations).
  F. HOOK FAIL-OPEN: malformed stdin (even when armed) -> allow stop, never crash-block.
  G. RUNNER: --check CONTRACT OK; --dry-run prints the self-prompt and launches NO claude (tattle-file proof);
     the script carries the STOP guard + MAX cap + uses the builder.
  H. SETTINGS: .claude/settings.json wires the Stop hook at hooks.Stop -> the hook script.
  I. SAFETY: no secret-value pattern in the runtime files; bounded (cap + MAX_CYCLES) + STOP-guarded + anti-slop +
     fail-open + inert-by-default are all present.

The hook's SENTINEL dir is redirected to a TEMP dir for every armed/STOP/cap test, so this proof NEVER touches (or
arms) the real .agent/LOOP_ACTIVE. Deterministic + offline; invokes no `claude`. Exit 0/1.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_HOOK = _resource("scripts/hooks/north_star_stop_hook.py")
_RUNNER = _resource("scripts/run_north_star_loop.sh")
_SETTINGS = _REPO.parent.parent / ".claude" / "settings.json"  # .claude stayed at the monorepo root (_repos/<sbc>.parent.parent)
_PAYLOAD = json.dumps({"session_id": "t", "hook_event_name": "Stop", "stop_hook_active": False})
_LEAK = re.compile(r"sk-[A-Za-z0-9]{16,}|gsk_[A-Za-z0-9]{16,}|AIza[A-Za-z0-9]{16,}|secret://[^\s\"']+|Bearer\s+[A-Za-z0-9._-]{16,}")


def _run_hook(agent_dir: Path, payload: str = _PAYLOAD, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "NORTH_STAR_LOOP_AGENT_DIR": str(agent_dir)}
    if env_extra:
        env.update(env_extra)
    return subprocess.run([sys.executable, str(_HOOK)], input=payload, capture_output=True, text=True,
                          env=env, cwd=str(_REPO), timeout=30)


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    from scripts.loop_prompt_builder import LOOP_COMMAND, _REQUIRED, build_prompt, emit

    # A — builder
    prompt = emit()
    check("A: builder emits every standing invariant", all(r in prompt for r in _REQUIRED),
          f"missing={[r for r in _REQUIRED if r not in prompt]}")
    check("A: builder is state-driven + deterministic",
          "ZZ_SENTINEL" in build_prompt({"next_target": "ZZ_SENTINEL"})
          and build_prompt({"next_target": "x"}) == build_prompt({"next_target": "x"}))

    d_empty = Path(tempfile.mkdtemp(prefix="nsloop-empty-"))
    d_arm = Path(tempfile.mkdtemp(prefix="nsloop-arm-"))
    try:
        # B — inert by default
        r = _run_hook(d_empty)
        check("B: inert (no LOOP_ACTIVE) -> allow stop (empty stdout, exit 0)", r.returncode == 0 and r.stdout.strip() == "")

        # C — armed -> block + self-prompt; counter increments
        (d_arm / "LOOP_ACTIVE").write_text("")
        (d_arm / "loop").mkdir(exist_ok=True)
        r = _run_hook(d_arm)
        try:
            blocked = json.loads(r.stdout or "{}")
        except Exception:
            blocked = {}
        check("C: armed -> block with the self-prompt + anti-slop gate as reason",
              blocked.get("decision") == "block" and LOOP_COMMAND in blocked.get("reason", "")
              and "NO fake completion" in blocked.get("reason", ""), str(blocked)[:120])
        check("C: per-run counter increments (bounded continuations)",
              (d_arm / "loop" / "hook_iterations").read_text() == "1")

        # D — STOP guard wins
        (d_arm / "STOP_REQUESTED").write_text("done")
        r = _run_hook(d_arm)
        check("D: STOP_REQUESTED -> allow stop (owner kill switch)", r.returncode == 0 and r.stdout.strip() == "")
        (d_arm / "STOP_REQUESTED").unlink()

        # E — cap reached
        (d_arm / "loop" / "hook_iterations").write_text("999")
        r = _run_hook(d_arm, env_extra={"NORTH_STAR_LOOP_MAX_ITERS": "200"})
        check("E: iteration cap reached -> allow stop", r.returncode == 0 and r.stdout.strip() == "")

        # F — fail-open on malformed stdin even when armed
        (d_arm / "loop" / "hook_iterations").write_text("0")
        r = _run_hook(d_arm, payload="not json {{{")
        check("F: malformed stdin -> fail-open allow stop (never crash-block)", r.returncode == 0 and r.stdout.strip() == "")
    finally:
        shutil.rmtree(d_empty, ignore_errors=True)
        shutil.rmtree(d_arm, ignore_errors=True)

    # G — runner --check + --dry-run (no claude launch, proven via a tattle file)
    rc = subprocess.run(["bash", str(_RUNNER), "--check"], capture_output=True, text=True, cwd=str(_REPO), timeout=60)
    check("G: runner --check -> CONTRACT OK", "CONTRACT OK" in rc.stdout)
    tattle = Path(tempfile.gettempdir()) / "ns_loop_claude_tattle"
    tattle.unlink(missing_ok=True)
    rd = subprocess.run(["bash", str(_RUNNER), "--dry-run"], capture_output=True, text=True, cwd=str(_REPO),
                        timeout=60, env={**os.environ, "CLAUDE_CODE_CMD": f"touch {tattle}"})
    check("G: --dry-run prints the self-prompt + launches NO claude (tattle file absent)",
          LOOP_COMMAND in rd.stdout and not tattle.exists())
    tattle.unlink(missing_ok=True)
    runner_src = _RUNNER.read_text()
    check("G: runner carries STOP guard + MAX cap + uses the self-prompt builder",
          "STOP_REQUESTED" in runner_src and "MAX_CYCLES" in runner_src and "loop_prompt_builder" in runner_src)

    # H — settings wiring
    settings = json.loads(_SETTINGS.read_text())
    stop_entry = json.dumps(settings.get("hooks", {}).get("Stop", []))
    check("H: .claude/settings.json wires the Stop hook -> north_star_stop_hook.py", "north_star_stop_hook.py" in stop_entry)

    # I — safety
    blob = "\n".join([(_resource(p)).read_text(encoding="utf-8") for p in (
        "scripts/loop_prompt_builder.py", "scripts/hooks/north_star_stop_hook.py",
        "scripts/run_north_star_loop.sh")] + [_SETTINGS.read_text(encoding="utf-8")])  # .claude stayed at root (not _resource-mapped)
    check("I: no secret-value pattern in the runtime files", not _LEAK.search(blob))
    low = blob.lower()
    check("I: bounded + STOP-guarded + inert-by-default + fail-open + anti-slop all present",
          "north_star_loop_max_iters" in low and "max_cycles" in low and "loop_active" in low
          and "stop_requested" in low and "fail-open" in low and "anti-slop" in low)

    print("\n" + ("PASS — check_loop_runtime: the self-prompting loop runtime generates each cycle's prompt from "
                  ".agent/next-action.json, continues forever in-session via a Stop hook that is INERT by default, "
                  "STOP-guarded, iteration-capped and fail-open, and runs durably across sessions via the runner "
                  "(--check/--dry-run launch nothing); no secret leak." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_loop_runtime.py --self-test")
    raise SystemExit(0)
