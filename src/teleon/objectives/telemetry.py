"""src.teleon.objectives.telemetry — OBSERVED measurement: turn real run outcomes into a MetricVector per impl.

The declared/seed MetricVector is a PRIOR; this is the EVIDENCE. A RunLedger ingests per-run observations
(cost, latency, llm calls, eval pass/fail, a stable output key) and derives an OBSERVED MetricVector per
implementation — the telemetry the CapabilityObjective actually selects on, so a unit IMPROVES as it runs
(the self-improvement signal: the distilled rule earns its promotion on observed parity, not a declared claim).

Measurement methods (the observed dimensions):
  cost        = mean observed cost (relative units)
  latency     = mean observed latency (ms)
  llm_usage   = mean observed model calls
  accuracy    = eval pass-rate (passed / total)
  determinism = output-stability = modal-output share among runs that recorded an output key (1.0 = always same)

Pure aggregation: deterministic, no clock/RNG/IO. Stdlib only; Teleon-layer — never imports src.baltor.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from src.teleon.objectives.objective import OBJECTIVE_DIMENSIONS, MetricVector


class TelemetryError(ValueError):
    """Raised on a malformed observation or a query for an impl with no recorded runs — never a silent guess."""


@dataclass(frozen=True)
class RunObservation:
    """One recorded run of an implementation. ``cost`` = relative units; ``latency_ms``; ``llm_calls`` = model
    calls made; ``passed`` = the eval verdict for this run; ``output_key`` = a stable key for the produced output
    (e.g. a hash of the normalized answer) used to MEASURE output-stability/determinism. A blank output_key means
    'stability not observed for this run' — it does not count as instability."""
    impl_id: str
    cost: float
    latency_ms: float
    llm_calls: float
    passed: bool
    output_key: str = ""


class RunLedger:
    """Accumulates RunObservations per implementation and derives an OBSERVED MetricVector + a blended prior.

    The ledger IS the telemetry trace (every observation is retained, in order). It feeds ``select()`` directly via
    :meth:`candidates`, and :meth:`blend` shrinks a declared prior toward observed evidence (evidence weight = run
    count) so a freshly-seeded unit has no cold-start cliff and converges to its real behaviour as it runs."""

    def __init__(self) -> None:
        self._obs: dict[str, list[RunObservation]] = {}

    def record(self, obs: RunObservation) -> None:
        if not getattr(obs, "impl_id", ""):
            raise TelemetryError("observation needs a non-empty impl_id")
        self._obs.setdefault(obs.impl_id, []).append(obs)

    def count(self, impl_id: str) -> int:
        return len(self._obs.get(impl_id, ()))

    def observations(self, impl_id: str) -> list[RunObservation]:
        """The retained, ordered observation trace for one impl (telemetry, never discarded)."""
        return list(self._obs.get(impl_id, ()))

    def observed_metrics(self, impl_id: str) -> MetricVector:
        """The MetricVector derived purely from this impl's recorded runs (see module docstring for methods)."""
        runs = self._obs.get(impl_id, ())
        if not runs:
            raise TelemetryError(f"no observations recorded for impl {impl_id!r}")
        n = len(runs)
        mean = lambda f: sum(f(r) for r in runs) / n
        keys = [r.output_key for r in runs if r.output_key]
        # output-stability over runs that reported a key; no keys reported -> instability unobserved -> neutral 1.0.
        determinism = (Counter(keys).most_common(1)[0][1] / len(keys)) if keys else 1.0
        return MetricVector(
            cost=mean(lambda r: float(r.cost)),
            latency=mean(lambda r: float(r.latency_ms)),
            llm_usage=mean(lambda r: float(r.llm_calls)),
            determinism=determinism,
            accuracy=mean(lambda r: 1.0 if r.passed else 0.0),
        )

    def candidates(self) -> list[tuple[str, MetricVector]]:
        """All impls with observations as (impl_id, observed MetricVector), sorted by impl_id — feeds ``select()``
        directly so a capability is selected on OBSERVED telemetry, not declared metrics."""
        return [(impl_id, self.observed_metrics(impl_id)) for impl_id in sorted(self._obs)]

    def blend(self, impl_id: str, prior: MetricVector, *, prior_weight: float = 1.0) -> MetricVector:
        """Blend a declared ``prior`` with observed evidence: a weighted mean where the prior counts as
        ``prior_weight`` pseudo-runs and the evidence counts as its run count. 0 runs -> the prior unchanged;
        many runs -> converges to observed. Lets units start from seed metrics and earn their real numbers."""
        n = self.count(impl_id)
        if n == 0:
            return prior
        obs = self.observed_metrics(impl_id)
        wp = max(0.0, float(prior_weight))
        wo = float(n)
        total = wp + wo
        if total <= 0:  # prior_weight 0 AND no runs is already handled; guard a 0/0 only if prior_weight<0 clamped
            return obs
        return MetricVector(**{d: (getattr(prior, d) * wp + getattr(obs, d) * wo) / total
                               for d in OBJECTIVE_DIMENSIONS})
