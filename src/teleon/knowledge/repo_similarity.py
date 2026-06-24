"""knowledge.repo_similarity — the Repository Embedding + Semantic Similarity Engine (the owner's §2).

'I need a retry system with exponential backoff and circuit breakers' -> instead of keyword match, embed the intent
and rank the closest existing repositories/packages by cosine: {tenacity, resilience4j, polly} with a confidence and
a count ('similar to N existing repositories'). This is semantic software understanding, not search.

Grounds the repo corpus in the federation's real component/package data + the embedder PLANE (best_embedder runtime;
lexical floor in proofs). serves_truth=false; equivalents are governed CANDIDATES to verify, never assertions.
"""
from __future__ import annotations

from ._vec import cosine, embed

_MATCH = 0.45  # cosine above this counts a repo as a semantic equivalent (tunable; lexical floor is conservative)
_TOP = 5


def build_repo_index(repos: list[dict], embed_fn=None) -> list[dict]:
    """repos = [{id, description}] -> embedded index. Use real federation/package records as the corpus."""
    return [{**r, "vector": embed(r.get("description", r.get("id", "")), embed_fn)} for r in repos]


def similar_repos(intent: str, index: list[dict], embed_fn=None) -> dict:
    """Rank the corpus by semantic closeness to the intent; surface equivalents + a confidence + a count."""
    qv = embed(intent, embed_fn)
    ranked = sorted(
        ({"id": r["id"], "similarity": round(cosine(qv, r["vector"]), 4),
          "description": r.get("description", "")} for r in index),
        key=lambda x: x["similarity"], reverse=True)
    equivalents = [r for r in ranked if r["similarity"] >= _MATCH]
    top = ranked[0]["similarity"] if ranked else 0.0
    return {
        "intent": intent[:120],
        "closest": ranked[:_TOP],
        "equivalent_count": len(equivalents),
        "confidence": top,
        "verdict": (f"semantically similar to {len(equivalents)} existing repositories — reuse before rebuild"
                    if equivalents else "no close existing repository — may be novel"),
        "serves_truth": False, "candidate": True,
    }


def _self_test() -> list[str]:
    fails = []

    def ck(name, ok):
        if not ok:
            fails.append(f"repo_similarity: {name}")
            print(f"  [XX] repo_similarity: {name}")

    lex = __import__("src.teleon.knowledge._vec", fromlist=["lexical_embed_fn"]).lexical_embed_fn()
    corpus = [
        {"id": "tenacity", "description": "python retrying library with exponential backoff and stop strategies"},
        {"id": "resilience4j", "description": "java fault tolerance retry circuit breaker rate limiter"},
        {"id": "polly", "description": "dotnet resilience retry circuit breaker policies"},
        {"id": "pillow", "description": "python imaging library to open manipulate and save images"},
        {"id": "fastapi", "description": "python web framework for building apis with type hints"},
    ]
    index = build_repo_index(corpus, embed_fn=lex)
    ck("index embeds every repo", len(index) == len(corpus) and all(r["vector"] for r in index))

    res = similar_repos("I need retry logic with exponential backoff and circuit breakers", index, embed_fn=lex)
    ck("retry intent surfaces a resilience repo on top", res["closest"][0]["id"] in {"tenacity", "resilience4j", "polly"})
    ck("an image library is NOT the top match for a retry intent", res["closest"][0]["id"] != "pillow")
    ck("ranking is monotonic", all(
        res["closest"][i]["similarity"] >= res["closest"][i + 1]["similarity"] for i in range(len(res["closest"]) - 1)))
    ck("reports an equivalent count", isinstance(res["equivalent_count"], int))
    ck("verdict is a governed candidate", res["serves_truth"] is False and res["candidate"])
    return fails
