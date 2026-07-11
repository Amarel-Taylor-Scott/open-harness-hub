#!/usr/bin/env python3
"""Backs `processor/fuzzy-trigram-retrieve` (process_kind ``retrieve.fuzzy_trigram``).

Substring / typo / name-variant matching via character trigrams (the pg_trgm
model) plus a bounded edit-distance check — language-agnostic, character-
level only, catches misspellings ("Volkov" / "Volkow") and name variants
that lexical and dense legs both miss. NOT a semantic ranker; it scores
surface-form closeness and says so.

Contract: deterministic; side_effects=read; on_error=raise.
Inputs query, corpus({"id","text"}), max_distance → output candidates.

CLI / self-test: python3 _repos/shared-backend-components/scripts/processors/retrieval/fuzzy_trigram_retrieve.py
"""
from __future__ import annotations

import json
import re
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: pg_trgm-style similarity floor: a candidate needs at least this trigram
#: Jaccard similarity (pg_trgm's default similarity threshold is 0.3).
DEFAULT_SIMILARITY_FLOOR = 0.3

#: Edit-distance ceiling used by the word-level typo check (Levenshtein).
DEFAULT_MAX_DISTANCE = 2

#: Words shorter than this skip the edit-distance lane (1-2 char words match
#: everything at distance 2 — pure noise).
MIN_WORD_LEN_FOR_EDIT = 4

#: Trigram padding marker, as pg_trgm does ("  w", " wo", ...).
PAD = "  "

_TOKEN_RE = re.compile(r"[a-z0-9]+")
SCORE_DECIMALS = 6


def trigrams(text: str) -> set[str]:
    grams: set[str] = set()
    for word in _TOKEN_RE.findall(text.lower()):
        padded = PAD + word + " "
        grams.update(padded[i:i + 3] for i in range(len(padded) - 2))
    return grams


def levenshtein(a: str, b: str, cap: int) -> int:
    """Bounded edit distance; returns cap+1 early when the bound is exceeded."""
    if abs(len(a) - len(b)) > cap:
        return cap + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        best = i
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[-1] + 1, prev[j - 1] + (ca != cb)))
            best = min(best, cur[-1])
        if best > cap:
            return cap + 1
        prev = cur
    return prev[-1]


def run(*, query: str, corpus: list[dict[str, Any]],
        max_distance: int = DEFAULT_MAX_DISTANCE) -> dict[str, Any]:
    """Rank ``corpus`` by trigram similarity to ``query``; flag word-level typo hits."""
    if not isinstance(query, str):
        raise TypeError(f"query must be str, got {type(query).__name__}")
    if not isinstance(corpus, list):
        raise TypeError("corpus must be a list of id/text dicts")
    if not isinstance(max_distance, int) or max_distance < 0:
        raise ValueError(f"max_distance must be >= 0, got {max_distance!r}")
    qgrams = trigrams(query)
    qwords = [w for w in _TOKEN_RE.findall(query.lower()) if len(w) >= MIN_WORD_LEN_FOR_EDIT]
    scored: list[dict[str, Any]] = []
    for i, d in enumerate(corpus):
        if not isinstance(d, dict) or "id" not in d or "text" not in d:
            raise ValueError(f"corpus[{i}] needs id and text")
        text = str(d["text"])
        dgrams = trigrams(text)
        union = qgrams | dgrams
        sim = (len(qgrams & dgrams) / len(union)) if union else 0.0
        # Word-level typo lane: any query word within max_distance of any doc word.
        typo_hits: list[dict[str, Any]] = []
        dwords = {w for w in _TOKEN_RE.findall(text.lower()) if len(w) >= MIN_WORD_LEN_FOR_EDIT}
        for qw in qwords:
            for dw in dwords:
                dist = levenshtein(qw, dw, max_distance)
                if dist <= max_distance:
                    typo_hits.append({"query_word": qw, "matched_word": dw, "distance": dist})
                    break
        if sim >= DEFAULT_SIMILARITY_FLOOR or typo_hits:
            scored.append({"id": str(d["id"]), "text": text,
                           "trigram_similarity": round(sim, SCORE_DECIMALS),
                           "typo_matches": typo_hits,
                           "match_kind": "surface_form_only"})
    scored.sort(key=lambda r: (-r["trigram_similarity"], r["id"]))
    return {"candidates": scored}


def _selftest() -> None:
    corpus = [
        {"id": "p1", "text": "Dmitri Volkov, listed individual"},
        {"id": "p2", "text": "Novaya Commerce LLC trading records"},
        {"id": "p3", "text": "completely unrelated gardening notes"},
    ]
    # A misspelled name still finds its record via the typo lane.
    out = run(query="Dmitri Volkow", corpus=corpus)["candidates"]
    assert out and out[0]["id"] == "p1"
    assert any(t["matched_word"] == "volkov" and t["distance"] == 1
               for t in out[0]["typo_matches"])
    # Substring/variant matching: 'Novaya Commerce' hits its doc, not gardening.
    out2 = run(query="novaya comerce", corpus=corpus)["candidates"]
    assert out2 and out2[0]["id"] == "p2"
    assert all(c["id"] != "p3" for c in out2)
    # Honest non-semantic labeling on every candidate.
    assert all(c["match_kind"] == "surface_form_only" for c in out)
    # Unrelated query → honest empty (floor + typo lane both miss).
    assert run(query="zzqx", corpus=corpus)["candidates"] == []
    # Bounded edit distance respects the cap.
    assert levenshtein("volkov", "volkow", 2) == 1
    assert levenshtein("volkov", "smith", 2) == 3  # cap+1 sentinel
    # Deterministic; corpus untouched; on_error=raise.
    snap = json.dumps(corpus, sort_keys=True)
    assert json.dumps(run(query="volkov", corpus=corpus), sort_keys=True) == \
           json.dumps(run(query="volkov", corpus=corpus), sort_keys=True)
    assert json.dumps(corpus, sort_keys=True) == snap
    raised = False
    try:
        run(query="x", corpus=corpus, max_distance=-1)
    except ValueError:
        raised = True
    assert raised
    print("PASS — fuzzy_trigram_retrieve: pg_trgm-style padded trigrams (floor "
          f"{DEFAULT_SIMILARITY_FLOOR}) + bounded Levenshtein typo lane, honest "
          "surface_form_only labeling, deterministic verified")


if __name__ == "__main__":
    _selftest()
