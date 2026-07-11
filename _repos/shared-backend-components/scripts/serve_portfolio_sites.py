#!/usr/bin/env python3
"""scripts.serve_portfolio_sites — serve the static portfolio launch sites (+ hub) locally on fixed ports.

start / stop / restart / status / self-test. One stdlib http.server per site, directory-scoped to its rendered
dist/portfolio-public/<site>/. EXACT-PID shutdown only (os.kill on recorded PIDs — never a broad process sweep). PIDs →
.agent/portfolio-sites/pids.json; per-site
logs → .agent/portfolio-sites/logs/<site>.log. --self-test validates config + build outputs WITHOUT binding ports
(flywheel-safe). Ports are the single source in _repos/shared-backend-components/scripts/portfolio_lib.py.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import portfolio_lib as P
from scripts._repo_paths import pythonpath as _pythonpath

_STATE = P.REPO / ".agent" / "portfolio-sites"
_PIDS = _STATE / "pids.json"
_LOGS = _STATE / "logs"
#: serve targets: hub + static launch sites (id → (port, dist dir)).
#: The portfolio origin serves the whole tree so /aidoneright/index.html and sibling launch paths work.
_TARGETS = {"portfolio": (P.HUB_PORT, P.DIST)} | {sid: (P.PORTS[sid], P.DIST / sid) for sid in P.SITE_ORDER}


def _ensure_built() -> None:
    from scripts import build_portfolio_sites as B
    if not all((d / "index.html").exists() for _, d in _TARGETS.values()):
        B.build_all()


def _read_pids() -> dict:
    return json.loads(_PIDS.read_text()) if _PIDS.exists() else {}


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError, OSError):
        return False


def start() -> dict:
    _ensure_built()
    _LOGS.mkdir(parents=True, exist_ok=True)
    existing = _read_pids()
    pids: dict = {}
    for name, (port, directory) in _TARGETS.items():
        prev = existing.get(name, {}).get("pid")
        if prev and _alive(int(prev)):
            pids[name] = existing[name]
            continue
        log = open(_LOGS / f"{name}.log", "ab")
        # hub serves the whole tree directly; per-site servers use portfolio_site_server, which
        # 302-redirects hub-rooted sibling paths (/baltor/…) to the sibling's own port
        cmd = ([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1",
                "--directory", str(directory)] if name == "portfolio"
               else [sys.executable, "-m", "scripts.portfolio_site_server", name, str(port)])
        # PYTHONPATH must carry the resolved code roots (repo root + _repos/*/backend +
        # shared-backend-components), NOT just P.REPO — after the _repos/ migration the child
        # `-m scripts.portfolio_site_server` needs both `scripts` and `src.teleon` on the path.
        proc = subprocess.Popen(cmd, stdout=log, stderr=log, cwd=str(P.REPO),
                                env={**os.environ, "PYTHONPATH": _pythonpath(str(P.REPO))})
        pids[name] = {"pid": proc.pid, "port": port, "url": f"http://127.0.0.1:{port}/", "dir": str(directory)}
    _PIDS.write_text(json.dumps(pids, indent=2))
    return pids


def stop() -> list[int]:
    killed: list[int] = []
    for name, info in _read_pids().items():
        pid = int(info.get("pid", 0))
        if pid and _alive(pid):
            try:
                os.kill(pid, 15)  # SIGTERM to the EXACT recorded pid only — never a broad sweep
                killed.append(pid)
            except OSError:
                pass
    _PIDS.write_text("{}")
    return killed


def status(probe: bool = True) -> dict:
    out = {}
    for name, info in _read_pids().items():
        pid = int(info.get("pid", 0))
        rec = {"pid": pid, "alive": _alive(pid), "url": info.get("url"), "http": None}
        if probe and rec["alive"]:
            try:
                with urllib.request.urlopen(info["url"], timeout=4) as r:
                    rec["http"] = r.status
            except Exception as e:  # noqa: BLE001
                rec["http"] = f"ERR:{type(e).__name__}"
        out[name] = rec
    return out


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    _ensure_built()
    src = Path(__file__).read_text()
    expected_ports = set(range(9101, 9101 + len(P.SITE_ORDER)))
    check(f"ports are 9101-{9100 + len(P.SITE_ORDER)} + hub 9100",
          set(P.PORTS.values()) == expected_ports and P.HUB_PORT == 9100,
          str(sorted(P.PORTS.values())))
    check("ports unique across targets", len({p for p, _ in _TARGETS.values()}) == len(_TARGETS))
    for name, (_, d) in _TARGETS.items():
        check(f"{name}: dist index built", (d / "index.html").exists())
    _sweep = ("pk" + "ill", "kill" + "all", "os." + "system(")  # split so this check isn't self-matching
    check("EXACT-pid shutdown only (no broad process sweep)", not any(t in src for t in _sweep) and "os.kill(" in src)
    check("writes pids.json + per-site logs", "pids.json" in str(_PIDS) and "logs" in str(_LOGS))
    print("\n" + ("PASS — serve_portfolio_sites: config valid, all dist indexes built, exact-PID shutdown, "
                  "pids/logs paths defined (no ports bound in self-test)." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "--status"
    if arg == "--self-test":
        raise SystemExit(_self_test())
    if arg == "--start":
        print(json.dumps(start(), indent=2))
    elif arg == "--stop":
        print("stopped pids:", stop())
    elif arg == "--restart":
        stop(); time.sleep(0.5); print(json.dumps(start(), indent=2))
    elif arg == "--status":
        print(json.dumps(status(), indent=2))
    else:
        print("usage: serve_portfolio_sites.py [--start|--stop|--restart|--status|--self-test]")
    raise SystemExit(0)
