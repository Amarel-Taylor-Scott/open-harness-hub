"""src.teleon.workers.execution_providers.local_worker_pool — the local equivalent for a Kubernetes
Deployment / warm worker pool. Runs N local workers that each atomically claim + drain from the
DurableFleetLedger (exactly-once across the pool), with cooldown drain + stale-lease reclaim. No truth.
"""
from __future__ import annotations

from src.teleon.workers.function_emulator import LocalFunctionEmulator

PROVIDER_ID = "execution.local_worker_pool@v1"


class LocalWorkerPool:
    provider_id = PROVIDER_ID

    def __init__(self, handlers: dict | None = None) -> None:
        self._emu = LocalFunctionEmulator(handlers)

    def describe(self) -> dict:
        return {"provider_id": self.provider_id, "kind": "local_worker_pool", "owns_truth": False}

    def health(self) -> dict:
        return {"provider_id": self.provider_id, "available": True}

    def run_pool(self, db: str, *, capability: str, n_workers: int = 2, max_tasks: int = 1000,
                 reclaim_now: str | None = None) -> dict:
        """N workers each drain via atomic claim — split with no double-processing. Optional lease reclaim."""
        from src.teleon.workers.durable_fleet_ledger import DurableFleetLedger
        if reclaim_now:
            L = DurableFleetLedger(db); L.reclaim_expired_leases(reclaim_now); L.close()
        per = []
        for i in range(n_workers):
            wid = f"pool-w{i}"
            out = self._emu.invoke_durable(db, worker_id=wid, capability=capability, max_tasks=max_tasks)
            per.append({"worker_id": wid, "processed": out["processed"]})
        return {"provider_id": self.provider_id, "n_workers": n_workers,
                "total_processed": sum(p["processed"] for p in per), "per_worker": per, "owns_truth": False}


__all__ = ["LocalWorkerPool", "PROVIDER_ID"]
