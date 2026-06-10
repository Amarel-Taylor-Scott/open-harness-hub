#!/usr/bin/env python3
"""scripts.check_live_pipeline — prove the live, connected pipeline end-to-end (offline, no Redis).

Spawns the admin server on an ephemeral port, POSTs /api/demo/run-full-pipeline (which drives the
shipped engines through the unified event bus), GETs /api/events, and asserts the expected ordered
event kinds accumulated — AND that /api/events/stream is a text/event-stream. This is the
"is it actually firing live?" proof, distinct from the unit self-tests.

CLI:
    python3 scripts/check_live_pipeline.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _get(url: str, timeout: float = 5.0):
    return urllib.request.urlopen(url, timeout=timeout)


def _post(url: str, timeout: float = 30.0):
    return urllib.request.urlopen(urllib.request.Request(url, method="POST", data=b""), timeout=timeout)


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    port = _free_port()
    base = f"http://127.0.0.1:{port}"
    env = {**os.environ, "PYTHONPATH": str(_REPO)}  # so the server can import scripts.*
    proc = subprocess.Popen([sys.executable, "scripts/baltor_admin_demo_server.py", "--port", str(port)],
                            cwd=str(_REPO), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        # wait for readiness
        ready = False
        for _ in range(60):
            try:
                if _get(base + "/api/health", timeout=1.0).status == 200:
                    ready = True
                    break
            except Exception:
                time.sleep(0.25)
        if not ready:
            err = (proc.stderr.read() or b"").decode("utf-8", "ignore")[-400:] if proc.stderr else ""
            check("server became ready", False, err)
            return 1
        check("server became ready (/api/health 200)", True)

        # SSE endpoint advertises text/event-stream (read headers, then close without draining)
        try:
            resp = _get(base + "/api/events/stream", timeout=3.0)
            ctype = resp.headers.get("Content-Type", "")
            resp.close()
            check("/api/events/stream is text/event-stream", "text/event-stream" in ctype, ctype)
        except Exception as e:  # noqa: BLE001
            check("/api/events/stream is text/event-stream", False, str(e))

        # run the full pipeline
        r = _post(base + "/api/demo/run-full-pipeline")
        result = json.loads(r.read().decode("utf-8"))
        check("run-full-pipeline returns ok + answer 5", result.get("ok") is True and result.get("answer_value") == 5, str(result)[:160])

        # read the accumulated events
        d = json.loads(_get(base + "/api/events?limit=500").read().decode("utf-8"))
        events = d.get("events", [])
        kinds = [e["kind"] for e in events]
        check("events accumulated on the bus", len(events) >= 10, str(len(events)))
        for need in ("pipeline.started", "context_object.created", "contradiction_found",
                     "context_pack.created", "swarm.started", "swarm.agent.completed", "review.requested",
                     "swarm.consensus.created", "source_handle.expanded", "receipt_issued",
                     # the real governed flow (verified_context_flow) now fires live on the rail:
                     "source.received", "verification.started", "verification.completed",
                     "eval.completed", "context_lift.calculated", "pipeline.completed"):
            check(f"event fired: {need}", need in kinds)
        # the Verification rail reports a positive measured lift (governed pack vs no-context)
        clc = next((e for e in events if e["kind"] == "context_lift.calculated"), None)
        check("context_lift.calculated reports a positive pack-vs-no_context lift",
              clc is not None and (clc.get("payload", {}).get("lift") or 0) > 0,
              str(clc.get("payload") if clc else None))
        # ordering: started before completed; contradiction + receipt between them
        if "pipeline.started" in kinds and "pipeline.completed" in kinds:
            i0, i1 = kinds.index("pipeline.started"), kinds.index("pipeline.completed")
            check("pipeline.started precedes pipeline.completed", i0 < i1)
            check("contradiction_found between start and completion",
                  any(k == "contradiction_found" and i0 < j < i1 for j, k in enumerate(kinds)))
        # event_kinds catalog exposed
        check("/api/events exposes the EVENT_KINDS catalog", isinstance(d.get("event_kinds"), list) and "pipeline.started" in d["event_kinds"])

        # the Context Auditor → Optimizer manifest route serves a well-formed, lossless manifest
        am = json.loads(_get(base + "/api/context/audit").read().decode("utf-8"))
        check("/api/context/audit returns a well-formed lossless manifest",
              isinstance(am.get("issues"), list) and am.get("optimized_tokens", 10 ** 9) < am.get("original_tokens", 0)
              and am.get("lossless") is True and am.get("applied") is False, str(am)[:160])

        # clear works
        _post(base + "/api/events/clear")
        d2 = json.loads(_get(base + "/api/events?limit=50").read().decode("utf-8"))
        check("clear empties the event buffer", d2.get("events") == [])
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()

    print(f"\n{'PASS — check_live_pipeline: the connected pipeline fires the full event sequence live (SSE stream + /api/events), proven against a spawned server, offline/no-Redis.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Prove the live connected pipeline end-to-end (spawns the server).")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
