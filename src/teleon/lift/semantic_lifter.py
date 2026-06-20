"""src.teleon.lift.semantic_lifter — infer a PurposeTaskDraft + CapabilityTaskDraft from an ImportedWorkload.

The lifter uses many weak signals (name, tags, triggers, repo, runtime class, telemetry) to draft a purpose and
a confidence. CRITICAL: inferred purpose is NEVER authoritative — `requires_human_review` is ALWAYS true; a human
must confirm purpose + boundaries before Teleon may manage the workload. Pure + deterministic.
"""
from __future__ import annotations

import re
from typing import Any

from . import model

_PURPOSE_DRAFT_SCHEMA = "PurposeTaskDraft.v1"
_CAP_DRAFT_SCHEMA = "CapabilityTaskDraft.v1"
_GENERIC_TOKENS = {"prod", "dev", "staging", "test", "function", "job", "app", "svc", "service", "worker",
                   "cron", "lambda", "fn", "handler", "v1", "v2"}

#: confidence weights per agreeing signal (sum ≤ 1.0)
_SIGNAL_WEIGHTS = {"name_informative": 0.30, "service_tag": 0.20, "trigger_known": 0.20, "repo_hint": 0.15,
                   "runtime_class_known": 0.15}

#: sensible runtime-class alternatives to offer a class (all within the capability_runtime_classes vocabulary).
_RUNTIME_ALTERNATIVES = {
    "cloud-function": ["cloud-function", "kubernetes-job", "queue-worker"],
    "kubernetes-job": ["kubernetes-job", "cloud-run-job", "batch-job"],
    "cron-task": ["cron-task", "kubernetes-job"],
    "kubernetes-worker": ["kubernetes-worker", "queue-worker", "serverless-container"],
    "queue-worker": ["queue-worker", "kubernetes-worker"],
    "durable-workflow": ["durable-workflow", "kubernetes-job"],
}


def _meaningful_tokens(name: str) -> list[str]:
    return [t for t in re.split(r"[-_./]", name.lower()) if t and t not in _GENERIC_TOKENS]


def infer_purpose_draft(workload: dict, *, runtime_profile: dict | None = None) -> dict[str, Any]:
    """Infer a PurposeTaskDraft from an ImportedWorkload (+ optional RuntimeProfile for success thresholds)."""
    name = workload["native_name"]
    tags = workload.get("owner_hints", {}).get("tags", {})
    tokens = _meaningful_tokens(name)

    signals: dict[str, bool] = {
        "name_informative": len(tokens) >= 1,
        "service_tag": bool(tags.get("service") or tags.get("team") or tags.get("app")),
        "trigger_known": len(workload.get("triggers", [])) >= 1,
        "repo_hint": bool(workload.get("owner_hints", {}).get("repo")),
        "runtime_class_known": workload.get("runtime_class_guess") is not None,
    }
    confidence = round(sum(w for s, w in _SIGNAL_WEIGHTS.items() if signals.get(s)), 2)
    inferred_from = [s for s, ok in signals.items() if ok]

    phrase = " ".join(tokens) if tokens else name
    svc = tags.get("service") or tags.get("app") or ""
    purpose_summary = (f"(DRAFT — confirm) {phrase.capitalize()}"
                       + (f" for service '{svc}'" if svc else "")
                       + f"; inferred from a {workload['source']} {workload['native_kind']}"
                       + (f" triggered by {workload['triggers'][0]['type']}" if signals['trigger_known'] else "")
                       + ".")

    # success-criteria draft — derived from observed telemetry when available, else conservative defaults
    p95 = (runtime_profile or {}).get("p95_latency_ms")
    latency_bound = int(p95 * 1.25) if p95 else 60000
    success_criteria_draft = [
        "output_schema_valid == true",
        f"p95_latency_ms <= {latency_bound}",
        "timeout_rate <= 0.005",
        "no_secret_in_output == true",
        "forbidden_tool_calls == 0",
    ]
    baseline_impl_id = model.stable_id("impl", name, "imported_baseline")
    return {
        "schema_version": _PURPOSE_DRAFT_SCHEMA,
        "name": "-".join(tokens) if tokens else name,
        "source_workload_id": workload["id"],
        "confidence": confidence,
        "inferred_from": inferred_from,
        "purpose_summary": purpose_summary,
        "input_candidate_schema": {"type": "object"},
        "output_candidate_schema": {"type": "object"},
        "connected_systems": workload.get("connected_systems", []),
        "success_criteria_draft": success_criteria_draft,
        "requires_human_review": True,            # ALWAYS — inferred purpose is never authoritative
        "baseline_implementation_id": baseline_impl_id,
        "rollback_target": baseline_impl_id,
    }


def infer_capability_draft(workload: dict, purpose_draft: dict) -> dict[str, Any]:
    """Derive a CapabilityTaskDraft (allowed runtime classes + candidate runtime moves) from the workload."""
    guess = workload.get("runtime_class_guess") or "local-subprocess"
    allowed = list(dict.fromkeys(_RUNTIME_ALTERNATIVES.get(guess, [guess]) + ["human-review"]))
    candidate_runtime_changes: list[dict] = []
    # a timeout-prone short function is a classic "move to a long-running job" candidate
    if guess == "cloud-function":
        candidate_runtime_changes.append({"reason": "timeout_or_long_payload", "from": "cloud-function", "to": "kubernetes-job"})
    return {
        "schema_version": _CAP_DRAFT_SCHEMA,
        "name": purpose_draft["name"],
        "source_workload_id": workload["id"],
        "capability_summary": purpose_draft["purpose_summary"],
        "allowed_runtime_classes": allowed,
        "candidate_runtime_changes": candidate_runtime_changes,
        "requires_human_review": True,
    }


__all__ = ["infer_purpose_draft", "infer_capability_draft"]
