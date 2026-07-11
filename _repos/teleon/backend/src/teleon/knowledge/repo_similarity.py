"""knowledge.repo_similarity — the Repository Embedding + Semantic Similarity Engine (the owner's §2).

'I need a retry system with exponential backoff and circuit breakers' -> instead of keyword match, embed the intent
and rank the closest existing repositories/packages by cosine: {tenacity, resilience4j, polly} with a confidence and
a count ('similar to N existing repositories'). This is semantic software understanding, not search.

Grounds the repo corpus in the federation's real component/package data + the embedder PLANE (best_embedder runtime;
lexical floor in proofs). serves_truth=false; equivalents are governed CANDIDATES to verify, never assertions.
"""
from __future__ import annotations

from ._vec import (
    py_function_src_teleon_knowledge__vec__cosine,
    py_function_src_teleon_knowledge__vec__embed,
    py_function_src_teleon_knowledge__vec__lexical_embed_fn,
)

py_var_src_teleon_knowledge_repo_similarity___MATCH = 0.45  # cosine above this counts a repo as a semantic equivalent (tunable; lexical floor is conservative)
py_var_src_teleon_knowledge_repo_similarity___TOP = 5


def py_function_src_teleon_knowledge_repo_similarity__build_repo_index(py_arg_src_teleon_knowledge_repo_similarity__py_function_src_teleon_knowledge_repo_similarity__build_repo_index__repos: list[dict], embed_fn=None) -> list[dict]:
    """repos = [{id, description}] -> embedded index. Use real federation/package records as the corpus."""
    return [{**r, "vector": py_function_src_teleon_knowledge__vec__embed(r.get("description", r.get("id", "")), embed_fn)} for r in py_arg_src_teleon_knowledge_repo_similarity__py_function_src_teleon_knowledge_repo_similarity__build_repo_index__repos]


def py_function_src_teleon_knowledge_repo_similarity__similar_repos(py_arg_src_teleon_knowledge_repo_similarity__py_function_src_teleon_knowledge_repo_similarity__similar_repos__intent: str, py_arg_src_teleon_knowledge_repo_similarity__py_function_src_teleon_knowledge_repo_similarity__similar_repos__index: list[dict], embed_fn=None) -> dict:
    """Rank the corpus by semantic closeness to the intent; surface equivalents + a confidence + a count."""
    py_local_src_teleon_knowledge_repo_similarity__similar_repos__qv = py_function_src_teleon_knowledge__vec__embed(py_arg_src_teleon_knowledge_repo_similarity__py_function_src_teleon_knowledge_repo_similarity__similar_repos__intent, embed_fn)
    py_local_src_teleon_knowledge_repo_similarity__similar_repos__ranked = sorted(
        ({"id": r["id"], "similarity": round(py_function_src_teleon_knowledge__vec__cosine(py_local_src_teleon_knowledge_repo_similarity__similar_repos__qv, r["vector"]), 4),
          "description": r.get("description", "")} for r in py_arg_src_teleon_knowledge_repo_similarity__py_function_src_teleon_knowledge_repo_similarity__similar_repos__index),
        key=lambda py_arg_src_teleon_knowledge_repo_similarity__py_function_src_teleon_knowledge_repo_similarity__similar_repos__x: py_arg_src_teleon_knowledge_repo_similarity__py_function_src_teleon_knowledge_repo_similarity__similar_repos__x["similarity"], reverse=True)
    py_local_src_teleon_knowledge_repo_similarity__similar_repos__equivalents = [r for r in py_local_src_teleon_knowledge_repo_similarity__similar_repos__ranked if r["similarity"] >= py_var_src_teleon_knowledge_repo_similarity___MATCH]
    py_local_src_teleon_knowledge_repo_similarity__similar_repos__top = py_local_src_teleon_knowledge_repo_similarity__similar_repos__ranked[0]["similarity"] if py_local_src_teleon_knowledge_repo_similarity__similar_repos__ranked else 0.0
    return {
        "intent": py_arg_src_teleon_knowledge_repo_similarity__py_function_src_teleon_knowledge_repo_similarity__similar_repos__intent[:120],
        "closest": py_local_src_teleon_knowledge_repo_similarity__similar_repos__ranked[:py_var_src_teleon_knowledge_repo_similarity___TOP],
        "equivalent_count": len(py_local_src_teleon_knowledge_repo_similarity__similar_repos__equivalents),
        "confidence": py_local_src_teleon_knowledge_repo_similarity__similar_repos__top,
        "verdict": (f"semantically similar to {len(py_local_src_teleon_knowledge_repo_similarity__similar_repos__equivalents)} existing repositories — reuse before rebuild"
                    if py_local_src_teleon_knowledge_repo_similarity__similar_repos__equivalents else "no close existing repository — may be novel"),
        "serves_truth": False, "candidate": True,
    }


