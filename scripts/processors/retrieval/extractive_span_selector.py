#!/usr/bin/env python3
"""Backs `processor/extractive-span-selector` (process_kind ``summarize.extractive``).

Deterministically select the query-relevant SPANS (sentences) from reranked
chunks — cheap, faithful compression that keeps the EXACT citable text: no
paraphrase, no model call, every span carries its source chunk id and char
offsets. The preferred compression for governed pipelines (freezable);
``contextual-compressor`` is the LLM escalation when extractive isn't enough.

Contract: deterministic; side_effects=none; on_error=raise.
Inputs chunks({"id","text"}), query → output spans.

CLI / self-test: python3 scripts/processors/retrieval/extractive_span_selector.py
"""
from __future__ import annotations

import json
import re
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: A sentence must share at least this many salient terms with the query to
#: be selected (1 = any topical contact; raise for tighter budgets).
MIN_QUERY_OVERLAP = 1

#: Cap on selected spans per chunk so one verbose chunk cannot crowd out the
#: rest of the evidence.
MAX_SPANS_PER_CHUNK = 3

STOPWORDS = frozenset({"a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
                       "how", "in", "is", "it", "of", "on", "or", "that", "the", "this",
                       "to", "was", "what", "when", "where", "which", "who", "why", "with"})
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
SCORE_DECIMALS = 6


def _salient(text: str) -> set[str]:
    return {t for t in _TOKEN_RE.findall(text.lower()) if t not in STOPWORDS}


def run(*, chunks: list[dict[str, Any]], query: str) -> dict[str, Any]:
    """Pick the query-relevant sentences from each chunk, verbatim, with offsets."""
    if not isinstance(query, str):
        raise TypeError(f"query must be str, got {type(query).__name__}")
    if not isinstance(chunks, list):
        raise TypeError("chunks must be a list of id/text dicts")
    qterms = _salient(query)
    spans: list[dict[str, Any]] = []
    total_in = total_out = 0
    for i, ch in enumerate(chunks):
        if not isinstance(ch, dict) or "id" not in ch or "text" not in ch:
            raise ValueError(f"chunks[{i}] needs id and text")
        text = str(ch["text"])
        total_in += len(text)
        picked: list[dict[str, Any]] = []
        cursor = 0
        for sent in _SENTENCE_SPLIT_RE.split(text):
            sent_stripped = sent.strip()
            if not sent_stripped:
                continue
            start = text.find(sent_stripped, cursor)
            cursor = start + len(sent_stripped) if start >= 0 else cursor
            overlap = _salient(sent_stripped) & qterms
            if len(overlap) >= MIN_QUERY_OVERLAP:
                picked.append({"chunk_id": str(ch["id"]), "text": sent_stripped,
                               "char_start": start, "char_end": start + len(sent_stripped),
                               "overlap_terms": sorted(overlap),
                               "score": round(len(overlap) / (len(qterms) or 1), SCORE_DECIMALS)})
        picked.sort(key=lambda s: (-s["score"], s["char_start"]))
        kept = sorted(picked[:MAX_SPANS_PER_CHUNK], key=lambda s: s["char_start"])
        spans.extend(kept)
        total_out += sum(len(s["text"]) for s in kept)
    return {"spans": {"spans": spans,
                      "chars_in": total_in, "chars_out": total_out,
                      "compression_ratio": round((total_out / total_in), SCORE_DECIMALS) if total_in else 0.0,
                      "method": "extractive_verbatim (no paraphrase, no model)"}}


def _selftest() -> None:
    chunks = [
        {"id": "c1", "text": ("Regulation E governs electronic transfers. The bank must give "
                              "provisional credit within ten business days. Branch hours vary "
                              "by location. Disputes need written notice in some cases.")},
        {"id": "c2", "text": "Unrelated marketing copy about a new mobile app design."},
    ]
    out = run(chunks=chunks, query="how fast must the bank give provisional credit?")["spans"]
    texts = [s["text"] for s in out["spans"]]
    # The on-point sentence is selected VERBATIM with exact offsets.
    target = "The bank must give provisional credit within ten business days."
    assert target in texts
    span = next(s for s in out["spans"] if s["text"] == target)
    assert chunks[0]["text"][span["char_start"]:span["char_end"]] == target
    assert span["overlap_terms"]  # citable why-selected
    # Off-topic sentences and chunks contribute nothing.
    assert all("marketing" not in t for t in texts)
    assert all("Branch hours" not in t for t in texts)
    # Real compression happened and is reported.
    assert out["chars_out"] < out["chars_in"] and 0 < out["compression_ratio"] < 1
    # Per-chunk cap holds.
    many = [{"id": "big", "text": ". ".join(f"credit fact number {i} about credit" for i in range(10)) + "."}]
    capped = run(chunks=many, query="credit")["spans"]["spans"]
    assert len(capped) == MAX_SPANS_PER_CHUNK
    # Deterministic; inputs untouched; honest empty.
    snap = json.dumps(chunks, sort_keys=True)
    assert json.dumps(run(chunks=chunks, query="credit"), sort_keys=True) == \
           json.dumps(run(chunks=chunks, query="credit"), sort_keys=True)
    assert json.dumps(chunks, sort_keys=True) == snap
    assert run(chunks=[], query="x")["spans"]["spans"] == []
    raised = False
    try:
        run(chunks=[{"id": "x"}], query="q")
    except ValueError:
        raised = True
    assert raised
    print("PASS — extractive_span_selector: verbatim sentence spans with exact offsets "
          f"+ overlap lineage, per-chunk cap {MAX_SPANS_PER_CHUNK}, no paraphrase, "
          "deterministic verified")


if __name__ == "__main__":
    _selftest()
