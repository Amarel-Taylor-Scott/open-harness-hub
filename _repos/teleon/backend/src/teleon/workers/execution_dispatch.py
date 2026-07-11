"""src.teleon.workers.execution_dispatch — wire the ExecutionBackendSelector into the LIVE dispatch path.

For a capability with queued durable work, this: (1) calls select_backend (policy + pricebook + health +
creds), (2) records an idempotent ExecutionProviderDecision in the SupervisorStore, (3) routes to the
chosen LOCAL executor — function emulator / job emulator / worker pool — which drains the durable ledger
via atomic claim. A cloud backend that is unavailable has already fallen back to a LOCAL backend in the
selector, so dispatch never blocks on missing credentials. No truth published; the executor still claims
atomically. The selector is no longer standalone — the supervisor calls this.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import time
from functools import lru_cache
from pathlib import Path

from src.teleon.runtime import execution_backend_selector as _sel

_MATRIX = _resource("architecture") / "execution_backend_policy_matrix.json"

#: local executor TYPE (the policy matrix's execution.local_* equivalents) → how it DRAINS the durable
#: ledger. SINGLE SOURCE: a chosen backend's drain executor is DERIVED from execution_backend_policy_matrix
#: (candidate_local_equivalents) below — NOT a hardcoded backend set — so a new backend in the matrix routes
#: correctly with zero code change, and a backend with NO declared local-drain executor FAILS LOUD (an
#: explicit unroutable_backend) instead of silently running on the function emulator.
_EXECUTOR_DRAIN = {
    "local_function_emulator": "function", "local_subprocess": "function", "managed_venv": "function",
    "local_job_emulator": "job", "local_cloud_run_job_emulator": "job",
    "local_worker_pool": "pool",
}


@lru_cache(maxsize=1)
def _candidate_local_equivalents() -> dict:
    return json.loads(_MATRIX.read_text(encoding="utf-8")).get("candidate_local_equivalents", {})


def _executor_for_backend(backend: str) -> str | None:
    """The drain executor ('function'/'job'/'pool') for a chosen backend, derived from the policy matrix: a
    @candidate backend maps via candidate_local_equivalents to its execution.local_* equivalent; a local
    backend names its executor directly. Returns None for a backend with no declared durable-drain executor
    (e.g. container_image_emulator) → the caller fails loud instead of silently using the function emulator."""
    equiv = _candidate_local_equivalents().get(backend, backend)  # @candidate → local equivalent; local → self
    return _EXECUTOR_DRAIN.get(equiv.split("@")[0].replace("execution.", ""))

# Map a supervisor SHARD id (a capability lane) → a policy-matrix worker_bucket, so select_backend
# exercises the REAL per-bucket policy on the live path (e.g. the `browser` shard hits the `browser`
# bucket, whose hard guard excludes generic cloud functions) instead of always hitting the fallback.
# Shard ids come from SupervisorStore.DEFAULT_SHARDS; anything unmapped is a short deterministic `utility`.
SHARD_BUCKET = {
    "ingest": "ingestion_sync", "browser": "browser", "verify": "verification_fact_check",
    "reconcile": "reconciliation_policy", "memory": "memory_context",
    "control": "control_plane", "proof_health": "control_plane", "worker_health": "control_plane",
    "fleet_capacity": "control_plane", "watch_policies": "control_plane", "monitoring": "control_plane",
    "optimize": "utility", "contextops": "utility", "native_export": "utility",
    "temporal_graph": "utility", "standards": "utility",
}


def _now_epoch(now) -> int:
    return int(now) if now is not None else int(time.time())


def _route_and_drain(backend: str, db: str, capability: str) -> dict:
    """Drain the durable queue for `capability` via the local executor the POLICY MATRIX maps `backend` to.
    A backend with no declared local-drain executor returns an explicit unroutable_backend (fail loud) —
    never silently the function emulator."""
    kind = _executor_for_backend(backend)
    if kind == "job":
        from .execution_providers.local_job_emulator import LocalJobEmulator
        out = LocalJobEmulator().invoke_batch(db, capability=capability, batch_min=1000)
        return {"executor": "local_job_emulator", "processed": out["processed"]}
    if kind == "pool":
        from .execution_providers.local_worker_pool import LocalWorkerPool
        out = LocalWorkerPool().run_pool(db, capability=capability, n_workers=2)
        return {"executor": "local_worker_pool", "processed": out["total_processed"]}
    if kind == "function":
        from .function_emulator import LocalFunctionEmulator
        out = LocalFunctionEmulator().invoke_durable(db, capability=capability)
        return {"executor": "local_function_emulator", "processed": out["processed"]}
    # FAIL LOUD: no declared local-drain executor for this backend → explicit unroutable decision.
    return {"executor": "unroutable_backend", "processed": 0, "unroutable_backend": backend}


def dispatch_capability(store, db: str, *, capability: str, bucket: str = "utility", now=None,
                        available_creds: set | None = None, provider_health: dict | None = None,
                        policy_override: dict | None = None, run: bool = True) -> dict:
    """Select the execution backend for `capability`'s queued durable work, record the decision, and (if
    `run`) drain via the chosen LOCAL executor. Returns {capability, queued, backend, action, executor,
    processed, decision_id}."""
    from .durable_fleet_ledger import DurableFleetLedger
    L = DurableFleetLedger(db)
    queued = L.queued_tasks(capability)
    L.close()
    if not queued:
        return {"capability": capability, "queued": 0, "backend": None, "processed": 0}

    task = {"capability_id": capability, "worker_bucket": bucket, "estimated_runtime_ms": 300}
    decision = _sel.py_function_src_teleon_runtime_execution_backend_selector__select_backend(task, available_creds=available_creds, provider_health=provider_health,
                                   policy_override=policy_override)
    backend = decision["backend"]
    decision_id = ""
    if store is not None:
        d = store.record_decision(supervisor_id="exec-dispatch", decision_type="execution_backend",
                                  idempotency_key=f"exec:{capability}:{backend}:{queued[0]['task_id']}",
                                  reason=f"{decision['action']} → {backend}: {decision['reason']}",
                                  now=_now_epoch(now))
        decision_id = d["decision_id"]
    routed = {"executor": None, "processed": 0}
    if run:
        routed = _route_and_drain(backend, db, capability)
    return {"capability": capability, "queued": len(queued), "backend": backend, "action": decision["action"],
            "executor": routed["executor"], "processed": routed["processed"], "decision_id": decision_id}


def dispatch_owned_shards(store, db: str, *, owned: list[str], now=None, run: bool = True,
                          available_creds: set | None = None, provider_health: dict | None = None) -> list[dict]:
    """Live-path entry: dispatch every owned capability shard that has queued durable work."""
    out = []
    for cap in owned:
        d = dispatch_capability(store, db, capability=cap, bucket=SHARD_BUCKET.get(cap, "utility"),
                                now=now, run=run, available_creds=available_creds, provider_health=provider_health)
        if d.get("queued"):
            out.append(d)
    return out


__all__ = ["dispatch_capability", "dispatch_owned_shards", "SHARD_BUCKET"]
