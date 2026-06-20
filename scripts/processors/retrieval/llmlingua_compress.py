#!/usr/bin/env python3
"""Backs `processor/llmlingua-compress` (process_kind ``summarize.llmlingua``).

LLMLingua-style prompt compression: drop low-information tokens to hit a
target ratio. Real LLMLingua scores tokens with a small causal LM's
perplexity; this implementation uses a **deterministic information proxy** —
corpus-level inverse term frequency + first-occurrence bonus + structural
keep-lists — and SAYS SO in every result (``scorer`` field). The contract,
budgeting, and ratio accounting are the real thing; swap the scorer for a
perplexity model behind the same ``run()`` to get learned compression.
MEASURE the breakeven before enabling (the manifest's own warning).

Contract: side_effects=none; on_error=raise; deterministic with the built-in
scorer (manifest allows non-deterministic learned scorers behind the seam).

Inputs context, ratio → output compressed.

CLI / self-test: python3 scripts/processors/retrieval/llmlingua_compress.py
"""
from __future__ import annotations

import json
import math
import re
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: Default keep-ratio (compressed/original tokens). 0.5 = 2x compression —
#: LLMLingua's conservative operating point; it reports up to ~20x on long
#: redundant prompts.
DEFAULT_RATIO = 0.5

#: Tokens always kept regardless of score: negations and numbers change
#: meaning when dropped.
ALWAYS_KEEP = frozenset({"not", "no", "never", "n't", "cannot"})
_NUMBER_RE = re.compile(r"^\d+(?:\.\d+)?%?$")

#: First occurrence of a content word is worth this bonus (novelty carries
#: information; repeats are the compressible part).
FIRST_OCCURRENCE_BONUS = 1.0

_TOKEN_RE = re.compile(r"\w+(?:'\w+)?|[^\w\s]")
SCORER_NOTE = "deterministic idf+novelty proxy (NOT a perplexity LM — swap behind run())"


def run(*, context: str, ratio: float = DEFAULT_RATIO) -> dict[str, Any]:
    """Keep the highest-information tokens of ``context`` at ``ratio`` budget."""
    if not isinstance(context, str):
        raise TypeError(f"context must be str, got {type(context).__name__}")
    if not isinstance(ratio, (int, float)) or not 0.0 < float(ratio) <= 1.0:
        raise ValueError(f"ratio must be in (0, 1], got {ratio!r}")
    tokens = _TOKEN_RE.findall(context)
    n = len(tokens)
    if n == 0:
        return {"compressed": {"text": "", "tokens_in": 0, "tokens_out": 0,
                               "achieved_ratio": 0.0, "scorer": SCORER_NOTE}}
    budget = max(1, math.ceil(n * float(ratio)))

    freq: dict[str, int] = {}
    for t in tokens:
        freq[t.lower()] = freq.get(t.lower(), 0) + 1
    seen: set[str] = set()
    scored: list[tuple[float, int]] = []  # (score, index)
    for i, t in enumerate(tokens):
        low = t.lower()
        score = 1.0 / freq[low]                       # inverse in-context frequency
        if low not in seen and low.isalnum():
            score += FIRST_OCCURRENCE_BONUS
            seen.add(low)
        if low in ALWAYS_KEEP or _NUMBER_RE.match(low):
            score = math.inf                           # meaning-bearing: never dropped
        scored.append((score, i))

    keep_idx = {i for _, i in sorted(scored, key=lambda s: (-s[0], s[1]))[:max(budget, sum(1 for s, _ in scored if s == math.inf))]}
    kept = [tokens[i] for i in sorted(keep_idx)]
    text = re.sub(r"\s+([^\w\s])", r"\1", " ".join(kept))  # reattach punctuation
    return {"compressed": {"text": text, "tokens_in": n, "tokens_out": len(kept),
                           "achieved_ratio": round(len(kept) / n, 6),
                           "requested_ratio": float(ratio), "scorer": SCORER_NOTE}}


def _selftest() -> None:
    context = ("The bank must not delay provisional credit. The bank must act within 10 "
               "business days. The bank must document the investigation. The bank must "
               "notify the consumer. The bank must keep records of the investigation.")
    out = run(context=context, ratio=0.5)["compressed"]
    # Budget respected (within the always-keep floor) and reported honestly.
    assert out["tokens_out"] <= math.ceil(out["tokens_in"] * 0.5) + 3
    assert 0 < out["achieved_ratio"] <= 0.6
    # Meaning-bearing tokens survive: the negation and the number are kept.
    assert "not" in out["text"] and "10" in out["text"]
    # Novel content words survive better than boilerplate repeats: 'investigation'
    # appears; the fifth repeat of 'bank' does not all survive.
    assert "investigation" in out["text"]
    assert out["text"].lower().count("the bank must") < 5
    # The scorer is honestly labeled as a proxy.
    assert "NOT a perplexity LM" in out["scorer"]
    # ratio=1 keeps everything verbatim token-wise.
    full = run(context=context, ratio=1.0)["compressed"]
    assert full["tokens_out"] == full["tokens_in"]
    # Deterministic; honest empty; on_error=raise.
    assert json.dumps(run(context=context, ratio=0.5), sort_keys=True) == \
           json.dumps(run(context=context, ratio=0.5), sort_keys=True)
    assert run(context="")["compressed"]["tokens_out"] == 0
    raised = False
    try:
        run(context=context, ratio=0.0)
    except ValueError:
        raised = True
    assert raised
    print("PASS — llmlingua_compress: idf+novelty token budgeting at target ratio, "
          "negations/numbers never dropped, honest proxy-scorer labeling, "
          "deterministic verified")


if __name__ == "__main__":
    _selftest()
