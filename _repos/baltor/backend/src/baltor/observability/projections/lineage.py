"""src.baltor.observability.projections.lineage — the LINEAGE PROVIDER seam.

Baltor wraps lineage tools (OpenLineage) as a CANDIDATE provider behind this port. A provider turns a
LineageEvent into a LineageFacet: Baltor's normalized lineage record PLUS the standards renderings
(PROV-JSON + OpenLineage RunEvent) carrying governance facets. It DESCRIBES; it never mutates canonical
state and never decides truth. The wired adapter is the local stub; OpenLineage is catalog-only.

Deterministic: ids/time come from the (already-injected) event; renderings are pure functions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from src.baltor.observability.projections.standards import (
    GOVERNANCE_FACET_KEYS,
    canonical_hash,
    governance_facet,
    to_openlineage_run_event,
    to_prov_json,
)


@dataclass(frozen=True)
class LineageEvent:
    """A lineage transition: an `activity` consumed `inputs` and produced `outputs` under an `agent`."""
    event_id: str
    activity: str
    occurred_at: str           # injected ISO-8601; NOT wall-clock
    inputs: tuple = ()
    outputs: tuple = ()
    agent: str = "baltor.runtime"
    governance: dict = field(default_factory=dict)


@dataclass(frozen=True)
class LineageFacet:
    """Baltor's normalized lineage record + standards renderings keyed by standard name + a content
    hash for CDC. A read-only projection — emitting it never touches canonical state."""
    event_id: str
    activity: str
    occurred_at: str
    inputs: tuple
    outputs: tuple
    agent: str
    governance: dict
    renderings: dict           # {"prov": {...}, "openlineage": {...}}
    content_hash: str


@runtime_checkable
class LineageProvider(Protocol):
    """Turns a LineageEvent into a LineageFacet. DESCRIBES; never mutates canonical, never serves truth."""
    adapter_id: str

    def emit(self, event: LineageEvent) -> LineageFacet: ...


class BaltorLocalLineage:
    """The wired stub (`lineage.baltor_local@v1`). Renders PROV-JSON + OpenLineage in-process with the
    governance facets attached, so the receipt is portable without OpenLineage being installed."""

    adapter_id = "lineage.baltor_local@v1"

    def emit(self, event: LineageEvent) -> LineageFacet:
        gov = governance_facet(event.governance or {})
        renderings = {
            "prov": to_prov_json(event),
            "openlineage": to_openlineage_run_event(event),
        }
        return LineageFacet(
            event_id=event.event_id,
            activity=event.activity,
            occurred_at=event.occurred_at,
            inputs=tuple(event.inputs),
            outputs=tuple(event.outputs),
            agent=event.agent,
            governance=gov,
            renderings=renderings,
            content_hash=canonical_hash({"e": event.event_id, "r": renderings}),
        )


__all__ = ["LineageEvent", "LineageFacet", "LineageProvider", "BaltorLocalLineage", "GOVERNANCE_FACET_KEYS"]
