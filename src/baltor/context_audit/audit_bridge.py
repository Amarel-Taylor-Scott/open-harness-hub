"""src.baltor.context_audit.audit_bridge — connect the Context Auditor to the running system.

"If a module doesn't emit an event, it isn't connected." This bridge runs the Context Auditor over a context
bundle and publishes each finding onto the shared event bus (scripts.context_events), then exposes the
governed PRE-CALL path: audit → emit → signal `inference.requested` with the manifest attached, so the Teleon
inference gateway is only ever called with an ALREADY-AUDITED bundle.

Issue → event mapping (conflict/stale reuse existing kinds; redundancy/bloat are Optimization-stage signals):
  conflicting_context → contradiction_found (Reconciliation)
  stale_context       → rot.detected         (Anti-Fragility)
  duplicate_context   → context.duplicate_found (Optimization)
  tool_bloat          → context.tool_bloat      (Optimization)
  + a context.audited summary (Optimization)

Governance: the auditor PROPOSES (the emitted manifest carries applied=False); events are SIGNALS, not truth.
The bus assigns a monotonic seq (no wall-clock). Baltor → Teleon direction only: this lives in Baltor and the
Teleon gateway never imports it.
"""
from __future__ import annotations

from typing import Any

from .context_auditor import ISSUE_TYPES, audit
from .optimizer import apply_manifest

# issue type → (event kind, macro stage). conflict/stale reuse existing EVENT_KINDS.
_ISSUE_EVENT: dict[str, tuple[str, str]] = {
    "conflicting_context": ("contradiction_found", "Reconciliation"),
    "stale_context": ("rot.detected", "Anti-Fragility"),
    "duplicate_context": ("context.duplicate_found", "Optimization"),
    "tool_bloat": ("context.tool_bloat", "Optimization"),
    "context_poisoning": ("context.poisoning_suspected", "Anti-Fragility"),
}
_COMPONENT = "context_auditor"
# fail fast if the auditor ever grows an issue type without a bus mapping (no silent un-emitted finding).
assert set(_ISSUE_EVENT) == set(ISSUE_TYPES), "every auditor issue type must map to an event kind"


def audit_and_emit(sources: list[dict[str, Any]], bus: Any, *,
                   correlation_id: str = "ctx-audit", **audit_kwargs: Any) -> dict[str, Any]:
    """Audit `sources`, publish one event per finding + a `context.audited` summary, return the report.

    `bus` is any object exposing `publish(kind, *, stage, component, correlation_id, payload)` — the
    scripts.context_events.EventBus. The bridge never mutates `sources` (the auditor is lossless)."""
    report = audit(sources, **audit_kwargs)

    by_type: dict[str, int] = {t: 0 for t in ISSUE_TYPES}
    for issue in report["issues"]:
        kind, stage = _ISSUE_EVENT[issue["type"]]
        by_type[issue["type"]] += 1
        bus.publish(kind, stage=stage, component=_COMPONENT, correlation_id=correlation_id, payload=issue)

    bus.publish("context.audited", stage="Optimization", component=_COMPONENT, correlation_id=correlation_id,
                payload={
                    "original_tokens": report["original_tokens"],
                    "estimated_optimized_tokens": report["estimated_optimized_tokens"],
                    "issue_count": len(report["issues"]),
                    "by_type": by_type,
                    "applied": report["applied"],  # PROPOSES, never disposes — the manifest is advice
                })
    return report


def audited_pre_call(sources: list[dict[str, Any]], bus: Any, *,
                     correlation_id: str = "ctx-audit", model_hint: str | None = None,
                     **audit_kwargs: Any) -> dict[str, Any]:
    """The governed gateway PRE-CALL path: audit + emit, then signal `inference.requested` with the manifest
    attached. The actual model invocation stays the caller's (TeleonClient / src/teleon/inference) — this is
    the Baltor-side pre-flight that guarantees the gateway sees an audited bundle. Returns the report."""
    report = audit_and_emit(sources, bus, correlation_id=correlation_id, **audit_kwargs)
    bus.publish("inference.requested", stage="Consumption", component=_COMPONENT, correlation_id=correlation_id,
                payload={
                    "audited": True,
                    "manifest_issue_count": len(report["issues"]),
                    "estimated_optimized_tokens": report["estimated_optimized_tokens"],
                    "applied": report["applied"],
                    "model_hint": model_hint,
                })
    return report


def optimize_pre_call(sources: list[dict[str, Any]], bus: Any, *,
                      correlation_id: str = "ctx-audit", **audit_kwargs: Any) -> dict[str, Any]:
    """The full Auditor→Optimizer pre-call path: audit + emit each finding + the context.audited manifest,
    then APPLY the manifest LOSSLESSLY (optimizer.apply_manifest) to produce the optimized bundle, and emit
    context.optimized carrying the ACTUAL optimized-token count + drop/supersede counts. Returns
    {report, envelope, optimized} — `optimized` is the bundle the gateway/TeleonClient should send; the raw
    bundle stays exactly rehydratable in envelope['raw'] (supersede≠delete). Never mutates `sources`."""
    report = audit_and_emit(sources, bus, correlation_id=correlation_id, **audit_kwargs)
    env = apply_manifest(sources, report)
    bus.publish("context.optimized", stage="Optimization", component="context_optimizer",
                correlation_id=correlation_id,
                payload={
                    "original_tokens": env["original_tokens"],
                    "optimized_tokens": env["optimized_tokens"],
                    "dropped": len(env["dropped"]),
                    "superseded": len(env["superseded"]),
                    "lossless": env["lossless"],
                    "rehydratable": env["rehydratable"],
                })
    return {"report": report, "envelope": env, "optimized": env["optimized"]}
