#!/usr/bin/env python3
"""Gap-detection screen — the cheap predictor of "lack" that runs BEFORE collection.

Solves the chicken-and-egg the collection grid hand-waves as "expected_lift comes
from external signals": the clean test (pipeline_score − bare_model_score) needs
content you don't have yet. So:

  Stage 1 — SCREEN (cheap, every candidate cell, no collection): combine a battery
            of gap signals into a `gap_likelihood`. → this module.
  Stage 2 — CONFIRM (expensive, only high-likelihood × high-value cells): collect a
            thin sample, build a minimal pipeline, run the REAL lift benchmark
            (_repos/shared-backend-components/scripts/eval/durable_gap_harness.py + the lift gate). Sample → confirm
            → scale. Only confirmed gaps earn deep-collection budget.

THE SAFEGUARD (do not skip): if you detect gaps by asking the model where it's
weak, you let the model draw the map again. Model-introspection (hedging,
disagreement) only catches KNOWN unknowns — places the model knows it's unsure.
It is structurally BLIND to CONFIDENT unknowns: things it never saw and will
answer about with total fluency and zero hedge — often the highest-value tier-4
gaps. So the weights below lean hard on MODEL-INDEPENDENT signals (corpus/index
density, source tier, regulatory velocity, query-miss logs), with the
confident-hallucination probe as the bridge. The model tells you where it knows
it's weak; only the external world tells you where it's confidently blind.

Two disciplines: a spike is model- and time-relative (re-run each model
generation → decay_signal), and you must probe the FRONTIER model your buyer would
use, never a weak open model (or everything looks like a gap).
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Signal weights. MODEL-INDEPENDENT signals dominate by design (see THE SAFEGUARD).
# confident_hallucination is the bridge: model-derived but catches confident
# unknowns, so it is weighted near the model-independent tier.
W_CORPUS_DENSITY_GAP = 1.6    # model-independent: sparse/non-English/PDF/login-walled text
W_QUERY_MISS_DEMAND = 1.4     # model-independent: registry questions we couldn't answer (purest)
W_SOURCE_TIER_GAP = 1.2       # model-independent: high retrievability tier = low training exposure
W_REGULATORY_VELOCITY = 1.2   # model-independent: fast-changing cells go stale in any snapshot
W_CONFIDENT_HALLUCINATION = 1.3  # BRIDGE: confidently-wrong on a verifiable artifact = high-value gap
W_CROSS_MODEL_DISAGREEMENT = 0.6  # model-dependent: known unknowns only
W_HEDGE_RATE = 0.5            # model-dependent: known unknowns only
W_RECENCY_GAP = 0.6           # model-dependent: latest-known issuance vs real cadence

SCREEN_THRESHOLD = 0.5        # gap_likelihood at/above which a cell goes to Stage-2 confirm

_MODEL_INDEPENDENT = ("corpus_density_gap", "query_miss_demand", "source_tier_gap", "regulatory_velocity")
_BRIDGE = ("confident_hallucination",)
_MODEL_DEPENDENT = ("cross_model_disagreement", "hedge_rate", "recency_gap")
_WEIGHT = {
    "corpus_density_gap": W_CORPUS_DENSITY_GAP,
    "query_miss_demand": W_QUERY_MISS_DEMAND,
    "source_tier_gap": W_SOURCE_TIER_GAP,
    "regulatory_velocity": W_REGULATORY_VELOCITY,
    "confident_hallucination": W_CONFIDENT_HALLUCINATION,
    "cross_model_disagreement": W_CROSS_MODEL_DISAGREEMENT,
    "hedge_rate": W_HEDGE_RATE,
    "recency_gap": W_RECENCY_GAP,
}


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


@dataclass
class GapSignals:
    """All 0..1 (higher = more gap-like) except query_misses (a count).

    Model-independent (lean on these): corpus_density_gap (1 − indexed-text
    density), source_tier_gap (retrievability tier normalized), regulatory_velocity,
    query_misses. Bridge: confident_hallucination (model confidently fabricated a
    verifiable artifact — a circular number, an effective date). Model-dependent
    (discount): cross_model_disagreement, hedge_rate, recency_gap — probe the
    FRONTIER model, not a weak one."""
    corpus_density_gap: float = 0.0
    source_tier_gap: float = 0.0
    regulatory_velocity: float = 0.0
    query_misses: int = 0
    confident_hallucination: float = 0.0
    cross_model_disagreement: float = 0.0
    hedge_rate: float = 0.0
    recency_gap: float = 0.0
    notes: list[str] = field(default_factory=list)

    def as_scores(self) -> dict[str, float]:
        return {
            "corpus_density_gap": _clamp01(self.corpus_density_gap),
            "query_miss_demand": _clamp01(self.query_misses / 10.0),  # 10+ misses saturates
            "source_tier_gap": _clamp01(self.source_tier_gap),
            "regulatory_velocity": _clamp01(self.regulatory_velocity),
            "confident_hallucination": _clamp01(self.confident_hallucination),
            "cross_model_disagreement": _clamp01(self.cross_model_disagreement),
            "hedge_rate": _clamp01(self.hedge_rate),
            "recency_gap": _clamp01(self.recency_gap),
        }


def screen(signals: GapSignals) -> dict:
    """Stage-1 gap-likelihood (0..1) + decision. Reports the model-independent
    share so you can SEE you're not letting the model draw the map."""
    scores = signals.as_scores()
    total_w = sum(_WEIGHT.values())
    weighted = sum(scores[k] * _WEIGHT[k] for k in scores)
    gap_likelihood = round(weighted / total_w, 4)

    def _part(keys) -> float:
        return round(sum(scores[k] * _WEIGHT[k] for k in keys) / total_w, 4)

    mi = _part(_MODEL_INDEPENDENT)
    bridge = _part(_BRIDGE)
    md = _part(_MODEL_DEPENDENT)
    return {
        "gap_likelihood": gap_likelihood,
        "decision": "confirm" if gap_likelihood >= SCREEN_THRESHOLD else "skip",
        "model_independent_component": mi,
        "bridge_component": bridge,
        "model_dependent_component": md,
        # what fraction of the verdict came from outside the model's own self-report
        "model_independent_share": round((mi + bridge) / gap_likelihood, 3) if gap_likelihood else 0.0,
        "signals": scores,
    }


