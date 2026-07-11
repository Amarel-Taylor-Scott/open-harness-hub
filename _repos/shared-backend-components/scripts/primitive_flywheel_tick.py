#!/usr/bin/env python3
"""scripts.primitive_flywheel_tick — the scheduled autonomous flywheel: one cron TICK rotates a bounded unit of
primitive-building work across ALL our model lanes (Ollama-GLM · Ollama-Kimi · OpenWebUI-Gemma-4 · Codex CLI)
and harnesses (buildout orchestrator · enrichment · idea mint), so the factory keeps building WITHOUT the
Claude Code harness.

Each tick: check the STOP gate + the daily cap -> pick the next (harness, lane) round-robin -> run it BOUNDED
-> append a receipt to .flywheel/ticks.jsonl -> advance the rotation state. Everything the harnesses produce
stays candidate/serves_truth=false (they enforce it); this dispatcher only schedules and bounds them.

Safety (autonomous + keyed lanes cost money, so this is conservative):
  * STOP gate — `touch .flywheel/STOP` halts every future tick immediately (no-op exit 0).
  * daily cap — at most --max-ticks-per-day ticks run; the rest are no-ops (bounded spend).
  * bounded per tick — small batch sizes; a per-tick timeout.
  * every action logged; rotation state is idempotent; the codex code-editing lane is OPT-IN (--enable-codex).

    python3 scripts/primitive_flywheel_tick.py --self-test          # offline: rotation + gates + dispatch
    python3 scripts/primitive_flywheel_tick.py --run               # run ONE tick (what cron calls)
    python3 scripts/primitive_flywheel_tick.py --status            # show rotation state + recent ticks
    python3 scripts/primitive_flywheel_tick.py --install-cron      # print the crontab line to add
    touch .flywheel/STOP        # stop the flywheel;   rm .flywheel/STOP   to resume
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap ─────────────────────────────────────────────────────────────────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import subprocess  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_REPO = _sbc_boot  # shared-backend-components root
_DEFAULT_MAX_TICKS_PER_DAY = 36
_PER_TICK_TIMEOUT = 3000  # seconds (bounded so a stuck lane can't hang the cron slot forever)

# ── the LANES (our model endpoints) — provider + model as _llm_client knows them, or the codex CLI ────────────
LANES: dict[str, dict[str, str]] = {
    "ollama_glm": {"provider": "ollama", "model": "glm-5.2", "desc": "Ollama Cloud GLM 5.2"},
    "ollama_kimi": {"provider": "ollama", "model": "kimi-k2.7-code", "desc": "Ollama Cloud Kimi K2.7-code"},
    "openwebui_gemma": {"provider": "openwebui", "model": "gemma-4-coding", "desc": "OpenWebUI Gemma 4"},
    "openwebui_cdp": {"provider": "openwebui_cdp", "model": "gemma-4-coding",
                      "desc": "Gemma 4 via the logged-in-Chrome CDP bridge (Cloudflare-bypassed)"},
    "codex": {"provider": "codex", "model": "codex", "desc": "Codex CLI (opt-in code lane)"},
}

# ── the ROTATION: (harness, lane) jobs cycled round-robin. Each is a bounded command run from the repo root
#    with PYTHONPATH=. and .env sourced. `needs_codex` jobs run only when --enable-codex. ─────────────────────
def _job(name: str, lane: str, argv: list[str], *, needs_codex: bool = False) -> dict[str, Any]:
    return {"name": name, "lane": lane, "argv": argv, "needs_codex": needs_codex}


JOBS: list[dict[str, Any]] = [
    _job("buildout", "ollama_glm",
         ["scripts/primitive_buildout_orchestrator.py", "--run", "--providers", "ollama", "--model", "glm-5.2",
          "--count", "6"]),
    _job("enrich", "ollama_glm",
         ["scripts/enrich_minted_primitives.py", "--run", "--limit", "80", "--workers", "6"]),
    _job("buildout", "ollama_kimi",
         ["scripts/primitive_buildout_orchestrator.py", "--run", "--providers", "ollama", "--model",
          "kimi-k2.7-code", "--count", "6"]),
    _job("mint", "deterministic",
         ["scripts/mint_idea_primitives.py", "--mint", "--target", "4000"]),
    _job("grid_mint", "deterministic",
         ["scripts/primitive_grid_remixer.py", "--mint", "--target", "50000"]),   # scaled toward the 40M goal
    _job("persona_mint", "deterministic",
         ["scripts/persona_primitive_explorer.py", "--mint", "--target", "20000"]),
    _job("expand", "ollama_glm",
         ["scripts/primitive_expansion_loop.py", "--run", "--esoteric", "--rounds", "2", "--seeds", "20",
          "--provider", "ollama,openwebui_cdp", "--model", "glm-5.2"]),   # falls through to Gemma-CDP if Ollama caps
    _job("expand_gemma", "openwebui_cdp",
         ["scripts/primitive_expansion_loop.py", "--run", "--rounds", "1", "--seeds", "12",
          "--provider", "openwebui_cdp", "--model", "gemma-4-coding"]),
    _job("census", "deterministic", ["scripts/primitive_census.py", "--run"]),
    _job("db_build", "deterministic", ["scripts/primitive_database.py", "--build"]),
    _job("verify", "deterministic", ["scripts/primitive_verification_pipeline.py", "--run"]),
    _job("semantic_index", "deterministic", ["scripts/primitive_semantic_index.py", "--build"]),
    # resumable: each tick appends one chunk of block/column rows, accumulating toward the full database
    _job("multi_index_blocks", "deterministic", ["scripts/primitive_multi_index.py", "--build-blocks", "--append", "--chunk", "200000"]),
    _job("multi_index_columns", "deterministic", ["scripts/primitive_multi_index.py", "--build-columns", "--append", "--chunk", "200000"]),
    _job("multi_index_purpose", "deterministic", ["scripts/primitive_multi_index.py", "--build-semantic", "--attribute", "purpose"]),
    _job("multi_index_solution", "deterministic", ["scripts/primitive_multi_index.py", "--build-semantic", "--attribute", "solution"]),
    _job("buildout", "openwebui_gemma",
         ["scripts/primitive_buildout_orchestrator.py", "--run", "--providers", "openwebui", "--model",
          "gemma-4-coding", "--count", "6"]),
    _job("library_selftest", "deterministic",
         ["scripts/executable_primitive_library.py", "--self-test"]),
    # OPT-IN codex lane: proposes primitive specs to a candidate file (NOT editing tracked code) — safe autonomy.
    _job("codex_propose", "codex", [], needs_codex=True),
]


def _flywheel_dir() -> Path:
    d = _REPO / ".flywheel"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _state_path() -> Path:
    return _flywheel_dir() / "state.json"


def _ticks_log() -> Path:
    return _flywheel_dir() / "ticks.jsonl"


def _stop_file() -> Path:
    return _flywheel_dir() / "STOP"


def load_state() -> dict[str, Any]:
    p = _state_path()
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:  # noqa: BLE001
            pass
    return {"tick_index": 0, "day": "", "ticks_today": 0}


def save_state(state: dict[str, Any]) -> None:
    _state_path().write_text(json.dumps(state, sort_keys=True))


def next_job(tick_index: int, *, enable_codex: bool) -> dict[str, Any]:
    """The next runnable job round-robin, skipping the codex lane unless enabled."""
    n = len(JOBS)
    for step in range(n):
        job = JOBS[(tick_index + step) % n]
        if job["needs_codex"] and not enable_codex:
            continue
        return job
    return JOBS[tick_index % n]


def _lane_ready(lane: str) -> tuple[bool, str]:
    """Cheap readiness check for a lane so a tick doesn't burn its slot on an unreachable endpoint."""
    if lane in ("deterministic",):
        return True, "local"
    if lane == "codex":
        from shutil import which  # noqa: PLC0415
        return (which("codex") is not None), ("codex CLI present" if which("codex") else "no codex CLI")
    return True, "assumed"  # the harnesses handle provider errors + rate-limit pauses themselves


