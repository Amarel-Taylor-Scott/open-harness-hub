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
from src.teleon.synthesis.dag_contract import py_function_src_teleon_synthesis_dag_contract__verify_buildable_dag


def py_function_src_teleon_synthesis_beam__rank_candidates(py_arg_src_teleon_synthesis_beam__rank_candidates__candidates: list, *, profile: PreferenceProfile | None = None, require_verified: bool = True,
                    shard: str = "000") -> list:
    """candidates: [{nodes, edges, ...}]. VERIFY each, then SIMULATE-rank the survivors. Returns
    [{candidate, estimate, score, verdict}] best (lowest simulated score) first. require_verified drops any candidate
    that isn't verified_working (never rank a DAG that won't run)."""
    profile = profile or cost_first()
    py_local_src_teleon_synthesis_beam__rank_candidates__survivors = []
    for py_local_src_teleon_synthesis_beam__rank_candidates__c in py_arg_src_teleon_synthesis_beam__rank_candidates__candidates:
        py_local_src_teleon_synthesis_beam__rank_candidates__verdict = py_function_src_teleon_synthesis_dag_contract__verify_buildable_dag(py_local_src_teleon_synthesis_beam__rank_candidates__c.get("nodes", []), py_local_src_teleon_synthesis_beam__rank_candidates__c.get("edges") or [])
        if require_verified and not py_local_src_teleon_synthesis_beam__rank_candidates__verdict["verified_working"]:
            continue
        py_local_src_teleon_synthesis_beam__rank_candidates__survivors.append((py_local_src_teleon_synthesis_beam__rank_candidates__c, py_local_src_teleon_synthesis_beam__rank_candidates__verdict))
    if not py_local_src_teleon_synthesis_beam__rank_candidates__survivors:
        return []
    py_local_src_teleon_synthesis_beam__rank_candidates__ranked = SIM.rank_candidates([py_local_src_teleon_synthesis_beam__rank_candidates__c for py_local_src_teleon_synthesis_beam__rank_candidates__c, _ in py_local_src_teleon_synthesis_beam__rank_candidates__survivors], profile=profile, shard=shard)   # [(index, estimate, score)]
    return [{"candidate": py_local_src_teleon_synthesis_beam__rank_candidates__survivors[i][0], "verdict": py_local_src_teleon_synthesis_beam__rank_candidates__survivors[i][1], "estimate": est, "score": score}
            for i, est, score in py_local_src_teleon_synthesis_beam__rank_candidates__ranked]


def py_function_src_teleon_synthesis_beam__beam_compose(py_arg_src_teleon_synthesis_beam__beam_compose__candidates: list, *, profile: PreferenceProfile | None = None, beam_width: int = 3,
                 py_arg_src_teleon_synthesis_beam__beam_compose__require_verified: bool = True, shard: str = "000") -> dict:
    """Keep the top `beam_width` VERIFIED candidates by simulated cost; the best is the chosen DAG. Honest empty when
    nothing verifies. Returns {chosen, beam, n_candidates, n_verified}."""
    profile = profile or cost_first()
    py_local_src_teleon_synthesis_beam__beam_compose__ranked = py_function_src_teleon_synthesis_beam__rank_candidates(py_arg_src_teleon_synthesis_beam__beam_compose__candidates, profile=profile, require_verified=py_arg_src_teleon_synthesis_beam__beam_compose__require_verified, shard=shard)
    py_local_src_teleon_synthesis_beam__beam_compose__beam = py_local_src_teleon_synthesis_beam__beam_compose__ranked[:beam_width]
    return {"chosen": (py_local_src_teleon_synthesis_beam__beam_compose__beam[0]["candidate"] if py_local_src_teleon_synthesis_beam__beam_compose__beam else None), "beam": py_local_src_teleon_synthesis_beam__beam_compose__beam, "n_candidates": len(py_arg_src_teleon_synthesis_beam__beam_compose__candidates),
            "n_verified": len(py_local_src_teleon_synthesis_beam__beam_compose__ranked), "serves_truth": False}
