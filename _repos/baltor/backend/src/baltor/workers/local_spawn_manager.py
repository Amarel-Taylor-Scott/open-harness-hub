"""src.baltor.workers.local_spawn_manager — turn a supervisor spawn decision into a LOCAL worker subprocess
command. Dry-run by default for self-tests (returns the argv, spawns nothing). Real spawn uses subprocess;
stop by EXACT pid only (no broad/pattern process kills). Maps later to a Kubernetes Job/Deployment/KEDA ScaledObject.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from scripts._repo_paths import resource

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])


def worker_id_for(capability_id: str, seq: str) -> str:
    return "w-" + hashlib.sha256(f"{capability_id}:{seq}".encode()).hexdigest()[:12]


def build_command(*, worker_id: str, capability_id: str, queue: str, db: str,
                  bootstrap_task_id: str = "", provider_id: str = "", keepalive_seconds: int = 120,
                  idle_shutdown_seconds: int = 120, max_concurrency: int = 1) -> list[str]:
    """The argv to start a capability worker. bootstrap_task_id is a HINT only — ownership begins after an
    atomic claim, never from being handed the id."""
    cmd = [sys.executable, str(resource("scripts/capability_worker.py")), "--worker-id", worker_id,
           "--capability-id", capability_id, "--queue", queue, "--db", db,
           "--keepalive-seconds", str(keepalive_seconds), "--idle-shutdown-seconds", str(idle_shutdown_seconds),
           "--max-concurrency", str(max_concurrency)]
    if bootstrap_task_id:
        cmd += ["--bootstrap-task-id", bootstrap_task_id]
    if provider_id:
        cmd += ["--provider-id", provider_id]
    return cmd


def spawn(*, worker_id: str, capability_id: str, queue: str, db: str, dry_run: bool = True, **kw) -> dict:
    cmd = build_command(worker_id=worker_id, capability_id=capability_id, queue=queue, db=db, **kw)
    if dry_run:
        return {"spawned": False, "dry_run": True, "worker_id": worker_id, "command": cmd}
    try:
        p = subprocess.Popen(cmd, cwd=str(_REPO))  # noqa: S603
        return {"spawned": True, "worker_id": worker_id, "pid": p.pid, "command": cmd}
    except Exception as e:  # noqa: BLE001
        return {"spawned": False, "error": f"{type(e).__name__}: {e}", "worker_id": worker_id, "command": cmd}


def stop(pid: int) -> dict:
    """Stop a worker by EXACT pid only (no broad/pattern process kills)."""
    import os
    import signal
    try:
        os.kill(pid, signal.SIGTERM)
        return {"stopped": True, "pid": pid}
    except ProcessLookupError:
        return {"stopped": False, "pid": pid, "reason": "no such pid"}
