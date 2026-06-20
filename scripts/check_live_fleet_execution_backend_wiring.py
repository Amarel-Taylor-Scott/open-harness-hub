#!/usr/bin/env python3
"""scripts.check_live_fleet_execution_backend_wiring — PROOF: the ExecutionBackendSelector is wired into
the LIVE fleet-supervisor dispatch path (CLOUD-DEFER-ONLY-AFTER-LOCAL-EQUIVALENT).

This is NOT "the selector is unit-correct" (check_execution_backend_selector already proves that). It proves
the selector is actually CALLED on the live dispatch path and that the path is governed + local-first:

  A. dispatch_capability over REAL queued durable work → selects a backend, records an idempotent
     ExecutionProviderDecision in the SupervisorStore, and DRAINS the durable ledger via the chosen LOCAL
     executor (tasks end SUCCEEDED). The offline default backend is the local function emulator.
  B. The decision is IDEMPOTENT — re-dispatching the same queued task records no second decision.
  C. CLOUD STAYS DEFERRED, NEVER BLOCKS — even with a cloud credential present, the browser bucket's hard
     guard keeps generic cloud functions off the live path; an unconfigured/unhealthy cloud backend falls
     back to a LOCAL backend so the capability still runs. Capability before cloud.
  D. NO TRUTH — the executor that runs the work returns is_truth=False (an execution backend never emits a
     CanonicalFact); the supervisor decision is governance, not a served fact.
  E. END-TO-END through the REAL supervisor_watch.step(execution_backend=True): claim shards → enqueue work
     → one step drains it via the selector-chosen local executor, records the decision, returns the dispatch
     records, and does NOT also spawn a raw worker (one drainer per queue).

Deterministic + offline: injected `now`, temp DB, no network, no real cloud SDK. Exit 0/1.
"""
from __future__ import annotations

import os
import sys
import tempfile

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from src.baltor.workers import execution_dispatch, supervisor_watch
from src.baltor.workers.durable_fleet_ledger import DurableFleetLedger
from src.baltor.workers.execution_backend_selector import GENERIC_FUNCTIONS
from src.baltor.workers.execution_providers.local_worker_pool import LocalWorkerPool
from src.baltor.workers.fleet_ledger import SUCCEEDED
from src.baltor.workers.function_emulator import LocalFunctionEmulator
from src.baltor.workers.supervisor_store import SupervisorStore

_NOW_ISO = "2026-06-06T00:00:00Z"
_NOW = 1_749_168_000          # fixed epoch (injected; never wall-clock)
_LOCAL_DEFAULT = "local_function_emulator@v1"


def _enqueue(db: str, capability: str, n: int, *, prefix: str) -> None:
    L = DurableFleetLedger(db)
    for i in range(n):
        L.enqueue_task(tenant_id="t", capability_id=capability, idempotency_key=f"{prefix}-{i}", now=_NOW_ISO)
    L.close()


