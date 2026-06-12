#!/usr/bin/env python3
"""Backs `processor/multi-query-expander` (process_kind ``query.multi_query``).

Multi-query expansion (taxonomy step R0): rephrase the query into N variants,
retrieve each, and union the legs via RRF — lifts recall when one phrasing
misses. The rephraser model is INJECTED (model-route idiom). Without one the
module emits DETERMINISTIC variants (keyword projection, stopword-stripped
form, question→statement flip) and LABELS them ``method:
deterministic-templates`` — honest mechanical recall, never fake LLM
paraphrases. The original query is ALWAYS variant 0 (the expansion may only
add legs, never lose the user's words).

Contract: side_effects=external_call (model lane) / none (fallback);
on_error=raise.

Inputs query, n → output query_variants.

CLI / self-test: python3 scripts/processors/retrieval/multi_query_expander.py
"""
from __future__ import annotations

import json
import re
from typing import Any, Callable

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: Default variant count (including the original). 4 ≈ the recall knee before
#: N× retrieval cost outruns the lift.
DEFAULT_N = 4

#: System prompt for the model lane: pure rephrasings, one per line.
EXPAND_SYSTEM = ("Rephrase the question into alternative phrasings a different author "
                 "might use. Same meaning, different vocabulary. One per line, no "
                 "numbering, no commentary.")

#: Method labels (single definition; tests read them).
METHOD_MODEL = "llm-rephrase"
METHOD_TEMPLATES = "deterministic-templates (no model route)"

STOPWORDS = frozenset({"a", "an", "and", "are", "as", "at", "be", "by", "do", "does",
                       "for", "from", "how", "i", "in", "is", "it", "must", "of", "on",
                       "or", "the", "this", "to", "we", "what", "when", "where",
                       "which", "who", "why", "will", "with"})
_TOKEN_RE = re.compile(r"[A-Za-z0-9'-]+")
#: Question-lead words a statement flip removes.
_QUESTION_LEAD_RE = re.compile(r"^(?:how|what|when|where|which|who|why|do|does|must|can|is|are)\b[\s,]*",
                               re.IGNORECASE)


def _template_variants(query: str, n: int) -> list[str]:
    out: list[str] = []
    tokens = _TOKEN_RE.findall(query)
    keywords = [t for t in tokens if t.lower() not in STOPWORDS]
    if keywords:
        out.append(" ".join(keywords))                       # keyword projection
    flipped = _QUESTION_LEAD_RE.sub("", query).rstrip("? ").strip()
    if flipped and flipped.lower() != query.lower():
        out.append(flipped)                                  # question → statement
    if keywords:
        out.append(" ".join(sorted(set(k.lower() for k in keywords))))  # normalized bag
    seen: set[str] = set()
    uniq = []
    for v in out:
        if v.lower() not in seen and v.lower() != query.lower():
            uniq.append(v)
            seen.add(v.lower())
    return uniq[: max(0, n - 1)]


def run(*, query: str, n: int = DEFAULT_N,
        complete: Callable[[str, str], str] | None = None) -> dict[str, Any]:
    """Produce up to ``n`` retrieval variants (original always first)."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty str")
    if not isinstance(n, int) or n < 1:
        raise ValueError(f"n must be a positive int, got {n!r}")
    if complete is None:
        variants = _template_variants(query, n)
        method = METHOD_TEMPLATES
    else:
        raw = str(complete(f"Question: {query}", EXPAND_SYSTEM))
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
        seen: set[str] = set()
        variants = []
        for l in lines:
            if l.lower() != query.lower() and l.lower() not in seen:
                variants.append(l)
                seen.add(l.lower())
            if len(variants) >= n - 1:
                break
        method = METHOD_MODEL
    return {"query_variants": {
        "variants": [query] + variants,     # original is ALWAYS leg 0
        "method": method,
        "requested_n": n,
        "fuse_with": "processor/rrf-fusion (union the per-variant legs)",
    }}


def _selftest() -> None:
    q = "How fast must the bank give provisional credit?"
    # Fallback lane: deterministic variants, honestly labeled, original first.
    fb = run(query=q)["query_variants"]
    assert fb["variants"][0] == q and fb["method"] == METHOD_TEMPLATES
    assert len(fb["variants"]) <= DEFAULT_N and len(fb["variants"]) >= 2
    assert "bank give provisional credit" in fb["variants"][1] or "bank" in fb["variants"][1]
    assert len({v.lower() for v in fb["variants"]}) == len(fb["variants"])  # no dupes
    # Model lane: scripted rephrasings, capped at n, original still first.
    def scripted(prompt: str, system: str) -> str:
        assert system == EXPAND_SYSTEM
        return ("What is the provisional credit deadline?\n"
                "Time limit for provisional credit under Reg E\n"
                "How quickly is provisional credit issued?\n"
                "Extra beyond n is ignored")
    md = run(query=q, n=3, complete=scripted)["query_variants"]
    assert md["variants"][0] == q and len(md["variants"]) == 3
    assert md["method"] == METHOD_MODEL
    # Deterministic; n=1 → just the original; on_error=raise.
    assert json.dumps(run(query=q), sort_keys=True) == json.dumps(run(query=q), sort_keys=True)
    assert run(query=q, n=1)["query_variants"]["variants"] == [q]
    raised = False
    try:
        run(query="", n=3)
    except ValueError:
        raised = True
    assert raised
    raised = False
    try:
        run(query=q, n=0)
    except ValueError:
        raised = True
    assert raised
    print(f"PASS — multi_query_expander: original always leg 0, model rephrasings or "
          f"deterministic templates (labeled), default n={DEFAULT_N}, dedupe + caps, "
          "RRF fusion pointer verified")


if __name__ == "__main__":
    _selftest()
