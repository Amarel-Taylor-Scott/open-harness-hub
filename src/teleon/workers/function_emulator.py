"""src.teleon.workers.function_emulator — the LOCAL FUNCTION EMULATOR execution backend (offline reference
path). It is contract-identical to a cloud function: given a capability, it atomically CLAIMS tasks from the
DurableFleetLedger, runs a registered lightweight handler, writes the result, and ack/nacks — idempotent,
retry/DLQ-preserving. It publishes NO truth. This is what proves the execution-backend abstraction offline
without any cloud credentials; cloud-function adapters are candidates behind the same contract.
"""
from __future__ import annotations

from src.teleon.runtime.execution_provider import ExecutionResult, ProviderUnavailableResult


def _echo_handler(task: dict) -> list:
    """Default deterministic handler: 'process' a task into a result id (no truth, no side effects)."""
    return [f"fn-art:{task['task_id']}"]


class LocalFunctionEmulator:
    provider_id = "local_function_emulator@v1"

    def __init__(self, handlers: dict | None = None) -> None:
        self.handlers = handlers or {}   # capability_id -> callable(task)->list[result_id]

    def describe(self) -> dict:
        return {"provider_id": self.provider_id, "kind": "local_function_emulator", "offline": True,
                "owns_truth": False, "contract": "CapabilityTask"}

    def health(self) -> dict:
        return {"provider_id": self.provider_id, "available": True, "reason": "offline emulator always available"}

    def invoke(self, task: dict):
        """Run ONE pre-claimed task (handler dispatch). Returns ExecutionResult (never truth)."""
        handler = self.handlers.get(task["capability_id"], _echo_handler)
        ids = handler(task)
        return ExecutionResult(provider_id=self.provider_id, execution_id="exec-" + task["task_id"],
                               task_id=task["task_id"], status="succeeded", result_ids=tuple(ids), is_truth=False)

    def invoke_durable(self, db: str, *, worker_id: str = "fn-emu", capability: str, max_tasks: int = 1000) -> dict:
        """Drain `capability` tasks from the durable ledger via ATOMIC CLAIM → handler → ack. Idempotent,
        bounded, no truth published. This is the function-as-worker correctness invariant."""
        from src.teleon.workers.durable_fleet_ledger import DurableFleetLedger
        L = DurableFleetLedger(db)
        L.register_worker(worker_id=worker_id, capability_ids=[capability])
        L.set_worker_status(worker_id, "warm")
        processed = 0
        while processed < max_tasks:
            t = L.claim_task(worker_id=worker_id, capability_id=capability)
            if t is None:
                break
            L.start_task(t["task_id"], worker_id)
            res = self.invoke(t)
            L.ack_task(t["task_id"], worker_id, list(res.result_ids))
            processed += 1
        L.set_worker_status(worker_id, "stopped")
        L.close()
        return {"provider_id": self.provider_id, "processed": processed, "status": "stopped", "owns_truth": False}


__all__ = ["LocalFunctionEmulator"]
