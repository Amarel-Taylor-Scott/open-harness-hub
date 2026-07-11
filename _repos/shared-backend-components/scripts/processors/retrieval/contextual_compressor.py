#!/usr/bin/env python3
"""Backs `processor/contextual-compressor` (process_kind ``summarize.contextual_compression``).

LLM contextual compression (taxonomy step R4): a model extracts only the
query-relevant content from each chunk — stronger token reduction than
extractive selection when chunks are verbose, at the cost of one model call
and paraphrase risk.

The model is INJECTED (``complete(prompt, system) -> str``, the model-route
idiom). WITHOUT a model this module does not fake one: it degrades to the
package's deterministic extractive selector (`extractive_span_selector` —
single source) and LABELS the result ``method: extractive-fallback`` — the
manifest's own guidance ("use when extractive isn't enough") run in reverse.
Model output is compression CANDIDATE text, never truth: every compressed
chunk keeps its source chunk id, and the envelope pins ``serves_truth: False``.

Contract: side_effects=external_call (model lane) / none (fallback);
on_error=raise.

Inputs chunks({"id","text"}), query → output compressed.

CLI / self-test: python3 _repos/shared-backend-components/scripts/processors/retrieval/contextual_compressor.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _RR = str(next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3]))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts.processors.retrieval.extractive_span_selector import run as extractive_run

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: System prompt for the extraction call — extract, never answer; verbatim
#: wherever possible; empty when nothing is relevant.
COMPRESS_SYSTEM = ("Extract ONLY the sentences relevant to the question, verbatim where "
                   "possible. Output the extracted text only. If nothing is relevant, "
                   "output exactly: NOTHING_RELEVANT")

#: The model's nothing-relevant sentinel (kept ugly so prose never collides).
NOTHING_SENTINEL = "NOTHING_RELEVANT"

#: Method labels (single definition; tests read them).
METHOD_MODEL = "llm-contextual-compression"
METHOD_FALLBACK = "extractive-fallback (no model route — deterministic)"


def run(*, chunks: list[dict[str, Any]], query: str,
        complete: Callable[[str, str], str] | None = None) -> dict[str, Any]:
    """Compress each chunk to its query-relevant content via the injected model,
    or deterministically via the extractive selector when no model is given."""
    if not isinstance(query, str):
        raise TypeError(f"query must be str, got {type(query).__name__}")
    if not isinstance(chunks, list):
        raise TypeError("chunks must be a list of id/text dicts")

    if complete is None:
        spans = extractive_run(chunks=chunks, query=query)["spans"]
        by_chunk: dict[str, list[str]] = {}
        for s in spans["spans"]:
            by_chunk.setdefault(s["chunk_id"], []).append(s["text"])
        items = [{"chunk_id": cid, "compressed_text": " ".join(texts), "dropped": False}
                 for cid, texts in sorted(by_chunk.items())]
        dropped = [{"chunk_id": str(c["id"]), "reason": "no query-relevant span"}
                   for c in chunks if str(c.get("id")) not in by_chunk]
        return {"compressed": {"items": items, "dropped": dropped,
                               "method": METHOD_FALLBACK,
                               "chars_in": spans["chars_in"], "chars_out": spans["chars_out"],
                               "serves_truth": False}}

    items: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    chars_in = chars_out = 0
    for i, c in enumerate(chunks):
        if not isinstance(c, dict) or "id" not in c or "text" not in c:
            raise ValueError(f"chunks[{i}] needs id and text")
        text = str(c["text"])
        chars_in += len(text)
        reply = str(complete(f"Question: {query}\n\nChunk:\n{text}", COMPRESS_SYSTEM)).strip()
        if not reply or reply == NOTHING_SENTINEL:
            dropped.append({"chunk_id": str(c["id"]), "reason": "model: nothing relevant"})
            continue
        chars_out += len(reply)
        items.append({"chunk_id": str(c["id"]), "compressed_text": reply, "dropped": False})
    return {"compressed": {"items": items, "dropped": dropped, "method": METHOD_MODEL,
                           "chars_in": chars_in, "chars_out": chars_out,
                           "serves_truth": False}}


def _selftest() -> None:
    chunks = [
        {"id": "c1", "text": ("Regulation E covers transfers. The bank must give provisional "
                              "credit within ten business days. Branch hours vary by location.")},
        {"id": "c2", "text": "Marketing copy about the new app design."},
    ]
    # Fallback lane (no model): deterministic, honestly labeled, lineage kept,
    # irrelevant chunks dropped WITH a reason.
    fb = run(chunks=chunks, query="how fast must provisional credit arrive?")["compressed"]
    assert fb["method"] == METHOD_FALLBACK and fb["serves_truth"] is False
    assert any("provisional credit" in i["compressed_text"] for i in fb["items"])
    assert all(i["chunk_id"] == "c1" for i in fb["items"])
    assert {"chunk_id": "c2", "reason": "no query-relevant span"} in fb["dropped"]
    assert fb["chars_out"] < fb["chars_in"]
    # Model lane: a scripted route compresses; the sentinel drops a chunk honestly.
    def scripted(prompt: str, system: str) -> str:
        assert system == COMPRESS_SYSTEM
        chunk_body = prompt.split("Chunk:\n", 1)[1]
        return ("The bank must give provisional credit within ten business days."
                if "provisional" in chunk_body else NOTHING_SENTINEL)
    md = run(chunks=chunks, query="provisional credit timing", complete=scripted)["compressed"]
    assert md["method"] == METHOD_MODEL
    assert md["items"][0]["chunk_id"] == "c1" and "ten business days" in md["items"][0]["compressed_text"]
    assert md["dropped"][0]["reason"] == "model: nothing relevant"
    assert md["serves_truth"] is False  # model text is candidate text, never truth
    # Deterministic fallback repeat; inputs untouched; on_error=raise.
    snap = json.dumps(chunks, sort_keys=True)
    assert json.dumps(run(chunks=chunks, query="credit"), sort_keys=True) == \
           json.dumps(run(chunks=chunks, query="credit"), sort_keys=True)
    assert json.dumps(chunks, sort_keys=True) == snap
    raised = False
    try:
        run(chunks=[{"id": "x"}], query="q", complete=scripted)
    except ValueError:
        raised = True
    assert raised
    print("PASS — contextual_compressor: injected-model extraction with honest "
          "NOTHING_RELEVANT drops, deterministic extractive fallback (labeled), "
          "chunk-id lineage, serves_truth pinned False verified")


if __name__ == "__main__":
    _selftest()