def _today(now_date: str) -> str:
    return now_date


def should_run(state: dict[str, Any], now_date: str, *, max_ticks_per_day: int) -> tuple[bool, str]:
    if _stop_file().exists():
        return False, "STOP file present"
    ticks = state["ticks_today"] if state.get("day") == now_date else 0
    if ticks >= max_ticks_per_day:
        return False, f"daily cap reached ({ticks}/{max_ticks_per_day})"
    return True, "ok"


def _default_runner(argv: list[str], *, timeout: int) -> dict[str, Any]:
    """Run a harness command from the repo root with PYTHONPATH=. and .env sourced. Bounded by a timeout."""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(_REPO)
    # source .env (best effort) into the child env
    dotenv = _REPO.parent.parent / ".env"
    if dotenv.exists():
        for line in dotenv.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env.setdefault(k.strip(), v.strip())
    cmd = [sys.executable] + argv
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=str(_REPO),  # noqa: S603
                              env=env, check=False)
        return {"rc": proc.returncode, "tail": (proc.stdout + proc.stderr)[-400:]}
    except subprocess.TimeoutExpired:
        return {"rc": 124, "tail": "timeout"}


def _codex_runner(_argv: list[str], *, timeout: int) -> dict[str, Any]:
    """The opt-in codex lane: propose primitive specs to a candidate file (read-mostly; does NOT edit tracked
    code). Bounded + non-destructive."""
    out_file = _flywheel_dir() / "codex_primitive_proposals.jsonl"
    prompt = ("Propose 3 NEW reusable coding primitives (name, tier common|rare|super_rare, a one-line testable "
              f"spec input->output). Append each as one JSON object to {out_file}. Do not edit any other file.")
    try:
        proc = subprocess.run(["codex", "exec", "--skip-git-repo-check", prompt],  # noqa: S603,S607
                              capture_output=True, text=True, timeout=min(timeout, 900), cwd=str(_REPO),
                              check=False)
        return {"rc": proc.returncode, "tail": (proc.stdout + proc.stderr)[-400:]}
    except FileNotFoundError:
        return {"rc": 127, "tail": "codex CLI not found"}
    except subprocess.TimeoutExpired:
        return {"rc": 124, "tail": "timeout"}


