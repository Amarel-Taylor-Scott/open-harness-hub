"""src.teleon.evolution.meta_learner — learn to distill cheaper + faster (the moat).

The distiller turns a capability into a deterministic fork using some strategy; THIS learns, from the
DistillationRecords that accumulate, WHICH strategy (and which inference lane) yields the most determinism/coverage
per unit of distillation COST — per capability CLASS (category x determinism band). So the next distillation of a
similar capability uses the strategy that has proven cheapest-and-effective, and the whole factory gets cheaper as
it runs. Cheaper + faster distillation than anyone else is the market-owning advantage; this is its learning loop.

Deterministic, evidence-based (it learns only from recorded outcomes, no clock/RNG) — the same shape as the
RunLedger, one level up: priors until evidence exists, then the learned best. Teleon-layer — never imports
src.baltor. A recommendation is a routing decision, never a fact.
"""
from __future__ import annotations

from src.teleon.evolution.distiller import choose_strategy

#: a class needs at least this many records before the learner trusts evidence over the prior (cold-start guard).
_MIN_OBS = 3
_BAND_EDGES = ((0.99, "direct"), (0.70, "extract"), (0.40, "partial"), (0.0, "template"))


def determinism_band(determinism_ceiling: float) -> str:
    """The determinism band ('direct'/'extract'/'partial'/'template') for a ceiling — the single source for bands."""
    dc = float(determinism_ceiling)
    return next(name for edge, name in _BAND_EDGES if dc >= edge)


def class_key(category: str, determinism_ceiling: float) -> str:
    """A capability class = category x determinism band — the grain at which a distillation strategy generalizes."""
    return f"{category}|{determinism_band(determinism_ceiling)}"


def _efficiency(rec: dict) -> float:
    """Determinism/coverage SAVING captured per unit of one-time distill COST. saving = coverage * per-call cost
    drop (model -> deterministic). Higher = a better deal; this is what the learner maximizes."""
    saving = float(rec.get("coverage", 0.0)) * (float(rec.get("per_call_cost_before", 0.0))
                                                - float(rec.get("per_call_cost_after", 0.0)))
    cost = float(rec.get("distill_cost", 0.0)) or 1e-9
    return saving / cost


class DistillationMetaLearner:
    """Accumulates DistillationRecords and recommends the cheapest-effective strategy + lane per capability class."""

    def __init__(self) -> None:
        self._recs: dict[str, list[dict]] = {}          # class_key -> records
        self._lane_ok: dict[str, dict[str, float]] = {}  # class_key -> {lane_id: min observed lane cost that succeeded}

    def record(self, rec: dict, *, lane_id: str | None = None, lane_cost: float | None = None) -> None:
        """Record one distillation outcome. A record only 'counts' as a success for learning if it was APPLIED
        (stayed within the org's confines) and produced a useful rule (covered a majority of cases)."""
        if not rec.get("category") or not rec.get("strategy"):
            raise ValueError("a distillation record needs a category and strategy")
        key = class_key(rec["category"], rec.get("determinism_ceiling", 0.0))
        self._recs.setdefault(key, []).append(rec)
        succeeded = bool(rec.get("applied")) and float(rec.get("coverage", 0.0)) >= 0.5
        if succeeded and lane_id is not None:
            prev = self._lane_ok.setdefault(key, {}).get(lane_id)
            c = float(lane_cost if lane_cost is not None else 0.0)
            if prev is None or c < prev:
                self._lane_ok[key][lane_id] = c

    def count(self, category: str, determinism_ceiling: float) -> int:
        return len(self._recs.get(class_key(category, determinism_ceiling), ()))

    def strategy_stats(self, category: str, determinism_ceiling: float) -> dict:
        """Per-strategy mean efficiency / coverage / distill_cost for a class (the learned table)."""
        recs = self._recs.get(class_key(category, determinism_ceiling), [])
        by_strat: dict[str, list[dict]] = {}
        for r in recs:
            if r.get("applied"):
                by_strat.setdefault(r["strategy"], []).append(r)
        out = {}
        for strat, rs in by_strat.items():
            n = len(rs)
            out[strat] = {"n": n, "mean_efficiency": sum(_efficiency(r) for r in rs) / n,
                          "mean_coverage": sum(float(r.get("coverage", 0.0)) for r in rs) / n,
                          "mean_distill_cost": sum(float(r.get("distill_cost", 0.0)) for r in rs) / n}
        return out

    def recommend_strategy(self, category: str, determinism_ceiling: float) -> dict:
        """The strategy to use next for this class: the learned highest-efficiency one once there is enough
        evidence (ties broken by lower distill cost, then name); otherwise the prior from choose_strategy."""
        prior = choose_strategy(determinism_ceiling)
        stats = self.strategy_stats(category, determinism_ceiling)
        total = sum(s["n"] for s in stats.values())
        if total < _MIN_OBS or not stats:
            return {"strategy": prior, "source": "prior", "evidence": total}
        best = max(stats.items(), key=lambda kv: (kv[1]["mean_efficiency"], -kv[1]["mean_distill_cost"],
                                                   _neg(kv[0])))
        return {"strategy": best[0], "source": "learned", "evidence": total,
                "mean_efficiency": round(best[1]["mean_efficiency"], 6)}

    def recommend_lane(self, category: str, determinism_ceiling: float) -> dict:
        """The cheapest INFERENCE LANE observed to successfully distill this class — so distillation runs on the
        cheapest model that proved sufficient (a costly frontier lane is not used where a cheap local one works).
        Returns the prior (no recommendation) until a lane has a recorded success for the class."""
        key = class_key(category, determinism_ceiling)
        ok = self._lane_ok.get(key, {})
        if not ok:
            return {"lane_id": None, "source": "prior"}
        cheapest = min(ok.items(), key=lambda kv: (kv[1], kv[0]))
        return {"lane_id": cheapest[0], "lane_cost": cheapest[1], "source": "learned"}

    def efficiency_summary(self) -> dict:
        """Across all classes with enough evidence: the learned best strategy + its efficiency, and the distill
        cost the learner SAVES by choosing the best strategy over the most-expensive-seen one (the moat metric)."""
        classes, saved = {}, 0.0
        for key, recs in self._recs.items():
            stats = {}
            for r in recs:
                if r.get("applied"):
                    stats.setdefault(r["strategy"], []).append(r)
            if sum(len(v) for v in stats.values()) < _MIN_OBS or not stats:
                continue
            means = {s: sum(_efficiency(r) for r in rs) / len(rs) for s, rs in stats.items()}
            costs = {s: sum(float(r.get("distill_cost", 0.0)) for r in rs) / len(rs) for s, rs in stats.items()}
            best = max(means, key=lambda s: (means[s], -costs[s], _neg(s)))
            classes[key] = {"best_strategy": best, "mean_efficiency": round(means[best], 6),
                            "best_distill_cost": round(costs[best], 6)}
            saved += max(costs.values()) - costs[best]
        return {"classes_learned": len(classes), "classes": classes, "distill_cost_saved_vs_worst": round(saved, 6)}


def _neg(s: str) -> tuple:
    """Tie-break key: after maximizing, the LOWEST name wins (deterministic)."""
    return tuple(-ord(c) for c in s)
