"""src.baltor.observability.tracing.provider — the OBSERVABILITY PROVIDER seam.

Baltor wraps observability tools (Langfuse / Phoenix / LangSmith) as CANDIDATE providers behind this
port. A provider turns a stream of context-operation spans into a SpanTree — it DESCRIBES what
happened. It is never the authority and never serves truth: Baltor proofs / receipts / the flywheel
stay authoritative. The wired adapter is always the local stub; external candidates are catalog-only
until adopted with a card + contract + fallback.

Deterministic: span ids are caller-supplied content ids, time is the injected `occurred_at`
(never wall-clock), ordering is by (occurred_at, span_id). Span records are FROZEN — a provider
physically cannot mutate canonical state through them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from src.baltor.observability.projections.standards import GOVERNANCE_FACET_KEYS, governance_facet


@dataclass(frozen=True)
class ContextOperationSpan:
    """One unit of work in a Baltor context operation (a pipeline stage / verifier / worker run)."""
    span_id: str
    parent_id: str | None
    operation: str                 # e.g. "reconciliation.find_contradictions"
    status: str                    # ok | error | held_out
    occurred_at: str               # injected ISO-8601; NOT wall-clock
    object_ref: str | None = None
    correlation_id: str | None = None
    governance: dict = field(default_factory=dict)
    attributes: dict = field(default_factory=dict)


@dataclass(frozen=True)
class SpanTree:
    """A read-only projection: nested {span, children:[...]} with a flat count + correlation id."""
    root: dict
    span_count: int
    correlation_id: str | None


@runtime_checkable
class ObservabilityProvider(Protocol):
    """Turns spans into a SpanTree. DESCRIBES; never the authority, never writes canonical state."""
    adapter_id: str

    def record(self, spans: list[ContextOperationSpan]) -> SpanTree: ...


def _node(span: ContextOperationSpan) -> dict:
    """A single tree node — governance is filtered to the allowed keys (no forged-authority leakage)."""
    return {
        "span_id": span.span_id,
        "operation": span.operation,
        "status": span.status,
        "occurred_at": span.occurred_at,
        "object_ref": span.object_ref,
        "correlation_id": span.correlation_id,
        "held_out": bool((span.governance or {}).get("held_out", False)),
        "governance": governance_facet(span.governance or {}),
        "children": [],
    }


class BaltorLocalObservability:
    """The wired stub (`observability.baltor_local_trace@v1`). Builds an in-process SpanTree with zero
    external deps. This is the local authority-neutral default; Langfuse/Phoenix are candidates."""

    adapter_id = "observability.baltor_local_trace@v1"

    def record(self, spans: list[ContextOperationSpan]) -> SpanTree:
        ordered = sorted(spans, key=lambda s: (s.occurred_at, s.span_id))
        nodes = {s.span_id: _node(s) for s in ordered}
        roots: list[dict] = []
        for s in ordered:
            if s.parent_id and s.parent_id in nodes:
                nodes[s.parent_id]["children"].append(nodes[s.span_id])
            else:
                roots.append(nodes[s.span_id])
        # a synthetic root when the operation has multiple top-level spans, else the single root
        if len(roots) == 1:
            root = roots[0]
        else:
            root = {"span_id": "root", "operation": "context_operation", "status": "ok",
                    "occurred_at": ordered[0].occurred_at if ordered else None,
                    "object_ref": None, "correlation_id": None, "held_out": False,
                    "governance": {}, "children": roots}
        corr = next((s.correlation_id for s in ordered if s.correlation_id), None)
        return SpanTree(root=root, span_count=len(ordered), correlation_id=corr)


__all__ = ["ContextOperationSpan", "SpanTree", "ObservabilityProvider", "BaltorLocalObservability",
           "GOVERNANCE_FACET_KEYS"]
