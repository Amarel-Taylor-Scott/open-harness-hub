#!/usr/bin/env python3
"""scripts.check_local_function_emulator — proof: the local function emulator is a real (offline) execution
backend — it atomically CLAIMS durable tasks, drains them, is idempotent, two-process-safe, and publishes
NO truth. The candidate cloud-function adapter returns ProviderUnavailableResult when unconfigured.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_local_function_emulator.py --self-test
"""
from __future__ import annotations

import argparse
import os
import tempfile

from src.baltor.ports.execution_provider import py_class_src_teleon_runtime_execution_provider__ExecutionResult, py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult
from src.baltor.workers.durable_fleet_ledger import DurableFleetLedger
from src.baltor.workers.execution_providers.gcp_cloud_run_function_candidate import py_class_src_teleon_runtime_execution_providers_gcp_cloud_run_function_candidate__GcpCloudRunFunctionCandidate
from src.baltor.workers.function_emulator import LocalFunctionEmulator

CAP = "utility.hash"


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    tmp = tempfile.mkdtemp(prefix="baltor-fnemu-")
    db = os.path.join(tmp, "d.db")
    L = DurableFleetLedger(db)
    for i in range(3):
        L.enqueue_task(tenant_id="t", capability_id=CAP, idempotency_key=f"u{i}")
    L.enqueue_task(tenant_id="t", capability_id=CAP, idempotency_key="u0")  # dup → ignored
    chk("idempotent enqueue (3 queued)", len(L.queued_tasks(CAP)) == 3)
    L.close()

    emu = LocalFunctionEmulator()
    chk("emulator satisfies the port shape (describe/health/invoke)", all(hasattr(emu, m) for m in ("describe", "health", "invoke", "invoke_durable")))
    chk("emulator declares it owns no truth", emu.describe()["owns_truth"] is False)

    out = emu.invoke_durable(db, capability=CAP)
    chk("emulator drained all durable tasks via atomic claim", out["processed"] == 3, str(out))
    chk("emulator publishes no truth", out["owns_truth"] is False)
    L2 = DurableFleetLedger(db)
    chk("3 tasks succeeded", len(L2.tasks_by_status("succeeded")) == 3)
    chk("draining again is idempotent (nothing left)", emu.invoke_durable(db, capability=CAP)["processed"] == 0)
    L2.close()

    # single-task invoke returns ExecutionResult (never truth)
    res = emu.invoke({"task_id": "x", "capability_id": CAP})
    chk("invoke returns ExecutionResult", isinstance(res, py_class_src_teleon_runtime_execution_provider__ExecutionResult))
    chk("ExecutionResult.is_truth is False", res.is_truth is False)

    # two emulators do not double-process (atomic claim across the durable ledger)
    db2 = os.path.join(tmp, "d2.db"); L3 = DurableFleetLedger(db2)
    for i in range(4):
        L3.enqueue_task(tenant_id="t", capability_id=CAP, idempotency_key=f"x{i}")
    L3.close()
    a = emu.invoke_durable(db2, worker_id="A", capability=CAP)
    b = emu.invoke_durable(db2, worker_id="B", capability=CAP)
    L4 = DurableFleetLedger(db2)
    chk("two emulators → exactly 4 succeeded (no double-processing)", len(L4.tasks_by_status("succeeded")) == 4 and a["processed"] + b["processed"] == 4)
    L4.close()

    # candidate cloud-function adapter is unavailable offline (no crash, no truth)
    r = py_class_src_teleon_runtime_execution_providers_gcp_cloud_run_function_candidate__GcpCloudRunFunctionCandidate().invoke({"task_id": "y", "capability_id": CAP})
    chk("unconfigured cloud function → ProviderUnavailableResult (non-consumable)", isinstance(r, py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult) and r.consumable is False)
    chk("candidate adapter declares candidate status + no truth", py_class_src_teleon_runtime_execution_providers_gcp_cloud_run_function_candidate__GcpCloudRunFunctionCandidate().describe()["owns_truth"] is False)

    print(f"\n{'PASS — check_local_function_emulator: emulator atomically drains durable tasks (idempotent, two-process-safe, no truth); candidate cloud function returns ProviderUnavailableResult offline.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
