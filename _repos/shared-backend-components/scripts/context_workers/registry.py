"""Small stateless worker registry for Context Fidelity jobs.

The registry is deliberately framework-neutral. A task is a JSON-compatible
payload, a worker is a pure function, and the queue backend can be the existing
SQLite/Redis adapter, Celery, RQ, SQS, Cloud Tasks, or K8/KEDA later.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


TaskHandler = Callable[["TaskContext", dict[str, Any]], "TaskResult"]


@dataclass(frozen=True)
class TaskContext:
    run_id: str
    job_id: str = ""
    tenant_id: str = "local"
    pass_index: int = 1
    parent_job_id: str | None = None


@dataclass
class TaskResult:
    ok: bool
    output: dict[str, Any] = field(default_factory=dict)
    enqueue: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    error: str = ""

    @classmethod
    def success(
        cls,
        output: dict[str, Any] | None = None,
        *,
        enqueue: list[dict[str, Any]] | None = None,
        warnings: list[str] | None = None,
    ) -> "TaskResult":
        return cls(True, output or {}, enqueue or [], warnings or [])

    @classmethod
    def failure(cls, error: str, *, output: dict[str, Any] | None = None) -> "TaskResult":
        return cls(False, output or {}, [], [], error)


@dataclass(frozen=True)
class WorkerSpec:
    name: str
    lane: str
    handler: TaskHandler
    description: str
    emits: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    task_types: tuple[str, ...] = ()
    image: str = "baltor-worker-cpu"
    output_contract: str = "task_result"
    max_retries: int = 2
    idempotent: bool = True


class WorkerRegistry:
    def __init__(self) -> None:
        self._workers: dict[str, WorkerSpec] = {}

    def register(
        self,
        name: str,
        *,
        lane: str,
        description: str,
        emits: tuple[str, ...] = (),
        capabilities: tuple[str, ...] = (),
        task_types: tuple[str, ...] = (),
        image: str = "baltor-worker-cpu",
        output_contract: str = "task_result",
        max_retries: int = 2,
        idempotent: bool = True,
    ) -> Callable[[TaskHandler], TaskHandler]:
        def deco(fn: TaskHandler) -> TaskHandler:
            if name in self._workers:
                raise ValueError(f"duplicate worker registered: {name}")
            self._workers[name] = WorkerSpec(
                name=name,
                lane=lane,
                handler=fn,
                description=description,
                emits=emits,
                capabilities=capabilities,
                task_types=task_types,
                image=image,
                output_contract=output_contract,
                max_retries=max_retries,
                idempotent=idempotent,
            )
            return fn

        return deco

    def get(self, name: str) -> WorkerSpec:
        try:
            return self._workers[name]
        except KeyError as exc:
            raise KeyError(f"unknown context worker: {name}") from exc

    def run(self, task: dict[str, Any]) -> TaskResult:
        name = str(task.get("task") or task.get("kind") or "")
        spec = self.get(name)
        ctx = TaskContext(
            job_id=str(task.get("job_id") or ""),
            run_id=str(task.get("run_id") or "local"),
            tenant_id=str(task.get("tenant_id") or "local"),
            pass_index=int(task.get("pass_index") or 1),
            parent_job_id=task.get("parent_job_id"),
        )
        payload = task.get("payload") if isinstance(task.get("payload"), dict) else {}
        return spec.handler(ctx, payload)

    def manifest(self) -> list[dict[str, Any]]:
        return [
            {
                "name": spec.name,
                "lane": spec.lane,
                "description": spec.description,
                "version": "0.1.0",
                "emits": list(spec.emits),
                "capabilities": list(spec.capabilities),
                "task_types": list(spec.task_types),
                "image": spec.image,
                "output_contract": spec.output_contract,
                "runtime": {
                    "execution_backends": ["local", "k8s_deployment", "temporal_activity", "celery_task"],
                    "always_on": spec.lane == "orchestrate",
                    "gpu_required": spec.image == "baltor-worker-gpu",
                    "browser_required": spec.image in {"baltor-worker-browser", "baltor-worker-research"},
                    "network_required": spec.image in {"baltor-worker-browser", "baltor-worker-research", "baltor-worker-archive"},
                    "scale_to_zero": spec.lane != "orchestrate",
                },
                "lifecycle": {
                    "preflight": True,
                    "load": True,
                    "execute": True,
                    "write_artifacts": True,
                    "emit_followups": True,
                    "shutdown": True,
                },
                "retry_policy": {
                    "max_retries": spec.max_retries,
                    "backoff": "exponential",
                    "terminal_state": "failed_permanently",
                    "approval_hold_state": "approval_required",
                    "budget_hold_state": "budget_blocked",
                    "idempotent": spec.idempotent,
                },
                "cost_policy": {
                    "emits_cost_estimate": True,
                    "default_budget_action": "batch" if spec.image in {"baltor-worker-research", "baltor-worker-browser", "baltor-worker-gpu"} else "allow",
                    "requires_budget_ceiling": spec.image in {"baltor-worker-research", "baltor-worker-browser", "baltor-worker-gpu", "baltor-worker-audit"},
                    "expensive_lane": spec.image in {"baltor-worker-research", "baltor-worker-browser", "baltor-worker-gpu", "baltor-worker-audit"},
                    "metered_resources": (
                        ["worker_seconds"]
                        + (["browser_seconds", "search_calls"] if spec.image in {"baltor-worker-research", "baltor-worker-browser"} else [])
                        + (["gpu_seconds"] if spec.image == "baltor-worker-gpu" else [])
                    ),
                },
                "safety_policy": {
                    "privacy_scope": "tenant",
                    "allowed_domains_required": spec.image in {"baltor-worker-browser", "baltor-worker-research"},
                    "source_text_is_untrusted": spec.lane in {"ingest", "normalize", "analyze", "verify", "refresh", "research"},
                    "requires_source_hash": spec.lane in {"ingest", "normalize", "verify", "refresh", "research", "archive"},
                    "requires_evidence_packet": spec.lane in {"verify", "refresh", "research", "archive", "promote"},
                    "requires_archive_capture": spec.lane in {"archive", "promote"},
                    "can_adopt_facts": spec.lane == "promote",
                    "requires_two_sources": spec.lane in {"verify", "refresh", "research", "promote"},
                },
                "max_retries": spec.max_retries,
                "idempotent": spec.idempotent,
            }
            for spec in sorted(self._workers.values(), key=lambda s: (s.lane, s.name))
        ]


registry = WorkerRegistry()
