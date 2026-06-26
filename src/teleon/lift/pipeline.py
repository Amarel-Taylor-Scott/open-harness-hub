"""src.teleon.lift.pipeline — the end-to-end Teleon Lift orchestrator.

native workload → ImportedWorkload → RuntimeProfile + Trigger/Dependency graphs → PurposeTaskDraft +
CapabilityTaskDraft → AdoptionPlan (with the imported baseline as the rollback target). Pure + deterministic;
imported_at is injected. RuntimeProfile is built ONLY from supplied observations — never fabricated (absent
telemetry → an explicit `unavailable` profile).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from . import adoption, normalize, semantic_lifter

_RUNTIME_PROFILE_SCHEMA = "RuntimeProfile"


@dataclass(frozen=True)
class LiftResult:
    """The full lift output for one workload (all components are JSON-serializable dicts)."""
    workload: dict
    runtime_profile: dict
    trigger_graph: dict
    dependency_graph: dict
    purpose_draft: dict
    capability_draft: dict
    adoption_plan: dict

    def as_dict(self) -> dict[str, Any]:
        return {"workload": self.workload, "runtime_profile": self.runtime_profile,
                "trigger_graph": self.trigger_graph, "dependency_graph": self.dependency_graph,
                "purpose_draft": self.purpose_draft, "capability_draft": self.capability_draft,
                "adoption_plan": self.adoption_plan}


def build_runtime_profile(workload: dict, observations: dict | None) -> dict[str, Any]:
    """A RuntimeProfile from SUPPLIED telemetry observations. No observations → an explicit `unavailable` profile
    (never fabricated)."""
    if not observations:
        return {"schema_version": _RUNTIME_PROFILE_SCHEMA, "workload_id": workload["id"], "source": "unavailable",
                "observed_window": "none", "invocations": None, "p50_latency_ms": None, "p95_latency_ms": None,
                "error_rate": None, "timeout_rate": None, "estimated_cost_usd": None}
    return {"schema_version": _RUNTIME_PROFILE_SCHEMA, "workload_id": workload["id"], "source": "observed",
            "observed_window": observations.get("observed_window", ""),
            "invocations": observations.get("invocations"),
            "p50_latency_ms": observations.get("p50_latency_ms"),
            "p95_latency_ms": observations.get("p95_latency_ms"),
            "error_rate": observations.get("error_rate"),
            "timeout_rate": observations.get("timeout_rate"),
            "estimated_cost_usd": observations.get("estimated_cost_usd")}


def build_trigger_graph(workload: dict) -> dict[str, Any]:
    triggers = workload.get("triggers", [])
    return {"workload_id": workload["id"], "triggers": triggers, "trigger_count": len(triggers)}


def build_dependency_graph(workload: dict) -> dict[str, Any]:
    return {"workload_id": workload["id"], "connected_systems": workload.get("connected_systems", []),
            "permissions_identity": workload.get("permissions", {}).get("identity", "")}


def lift_workload(native: dict, *, imported_at: str, observations: dict | None = None) -> LiftResult:
    """Run the full lift on ONE provider-native workload. Discover/model only — no production change."""
    workload = normalize.normalize(native, imported_at=imported_at)
    profile = build_runtime_profile(workload, observations)
    purpose_draft = semantic_lifter.infer_purpose_draft(workload, runtime_profile=profile)
    capability_draft = semantic_lifter.infer_capability_draft(workload, purpose_draft)
    plan = adoption.build_adoption_plan(workload, purpose_draft)  # defaults: discover, unconfirmed, not manageable
    return LiftResult(workload=workload, runtime_profile=profile,
                      trigger_graph=build_trigger_graph(workload), dependency_graph=build_dependency_graph(workload),
                      purpose_draft=purpose_draft, capability_draft=capability_draft, adoption_plan=plan)


def lift_inventory(connectors, *, imported_at: str, observations_by_name: dict | None = None) -> list[LiftResult]:
    """Scan each connector (read-only) and lift every discovered workload. `observations_by_name` maps a workload's
    native_name → its telemetry observations (optional)."""
    obs = observations_by_name or {}
    out: list[LiftResult] = []
    for conn in connectors:
        for native in conn.scan():
            name = native.get("name", "")
            out.append(lift_workload(native, imported_at=imported_at, observations=obs.get(name)))
    return out


__all__ = ["LiftResult", "lift_workload", "lift_inventory", "build_runtime_profile", "build_trigger_graph",
           "build_dependency_graph"]