def run_tick(*, now_date: str, enable_codex: bool = False, max_ticks_per_day: int = _DEFAULT_MAX_TICKS_PER_DAY,
             runner: Optional[Callable[..., dict[str, Any]]] = None,
             codex_runner: Optional[Callable[..., dict[str, Any]]] = None) -> dict[str, Any]:
    """One flywheel tick. `now_date` is injected (YYYY-MM-DD) so the daily cap is testable without wall-clock."""
    state = load_state()
    ok, reason = should_run(state, now_date, max_ticks_per_day=max_ticks_per_day)
    if not ok:
        receipt = {"outcome": "skipped", "reason": reason, "date": now_date, **BOUNDARY}
        return receipt
    job = next_job(state["tick_index"], enable_codex=enable_codex)
    lane_ok, lane_note = _lane_ready(job["lane"])
    if not lane_ok:
        # advance past an unready lane without burning the daily budget on a guaranteed failure
        state["tick_index"] += 1
        save_state(state)
        return {"outcome": "lane_unready", "job": job["name"], "lane": job["lane"], "note": lane_note,
                "date": now_date, **BOUNDARY}
    run = (codex_runner or _codex_runner) if job["lane"] == "codex" else (runner or _default_runner)
    result = run(job["argv"], timeout=_PER_TICK_TIMEOUT)
    # advance rotation + daily counter
    state["tick_index"] += 1
    state["ticks_today"] = (state["ticks_today"] + 1) if state.get("day") == now_date else 1
    state["day"] = now_date
    save_state(state)
    receipt = {"outcome": "ran", "job": job["name"], "lane": job["lane"],
               "lane_desc": LANES.get(job["lane"], {}).get("desc", job["lane"]),
               "rc": result.get("rc"), "tail": result.get("tail", "")[-200:], "date": now_date,
               "tick_index": state["tick_index"], "ticks_today": state["ticks_today"], **BOUNDARY}
    with _ticks_log().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(receipt, sort_keys=True) + "\n")
    return receipt


