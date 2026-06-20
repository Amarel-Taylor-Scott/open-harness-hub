#!/usr/bin/env python3
"""scripts.check_live_supervisor_api — proof (OPP-supervisor-scaling-live, API): the /api/fleet/* routes
serve a READ-ONLY projection of live supervisor state. Seeds a temp durable DB with one coordination step,
spawns the REAL admin server against it, and asserts the endpoints return the contract. Also asserts the
projection module performs no writes (projection-only).

CLI: PYTHONPATH=. python3 scripts/check_live_supervisor_api.py --self-test
"""
from __future__ import annotations

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

_REPO = Path(__file__).resolve().parents[1]


def _free_port() -> int:
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def _get(url, timeout=5.0):
    return urllib.request.urlopen(url, timeout=timeout)


def _self_test() -> int:
    from src.baltor.workers.supervisor_store import SupervisorStore
    from src.baltor.workers import supervisor_watch
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    tmp = tempfile.mkdtemp(prefix="baltor-sup-api-")
    db = os.path.join(tmp, "durable.db")
    # seed with a REAL timestamp + long TTL so the lease is still valid when the server's projection reads
    # it with wall-clock (the live path uses real time across processes).
    t0 = int(time.time())
    s = SupervisorStore(db)
    s.register_instance(supervisor_id="api-A", pid=1, now=t0)
    supervisor_watch.step(s, supervisor_id="api-A", leader_ttl=3600, shard_ttl=3600, max_shards=14, now=t0)
    s.close()

    port = _free_port()
    base = f"http://127.0.0.1:{port}"
    env = {**os.environ, "PYTHONPATH": str(_REPO), "BALTOR_DURABLE_DB": db}
    proc = subprocess.Popen([sys.executable, "scripts/baltor_admin_demo_server.py", "--port", str(port)],
                            cwd=str(_REPO), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        ready = False
        for _ in range(80):
            try:
                if _get(base + "/api/health", timeout=1.0).status == 200:
                    ready = True; break
            except Exception:
                if proc.poll() is not None:
                    break
                time.sleep(0.25)
        chk("admin server came up", ready)
        if ready:
            full = json.loads(_get(base + "/api/fleet").read().decode())
            chk("/api/fleet ok", full.get("ok") is True)
            for k in ("leader", "supervisors", "shards", "ticks", "decisions", "capacity", "failovers", "tasks", "spawn_requests", "contract"):
                chk(f"/api/fleet has section '{k}'", k in full)
            chk("/api/fleet tasks projection has by_status (durable queue)", isinstance(full.get("tasks", {}).get("by_status"), dict))
            chk("/api/fleet leader is api-A", full.get("leader") == "api-A", str(full.get("leader")))
            chk("/api/fleet projection declares read-only", full.get("contract", {}).get("projection") == "read-only")
            leader = json.loads(_get(base + "/api/fleet/leader").read().decode())
            chk("/api/fleet/leader section ok", leader.get("ok") and leader.get("section") == "leader")
            shards = json.loads(_get(base + "/api/fleet/shards").read().decode())
            chk("/api/fleet/shards returns shards", shards.get("ok") and len(shards.get("shards", [])) >= 14)
            detail = json.loads(_get(base + "/api/fleet/supervisors/api-A").read().decode())
            chk("/api/fleet/supervisors/<id> returns the instance", detail.get("ok") and detail.get("supervisor", {}).get("supervisor_id") == "api-A")
            page = _get(base + "/fleet").read().decode()
            chk("/fleet page served", "Live Supervisor Fleet" in page)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except Exception:
            proc.kill()

    # projection-only: the projection module performs NO writes
    proj_src = (_REPO / "src/baltor/workers/supervisor_projection.py").read_text()
    writes = [t for t in ("INSERT", "UPDATE", "DELETE", ".record_", ".try_claim", ".claim_shard", ".renew_") if t in proj_src]
    chk("projection module performs no writes (read-only)", writes == [], str(writes))

    print(f"\n{'PASS — check_live_supervisor_api: /api/fleet/* + /fleet served by the real admin server (read-only projection of seeded supervisor state); projection module writes nothing.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
