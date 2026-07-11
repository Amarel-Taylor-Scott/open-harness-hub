#!/usr/bin/env python3
"""scripts.check_durable_restart_survival — INTEGRATED proof that durability survives a real restart.

Not a module self-test: this spawns the actual admin server with BALTOR_DURABLE_DB set, drives real
events through an HTTP endpoint, KILLS the server, restarts it on the SAME durable db, and asserts the
events hydrate back — with the expected correlation_id/kind, and seq monotonicity continuing past the
restored max. This is the acceptance test for "events lost on restart" — it fails loudly if durability
regresses.

CLI:
    python3 _repos/shared-backend-components/scripts/check_durable_restart_survival.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import pythonpath as _pythonpath  # noqa: E402
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def _get(url: str, timeout: float = 5.0):
    return urllib.request.urlopen(url, timeout=timeout)


def _post(url: str, timeout: float = 40.0):
    return urllib.request.urlopen(urllib.request.Request(url, method="POST", data=b""), timeout=timeout)


def _spawn(port: int, db: str):
    env = {**os.environ, "PYTHONPATH": _pythonpath("."), "BALTOR_DURABLE_DB": db}
    env.pop("OH_SHOWCASE_TOKEN", None)  # leave POSTs open so the proof needs no token
    return subprocess.Popen([sys.executable, str(_resource("scripts/baltor_admin_demo_server.py")), "--port", str(port)],
                            cwd=str(_REPO), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def _wait_ready(base: str, proc) -> bool:
    for _ in range(80):
        try:
            if _get(base + "/api/health", timeout=1.0).status == 200:
                return True
        except Exception:
            if proc.poll() is not None:
                return False
            time.sleep(0.25)
    return False


def _events(base: str) -> list[dict]:
    return json.loads(_get(base + "/api/events?limit=500").read().decode("utf-8")).get("events", [])


def _stop(proc) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=8)
    except Exception:
        proc.kill()


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    tmp = tempfile.mkdtemp(prefix="baltor-restart-")
    db = os.path.join(tmp, "durable.db")
    port = _free_port()
    base = f"http://127.0.0.1:{port}"

    proc = _spawn(port, db)
    try:
        if not _wait_ready(base, proc):
            err = (proc.stderr.read() or b"").decode("utf-8", "ignore")[-500:] if proc.stderr else ""
            check("server #1 became ready", False, err)
            return 1
        # drive real events through a real endpoint
        res = json.loads(_post(base + "/api/demo/run-full-pipeline").read().decode("utf-8"))
        check("pipeline ran (answer 5)", res.get("ok") and res.get("answer_value") == 5, str(res)[:140])
        before = _events(base)
        n1 = len(before)
        kinds1 = {e["kind"] for e in before}
        max_seq1 = max((e.get("seq") or 0) for e in before) if before else 0
        check("BEFORE restart: events present (>0)", n1 > 0, str(n1))
        check("BEFORE restart: expected kind + correlation present",
              "pipeline.completed" in kinds1 and any(e.get("correlation_id") == "pipeline-acme" for e in before))
    finally:
        _stop(proc)
    print(f"   · killed server #1 (events before restart: {n1})")

    # RESTART on the SAME durable db (a fresh process)
    proc2 = _spawn(port, db)
    try:
        if not _wait_ready(base, proc2):
            err = (proc2.stderr.read() or b"").decode("utf-8", "ignore")[-500:] if proc2.stderr else ""
            check("server #2 became ready", False, err)
            return 1
        after = _events(base)
        n2 = len(after)
        kinds2 = {e["kind"] for e in after}
        max_seq2 = max((e.get("seq") or 0) for e in after) if after else 0
        print(f"   · restarted server #2 (events after restart: {n2})")
        check("AFTER restart: events SURVIVED (>0)", n2 > 0, str(n2))
        check("AFTER restart: count >= before (hydrated)", n2 >= n1, f"{n2} < {n1}")
        check("AFTER restart: expected kind + correlation still present",
              "pipeline.completed" in kinds2 and any(e.get("correlation_id") == "pipeline-acme" for e in after))
        check("AFTER restart: restored max seq matches", max_seq2 == max_seq1, f"{max_seq2} vs {max_seq1}")
        # seq monotonicity continues: a NEW event after restore must exceed the restored max
        _post(base + "/api/demo/run-full-pipeline")
        after2 = _events(base)
        max_seq3 = max((e.get("seq") or 0) for e in after2)
        check("seq monotonic AFTER restore (new seq > restored max)", max_seq3 > max_seq2, f"{max_seq3} <= {max_seq2}")
    finally:
        _stop(proc2)

    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'PASS — check_durable_restart_survival: real server lost+regained nothing across a kill+restart (events hydrate from the durable log; seq stays monotonic).' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Integrated proof: durable events survive a real server restart.")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
