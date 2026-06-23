"""beam — System 5 (multi-candidate composition). Turn "one DAG" into "the best of many" WITHOUT executing them: VERIFY
each candidate (type-compatible + satisfiable + dry-run), SIMULATE each (cheap economic scoring, no real calls), and keep
the top `beam_width` by the cost model. The simulator (System 12) is what makes this affordable — only the winner is
built/run. Honest finding baked in: classical synthesis scales poorly with library size, so the candidates come from
templates + a few LLM samples + variants, not an exhaustive search; we accept the best verified candidate over the
threshold, not a global optimum. serves_truth=false.
"""
from __future__ import annotations

from src.teleon.economics import simulator as SIM
from src.teleon.inference.preference_profile import PreferenceProfile, cost_first
from src.teleon.synthesis.dag_contract import verify_buildable_dag


def rank_candidates(candidates: list, *, profile: PreferenceProfile | None = None, require_verified: bool = True,
                    shard: str = "000") -> list:
    """candidates: [{nodes, edges, ...}]. VERIFY each, then SIMULATE-rank the survivors. Returns
    [{candidate, estimate, score, verdict}] best (lowest simulated score) first. require_verified drops any candidate
    that isn't verified_working (never rank a DAG that won't run)."""
    profile = profile or cost_first()
    survivors = []
    for c in candidates:
        verdict = verify_buildable_dag(c.get("nodes", []), c.get("edges") or [])
        if require_verified and not verdict["verified_working"]:
            continue
        survivors.append((c, verdict))
    if not survivors:
        return []
    ranked = SIM.rank_candidates([c for c, _ in survivors], profile=profile, shard=shard)   # [(index, estimate, score)]
    return [{"candidate": survivors[i][0], "verdict": survivors[i][1], "estimate": est, "score": score}
            for i, est, score in ranked]


def beam_compose(candidates: list, *, profile: PreferenceProfile | None = None, beam_width: int = 3,
                 require_verified: bool = True, shard: str = "000") -> dict:
    """Keep the top `beam_width` VERIFIED candidates by simulated cost; the best is the chosen DAG. Honest empty when
    nothing verifies. Returns {chosen, beam, n_candidates, n_verified}."""
    profile = profile or cost_first()
    ranked = rank_candidates(candidates, profile=profile, require_verified=require_verified, shard=shard)
    beam = ranked[:beam_width]
    return {"chosen": (beam[0]["candidate"] if beam else None), "beam": beam, "n_candidates": len(candidates),
            "n_verified": len(ranked), "serves_truth": False}
