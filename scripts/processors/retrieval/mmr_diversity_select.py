#!/usr/bin/env python3
"""Backs `processor/mmr-diversity-select` (process_kind ``select.mmr_diversity``).

Maximal-Marginal-Relevance selection (taxonomy step R5): greedily pick the
candidate that maximizes ``λ·relevance − (1−λ)·max-similarity-to-already-
selected`` — trading relevance against redundancy so the final top-k covers
the query instead of repeating its best paragraph k times. Similarity is a
deterministic bag-of-words cosine over candidate texts.

Contract: deterministic; side_effects=none; on_error=raise.
Inputs candidates({"id","text","score"}), lambda, k → output selected.

CLI / self-test: python3 scripts/processors/retrieval/mmr_diversity_select.py
"""
from __future__ import annotations

import json
import math
import re
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: λ=0.7 favors relevance over diversity ~2:1 — the common starting point;
#: λ=1.0 degenerates to pure relevance ranking, λ=0 to pure anti-redundancy.
DEFAULT_LAMBDA = 0.7
DEFAULT_K = 5

_TOKEN_RE = re.compile(r"[a-z0-9]+")
SCORE_DECIMALS = 6


def _vector(text: str) -> dict[str, int]:
    vec: dict[str, int] = {}
    for t in _TOKEN_RE.findall(text.lower()):
        vec[t] = vec.get(t, 0) + 1
    return vec


def _cosine(a: dict[str, int], b: dict[str, int]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(n * b.get(t, 0) for t, n in a.items())
    if dot == 0:
        return 0.0
    return dot / (math.sqrt(sum(n * n for n in a.values())) * math.sqrt(sum(n * n for n in b.values())))


def run(*, candidates: list[dict[str, Any]], lambda_: float | None = None,
        k: int = DEFAULT_K, **kwargs: Any) -> dict[str, Any]:
    """Select up to ``k`` candidates by MMR. ``lambda`` may be passed as
    ``lambda_`` or the raw manifest name via ``kwargs['lambda']``."""
    if lambda_ is None:
        lambda_ = kwargs.pop("lambda", DEFAULT_LAMBDA)
    if kwargs:
        raise TypeError(f"unexpected arguments: {sorted(kwargs)}")
    if not isinstance(candidates, list):
        raise TypeError("candidates must be a list of id/text/score dicts")
    if not isinstance(lambda_, (int, float)) or not 0.0 <= float(lambda_) <= 1.0:
        raise ValueError(f"lambda must be in [0, 1], got {lambda_!r}")
    if not isinstance(k, int) or k < 1:
        raise ValueError(f"k must be a positive int, got {k!r}")
    lam = float(lambda_)
    pool: list[dict[str, Any]] = []
    for i, c in enumerate(candidates):
        if not isinstance(c, dict) or "id" not in c or "text" not in c:
            raise ValueError(f"candidates[{i}] needs id and text")
        pool.append({"id": str(c["id"]), "text": str(c["text"]),
                     "score": float(c.get("score", 0.0)), "vec": _vector(str(c["text"]))})

    selected: list[dict[str, Any]] = []
    while pool and len(selected) < k:
        best = None
        best_val = -math.inf
        for c in pool:
            redundancy = max((_cosine(c["vec"], s["vec"]) for s in selected), default=0.0)
            val = lam * c["score"] - (1.0 - lam) * redundancy
            # Deterministic ties: higher value, then higher score, then id.
            key = (val, c["score"], c["id"])
            if best is None or key > (best_val, best["score"], best["id"]):
                best, best_val = c, val
        selected.append(best)
        pool = [c for c in pool if c["id"] != best["id"]]
    return {"selected": [{"id": s["id"], "text": s["text"], "score": s["score"],
                          "mmr_rank": i + 1} for i, s in enumerate(selected)]}


def _selftest() -> None:
    cands = [
        {"id": "a1", "text": "reg e requires provisional credit in ten business days", "score": 0.95},
        {"id": "a2", "text": "reg e requires provisional credit in ten business days exactly", "score": 0.94},
        {"id": "b", "text": "the dispute must be filed within sixty days of the statement", "score": 0.80},
        {"id": "c", "text": "liability caps differ for debit and credit cards", "score": 0.75},
    ]
    # Pure relevance (λ=1) keeps the near-duplicate pair at the top.
    rel = run(candidates=cands, k=3, **{"lambda": 1.0})["selected"]
    assert [r["id"] for r in rel][:2] == ["a1", "a2"]
    # Balanced λ kicks the near-duplicate out in favor of coverage.
    mmr = run(candidates=cands, k=3)["selected"]
    ids = [r["id"] for r in mmr]
    assert ids[0] == "a1" and "a2" not in ids[:3] or ids.index("a2") > ids.index("b")
    assert "b" in ids and "c" in ids
    # k respected; deterministic; inputs untouched; honest empty.
    assert len(run(candidates=cands, k=2)["selected"]) == 2
    snap = json.dumps(cands, sort_keys=True)
    assert json.dumps(run(candidates=cands), sort_keys=True) == json.dumps(run(candidates=cands), sort_keys=True)
    assert json.dumps(cands, sort_keys=True) == snap
    assert run(candidates=[])["selected"] == []
    # on_error=raise.
    raised = False
    try:
        run(candidates=cands, **{"lambda": 1.5})
    except ValueError:
        raised = True
    assert raised
    print(f"PASS — mmr_diversity_select: greedy MMR (default λ={DEFAULT_LAMBDA}) demotes "
          "near-duplicates for coverage, λ=1 degenerates to relevance, deterministic verified")


if __name__ == "__main__":
    _selftest()
