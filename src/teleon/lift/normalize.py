"""src.teleon.lift.normalize — normalize provider-native workloads into a canonical ImportedWorkload.

Provider-specific shapes (a Kubernetes object, an AWS Lambda config) → ONE ImportedWorkload. SAFETY: env-var
VALUES are never carried through — only key names (env_redacted_keys). Pure + deterministic; imported_at is
injected (no wall-clock). The LIVE connectors map the real provider API into the simplified native shapes these
functions accept (the offline canned connectors already emit that shape).
"""
from __future__ import annotations

from typing import Any

from . import model

_IMPORTED_WORKLOAD_SCHEMA = "ImportedWorkload"


def _redact_env_list(env: list[dict] | None) -> list[str]:
    """Kubernetes-style env ([{name,value|valueFrom}, ...]) → sorted KEY NAMES only (values dropped)."""
    return sorted({e["name"] for e in (env or []) if "name" in e})


def _redact_env_map(env: dict | None) -> list[str]:
    """Lambda-style env ({KEY: value}) → sorted KEY NAMES only (values dropped)."""
    return sorted((env or {}).keys())


def _workload(source: str, native_kind: str, native_name: str, *, runtime_class_guess: str | None,
              interpretation: str, interpretation_note: str, imported_at: str, account: str = "",
              region: str = "", namespace: str = "", tags: dict | None = None, runtime: dict | None = None,
              triggers: list[dict] | None = None, identity: str = "", env_keys: list[str] | None = None,
              connected_systems: list[str] | None = None, telemetry: dict | None = None,
              repo: str = "") -> dict[str, Any]:
    env_keys = env_keys or []
    return {
        "schema_version": _IMPORTED_WORKLOAD_SCHEMA,
        "id": model.stable_id("workload", native_name, source, native_kind),
        "source": source,
        "native_kind": native_kind,
        "native_name": native_name,
        "account": account,
        "region": region,
        "namespace": namespace,
        "runtime_class_guess": runtime_class_guess,
        "interpretation": interpretation,
        "interpretation_note": interpretation_note,
        "owner_hints": {"tags": tags or {}, "repo": repo},
        "runtime": runtime or {},
        "triggers": triggers or [],
        "permissions": {"identity": identity},
        "env_redacted_keys": env_keys,
        "connected_systems": sorted(set((connected_systems or []) + model.connected_systems_from_env_keys(env_keys))),
        "telemetry_refs": telemetry or {},
        "imported_at": imported_at,
    }


def normalize_k8s(resource: dict, *, imported_at: str) -> dict[str, Any]:
    """A (simplified) Kubernetes resource → ImportedWorkload. Honors the K8s interpretation table."""
    kind = resource["kind"]
    rc, interp, note = model.K8S_INTERPRETATION.get(kind, (None, "unknown_kind", "unrecognized K8s kind"))
    env_keys = _redact_env_list(resource.get("env"))
    triggers: list[dict] = []
    if resource.get("schedule"):
        triggers.append({"type": "schedule", "ref": resource["schedule"]})
    for exp in resource.get("exposed_by", []):
        triggers.append({"type": "http", "ref": exp})
    if resource.get("queue"):
        triggers.append({"type": "queue", "ref": resource["queue"]})
    runtime = {"kind": kind, "image": resource.get("image", ""), "command": resource.get("command", []),
               "replicas": resource.get("replicas"), "resources": resource.get("resources", {})}
    return _workload(
        "k8s", kind, resource["name"], runtime_class_guess=rc, interpretation=interp, interpretation_note=note,
        imported_at=imported_at, region=resource.get("cluster", ""), namespace=resource.get("namespace", ""),
        tags=resource.get("labels", {}), runtime=runtime, triggers=triggers,
        identity=resource.get("service_account", ""), env_keys=env_keys,
        connected_systems=[resource["queue"]] if resource.get("queue") else [],
        telemetry={k: resource[k] for k in ("logs_ref", "metrics_ref") if resource.get(k)},
        repo=resource.get("repo", ""))


def normalize_lambda(resource: dict, *, imported_at: str) -> dict[str, Any]:
    """An AWS Lambda (or GCP/Azure function — same shape) config → ImportedWorkload (cloud-function class)."""
    rc, interp, note = model.FUNCTION_INTERPRETATION
    env_keys = _redact_env_map(resource.get("env"))
    triggers = [{"type": m["type"], "ref": m.get("ref", "")} for m in resource.get("event_source_mappings", [])]
    if resource.get("function_url"):
        triggers.append({"type": "http", "ref": "function_url"})
    runtime = {"runtime": resource.get("runtime", ""), "handler": resource.get("handler", ""),
               "memory_mb": resource.get("memory_mb"), "timeout_s": resource.get("timeout_s"),
               "image": resource.get("image", "")}
    return _workload(
        resource.get("source", "aws"), "function", resource["name"], runtime_class_guess=rc, interpretation=interp,
        interpretation_note=note, imported_at=imported_at, account=resource.get("account", ""),
        region=resource.get("region", ""), tags=resource.get("tags", {}), runtime=runtime, triggers=triggers,
        identity=resource.get("role", ""), env_keys=env_keys,
        connected_systems=[m.get("ref", "") for m in resource.get("event_source_mappings", []) if m.get("ref")],
        telemetry={k: resource[k] for k in ("logs_ref", "metrics_ref") if resource.get(k)},
        repo=resource.get("repo", ""))


def normalize(resource: dict, *, imported_at: str) -> dict[str, Any]:
    """Dispatch by source/shape: a dict with a K8s `kind` → normalize_k8s; otherwise a function → normalize_lambda."""
    if resource.get("kind") in model.K8S_INTERPRETATION or (resource.get("source") == "k8s"):
        return normalize_k8s(resource, imported_at=imported_at)
    return normalize_lambda(resource, imported_at=imported_at)


__all__ = ["normalize", "normalize_k8s", "normalize_lambda"]
