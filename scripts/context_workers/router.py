"""Deterministic worker routing for Baltor context tasks."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from scripts.context_workers.registry import WorkerRegistry, WorkerSpec, registry


IMAGE_AUDIT = "baltor-worker-audit"
IMAGE_GPU = "baltor-worker-gpu"
IMAGE_RESEARCH = "baltor-worker-research"

MODEL_GPU_LANES = {"gpu", "local_gpu", "local_model"}
AUDIT_TASK_TYPES = {"openclaw.adversarial.review", "source.trust.score"}
RESEARCH_TASK_PREFIXES = ("web.", "verify.")


@dataclass(frozen=True)
class RouteDecision:
    worker: str
    lane: str
    image: str
    output_contract: str
    reason_codes: tuple[str, ...]

    def asdict(self) -> dict[str, Any]:
        return {
            "worker": self.worker,
            "lane": self.lane,
            "image": self.image,
            "output_contract": self.output_contract,
            "reason_codes": list(self.reason_codes),
        }


def _task_type(task: dict[str, Any]) -> str:
    return str(task.get("task_type") or task.get("task") or "")


def _queue_policy(task: dict[str, Any]) -> dict[str, Any]:
    policy = task.get("queue_policy")
    return policy if isinstance(policy, dict) else {}


def _priority_signals(task: dict[str, Any]) -> dict[str, Any]:
    signals = task.get("priority_signals")
    if not isinstance(signals, dict):
        payload = task.get("payload")
        signals = payload.get("priority_signals") if isinstance(payload, dict) else {}
    return signals if isinstance(signals, dict) else {}


def _model_policy(task: dict[str, Any]) -> dict[str, Any]:
    policy = task.get("model_policy")
    if not isinstance(policy, dict):
        payload = task.get("payload")
        policy = payload.get("model_policy") if isinstance(payload, dict) else {}
    return policy if isinstance(policy, dict) else {}


def _score(spec: WorkerSpec, task: dict[str, Any]) -> tuple[int, tuple[str, ...]]:
    task_type = _task_type(task)
    policy = _queue_policy(task)
    signals = _priority_signals(task)
    model_policy = _model_policy(task)
    requested_lane = str(task.get("lane") or policy.get("lane") or "")
    requested_image = str(task.get("image") or policy.get("image") or "")
    score = 0
    reasons: list[str] = []

    if task.get("task") == spec.name:
        score += 100
        reasons.append("explicit_worker_match")
    if task_type and task_type in spec.task_types:
        score += 80
        reasons.append("task_type_match")
    if requested_lane and requested_lane == spec.lane:
        score += 20
        reasons.append("lane_match")
    if requested_image and requested_image == spec.image:
        score += 20
        reasons.append("image_match")
    if float(signals.get("injection_risk") or 0.0) >= 0.70 and spec.image == IMAGE_AUDIT:
        score += 55
        reasons.append("high_injection_risk_prefers_audit")
    if task_type in AUDIT_TASK_TYPES and spec.image == IMAGE_AUDIT:
        score += 55
        reasons.append("audit_task_prefers_audit_pool")
    if task_type.startswith(RESEARCH_TASK_PREFIXES) and spec.image == IMAGE_RESEARCH:
        score += 40
        reasons.append("research_task_prefers_research_pool")
    if str(model_policy.get("lane") or "") in MODEL_GPU_LANES and spec.image == IMAGE_GPU:
        score += 40
        reasons.append("model_policy_prefers_gpu")

    return score, tuple(reasons)


def route_task(task: dict[str, Any], worker_registry: WorkerRegistry = registry) -> RouteDecision:
    """Return the best registered worker for a task envelope.

    The router is deterministic and advisory. Queue backends can use the result
    to select a queue key, K8s image, Cloud Run job, Temporal task queue, or
    Argo template without changing worker code.
    """
    candidates = []
    for item in worker_registry.manifest():
        spec = worker_registry.get(str(item["name"]))
        score, reasons = _score(spec, task)
        if score > 0:
            candidates.append((score, spec.name, spec, reasons))
    if not candidates:
        task_type = _task_type(task)
        raise KeyError(f"no registered worker can route task_type={task_type!r}")

    _score_value, _name, spec, reasons = sorted(candidates, key=lambda row: (-row[0], row[1]))[0]
    return RouteDecision(
        worker=spec.name,
        lane=spec.lane,
        image=spec.image,
        output_contract=spec.output_contract,
        reason_codes=reasons,
    )