def _self_test() -> int:
    # PH × AML × BSP × 2026: low/PDF/ASPX density, high tier, high velocity, query
    # misses, and the model confidently fabricates the Circular 1230 threshold.
    ph = screen(GapSignals(corpus_density_gap=0.9, source_tier_gap=0.7, regulatory_velocity=0.9,
                           query_misses=6, confident_hallucination=0.9,
                           cross_model_disagreement=0.7, hedge_rate=0.6, recency_gap=0.9))
    # France × corporate-tax basics: enormous indexed corpus, models agree → spike.
    fr = screen(GapSignals(corpus_density_gap=0.05, source_tier_gap=0.1, regulatory_velocity=0.1,
                           query_misses=0, confident_hallucination=0.05,
                           cross_model_disagreement=0.1, hedge_rate=0.05, recency_gap=0.1))
    assert ph["decision"] == "confirm" and ph["gap_likelihood"] >= SCREEN_THRESHOLD, ph
    assert fr["decision"] == "skip" and fr["gap_likelihood"] < SCREEN_THRESHOLD, fr
    assert ph["gap_likelihood"] > fr["gap_likelihood"]
    # the verdict must be majority model-INDEPENDENT (we don't let the model draw the map)
    assert ph["model_independent_share"] >= 0.5, ph
    print(f"gap_screen OK · PH confirm@{ph['gap_likelihood']} "
          f"(model-independent share {ph['model_independent_share']}) · "
          f"France skip@{fr['gap_likelihood']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_self_test())
