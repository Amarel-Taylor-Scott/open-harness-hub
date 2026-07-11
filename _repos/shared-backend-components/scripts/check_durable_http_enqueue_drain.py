#!/usr/bin/env python3
"""scripts.check_durable_http_enqueue_drain — INTEGRATED proof of the durable work route.

Spawns the real admin server with BALTOR_DURABLE_DB, enqueues a durable command over HTTP
(`/api/dev/enqueue`), proves idempotent enqueue (same key ⇒ duplicate, no second job), drains it
(`/api/dev/drain` claims → emits a work-plane event → acks), and asserts the queue reaches done with a
durable work-plane event persisted. Proves push (enqueue) + pull (drain/claim) over a DURABLE queue —
the seam the in-proc bus lacked.

CLI:
    python3 _repos/shared-backend-components/scripts/check_durable_http_enqueue_drain.py --self-test
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


def _post_json(url: str, body: dict, timeout: float = 15.0) -> dict:
    req = urllib.request.Request(url, method="POST", data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8"))


def _get(url: str):
    return json.loads(urllib.request.urlopen(url, timeout=5.0).read().decode("utf-8"))


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    tmp = tempfile.mkdtemp(prefix="baltor-enqueue-")
    db = os.path.join(tmp, "durable.db")
    port = _free_port()
    base = f"http://127.0.0.1:{port}"
    env = {**os.environ, "PYTHONPATH": _pythonpath("."), "BALTOR_DURABLE_DB": db}
    env.pop("OH_SHOWCASE_TOKEN", None)
    proc = subprocess.Popen([sys.executable, str(_resource("scripts/baltor_admin_demo_server.py")), "--port", str(port)],
                            cwd=str(_REPO), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        ready = False
        for _ in range(80):
            try:
                if urllib.request.urlopen(base + "/api/health", timeout=1.0).status == 200:
                    ready = True
                    break
            except Exception:
                if proc.poll() is not None:
                    break
                time.sleep(0.25)
        if not ready:
            err = (proc.stderr.read() or b"").decode("utf-8", "ignore")[-500:] if proc.stderr else ""
            check("server became ready (durable)", False, err)
            return 1

        q = "flywheel.commands.proof_runner"
        cmd = {"queue": q, "command_type": "run_proof", "priority": "p0",
               "correlation_id": "tick-1", "idempotency_key": "tick-1:validate_stages:v1",
               "payload": {"proof": "validate_stages"}}
        r1 = _post_json(base + "/api/dev/enqueue", cmd)
        check("enqueue accepted (returns job_id, not duplicate)", r1.get("ok") and r1.get("job_id") and not r1.get("duplicate"), str(r1))
        r2 = _post_json(base + "/api/dev/enqueue", cmd)
        check("idempotent enqueue: same key ⇒ duplicate (no new job)", r2.get("duplicate") is True and r2.get("job_id") == r1.get("job_id"), str(r2))

        d = _post_json(base + "/api/dev/drain", {"queue": q, "max": 10})
        check("drain processed exactly one job", len(d.get("processed", [])) == 1, str(d.get("processed")))
        check("queue reaches done=1, queued=0", d["stats"].get("done") == 1 and d["stats"].get("queued") == 0, str(d.get("stats")))
        d2 = _post_json(base + "/api/dev/drain", {"queue": q, "max": 10})
        check("second drain is empty (acked job not reprocessed)", d2.get("processed") == [])

        # a durable work-plane event was emitted by the drain (push from a pulled job)
        evs = _get(base + "/api/events?limit=500").get("events", [])
        check("drain emitted a durable Work-plane component.finished event",
              any(e["kind"] == "component.finished" and e.get("component") == "durable_worker" for e in evs))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except Exception:
            proc.kill()

    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'PASS — check_durable_http_enqueue_drain: HTTP enqueue → durable queue → idempotent dedupe → drain(claim→work-event→ack) → not reprocessed. Durable push+pull proven.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Integrated proof: durable HTTP enqueue + drain + idempotency.")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
