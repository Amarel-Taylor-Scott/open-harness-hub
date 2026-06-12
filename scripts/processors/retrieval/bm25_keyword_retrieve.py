#!/usr/bin/env python3
"""Backs `processor/bm25-keyword-retrieve` (process_kind ``retrieve.lexical_bm25``).

Okapi BM25 lexical retrieval — the hybrid leg that guarantees exact
surface-form matching for rare terms, codes, identifiers and named entities,
where embeddings over-generalize. Zero inference; fully interpretable; the
score of every hit decomposes into per-term contributions.

Contract: deterministic; side_effects=read; on_error=raise.
Inputs query(str), corpus(list of {"id","text"}), top_k → output candidates.

CLI / self-test: python3 scripts/processors/retrieval/bm25_keyword_retrieve.py
"""
from __future__ import annotations

import json
import math
import re
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: Okapi BM25 parameters — the canonical defaults from Robertson & Zaragoza:
#: k1 controls term-frequency saturation, b controls length normalization.
BM25_K1 = 1.5
BM25_B = 0.75

DEFAULT_TOP_K = 10

#: Tokenizer: runs of letters/digits, lowercased (single site, both sides).
_TOKEN_RE = re.compile(r"[a-z0-9]+")

SCORE_DECIMALS = 6


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def run(*, query: str, corpus: list[dict[str, Any]], top_k: int = DEFAULT_TOP_K) -> dict[str, Any]:
    """Score ``corpus`` against ``query`` with Okapi BM25; return the top_k candidates."""
    if not isinstance(query, str):
        raise TypeError(f"query must be str, got {type(query).__name__}")
    if not isinstance(corpus, list):
        raise TypeError(f"corpus must be a list of id/text dicts, got {type(corpus).__name__}")
    if not isinstance(top_k, int) or top_k < 1:
        raise ValueError(f"top_k must be a positive int, got {top_k!r}")
    docs: list[tuple[str, list[str], str]] = []
    for i, d in enumerate(corpus):
        if not isinstance(d, dict) or "id" not in d or "text" not in d:
            raise ValueError(f"corpus[{i}] needs id and text")
        docs.append((str(d["id"]), _tokens(str(d["text"])), str(d["text"])))

    n = len(docs)
    avgdl = (sum(len(t) for _, t, _ in docs) / n) if n else 0.0
    df: dict[str, int] = {}
    for _, toks, _ in docs:
        for t in set(toks):
            df[t] = df.get(t, 0) + 1

    qterms = _tokens(query)
    scored: list[dict[str, Any]] = []
    for did, toks, text in docs:
        tf: dict[str, int] = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        score = 0.0
        per_term: dict[str, float] = {}
        for t in qterms:
            if t not in tf:
                continue
            idf = math.log(1.0 + (n - df[t] + 0.5) / (df[t] + 0.5))
            denom = tf[t] + BM25_K1 * (1 - BM25_B + BM25_B * len(toks) / avgdl)
            contrib = idf * tf[t] * (BM25_K1 + 1) / denom
            per_term[t] = round(contrib, SCORE_DECIMALS)
            score += contrib
        if score > 0:
            scored.append({"id": did, "score": round(score, SCORE_DECIMALS),
                           "text": text, "term_contributions": per_term})
    scored.sort(key=lambda r: (-r["score"], r["id"]))  # deterministic ties
    return {"candidates": scored[:top_k]}


def _selftest() -> None:
    corpus = [
        {"id": "d1", "text": "CVE-2024-3094 is a backdoor in xz-utils liblzma"},
        {"id": "d2", "text": "general discussion of software supply chain security"},
        {"id": "d3", "text": "xz compression formats and liblzma performance"},
        {"id": "d4", "text": "cooking recipes for pasta"},
    ]
    # Exact rare-term match wins: the CVE id ranks its doc first.
    out = run(query="CVE-2024-3094 xz backdoor", corpus=corpus)["candidates"]
    assert out[0]["id"] == "d1" and out[0]["score"] > 0
    assert all(h["id"] != "d4" for h in out)  # zero-overlap docs never appear
    # Interpretability: every hit decomposes into per-term contributions.
    assert math.isclose(sum(out[0]["term_contributions"].values()), out[0]["score"], rel_tol=1e-4)
    # Rare terms outweigh common ones (idf): "security" appears in 1 doc,
    # "liblzma" in 2 — so the security doc wins this mixed query.
    out2 = run(query="liblzma security", corpus=corpus)["candidates"]
    assert out2[0]["id"] == "d2"
    assert out2[0]["term_contributions"]["security"] > out2[1]["term_contributions"]["liblzma"]
    # top_k respected; deterministic byte-identical repeats; corpus untouched.
    assert len(run(query="xz", corpus=corpus, top_k=1)["candidates"]) == 1
    snap = json.dumps(corpus, sort_keys=True)
    a = json.dumps(run(query="xz liblzma", corpus=corpus), sort_keys=True)
    b = json.dumps(run(query="xz liblzma", corpus=corpus), sort_keys=True)
    assert a == b and json.dumps(corpus, sort_keys=True) == snap
    # Honest empties + on_error=raise.
    assert run(query="nothing matches this", corpus=corpus)["candidates"] == []
    assert run(query="x", corpus=[])["candidates"] == []
    raised = False
    try:
        run(query="x", corpus=[{"text": "no id"}])
    except ValueError:
        raised = True
    assert raised
    print("PASS — bm25_keyword_retrieve: Okapi BM25 (k1=1.5, b=0.75) with per-term "
          "decomposition, exact rare-term wins, deterministic ties, honest empties verified")


if __name__ == "__main__":
    _selftest()
