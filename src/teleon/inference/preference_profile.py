"""src.teleon.inference.preference_profile — the USER's definition of "efficient", made multi-objective.

A Teleon capability unit turns a plain-text human capability into a more bounded + more EFFICIENT system. "Efficient"
is not one number: it is the user's weighted trade-off across cost, speed/latency, token burn, determinism, and
freshness, plus HARD constraints (e.g. "never above 200ms", "must be fully deterministic", "stay under $0.01"). This
generalizes the single-objective selector (cheapest / most_deterministic) into a user-set preference profile: among the
candidate bounded implementations, choose the one that best fits the user's weights AND meets every hard constraint —
or report honestly that none does. Pure + deterministic; serves_truth=false; Teleon-layer (never imports baltor).
"""
from __future__ import annotations

from dataclasses import dataclass, field

#: each objective + whether lower or higher is better. cost/latency/token_burn: minimize; determinism/freshness: maximize.
OBJECTIVES = ("cost", "latency_ms", "token_burn", "determinism", "freshness")
_MAXIMIZE = ("determinism", "freshness")   # the rest are minimized


@dataclass(frozen=True)
class PreferenceProfile:
    """User-set weights (relative importance per objective) + optional hard constraints. Weights are normalized; a
    missing weight defaults to 0 (the user doesn't care about that objective)."""
    weights: dict = field(default_factory=lambda: {o: 1.0 for o in OBJECTIVES})
    max_cost: float | None = None
    max_latency_ms: float | None = None
    max_token_burn: int | None = None
    min_determinism: float | None = None
    min_freshness: float | None = None

    def normalized_weights(self) -> dict:
        w = {o: float(self.weights.get(o, 0.0)) for o in OBJECTIVES}
        total = sum(w.values())
        return {o: (w[o] / total if total else 0.0) for o in OBJECTIVES}

    def unmet_constraints(self, cand: dict) -> list[str]:
        out = []
        if self.max_cost is not None and cand.get("cost", 0.0) > self.max_cost:
            out.append(f"cost {cand.get('cost')} > max {self.max_cost}")
        if self.max_latency_ms is not None and cand.get("latency_ms", 0) > self.max_latency_ms:
            out.append(f"latency {cand.get('latency_ms')}ms > max {self.max_latency_ms}ms")
        if self.max_token_burn is not None and cand.get("token_burn", 0) > self.max_token_burn:
            out.append(f"token_burn {cand.get('token_burn')} > max {self.max_token_burn}")
        if self.min_determinism is not None and cand.get("determinism", 0.0) < self.min_determinism:
            out.append(f"determinism {cand.get('determinism')} < min {self.min_determinism}")
        if self.min_freshness is not None and cand.get("freshness", 0.0) < self.min_freshness:
            out.append(f"freshness {cand.get('freshness')} < min {self.min_freshness}")
        return out


def _normalize(values: list[float]) -> dict:
    """Min-max normalize a column to 0..1 so weights across objectives are comparable; all-equal -> all 0."""
    lo, hi = min(values), max(values)
    span = hi - lo
    return {i: ((v - lo) / span if span else 0.0) for i, v in enumerate(values)}


def score_candidates(candidates: list[dict], profile: PreferenceProfile) -> list[float]:
    """Weighted composite score per candidate (LOWER is better). Each objective is min-max normalized across the set;
    maximize-objectives are inverted so lower-composite always means better-on-the-user's-weights."""
    w = profile.normalized_weights()
    cols = {o: _normalize([float(c.get(o, 0.0)) for c in candidates]) for o in OBJECTIVES}
    scores = []
    for i in range(len(candidates)):
        s = 0.0
        for o in OBJECTIVES:
            norm = cols[o][i]
            if o in _MAXIMIZE:
                norm = 1.0 - norm   # higher determinism/freshness -> lower (better) composite
            s += w[o] * norm
        scores.append(round(s, 6))
    return scores


def choose(candidates: list[dict], profile: PreferenceProfile) -> dict:
    """Choose the bounded implementation that meets EVERY hard constraint with the best weighted score. If none meets
    the constraints, return chosen=None with the reason — never fabricate a pick. Ties break by lower cost then id."""
    eligible = [(i, c) for i, c in enumerate(candidates) if not profile.unmet_constraints(c)]
    if not eligible:
        viol = {c.get("id", i): profile.unmet_constraints(c) for i, c in enumerate(candidates)}
        return {"chosen": None, "reason": "no candidate meets the hard constraints", "violations": viol, "serves_truth": False}
    scores = score_candidates(candidates, profile)
    best = min(eligible, key=lambda ic: (scores[ic[0]], ic[1].get("cost", 0.0), str(ic[1].get("id", ic[0]))))
    i, c = best
    return {"chosen": c.get("id", i), "candidate": c, "score": scores[i],
            "weights": profile.normalized_weights(), "serves_truth": False}


#: named starting points — but the POINT is that the user sets their own weights/constraints.
def cost_first() -> PreferenceProfile:
    return PreferenceProfile(weights={"cost": 1.0})


def latency_first() -> PreferenceProfile:
    return PreferenceProfile(weights={"latency_ms": 1.0})


def token_thrifty() -> PreferenceProfile:
    return PreferenceProfile(weights={"token_burn": 1.0})


def determinism_required() -> PreferenceProfile:
    return PreferenceProfile(weights={"determinism": 0.6, "cost": 0.4}, min_determinism=1.0)


def balanced() -> PreferenceProfile:
    return PreferenceProfile(weights={o: 1.0 for o in OBJECTIVES})