def crontab_line(minutes: int = 45) -> str:
    """The crontab entry that runs a tick every `minutes` minutes."""
    py = sys.executable
    return (f"*/{minutes} * * * * cd {_REPO} && {py} scripts/primitive_flywheel_tick.py --run "
            f">> {_flywheel_dir()}/cron.log 2>&1")


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    # use a temp flywheel dir so the real state is untouched
    import tempfile  # noqa: PLC0415
    global _REPO
    orig_repo = _REPO
    with tempfile.TemporaryDirectory() as td:
        _REPO = Path(td)
        calls: list[list[str]] = []

        def _stub(argv: list[str], *, timeout: int) -> dict[str, Any]:
            calls.append(argv)
            return {"rc": 0, "tail": "ok"}

        # rotation: consecutive ticks pick DIFFERENT jobs, cycling
        r1 = run_tick(now_date="2026-07-07", runner=_stub)
        r2 = run_tick(now_date="2026-07-07", runner=_stub)
        r3 = run_tick(now_date="2026-07-07", runner=_stub)
        checks.append(("consecutive ticks rotate across harnesses/lanes",
                       r1["job"] != r2["job"] or r1["lane"] != r2["lane"]))
        checks.append(("ticks run and log a receipt with rc + lane",
                       all(r["outcome"] == "ran" and "lane" in r for r in (r1, r2, r3))))
        checks.append(("codex lane is skipped unless enabled (no codex job ran)",
                       all(r["lane"] != "codex" for r in (r1, r2, r3))))
        # daily cap: after max, ticks become no-ops
        for _ in range(40):
            run_tick(now_date="2026-07-07", runner=_stub, max_ticks_per_day=5)
        capped = run_tick(now_date="2026-07-07", runner=_stub, max_ticks_per_day=5)
        checks.append(("daily cap halts further ticks (skipped, bounded spend)",
                       capped["outcome"] == "skipped" and "cap" in capped["reason"]))
        # new day resets the cap
        fresh = run_tick(now_date="2026-07-08", runner=_stub, max_ticks_per_day=5)
        checks.append(("a new day resets the daily cap", fresh["outcome"] == "ran"))
        # STOP gate
        (_flywheel_dir() / "STOP").write_text("stop")
        stopped = run_tick(now_date="2026-07-08", runner=_stub)
        checks.append(("STOP file halts the tick immediately", stopped["outcome"] == "skipped"
                       and "STOP" in stopped["reason"]))
        (_flywheel_dir() / "STOP").unlink()
        # a mint/deterministic job needs no lane; buildout jobs carry a real model flag
        checks.append(("jobs cover buildout/enrich/mint across GLM/Kimi/Gemma lanes",
                       {j["lane"] for j in JOBS} >= {"ollama_glm", "ollama_kimi", "openwebui_gemma"}
                       and {j["name"] for j in JOBS} >= {"buildout", "enrich", "mint"}))
        # codex enabled -> its job becomes reachable in the rotation
        codex_seen = any(next_job(i, enable_codex=True)["lane"] == "codex" for i in range(len(JOBS)))
        checks.append(("--enable-codex makes the codex lane reachable", codex_seen))
        # crontab line is well-formed
        checks.append(("crontab line targets --run and logs", "--run" in crontab_line() and "cron.log" in crontab_line()))
    _REPO = orig_repo

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - primitive_flywheel_tick: a cron tick rotates bounded primitive-building work across our "
          "lanes (Ollama-GLM/Kimi, OpenWebUI-Gemma-4, opt-in Codex) and harnesses (buildout/enrich/mint); "
          "STOP-gated, daily-capped, receipt-logged, idempotent rotation. serves_truth=false.")
    return 0


def _status() -> int:
    state = load_state()
    recent = []
    if _ticks_log().exists():
        recent = [json.loads(l) for l in _ticks_log().read_text().splitlines()[-5:]]
    print(json.dumps({"state": state, "stop_present": _stop_file().exists(),
                      "lanes": {k: v["desc"] for k, v in LANES.items()},
                      "recent_ticks": [{k: r.get(k) for k in ("job", "lane", "rc", "date")} for r in recent]},
                     indent=2))
    return 0


def _install_cron(minutes: int) -> int:
    line = crontab_line(minutes)
    print("Add this crontab entry (runs a bounded flywheel tick every "
          f"{minutes} min; `touch {_flywheel_dir()}/STOP` to pause):\n")
    print("  " + line + "\n")
    print("Install it with:\n")
    print(f'  ( crontab -l 2>/dev/null; echo "{line}" ) | crontab -')
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true", help="run ONE bounded tick (what cron calls)")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--install-cron", action="store_true")
    ap.add_argument("--enable-codex", action="store_true", help="allow the opt-in codex propose lane")
    ap.add_argument("--max-ticks-per-day", type=int, default=_DEFAULT_MAX_TICKS_PER_DAY)
    ap.add_argument("--minutes", type=int, default=45, help="cron interval for --install-cron")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.status:
        return _status()
    if args.install_cron:
        return _install_cron(args.minutes)
    if args.run:
        import datetime  # noqa: PLC0415 — real wall-clock only in the live --run path
        rec = run_tick(now_date=datetime.date.today().isoformat(), enable_codex=args.enable_codex,
                       max_ticks_per_day=args.max_ticks_per_day)
        print(json.dumps(rec, indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
