#!/usr/bin/env python3
"""Backs `processor/cross-encoder-reranker` (process_kind ``rerank.cross_encoder``).

Cross-encoder rescoring (taxonomy step R3): jointly score (query, document)
pairs over the fused top candidates and keep the precision head — the single
highest-precision lever in the retrieval pipeline; cost bounded by candidate
count, not corpus size.

The scorer is INJECTED (any ``(query, text) -> float``; production wires an
open-weight cross-encoder like bge-reranker-v2-m3 behind it). Without one,
a deterministic lexical-overlap proxy scores instead and every result SAYS
SO (``scorer`` field) — a proxy never masquerades as a model (the repo's
placeholder law).

Contract: side_effects=read; on_error=raise; deterministic with the proxy
(the manifest allows non-deterministic learned scorers).

Inputs query, candidates({"id","text"}), top_n → output reranked.

CLI / self-test: python3 scripts/processors/retrieval/cross_encoder_reranker.py
"""
from __future__ import annotations

import json
import math
import re
from typing import Any, Callable

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: Keep the precision head: rerank the fused 50–100, keep ~5 (manifest guidance).
DEFAULT_TOP_N = 5

#: Labels for the scorer provenance (single definition; tests read them).
PROXY_SCORER = "lexical-overlap-proxy (NOT a cross-encoder — inject one via scorer=)"
INJECTED_SCORER = "injected-cross-encoder"

STOPWORDS = frozenset({"a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
                       "how", "in", "is", "it", "of", "on", "or", "that", "the", "this",
                       "to", "was", "what", "when", "where", "which", "who", "why", "with"})
_TOKEN_RE = re.compile(r"[a-z0-9]+")
SCORE_DECIMALS = 6


def _proxy_score(query: str, text: str) -> float:
    """Deterministic stand-in: salient-term overlap, length-normalized."""
    q = {t for t in _TOKEN_RE.findall(query.lower()) if t not in STOPWORDS}
    d = {t for t in _TOKEN_RE.findall(text.lower()) if t not in STOPWORDS}
    if not q or not d:
        return 0.0
    return len(q & d) / math.sqrt(len(q) * len(d))


def run(*, query: str, candidates: list[dict[str, Any]], top_n: int = DEFAULT_TOP_N,
        scorer: Callable[[str, str], float] | None = None) -> dict[str, Any]:
    """Rescore every (query, candidate) pair; keep the top_n precision head."""
    if not isinstance(query, str):
        raise TypeError(f"query must be str, got {type(query).__name__}")
    if not isinstance(candidates, list):
        raise TypeError("candidates must be a list of id/text dicts")
    if not isinstance(top_n, int) or top_n < 1:
        raise ValueError(f"top_n must be a positive int, got {top_n!r}")
    score = scorer if scorer is not None else _proxy_score
    rows: list[dict[str, Any]] = []
    for i, c in enumerate(candidates):
        if not isinstance(c, dict) or "id" not in c or "text" not in c:
            raise ValueError(f"candidates[{i}] needs id and text")
        s = float(score(query, str(c["text"])))
        rows.append({"id": str(c["id"]), "text": str(c["text"]),
                     "rerank_score": round(s, SCORE_DECIMALS),
                     "retriever_score": c.get("score")})
    rows.sort(key=lambda r: (-r["rerank_score"], r["id"]))  # deterministic ties
    return {"reranked": {"results": rows[:top_n],
                         "candidates_scored": len(rows),
                         "scorer": INJECTED_SCORER if scorer is not None else PROXY_SCORER,
                         "is_proxy": scorer is None}}


def _selftest() -> None:
    cands = [
        {"id": "noise", "text": "general banking overview and history", "score": 0.9},
        {"id": "exact", "text": "provisional credit must arrive within ten business days of the notice", "score": 0.4},
        {"id": "near", "text": "the bank investigates errors and may credit the account", "score": 0.7},
    ]
    # The proxy rescores by joint relevance — the exact answer overtakes the
    # retriever's higher-scored generic doc — and HONESTLY labels itself.
    out = run(query="how fast must provisional credit arrive?", candidates=cands)["reranked"]
    assert out["results"][0]["id"] == "exact"
    assert out["is_proxy"] is True and "NOT a cross-encoder" in out["scorer"]
    # Retriever scores ride along for telemetry, never drive the order.
    assert out["results"][0]["retriever_score"] == 0.4
    # Injected scorer wins authority and flips the label.
    def model(query: str, text: str) -> float:
        return 1.0 if "investigates" in text else 0.1
    inj = run(query="anything", candidates=cands, scorer=model)["reranked"]
    assert inj["results"][0]["id"] == "near" and inj["is_proxy"] is False
    assert inj["scorer"] == INJECTED_SCORER
    # top_n respected; deterministic; inputs untouched; honest empty.
    assert len(run(query="credit", candidates=cands, top_n=2)["reranked"]["results"]) == 2
    snap = json.dumps(cands, sort_keys=True)
    assert json.dumps(run(query="credit", candidates=cands), sort_keys=True) == \
           json.dumps(run(query="credit", candidates=cands), sort_keys=True)
    assert json.dumps(cands, sort_keys=True) == snap
    assert run(query="x", candidates=[])["reranked"]["results"] == []
    # on_error=raise.
    raised = False
    try:
        run(query="x", candidates=[{"id": "a"}])
    except ValueError:
        raised = True
    assert raised
    print(f"PASS — cross_encoder_reranker: joint (query,doc) rescoring keeps the top-{DEFAULT_TOP_N} "
          "precision head, injected scorer behind one seam, proxy honestly labeled, "
          "deterministic verified")


if __name__ == "__main__":
    _selftest()
