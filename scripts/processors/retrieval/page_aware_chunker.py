#!/usr/bin/env python3
"""Backs `processor/page-aware-chunker` (process_kind ``chunk.layout_aware``).

Layout-aware chunking (taxonomy step R2): split on headings, page anchors and
table boundaries so every chunk cites a REAL location ("p.12, §3.2") and a
table is never torn in half. Needs structured input — a document plus a
layout description (pages with headings/tables) — and refuses to fake
structure when none is provided (it reports ``layout_used: False`` and falls
back to a single un-anchored chunk rather than inventing page numbers).

Contract: deterministic; side_effects=none; on_error=raise.
Inputs document, layout(pages:[{page,headings,tables}]) → output chunks.

CLI / self-test: python3 scripts/processors/retrieval/page_aware_chunker.py
"""
from __future__ import annotations

import json
import re
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: Soft token budget per chunk; a TABLE block may exceed it (tables stay
#: intact by design) and is flagged instead of split.
SOFT_CHUNK_TOKENS = 400

_TOKEN_RE = re.compile(r"\w+|[^\w\s]")
TOKENIZER_NOTE = "deterministic word/punct proxy (not model BPE)"


def _count(text: str) -> int:
    return len(_TOKEN_RE.findall(text))


def run(*, document: str, layout: dict[str, Any] | None = None) -> dict[str, Any]:
    """Chunk ``document`` along the page/heading/table anchors in ``layout``.

    ``layout`` = {"pages": [{"page": int, "start": char, "end": char,
    "headings": [{"text", "start"}], "tables": [{"start", "end", "label"}]}]}
    (char offsets into ``document``). Every chunk carries its page, heading
    path and char span — the citable anchor.
    """
    if not isinstance(document, str):
        raise TypeError(f"document must be str, got {type(document).__name__}")
    if layout is None or not isinstance(layout.get("pages"), list) or not layout["pages"]:
        body = document.strip()
        chunks = ([{"chunk_id": "chunk-0000", "text": body, "page": None, "heading": None,
                    "char_start": 0, "char_end": len(document), "is_table": False,
                    "anchor": None}] if body else [])
        return {"chunks": {"chunks": chunks, "count": len(chunks), "layout_used": False,
                           "tokenizer": TOKENIZER_NOTE,
                           "note": "no layout provided — single un-anchored chunk, anchors never invented"}}

    cut_points: list[dict[str, Any]] = []
    for p in layout["pages"]:
        if "page" not in p or "start" not in p:
            raise ValueError("every layout page needs page and start")
        cut_points.append({"pos": int(p["start"]), "page": int(p["page"]),
                           "heading": None, "table": None})
        for h in p.get("headings", []) or []:
            cut_points.append({"pos": int(h["start"]), "page": int(p["page"]),
                               "heading": str(h["text"]), "table": None})
        for t in p.get("tables", []) or []:
            cut_points.append({"pos": int(t["start"]), "page": int(p["page"]),
                               "heading": None,
                               "table": {"end": int(t["end"]), "label": str(t.get("label", "table"))}})
    cut_points.sort(key=lambda c: (c["pos"], c["heading"] is None))

    chunks: list[dict[str, Any]] = []
    current_heading: str | None = None
    i = 0
    while i < len(cut_points):
        cp = cut_points[i]
        if cp["heading"] is not None:
            current_heading = cp["heading"]
        if cp["table"] is not None:
            start, end = cp["pos"], cp["table"]["end"]
            text = document[start:end]
            chunks.append({"text": text, "page": cp["page"], "heading": current_heading,
                           "char_start": start, "char_end": end, "is_table": True,
                           "table_label": cp["table"]["label"],
                           "oversize": _count(text) > SOFT_CHUNK_TOKENS})
            i += 1
            continue
        next_pos = cut_points[i + 1]["pos"] if i + 1 < len(cut_points) else len(document)
        text = document[cp["pos"]:next_pos]
        if text.strip():
            chunks.append({"text": text, "page": cp["page"], "heading": current_heading,
                           "char_start": cp["pos"], "char_end": next_pos, "is_table": False,
                           "oversize": _count(text) > SOFT_CHUNK_TOKENS})
        i += 1
    for n, c in enumerate(chunks):
        c["chunk_id"] = f"chunk-{n:04d}"
        c["anchor"] = f"p.{c['page']}" + (f" — {c['heading']}" if c.get("heading") else "")
    return {"chunks": {"chunks": chunks, "count": len(chunks), "layout_used": True,
                       "tokenizer": TOKENIZER_NOTE}}


def _selftest() -> None:
    intro = "Introduction prose about error resolution rights. "
    sec = "Section two explains provisional credit timing in detail. "
    table = "| day | action |\n| 1 | notice |\n| 10 | credit |\n"
    tail = "Closing remarks and references. "
    document = intro + sec + table + tail
    layout = {"pages": [
        {"page": 1, "start": 0, "headings": [{"text": "Introduction", "start": 0}]},
        {"page": 2, "start": len(intro),
         "headings": [{"text": "§2 Provisional credit", "start": len(intro)}],
         "tables": [{"start": len(intro + sec), "end": len(intro + sec + table), "label": "timing table"}]},
    ]}
    out = run(document=document, layout=layout)["chunks"]
    chunks = out["chunks"]
    assert out["layout_used"] is True and out["count"] >= 3
    # Citable anchors resolve to real pages + headings.
    assert chunks[0]["anchor"] == "p.1 — Introduction"
    sec_chunk = next(c for c in chunks if c["heading"] == "§2 Provisional credit" and not c["is_table"])
    assert sec_chunk["page"] == 2
    # The table stays intact as ONE chunk with its label.
    tbl = next(c for c in chunks if c["is_table"])
    assert tbl["text"] == table and tbl["table_label"] == "timing table"
    # Spans are exact: text == document[start:end] for every chunk.
    assert all(c["text"] == document[c["char_start"]:c["char_end"]] for c in chunks)
    # No layout → honest fallback, anchors never invented.
    bare = run(document=document)["chunks"]
    assert bare["layout_used"] is False and bare["chunks"][0]["anchor"] is None
    assert "never invented" in bare["note"]
    # Deterministic; on_error=raise.
    assert json.dumps(run(document=document, layout=layout), sort_keys=True) == \
           json.dumps(run(document=document, layout=layout), sort_keys=True)
    raised = False
    try:
        run(document=document, layout={"pages": [{"start": 0}]})
    except ValueError:
        raised = True
    assert raised
    print("PASS — page_aware_chunker: heading/page/table anchors, tables never torn, "
          "exact char spans, honest un-anchored fallback (no invented pages) verified")


if __name__ == "__main__":
    _selftest()
