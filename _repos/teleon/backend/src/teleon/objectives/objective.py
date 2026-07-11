"""src.teleon.objectives.objective — the capability-level OBJECTIVE policy + measurement + traceable selection.

Teleon is the LOGIC that decides which implementation of a capability unit to run and how hard to drive the
non-det->det descent. THIS module makes that decision flexible + measurable + traceable:

  * MetricVector — the per-implementation MEASUREMENT (telemetry): cost, latency, llm_usage, determinism,
    accuracy. The measurement methods are the named dimensions; richer than a single exact-match pass-rate.
  * CapabilityObjective — a numeric PRIORITY policy (weights over the dimensions) so a tenant/task can prioritize
    speed, cost, LLM-minimization, determinism, or accuracy. Presets (minimize_cost / minimize_latency /
    minimize_llm / maximize_determinism / maximize_accuracy / balanced) + arbitrary weights.
  * select(...) — scores each candidate implementation against the objective (min-max normalized across the
    candidate set, lower-is-better dims inverted) and returns the best WITH a full SelectionTrace (every
    candidate's score + the weights + the reason) — DETERMINISTIC and TRACEABLE. serves_truth is pinned False
    (a selection is a routing decision, never a fact); SAFETY beats the objective (forbidden impls are excluded
    before scoring, so a "minimize cost" objective can never pick a forbidden-capability implementation).

Pure + deterministic (no clock/RNG/IO). Stdlib only; Teleon-layer — never imports src.baltor.
"""
from __future__ import annotations

from dataclasses import dataclass, field

#: the measurable axes a capability implementation is scored on (the "measurement methods").
OBJECTIVE_DIMENSIONS = ("cost", "latency", "llm_usage", "determinism", "accuracy")
#: dimensions where a LOWER raw value is better (inverted before scoring).
LOWER_IS_BETTER = ("cost", "latency", "llm_usage")
#: dimensions where a HIGHER raw value is better.
HIGHER_IS_BETTER = ("determinism", "accuracy")

_ROUND = 6


class ObjectiveError(ValueError):
    """Raised on a malformed objective/metric or an empty candidate set — explicit failure, never a silent pick."""


@dataclass(frozen=True)
class MetricVector:
    """The per-implementation MEASUREMENT (telemetry). cost = relative units; latency = ms; llm_usage = model
    calls; determinism + accuracy = 0..1 (1.0 = fully deterministic / perfectly accurate)."""
    cost: float = 0.0
    latency: float = 0.0
    llm_usage: float = 0.0
    determinism: float = 1.0
    accuracy: float = 1.0

    def value(self, dimension: str) -> float:
        return float(getattr(self, dimension))

    def as_dict(self) -> dict:
        return {d: self.value(d) for d in OBJECTIVE_DIMENSIONS}


@dataclass(frozen=True)
class CapabilityObjective:
    """A numeric PRIORITY policy over the measurement dimensions. weights need not sum to 1 (they are normalized
    at scoring); a dimension absent from weights contributes 0. ``name`` is for the trace."""
    name: str
    weights: dict = field(default_factory=dict)

    def normalized_weights(self) -> dict:
        total = sum(max(0.0, float(self.weights.get(d, 0.0))) for d in OBJECTIVE_DIMENSIONS)
        if total <= 0:
            raise ObjectiveError(f"objective {self.name!r} has no positive weight on any known dimension")
        return {d: max(0.0, float(self.weights.get(d, 0.0))) / total for d in OBJECTIVE_DIMENSIONS}


#: preset objectives — the common priorities. Each names a dominant dimension with small floors elsewhere
#: (accuracy keeps a floor everywhere so the objective never picks a wrong-but-cheap impl when one is worse).
PRESETS = {
    "minimize_cost": CapabilityObjective("minimize_cost",
        {"cost": 0.55, "llm_usage": 0.15, "latency": 0.10, "determinism": 0.10, "accuracy": 0.10}),
    "minimize_latency": CapabilityObjective("minimize_latency",
        {"latency": 0.55, "cost": 0.15, "llm_usage": 0.10, "determinism": 0.10, "accuracy": 0.10}),
    "minimize_llm": CapabilityObjective("minimize_llm",
        {"llm_usage": 0.55, "cost": 0.15, "determinism": 0.15, "latency": 0.05, "accuracy": 0.10}),
    "maximize_determinism": CapabilityObjective("maximize_determinism",
        {"determinism": 0.55, "cost": 0.15, "llm_usage": 0.15, "latency": 0.05, "accuracy": 0.10}),
    "maximize_accuracy": CapabilityObjective("maximize_accuracy",
        {"accuracy": 0.60, "determinism": 0.10, "cost": 0.10, "latency": 0.10, "llm_usage": 0.10}),
    "balanced": CapabilityObjective("balanced",
        {"cost": 0.20, "latency": 0.20, "llm_usage": 0.20, "determinism": 0.20, "accuracy": 0.20}),
}


def _goodness(value: float, lo: float, hi: float, dimension: str) -> float:
    """Map a raw dimension value to a 0..1 'goodness' relative to the candidate set: min-max normalize, then
    invert for lower-is-better dimensions. No spread (lo==hi) → neutral 1.0 (the dimension can't discriminate)."""
    if hi == lo:
        return 1.0
    norm = (value - lo) / (hi - lo)
    return (1.0 - norm) if dimension in LOWER_IS_BETTER else norm


def select(candidates: list[tuple[str, MetricVector]], objective: CapabilityObjective, *,
           forbidden: set | None = None) -> dict:
    """Pick the implementation that best satisfies ``objective`` and return a full SelectionTrace.

    SAFETY > objective: ``forbidden`` impl_ids are EXCLUDED before scoring (a cost objective can never select a
    forbidden-capability impl). Scoring is min-max normalized ACROSS the allowed candidates (a relative, fair
    comparison), weighted by the normalized objective. DETERMINISTIC: ties break by impl_id; same inputs → same
    result. serves_truth pinned False."""
    forbidden = set(forbidden or ())
    allowed = [(cid, m) for cid, m in candidates if cid not in forbidden]
    if not allowed:
        raise ObjectiveError("no allowed candidate implementations to select among")
    w = objective.normalized_weights()
    bounds = {d: (min(m.value(d) for _, m in allowed), max(m.value(d) for _, m in allowed))
              for d in OBJECTIVE_DIMENSIONS}
    ranked = []
    for cid, m in allowed:
        score = sum(w[d] * _goodness(m.value(d), bounds[d][0], bounds[d][1], d) for d in OBJECTIVE_DIMENSIONS)
        ranked.append({"impl_id": cid, "score": round(score, _ROUND), "metrics": m.as_dict()})
    ranked.sort(key=lambda r: (-r["score"], r["impl_id"]))
    chosen = ranked[0]
    return {
        "chosen": chosen["impl_id"],
        "objective": objective.name,
        "weights": w,
        "ranked": ranked,
        "rationale": (f"chose {chosen['impl_id']} (score {chosen['score']}) under objective {objective.name!r}: "
                      f"best weighted fit across cost/latency/llm_usage/determinism/accuracy among "
                      f"{len(allowed)} allowed candidate(s)"),
        "excluded_forbidden": sorted(set(cid for cid, _ in candidates) & forbidden),
        "serves_truth": False,
    }
