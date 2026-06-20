"""src.teleon.lift.model — Teleon Lift constants, mapping tables, and stable-id helpers.

The runtime_class_guess values come FROM architecture/capability_runtime_classes.json (no reinvented vocabulary)
so a lifted workload is already CTS-1-bindable. The K8s/Lambda interpretation tables encode the owner's mapping
(Job → CapabilityTask candidate; Deployment → worker; CronJob → trigger; etc.). Pure + deterministic.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

_RUNTIME_CLASSES_PATH = Path(__file__).resolve().parents[3] / "architecture" / "capability_runtime_classes.json"

#: Kubernetes kind → (runtime_class_guess, interpretation, note). runtime_class_guess is None for pure hints
#: (Service/Ingress) that inform triggers but aren't a workload runtime themselves.
K8S_INTERPRETATION: dict[str, tuple[str | None, str, str]] = {
    "Job":         ("kubernetes-job",   "capability_task_implementation", "runs to completion — a clean CapabilityTask candidate"),
    "CronJob":     ("cron-task",        "scheduled_trigger",              "a schedule that triggers a CapabilityTask"),
    "Deployment":  ("kubernetes-worker","long_running_worker_or_service", "API/daemon/worker — disambiguate via Service/Ingress"),
    "StatefulSet": ("kubernetes-worker","stateful_dependency",            "stateful — rarely a direct PurposeTask"),
    "DaemonSet":   ("kubernetes-worker","node_agent",                     "per-node agent — rarely a PurposeTask"),
    "ScaledObject":("queue-worker",     "event_driven_runtime_binding",   "KEDA scaling evidence"),
    "Workflow":    ("durable-workflow", "workflow_implementation_candidate","Argo/durable workflow implementation"),
    "Service":     (None,               "trigger_or_interface_hint",      "HTTP interface hint"),
    "Ingress":     (None,               "trigger_or_interface_hint",      "external HTTP route hint"),
}

#: A serverless function (AWS Lambda / GCP Cloud Function / Azure Function) always maps to the cloud-function class.
FUNCTION_INTERPRETATION: tuple[str, str, str] = (
    "cloud-function", "capability_task_implementation", "stateless event handler — a CapabilityTask candidate")

#: The 6-mode ADOPTION LADDER (owner-specified). Numeric + ordered; entry mode is `discover` (read-only). Managed
#: takeover (affects_production) only at level >= 4 and only with a human-confirmed purpose.
ADOPTION_LADDER: list[dict] = [
    {"level": 0, "mode": "discover",          "reads_only": True,  "executes_candidate": False, "affects_production": False},
    {"level": 1, "mode": "model",             "reads_only": True,  "executes_candidate": False, "affects_production": False},
    {"level": 2, "mode": "observe",           "reads_only": True,  "executes_candidate": False, "affects_production": False},
    {"level": 3, "mode": "shadow",            "reads_only": False, "executes_candidate": True,  "affects_production": False},
    {"level": 4, "mode": "managed_promotion", "reads_only": False, "executes_candidate": True,  "affects_production": True},
    {"level": 5, "mode": "full_managed",      "reads_only": False, "executes_candidate": True,  "affects_production": True},
]
ENTRY_MODE = "discover"
MANAGED_MIN_LEVEL = 4  # at/above this the platform can affect production — requires human-confirmed purpose

#: connected-system inference: an env-var KEY NAME (we never read values) → a connected-system kind.
_ENV_KEY_HINTS: tuple[tuple[str, str], ...] = (
    ("DATABASE", "database"), ("DB_", "database"), ("POSTGRES", "database"), ("MYSQL", "database"),
    ("REDIS", "cache"), ("QUEUE", "queue"), ("SQS", "queue"), ("KAFKA", "queue"), ("TOPIC", "queue"),
    ("BUCKET", "object_store"), ("S3", "object_store"), ("GCS", "object_store"), ("BLOB", "object_store"),
    ("OPENAI", "llm_provider"), ("ANTHROPIC", "llm_provider"), ("LLM", "llm_provider"),
    ("SMTP", "email"), ("SENDGRID", "email"), ("STRIPE", "payments"), ("API_KEY", "external_api"),
    ("WEBHOOK", "external_api"), ("ENDPOINT", "external_api"),
)


def runtime_class_vocabulary() -> set[str]:
    """The valid runtime classes (from capability_runtime_classes.json) — Lift guesses must stay within these."""
    doc = json.loads(_RUNTIME_CLASSES_PATH.read_text(encoding="utf-8"))
    return {c["class"] for c in doc.get("classes", [])}


def connected_systems_from_env_keys(env_keys: list[str]) -> list[str]:
    """Infer connected-system kinds from env-var KEY NAMES only (values are never imported). Deterministic, sorted."""
    out: set[str] = set()
    for k in env_keys:
        ku = k.upper()
        for needle, kind in _ENV_KEY_HINTS:
            if needle in ku:
                out.add(kind)
    return sorted(out)


def stable_id(prefix: str, *parts: str) -> str:
    """A deterministic id: prefix + short blake2b of the parts (never truncation-only; stable across runs)."""
    h = hashlib.blake2b("|".join(parts).encode("utf-8"), digest_size=8).hexdigest()
    slug = "".join(c if (c.isalnum() or c in "-_") else "-" for c in (parts[0] if parts else "x")).strip("-").lower()[:40]
    return f"{prefix}-{slug}-{h}"


__all__ = ["K8S_INTERPRETATION", "FUNCTION_INTERPRETATION", "ADOPTION_LADDER", "ENTRY_MODE", "MANAGED_MIN_LEVEL",
           "runtime_class_vocabulary", "connected_systems_from_env_keys", "stable_id"]
