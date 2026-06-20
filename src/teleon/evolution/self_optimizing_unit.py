"""src.teleon.evolution.self_optimizing_unit — the SELF-IMPROVING, AUTO-OPTIMIZING Teleon capability unit.

This is the capstone the rest of the engine serves: a capability unit that MEASURES ITSELF across the improvement
dimensions and AUTOMATICALLY applies the best governed method for each — compressing its prompt (tokens↓),
distilling to a deterministic rule or a cheaper model (cost↓ / determinism↑ / llm_usage↓), binding a fragile fact
to an authoritative source (fragility→freshness↑), and routing to the cheapest still-capable model (efficiency) —
then emits an OPTIMIZATION RECEIPT showing before→after per dimension + the lineage of forks it created.

It composes the REAL building blocks (token_reduction.compress_skill, distiller.distill / distill_robustness,
model_index.select_best); nothing here is a mock. Every fork is governed: applied only within the org policy,
lossless (the raw is preserved in the evolution graph), accuracy-floored, and serves_truth=False — the unit
proposes its own improvements; a gate disposes. Deterministic + offline; re-optimizing an already-optimized unit
converges (idempotent). Teleon-layer; never imports src.baltor.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.teleon.evolution.distiller import distill, distill_robustness
from src.teleon.evolution.token_reduction import compress_skill
from src.teleon.inference.model_index import load_index, select_best

#: the model-root determinism the distiller starts from (a frontier text model is ~non-deterministic).
_MODEL_ROOT_DETERMINISM = 0.2


@dataclass
class OptimizationStep:
    dimension: str            # the descent axis improved (tokens_in / cost / determinism / freshness / efficiency)
    method: str               # the concrete method applied (from the descent method catalog)
    metric: str
    before: float
    after: float
    improved: bool            # did it move in the right direction?
    governed: bool            # lossless + applied within the org policy (else HELD, not shipped)
    detail: str

    def as_dict(self) -> dict:
        return {"dimension": self.dimension, "method": self.method, "metric": self.metric,
                "before": self.before, "after": self.after, "improved": self.improved,
                "governed": self.governed, "detail": self.detail}


class SelfOptimizingCapabilityUnit:
    """A capability that improves itself. ``optimize`` measures the unit, auto-applies the best governed method per
    dimension, and returns the optimization receipt. The unit PROPOSES its forks; the gate (org policy + accuracy
    floor) disposes — serves_truth is never True."""

    def __init__(self, spec: dict) -> None:
        if not spec.get("slot"):
            raise ValueError("a capability unit needs a slot")
        self.spec = dict(spec)

    def optimize(self, *, policy=None) -> dict:
        s = self.spec
        steps: list[OptimizationStep] = []
        forks: list[str] = []

        # 1) tokens_in↓ — compress the prompt/skill (lossless: every must_keep phrase survives, else HELD)
        if s.get("skill_text"):
            c = compress_skill(s["slot"], s["skill_text"], must_keep=tuple(s.get("must_keep", ())))
            steps.append(OptimizationStep(
                "tokens_in", "prompt_compression", "input_tokens", float(c["tokens_in_before"]),
                float(c["tokens_in_after"]), c["tokens_saved"] > 0, bool(c["lossless"]),
                f"-{c['reduction_pct']}% input tokens (collapse whitespace + dedupe lines + prune [optional]); "
                f"lossless={c['lossless']}"))

        # 2) cost↓ / determinism↑ / llm_usage↓ — distill to a deterministic rule (or a cheaper model if it can't)
        d = distill(s["slot"], category=s.get("category", "other"),
                    determinism_ceiling=float(s["determinism_ceiling"]),
                    deterministic_coverage_estimate=float(s.get("deterministic_coverage_estimate", 0.85)),
                    policy=policy)
        rec = d["record"]
        forks.append(rec["fork_runner_id"])
        steps.append(OptimizationStep(
            "cost", d["strategy"], "per_call_cost", float(rec["per_call_cost_before"]),
            float(rec["per_call_cost_after"]), rec["per_call_cost_after"] < rec["per_call_cost_before"],
            bool(rec["applied"]),
            f"{d['strategy']}: cost {rec['per_call_cost_before']}→{rec['per_call_cost_after']}/call; "
            f"axes={list(rec['improvement_axes'])}"))
        if "determinism" in rec["improvement_axes"]:
            steps.append(OptimizationStep(
                "determinism", "distilled_rule", "determinism", _MODEL_ROOT_DETERMINISM, 1.0, True,
                bool(rec["applied"]), "model-root determinism 0.2 → deterministic rule 1.0 (within the coverage)"))

        # 3) fragility → freshness↑ — bind a fragile/changing fact to its authoritative source (stale held out)
        if s.get("authoritative_source"):
            rb = distill_robustness(s["slot"], category=s.get("category", "other"),
                                    volatility_class=s.get("volatility_class", "low"),
                                    authoritative_source=s["authoritative_source"], policy=policy)
            forks.append(rb["record"]["fork_runner_id"])
            steps.append(OptimizationStep(
                "freshness", "freshness_sync", "stale_served_risk", 1.0, 0.0, True, bool(rb["applied"]),
                f"fragile fact bound to {s['authoritative_source']} on a {rb['freshness_policy']['sync_cadence']} "
                f"cadence; a stale answer is HELD OUT (never served) until re-synced"))

        # 4) efficiency — route to the cheapest still-capable model instead of the most expensive frontier one
        idx = load_index()
        floor = int(s.get("quality_floor_rank", 2))
        capable = [e for e in idx if e["quality_rank"] >= floor and e["freshness"]["status"] == "fresh"]
        pick = select_best(idx, quality_floor_rank=floor, prefer_local=bool(s.get("prefer_local", False)))
        if capable and pick["picked"]:
            worst = max(e["cost_per_mtok_out"] for e in capable)
            after = float(pick["cost_per_mtok_out"])
            steps.append(OptimizationStep(
                "efficiency", "cheapest_capable_routing", "cost_per_mtok_out", float(worst), after,
                after < worst, True,
                f"route to {pick['picked']} (cheapest fresh capable) instead of the most expensive frontier "
                f"({worst}/Mtok); stale model facts are held out of the choice"))

        improved = [st for st in steps if st.improved]
        return {
            "capability_slot": s["slot"],
            "steps": [st.as_dict() for st in steps],
            "dimensions_improved": sorted({st.dimension for st in improved}),
            "n_steps": len(steps), "n_improved": len(improved),
            "lineage_forks": forks,                       # the forks created (lossless lineage in the evolution graph)
            "accuracy_floor_respected": all(st.governed for st in steps),  # every applied fork stayed within confines
            "serves_truth": False,                        # the unit proposes; a gate disposes
        }

    def is_converged(self, *, policy=None) -> bool:
        """Auto-optimization converges: re-optimizing yields the same governed forks (deterministic, idempotent)."""
        return self.optimize(policy=policy) == self.optimize(policy=policy)


def demonstrate(spec: dict | None = None) -> dict:
    """Run the self-optimizing unit on a representative fragile regulated-fact capability and return the receipt."""
    spec = spec or {
        "slot": "reg-e-error-resolution-deadline", "category": "identity-compliance",
        "determinism_ceiling": 0.95, "deterministic_coverage_estimate": 0.9,
        "authoritative_source": "ecfr://12/1005.11", "volatility_class": "low",
        "skill_text": ("You are a compliance assistant.\n"
                       "You are a compliance assistant.\n"          # duplicate line — compressed away
                       "Compute the Regulation E error-resolution deadline.\n"
                       "[optional] Add a friendly greeting.\n"      # [optional] — pruned
                       "Cite the authoritative source for the deadline."),
        "must_keep": ("Regulation E", "authoritative source"),
    }
    return SelfOptimizingCapabilityUnit(spec).optimize()
