"""src.baltor.workers.execution_providers.local_job_emulator — the local equivalent for Kubernetes Job /
Cloud Run Job / batch execution. Claims a BATCH from the DurableFleetLedger (batch_min thresholds or a
partial batch at max_wait), processes each item via the function emulator with retry/DLQ, records the
batch result, exits. No truth published. `execution.local_cloud_run_job_emulator@v1` is an alias.
"""
from __future__ import annotations

from src.teleon.workers.function_emulator import LocalFunctionEmulator

PROVIDER_ID = "execution.local_job_emulator@v1"
CLOUD_RUN_JOB_ALIAS = "execution.local_cloud_run_job_emulator@v1"


class LocalJobEmulator:
    provider_id = PROVIDER_ID

    def __init__(self, handlers: dict | None = None) -> None:
        self._emu = LocalFunctionEmulator(handlers)

    def describe(self) -> dict:
        return {"provider_id": self.provider_id, "kind": "local_job", "aliases": [CLOUD_RUN_JOB_ALIAS], "owns_truth": False}

    def health(self) -> dict:
        return {"provider_id": self.provider_id, "available": True}

    def invoke_batch(self, db: str, *, capability: str, batch_min: int, worker_id: str = "job",
                     max_items: int = 1000) -> dict:
        """Drain up to batch_min ready tasks (or fewer = a partial batch). Atomic claim per item; no truth."""
        from src.teleon.workers.durable_fleet_ledger import DurableFleetLedger
        L = DurableFleetLedger(db)
        L.register_worker(worker_id=worker_id, capability_ids=[capability])
        L.set_worker_status(worker_id, "warm")
        processed = 0
        limit = min(batch_min, max_items)
        while processed < limit:
            t = L.claim_task(worker_id=worker_id, capability_id=capability)
            if t is None:
                break
            L.start_task(t["task_id"], worker_id)
            res = self._emu.invoke(t)
            L.ack_task(t["task_id"], worker_id, list(res.result_ids))
            processed += 1
        L.set_worker_status(worker_id, "stopped")
        L.close()
        return {"provider_id": self.provider_id, "processed": processed, "batch_min": batch_min,
                "partial": processed < batch_min, "owns_truth": False}


# alias provider (same behavior; a Cloud Run Job is a batch job locally)
class LocalCloudRunJobEmulator(LocalJobEmulator):
    provider_id = CLOUD_RUN_JOB_ALIAS


__all__ = ["LocalJobEmulator", "LocalCloudRunJobEmulator", "PROVIDER_ID", "CLOUD_RUN_JOB_ALIAS"]