def _self_test() -> list[str]:
    py_local_src_teleon_knowledge_repo_similarity__self_test__fails = []

    def ck(py_arg_src_teleon_knowledge_repo_similarity__self_test_ck__name, py_arg_src_teleon_knowledge_repo_similarity__self_test_ck__ok):
        if not py_arg_src_teleon_knowledge_repo_similarity__self_test_ck__ok:
            py_local_src_teleon_knowledge_repo_similarity__self_test__fails.append(f"repo_similarity: {py_arg_src_teleon_knowledge_repo_similarity__self_test_ck__name}")
            print(f"  [XX] repo_similarity: {py_arg_src_teleon_knowledge_repo_similarity__self_test_ck__name}")

    py_local_src_teleon_knowledge_repo_similarity__self_test__lex = py_function_src_teleon_knowledge__vec__lexical_embed_fn()
    py_local_src_teleon_knowledge_repo_similarity__self_test__corpus = [
        {"id": "tenacity", "description": "python retrying library with exponential backoff and stop strategies"},
        {"id": "resilience4j", "description": "java fault tolerance retry circuit breaker rate limiter"},
        {"id": "polly", "description": "dotnet resilience retry circuit breaker policies"},
        {"id": "pillow", "description": "python imaging library to open manipulate and save images"},
        {"id": "fastapi", "description": "python web framework for building apis with type hints"},
    ]
    py_local_src_teleon_knowledge_repo_similarity__self_test__index = py_function_src_teleon_knowledge_repo_similarity__build_repo_index(py_local_src_teleon_knowledge_repo_similarity__self_test__corpus, embed_fn=py_local_src_teleon_knowledge_repo_similarity__self_test__lex)
    ck("index embeds every repo", len(py_local_src_teleon_knowledge_repo_similarity__self_test__index) == len(py_local_src_teleon_knowledge_repo_similarity__self_test__corpus) and all(r["vector"] for r in py_local_src_teleon_knowledge_repo_similarity__self_test__index))

    py_local_src_teleon_knowledge_repo_similarity__self_test__res = py_function_src_teleon_knowledge_repo_similarity__similar_repos("I need retry logic with exponential backoff and circuit breakers", py_local_src_teleon_knowledge_repo_similarity__self_test__index, embed_fn=py_local_src_teleon_knowledge_repo_similarity__self_test__lex)
    ck("retry intent surfaces a resilience repo on top", py_local_src_teleon_knowledge_repo_similarity__self_test__res["closest"][0]["id"] in {"tenacity", "resilience4j", "polly"})
    ck("an image library is NOT the top match for a retry intent", py_local_src_teleon_knowledge_repo_similarity__self_test__res["closest"][0]["id"] != "pillow")
    ck("ranking is monotonic", all(
        py_local_src_teleon_knowledge_repo_similarity__self_test__res["closest"][i]["similarity"] >= py_local_src_teleon_knowledge_repo_similarity__self_test__res["closest"][i + 1]["similarity"] for i in range(len(py_local_src_teleon_knowledge_repo_similarity__self_test__res["closest"]) - 1)))
    ck("reports an equivalent count", isinstance(py_local_src_teleon_knowledge_repo_similarity__self_test__res["equivalent_count"], int))
    ck("verdict is a governed candidate", py_local_src_teleon_knowledge_repo_similarity__self_test__res["serves_truth"] is False and py_local_src_teleon_knowledge_repo_similarity__self_test__res["candidate"])
    return py_local_src_teleon_knowledge_repo_similarity__self_test__fails
