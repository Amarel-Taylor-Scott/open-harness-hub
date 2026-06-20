#!/usr/bin/env python3
"""Backs `processor/rrf-fusion` (process_kind ``rerank.reciprocal_rank_fusion``).

Reciprocal-Rank Fusion: merge multiple retrieval legs by rank position alone
(score = Σ 1/(k + rank)), with k≈60 — no score normalization, so BM25 and
cosine legs with incompatible scales fuse robustly and no labeled data is
needed. The default fusion of the hybrid pipeline (taxonomy step R3).

Contract: deterministic; side_effects=none; on_error=raise.
Inputs ranked_lists (list of lists of {"id",...} or plain ids), k → fused_list.

CLI / self-test: python3 scripts/processors/retrieval/rrf_fusion.py
"""
from __future__ import annotations

import json
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: The canonical RRF constant from Cormack et al. — dampens the head so one
#: leg's #1 cannot dominate every other leg's consensus.
DEFAULT_RRF_K = 60

SCORE_DECIMALS = 6


def _entry_id(entry: Any) -> str:
    if isinstance(entry, dict):
        if "id" not in entry:
            raise ValueError("ranked entries must carry an id")
        return str(entry["id"])
    return str(entry)


def run(*, ranked_lists: list[list[Any]], k: int = DEFAULT_RRF_K) -> dict[str, Any]:
    """Fuse ``ranked_lists`` (best-first) by reciprocal rank into one list."""
    if not isinstance(ranked_lists, list) or not all(isinstance(l, list) for l in ranked_lists):
        raise TypeError("ranked_lists must be a list of ranked lists")
    if not isinstance(k, int) or k < 1:
        raise ValueError(f"k must be a positive int, got {k!r}")
    scores: dict[str, float] = {}
    appears: dict[str, int] = {}
    payload: dict[str, Any] = {}
    for leg in ranked_lists:
        for rank, entry in enumerate(leg, start=1):
            eid = _entry_id(entry)
            scores[eid] = scores.get(eid, 0.0) + 1.0 / (k + rank)
            appears[eid] = appears.get(eid, 0) + 1
            if isinstance(entry, dict):
                payload.setdefault(eid, entry)
    fused = [{"id": eid, "rrf_score": round(s, SCORE_DECIMALS), "legs": appears[eid],
              **({"entry": payload[eid]} if eid in payload else {})}
             for eid, s in scores.items()]
    fused.sort(key=lambda r: (-r["rrf_score"], r["id"]))  # deterministic ties
    return {"fused_list": fused}


def _selftest() -> None:
    bm25_leg = ["a", "b", "c", "d"]                      # plain ids work
    dense_leg = [{"id": "c", "score": 0.93}, {"id": "a", "score": 0.91}, {"id": "e", "score": 0.5}]
    out = run(ranked_lists=[bm25_leg, dense_leg])["fused_list"]
    ids = [r["id"] for r in out]
    # Consensus wins: 'a' (1st + 2nd) and 'c' (3rd + 1st) beat single-leg items.
    assert set(ids[:2]) == {"a", "c"}
    assert out[0]["legs"] == 2
    # Exact RRF arithmetic at k=60.
    a_row = next(r for r in out if r["id"] == "a")
    assert a_row["rrf_score"] == round(1 / 61 + 1 / 62, SCORE_DECIMALS)
    # No score normalization: incompatible raw scales never matter (ranks only).
    huge = [{"id": "a", "score": 9999.0}, {"id": "z", "score": 9000.0}]
    tiny = [{"id": "z", "score": 0.002}, {"id": "a", "score": 0.001}]
    sym = run(ranked_lists=[huge, tiny])["fused_list"]
    assert sym[0]["rrf_score"] == sym[1]["rrf_score"]  # perfectly symmetric ranks tie
    assert [r["id"] for r in sym] == ["a", "z"]        # tie broken deterministically by id
    # Dict payloads ride along.
    assert next(r for r in out if r["id"] == "e")["entry"]["score"] == 0.5
    # Deterministic; honest empty; on_error=raise.
    assert run(ranked_lists=[])["fused_list"] == []
    x = json.dumps(run(ranked_lists=[bm25_leg, dense_leg]), sort_keys=True)
    assert x == json.dumps(run(ranked_lists=[bm25_leg, dense_leg]), sort_keys=True)
    raised = False
    try:
        run(ranked_lists=[["ok"]], k=0)
    except ValueError:
        raised = True
    assert raised
    print(f"PASS — rrf_fusion: rank-only fusion at k={DEFAULT_RRF_K} (scale-free, "
          "consensus wins, exact arithmetic, deterministic ties) verified")


if __name__ == "__main__":
    _selftest()
