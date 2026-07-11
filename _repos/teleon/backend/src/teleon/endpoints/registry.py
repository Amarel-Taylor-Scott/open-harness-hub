"""src.teleon.endpoints.registry — interchangeable PROVIDER ENDPOINTS per capability, selected by objective.

A capability often has many providers behind it: WHOIS via RDAP, a paid API, or a library; geocoding via the US
Census, Google, or Mapbox. This registry maps a capability_slot to its endpoints and SELECTS the best one for a
tenant's priority using the SAME objective layer that selects runners — minimize_cost picks the cheapest,
minimize_latency the fastest, maximize_accuracy the most reliable. Two hooks make it governed and self-improving:
  * ``forbidden`` — endpoint_ids the org guardrail policy disallows (license/domain/egress) are excluded BEFORE
    scoring, so safety beats the objective (a "minimize cost" priority can never pick a banned provider).
  * ``ledger`` — a RunLedger of observed calls refines each endpoint's declared prior (an endpoint observed to be
    slow/unreliable is deprioritized on the next selection).

Pure + deterministic; reads shared DATA only; Teleon-layer — never imports src.baltor. A selection is a routing
decision, never a fact (serves_truth pinned False).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from dataclasses import dataclass
from pathlib import Path

from src.teleon.objectives import MetricVector, select

#: repo root: _repos/teleon/backend/src/teleon/endpoints/registry.py -> parents[3].
_REGISTRY_PATH = _resource("architecture") / "capability_endpoint_registry.json"
#: an API/library call is a deterministic OPERATION (the returned data may change; the call mechanism does not),
#: so determinism is uniform across endpoints and does not discriminate — cost/latency/reliability do.
_ENDPOINT_DETERMINISM = 1.0


class EndpointError(ValueError):
    """Raised when a capability has no registered endpoints, or a registry row is malformed."""


@dataclass(frozen=True)
class ProviderEndpoint:
    """One provider that can serve a capability. ``cost`` = relative per-call units; ``latency_ms`` typical;
    ``reliability`` 0..1; plus the governance signals (``license``, ``egress_domain``, ``access``, ``region``)."""
    endpoint_id: str
    capability_slot: str
    provider: str
    kind: str
    access: str
    cost: float
    latency_ms: float
    reliability: float
    license: str
    egress_domain: str
    region: str = "global"
    notes: str = ""

    def metric_vector(self) -> MetricVector:
        """Endpoints differ on cost / latency / reliability; determinism is uniform (=1.0) and no LLM is used,
        so those dimensions stay neutral and the cost/latency/reliability priorities drive the choice."""
        return MetricVector(cost=float(self.cost), latency=float(self.latency_ms), llm_usage=0.0,
                            determinism=_ENDPOINT_DETERMINISM, accuracy=float(self.reliability))

    def as_dict(self) -> dict:
        return {"endpoint_id": self.endpoint_id, "capability_slot": self.capability_slot, "provider": self.provider,
                "kind": self.kind, "access": self.access, "cost": self.cost, "latency_ms": self.latency_ms,
                "reliability": self.reliability, "license": self.license, "egress_domain": self.egress_domain,
                "region": self.region, "notes": self.notes}


def _load(registry: dict | None = None) -> dict:
    return registry if registry is not None else json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))


def registered_capabilities(*, registry: dict | None = None) -> list[str]:
    return sorted(_load(registry).get("endpoints", {}))


def endpoints_for(capability_slot: str, *, registry: dict | None = None) -> list[ProviderEndpoint]:
    """Every registered endpoint for a capability (raises if none — never a silent empty selection)."""
    raw = _load(registry).get("endpoints", {}).get(capability_slot)
    if not raw:
        raise EndpointError(f"no endpoints registered for capability {capability_slot!r}")
    out = []
    for e in raw:
        try:
            out.append(ProviderEndpoint(capability_slot=capability_slot, **e))
        except TypeError as exc:
            raise EndpointError(f"malformed endpoint row for {capability_slot!r}: {exc}") from exc
    return out


def select_endpoint(capability_slot: str, objective, *, forbidden: set | None = None,
                    ledger=None, registry: dict | None = None) -> dict:
    """Pick the best provider endpoint for ``capability_slot`` under ``objective``. ``forbidden`` endpoint_ids
    (from an org guardrail policy) are excluded before scoring (safety beats objective); a RunLedger ``ledger``
    refines each endpoint's declared metrics with observed calls. Returns the objective layer's full, deterministic
    SelectionTrace plus the chosen endpoint's detail. serves_truth False."""
    eps = endpoints_for(capability_slot, registry=registry)
    candidates = []
    for ep in eps:
        mv = ep.metric_vector()
        if ledger is not None and ledger.count(ep.endpoint_id) > 0:
            mv = ledger.blend(ep.endpoint_id, mv)  # observed telemetry refines the declared prior
        candidates.append((ep.endpoint_id, mv))
    trace = select(candidates, objective, forbidden=forbidden)
    chosen = next(ep for ep in eps if ep.endpoint_id == trace["chosen"])
    return {**trace, "capability_slot": capability_slot, "chosen_endpoint": chosen.as_dict()}
