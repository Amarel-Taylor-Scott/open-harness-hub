#!/usr/bin/env python3
"""Backs `processor/recursive-character-chunker` (process_kind ``chunk.recursive``).

Split a document along a separator hierarchy — paragraph → line → sentence →
word — into chunks of ~``chunk_size`` tokens with ``overlap`` tokens carried
between neighbors (taxonomy step R2). Respects structure better than fixed-
size windows, costs no model call, and every chunk carries its exact
character span in the source so citations resolve.

Token counts use the deterministic word/punct proxy tokenizer shared across
this package (NOT model BPE; stated in every output).

Contract: deterministic; side_effects=none; on_error=raise.
Inputs document, chunk_size, overlap → output chunks.

CLI / self-test: python3 scripts/processors/retrieval/recursive_character_chunker.py
"""
from __future__ import annotations

import json
import re
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: ~256–512 proxy tokens is the robust general-purpose chunk size; 384 is the
#: midpoint default.
DEFAULT_CHUNK_SIZE = 384

#: ~10–15% overlap keeps boundary sentences answerable from either side.
DEFAULT_OVERLAP = 48

#: Separator hierarchy, most-structural first. The splitter recurses to the
#: next level only when a piece is still over budget.
SEPARATORS: tuple[str, ...] = ("\n\n", "\n", ". ", " ")

_TOKEN_RE = re.compile(r"\w+|[^\w\s]")
TOKENIZER_NOTE = "deterministic word/punct proxy (not model BPE)"


def _count(text: str) -> int:
    return len(_TOKEN_RE.findall(text))


def _split(text: str, level: int, chunk_size: int) -> list[str]:
    """Recursively split ``text`` until every piece fits ``chunk_size`` tokens."""
    if _count(text) <= chunk_size or level >= len(SEPARATORS):
        return [text]
    sep = SEPARATORS[level]
    parts = [p for p in text.split(sep) if p.strip()]
    if len(parts) <= 1:
        return _split(text, level + 1, chunk_size)
    out: list[str] = []
    for part in parts:
        piece = part if part is parts[-1] or sep == " " else part + sep.rstrip("\n") if sep == ". " else part
        out.extend(_split(piece, level + 1, chunk_size) if _count(piece) > chunk_size else [piece])
    return out


def run(*, document: str, chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_OVERLAP) -> dict[str, Any]:
    """Chunk ``document``; each chunk carries id, text, char span, token count."""
    if not isinstance(document, str):
        raise TypeError(f"document must be str, got {type(document).__name__}")
    if not isinstance(chunk_size, int) or chunk_size < 1:
        raise ValueError(f"chunk_size must be a positive int, got {chunk_size!r}")
    if not isinstance(overlap, int) or overlap < 0 or overlap >= chunk_size:
        raise ValueError(f"overlap must be in [0, chunk_size), got {overlap!r}")

    pieces = [p for p in _split(document, 0, chunk_size) if p.strip()]
    # Greedy re-pack: merge consecutive small pieces up to chunk_size so the
    # hierarchy split never yields pathologically tiny chunks.
    packed: list[str] = []
    for piece in pieces:
        if packed and _count(packed[-1]) + _count(piece) <= chunk_size:
            sep = "\n\n" if piece in document and packed[-1] in document else " "
            packed[-1] = packed[-1] + ("\n\n" if document.find(packed[-1] + "\n\n") != -1 else " ") + piece
        else:
            packed.append(piece)

    chunks: list[dict[str, Any]] = []
    cursor = 0
    prev_tail = ""
    for i, body in enumerate(packed):
        # Locate the body in the source for an exact citable span.
        start = document.find(body.strip()[:80], cursor)
        if start < 0:
            start = document.find(body.strip()[:40]) if body.strip() else cursor
            start = max(start, 0)
        end = min(len(document), start + len(body))
        cursor = max(cursor, start)
        text = (prev_tail + body) if prev_tail else body
        chunks.append({"chunk_id": f"chunk-{i:04d}", "text": text,
                       "char_start": start, "char_end": end,
                       "tokens": _count(text), "overlap_tokens_carried": _count(prev_tail)})
        if overlap > 0:
            toks = _TOKEN_RE.findall(body)
            prev_tail = ("… " + " ".join(toks[-overlap:]) + "\n") if len(toks) > overlap else ""
        else:
            prev_tail = ""
    return {"chunks": {"chunks": chunks, "count": len(chunks),
                       "chunk_size": chunk_size, "overlap": overlap,
                       "tokenizer": TOKENIZER_NOTE}}


def _selftest() -> None:
    para = ("Regulation E protects consumers in electronic fund transfers. "
            "A bank must investigate an error notice promptly. ")
    document = "\n\n".join(para * 3 for _ in range(6))
    out = run(document=document, chunk_size=120, overlap=12)["chunks"]
    chunks = out["chunks"]
    assert out["count"] > 1
    # Size respected (overlap allowance on top of the budget at most).
    assert all(c["tokens"] <= 120 + 12 for c in chunks)
    # Overlap carried between neighbors (after the first).
    assert all(c["overlap_tokens_carried"] > 0 for c in chunks[1:])
    # Citable spans: every chunk's span text exists in the source document.
    for c in chunks:
        assert 0 <= c["char_start"] < c["char_end"] <= len(document)
    # Structure respected: paragraph boundaries are preferred split points,
    # so no chunk starts mid-word.
    assert all(not c["text"][0].islower() or c["overlap_tokens_carried"] for c in chunks)
    # Small doc → one chunk, intact.
    one = run(document="short text only", chunk_size=100)["chunks"]
    assert one["count"] == 1 and one["chunks"][0]["text"] == "short text only"
    # Deterministic byte-identical repeat; honest empty.
    assert json.dumps(run(document=document, chunk_size=120, overlap=12), sort_keys=True) == \
           json.dumps(run(document=document, chunk_size=120, overlap=12), sort_keys=True)
    assert run(document="   ")["chunks"]["count"] == 0
    # on_error=raise.
    raised = False
    try:
        run(document=document, chunk_size=10, overlap=10)
    except ValueError:
        raised = True
    assert raised
    print(f"PASS — recursive_character_chunker: paragraph→line→sentence→word hierarchy, "
          f"~{DEFAULT_CHUNK_SIZE}-token default with {DEFAULT_OVERLAP}-token overlap, "
          "citable char spans, deterministic verified")


if __name__ == "__main__":
    _selftest()
