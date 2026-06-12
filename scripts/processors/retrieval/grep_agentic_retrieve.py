#!/usr/bin/env python3
"""Backs `processor/grep-agentic-retrieve` (process_kind ``retrieve.grep_agentic``).

Agentic regex/grep retrieval (ripgrep-style, the way Claude Code searches):
exact pattern matching over an in-memory corpus — no index, no embeddings,
fully private, and every hit is a real line with its exact location and a
context window. On well-named corpora this recovers most of RAG's value at
zero build cost; it is surface-exact, so pair it with a dense leg when
paraphrase recall matters (the manifest's own guidance).

Contract: deterministic; side_effects=read; on_error=raise (an invalid regex
is a caller error, never silently treated as a literal).

Inputs pattern, corpus({"id","text"}) → output matches.

CLI / self-test: python3 scripts/processors/retrieval/grep_agentic_retrieve.py
"""
from __future__ import annotations

import json
import re
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: Context lines captured on each side of a hit (ripgrep's -C semantics).
DEFAULT_CONTEXT_LINES = 2

#: Per-document hit cap so one log-shaped document cannot flood the result.
MAX_HITS_PER_DOC = 20

#: Compiled-pattern flags: multiline so ^/$ anchor per line, like grep.
_FLAGS = re.MULTILINE


def run(*, pattern: str, corpus: list[dict[str, Any]],
        context_lines: int = DEFAULT_CONTEXT_LINES,
        case_insensitive: bool = False) -> dict[str, Any]:
    """Regex-search every corpus document; return line-exact hits with context."""
    if not isinstance(pattern, str) or not pattern:
        raise TypeError("pattern must be a non-empty str")
    if not isinstance(corpus, list):
        raise TypeError("corpus must be a list of id/text dicts")
    if not isinstance(context_lines, int) or context_lines < 0:
        raise ValueError(f"context_lines must be >= 0, got {context_lines!r}")
    try:
        rx = re.compile(pattern, _FLAGS | (re.IGNORECASE if case_insensitive else 0))
    except re.error as exc:
        raise ValueError(f"invalid regex pattern: {exc}") from exc

    hits: list[dict[str, Any]] = []
    truncated_docs: list[str] = []
    for i, d in enumerate(corpus):
        if not isinstance(d, dict) or "id" not in d or "text" not in d:
            raise ValueError(f"corpus[{i}] needs id and text")
        lines = str(d["text"]).splitlines()
        doc_hits = 0
        for ln, line in enumerate(lines):
            m = rx.search(line)
            if not m:
                continue
            if doc_hits >= MAX_HITS_PER_DOC:
                truncated_docs.append(str(d["id"]))  # capped — reported, never silent
                break
            lo = max(0, ln - context_lines)
            hi = min(len(lines), ln + context_lines + 1)
            hits.append({"id": str(d["id"]), "line_number": ln + 1, "line": line,
                         "matched_text": m.group(0),
                         "span": [m.start(), m.end()],
                         "context": lines[lo:hi]})
            doc_hits += 1
    hits.sort(key=lambda h: (h["id"], h["line_number"]))  # deterministic order
    return {"matches": {"hits": hits, "pattern": pattern,
                        "documents_searched": len(corpus),
                        "truncated_documents": sorted(set(truncated_docs)),
                        "match_kind": "surface_exact (no semantic recall)"}}


def _selftest() -> None:
    corpus = [
        {"id": "reg-e.md", "text": ("# Error resolution\n"
                                    "The bank must investigate within 10 business days.\n"
                                    "Provisional credit applies while investigating.\n"
                                    "See 12 CFR 1005.11 for the rule text.")},
        {"id": "notes.txt", "text": "unrelated meeting notes\nlunch at noon"},
    ]
    out = run(pattern=r"\b10 business days\b", corpus=corpus)["matches"]
    # Line-exact hit with span + context window.
    assert len(out["hits"]) == 1
    h = out["hits"][0]
    assert h["id"] == "reg-e.md" and h["line_number"] == 2
    assert h["matched_text"] == "10 business days"
    assert h["line"][h["span"][0]:h["span"][1]] == "10 business days"
    assert "# Error resolution" in h["context"] and "Provisional credit applies while investigating." in h["context"]
    # Regex power: alternation + statute shape.
    cfr = run(pattern=r"12 CFR \d+\.\d+", corpus=corpus)["matches"]["hits"]
    assert cfr and cfr[0]["matched_text"] == "12 CFR 1005.11"
    # Case-insensitive flag.
    ci = run(pattern="PROVISIONAL", corpus=corpus, case_insensitive=True)["matches"]["hits"]
    assert ci and ci[0]["line_number"] == 3
    # Per-doc cap is honest: a log-shaped doc reports truncation.
    log = [{"id": "big.log", "text": "\n".join(f"error {i}" for i in range(50))}]
    capped = run(pattern=r"^error", corpus=log)["matches"]
    assert len(capped["hits"]) == MAX_HITS_PER_DOC and capped["truncated_documents"] == ["big.log"]
    # Honest empty; surface-exact labeling; deterministic; corpus untouched.
    assert run(pattern="zebra", corpus=corpus)["matches"]["hits"] == []
    assert "surface_exact" in out["match_kind"]
    snap = json.dumps(corpus, sort_keys=True)
    assert json.dumps(run(pattern="bank", corpus=corpus), sort_keys=True) == \
           json.dumps(run(pattern="bank", corpus=corpus), sort_keys=True)
    assert json.dumps(corpus, sort_keys=True) == snap
    # on_error=raise: invalid regex is an error, never a literal fallback.
    raised = False
    try:
        run(pattern="(unclosed", corpus=corpus)
    except ValueError:
        raised = True
    assert raised
    print("PASS — grep_agentic_retrieve: line-exact regex hits with spans + context "
          f"windows (-C {DEFAULT_CONTEXT_LINES}), honest per-doc cap {MAX_HITS_PER_DOC}, "
          "surface_exact labeling, invalid-regex raises verified")


if __name__ == "__main__":
    _selftest()