def _count(db: str, status: str, capability: str | None = None) -> int:
    L = DurableFleetLedger(db)
    rows = L.tasks_by_status(status)
    L.close()
    return len([r for r in rows if capability is None or r["capability_id"] == capability])


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "fleet.db")
        store = SupervisorStore(db)

        # ── A. dispatch_capability selects, records a decision, drains via the chosen LOCAL executor ──
        _enqueue(db, "verify", 3, prefix="A")
        a = execution_dispatch.dispatch_capability(store, db, capability="verify",
                                                   bucket="verification_fact_check", now=_NOW, run=True)
        check("A: dispatch saw the 3 queued tasks", a["queued"] == 3, str(a["queued"]))
        check("A: chose the offline LOCAL default backend", a["backend"] == _LOCAL_DEFAULT, str(a["backend"]))
        check("A: drained all 3 via the local executor", a["processed"] == 3, str(a["processed"]))
        check("A: recorded an ExecutionProviderDecision id", bool(a["decision_id"]), str(a))
        decs = store.decisions(decision_type="execution_backend")
        check("A: decision persisted with type=execution_backend", len(decs) == 1, str(len(decs)))
        check("A: queue is now empty (work drained, not just decided)",
              _count(db, SUCCEEDED, "verify") == 3 and DurableFleetLedger(db).queued_tasks("verify") == [],
              f"succeeded={_count(db, SUCCEEDED, 'verify')}")

        # ── B. the decision is IDEMPOTENT (re-dispatch the SAME queued task → no new decision) ──
        _enqueue(db, "ingest", 2, prefix="B")
        b1 = execution_dispatch.dispatch_capability(store, db, capability="ingest", bucket="ingestion_sync",
                                                    now=_NOW, run=False)   # decide only, don't drain
        b2 = execution_dispatch.dispatch_capability(store, db, capability="ingest", bucket="ingestion_sync",
                                                    now=_NOW, run=False)   # same first-task key → dedup
        check("B: same idempotency key → same decision_id (idempotent)",
              b1["decision_id"] == b2["decision_id"] and bool(b1["decision_id"]), f"{b1['decision_id']} vs {b2['decision_id']}")
        check("B: exactly ONE ingest decision recorded",
              len([d for d in store.decisions(decision_type="execution_backend")
                   if "exec:ingest:" in d["idempotency_key"]]) == 1)

        # ── C. CLOUD STAYS DEFERRED, NEVER BLOCKS — even with a cloud cred present ──
        # browser bucket hard-guards generic functions; the cloud cred must NOT win the live path.
        _enqueue(db, "browser", 2, prefix="C")
        c = execution_dispatch.dispatch_capability(
            store, db, capability="browser", bucket="browser",
            available_creds={"aws_lambda@candidate"}, provider_health={"aws_lambda@candidate": True},
            now=_NOW, run=True)
        check("C: a generic cloud function is NEVER chosen on the live path (hard guard holds)",
              c["backend"] not in GENERIC_FUNCTIONS, str(c["backend"]))
        check("C: capability still RAN locally (cloud deferred, not blocked)", c["processed"] == 2, str(c["processed"]))

        # An unconfigured cloud backend (no creds) for a function-eligible bucket also falls back to local.
        _enqueue(db, "utility_cap", 1, prefix="C2")
        c2 = execution_dispatch.dispatch_capability(store, db, capability="utility_cap", bucket="utility",
                                                    now=_NOW, run=True)   # no cloud creds supplied
        check("C2: unconfigured cloud → local fallback, work runs",
              c2["backend"] in (_LOCAL_DEFAULT, "local_subprocess@v1") and c2["processed"] == 1, str(c2))

        # ── D. NO TRUTH — the executor that runs the work never produces a CanonicalFact ──
        res = LocalFunctionEmulator().invoke({"task_id": "x", "capability_id": "verify"})
        check("D: local function executor result is_truth=False", getattr(res, "is_truth", True) is False)
        check("D: worker-pool provider declares owns_truth=False", LocalWorkerPool().describe().get("owns_truth") is False)

        store.close()

        # ── E. END-TO-END via the REAL supervisor_watch.step(execution_backend=True) ──
        db2 = os.path.join(tmp, "fleet2.db")
        store2 = SupervisorStore(db2)
        L2 = DurableFleetLedger(db2)
        store2.register_instance(supervisor_id="S1", now=_NOW)
        # step 1: claim leader + shards (queues empty → nothing dispatched yet)
        r0 = supervisor_watch.step(store2, supervisor_id="S1", max_shards=16, now=_NOW,
                                   fleet_ledger=L2, db=db2, execution_backend=True)
        check("E: supervisor owns the 'verify' shard", "verify" in r0["owned_shards"], str(r0["owned_shards"]))
        check("E: nothing dispatched on an empty queue", r0["execution_dispatched"] == [], str(r0["execution_dispatched"]))
        # enqueue real work, then ONE step must drain it through the selector-chosen local executor
        for i in range(4):
            L2.enqueue_task(tenant_id="t", capability_id="verify", idempotency_key=f"E-{i}", now=_NOW_ISO)
        r1 = supervisor_watch.step(store2, supervisor_id="S1", max_shards=16, now=_NOW + 1,
                                   fleet_ledger=L2, db=db2, execution_backend=True)
        verify_disp = [d for d in r1["execution_dispatched"] if d["capability"] == "verify"]
        check("E: the live step dispatched the 'verify' shard via the selector", len(verify_disp) == 1, str(r1["execution_dispatched"]))
        check("E: it chose the local backend + drained all 4",
              bool(verify_disp) and verify_disp[0]["backend"] == _LOCAL_DEFAULT and verify_disp[0]["processed"] == 4,
              str(verify_disp))
        check("E: an execution_backend decision was recorded by the live step",
              len(store2.decisions(decision_type="execution_backend")) >= 1)
        check("E: 4 tasks ended SUCCEEDED via the live path", _count(db2, SUCCEEDED, "verify") == 4,
              str(_count(db2, SUCCEEDED, "verify")))
        # one drainer per queue: execution_backend mode must NOT also spawn a raw worker subprocess
        check("E: no raw worker spawn issued in execution_backend mode (one drainer per queue)",
              store2.spawn_requests() == [], str(len(store2.spawn_requests())))
        L2.close()
        store2.close()

    print("\n" + ("PASS — check_live_fleet_execution_backend_wiring: the ExecutionBackendSelector is on the LIVE "
                  "fleet-supervisor dispatch path — governed (idempotent ExecutionProviderDecision), local-first "
                  "(offline default = function emulator), cloud-deferred-never-blocking, no-truth, and drains real "
                  "durable work through supervisor_watch.step(execution_backend=True)."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_live_fleet_execution_backend_wiring.py --self-test")
    raise SystemExit(0)
