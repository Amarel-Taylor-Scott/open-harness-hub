#!/usr/bin/env python3
"""Backs `processor/curriculum-qa-dataset-builder` (process_kind ``extract.pdf_to_dataset``).

The ShikshaEdge "build your own corpus" pattern: turn curriculum PDFs into a
domain Q&A dataset for on-device tutoring. Stage 1 extracts page text via an
INJECTED extractor (PyMuPDF adapter in production — page list in, never
bundled); stage 2 chunks via the single-source recursive chunker; stage 3
generates Q&A pairs per chunk via the INJECTED model adapter (strict JSON
contract — malformed/oversized outputs are DROPPED AND COUNTED, never
patched into the dataset); stage 4 writes JSONL rows to the injected sink
with page lineage on every pair. Without the model adapter it RAISES — a
training dataset is never fabricated.

Contract: side_effects=write (the injected sink only); on_error=raise.
Inputs pdf_path, language_hint, chunk_size_tokens, chunk_stride_tokens,
max_qa_pairs_per_chunk, model_adapter_ref, output_path → output_jsonl_path,
total_chunks, total_qa_pairs, dropped_pairs, coverage_pages.

CLI / self-test: python3 scripts/processors/curriculum_qa_dataset_builder.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _RR = str(Path(__file__).resolve().parents[2])
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts.processors.retrieval.recursive_character_chunker import run as chunk_run

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

DEFAULT_CHUNK_SIZE_TOKENS = 384
DEFAULT_CHUNK_STRIDE_TOKENS = 48
DEFAULT_MAX_QA_PER_CHUNK = 3

#: The generation contract sent to the model adapter.
QA_SYSTEM = ("Write question-answer pairs a student could be drilled on, grounded ONLY "
             "in the given passage. Reply as a JSON array: "
             '[{"question": ..., "answer": ...}]. No prose.')

#: Drop reasons (single definition; the report counts by these).
DROP_MALFORMED = "malformed model output (not a JSON array of question/answer)"
DROP_OVERFLOW = "over max_qa_pairs_per_chunk"
DROP_EMPTY_FIELD = "empty question or answer"


def run(*, pdf_path: str, language_hint: str | None = None,
        chunk_size_tokens: int = DEFAULT_CHUNK_SIZE_TOKENS,
        chunk_stride_tokens: int = DEFAULT_CHUNK_STRIDE_TOKENS,
        max_qa_pairs_per_chunk: int = DEFAULT_MAX_QA_PER_CHUNK,
        output_path: str = "qa_dataset.jsonl",
        extract_pages: Callable[[str], list[dict[str, Any]]] | None = None,
        generate: Callable[[str, str], str] | None = None,
        sink: Callable[[str, str], str] | None = None) -> dict[str, Any]:
    """PDF → pages → chunks → Q&A pairs → JSONL, all seams injected."""
    if not isinstance(pdf_path, str) or not pdf_path:
        raise ValueError("pdf_path must be a non-empty path string")
    if not isinstance(max_qa_pairs_per_chunk, int) or max_qa_pairs_per_chunk < 1:
        raise ValueError(f"max_qa_pairs_per_chunk must be >= 1, got {max_qa_pairs_per_chunk!r}")
    if extract_pages is None:
        raise RuntimeError("requires an injected page extractor (extract_pages=(path) -> "
                           "[{'page': int, 'text': str}]); extracted text is never faked")
    if generate is None:
        raise RuntimeError("requires an injected model adapter (generate=(prompt, system) -> "
                           "json text); a training dataset is never fabricated")
    if sink is None:
        raise RuntimeError("requires an injected sink (sink=(path, jsonl_text) -> uri)")
    pages = extract_pages(pdf_path)
    if not isinstance(pages, list) or not pages:
        raise ValueError("extractor returned no pages")
    for i, p in enumerate(pages):
        if not isinstance(p, dict) or "page" not in p or "text" not in p:
            raise ValueError(f"pages[{i}] needs page and text")

    rows: list[dict[str, Any]] = []
    dropped: dict[str, int] = {DROP_MALFORMED: 0, DROP_OVERFLOW: 0, DROP_EMPTY_FIELD: 0}
    covered_pages: set[int] = set()
    total_chunks = 0
    for p in pages:
        chunked = chunk_run(document=str(p["text"]), chunk_size=chunk_size_tokens,
                            overlap=chunk_stride_tokens)["chunks"]
        for c in chunked["chunks"]:
            total_chunks += 1
            hint = f" (language: {language_hint})" if language_hint else ""
            reply = str(generate(f"Passage{hint}:\n{c['text']}", QA_SYSTEM))
            try:
                data = json.loads(reply.strip().removeprefix("```json").removesuffix("```").strip())
                if not isinstance(data, list):
                    raise ValueError("not a list")
            except (json.JSONDecodeError, ValueError):
                dropped[DROP_MALFORMED] += 1
                continue
            kept_this_chunk = 0
            for item in data:
                if kept_this_chunk >= max_qa_pairs_per_chunk:
                    dropped[DROP_OVERFLOW] += 1
                    continue
                q = str(item.get("question", "")).strip() if isinstance(item, dict) else ""
                a = str(item.get("answer", "")).strip() if isinstance(item, dict) else ""
                if not q or not a:
                    dropped[DROP_EMPTY_FIELD] += 1
                    continue
                rows.append({"question": q, "answer": a,
                             "source_pdf": pdf_path, "page": int(p["page"]),
                             "chunk_id": c["chunk_id"], "language_hint": language_hint,
                             "serves_truth": False})
                kept_this_chunk += 1
                covered_pages.add(int(p["page"]))
    jsonl = "\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in rows) + ("\n" if rows else "")
    uri = str(sink(output_path, jsonl))
    return {"output_jsonl_path": uri, "total_chunks": total_chunks,
            "total_qa_pairs": len(rows),
            "dropped_pairs": dropped,
            "coverage_pages": sorted(covered_pages),
            "pages_in": len(pages)}


def _selftest() -> None:
    pages = [
        {"page": 1, "text": "Photosynthesis converts sunlight into chemical energy. " * 6},
        {"page": 2, "text": "The water cycle moves water through evaporation and rain. " * 6},
    ]
    replies = {
        1: '[{"question": "What does photosynthesis convert?", "answer": "Sunlight into chemical energy"},'
           ' {"question": "Q2", "answer": "A2"}, {"question": "Q3", "answer": "A3"},'
           ' {"question": "Q4 over the cap", "answer": "A4"}]',
        2: 'not json at all',
    }
    def generate(prompt: str, system: str) -> str:
        assert system == QA_SYSTEM
        return replies[1] if "Photosynthesis" in prompt else replies[2]
    written: dict[str, str] = {}
    out = run(pdf_path="grade7-science.pdf", language_hint="fil",
              extract_pages=lambda p: pages, generate=generate,
              sink=lambda path, text: written.setdefault(f"file:///{path}", text) and f"file:///{path}" or f"file:///{path}",
              max_qa_pairs_per_chunk=3)
    # Pairs kept with page + chunk lineage; the cap and malformed output COUNTED.
    assert out["total_qa_pairs"] == 3 and out["coverage_pages"] == [1]
    assert out["dropped_pairs"][DROP_OVERFLOW] == 1
    assert out["dropped_pairs"][DROP_MALFORMED] == 1   # page 2's reply
    rows = [json.loads(l) for l in written[out["output_jsonl_path"]].splitlines()]
    assert rows[0]["page"] == 1 and rows[0]["chunk_id"].startswith("chunk-")
    assert all(r["serves_truth"] is False and r["language_hint"] == "fil" for r in rows)
    # Refusals: every missing seam refuses (nothing fabricated).
    for bad in (lambda: run(pdf_path="x", generate=generate, sink=lambda p, t: p),
                lambda: run(pdf_path="x", extract_pages=lambda p: pages, sink=lambda p, t: p),
                lambda: run(pdf_path="x", extract_pages=lambda p: pages, generate=generate),
                lambda: run(pdf_path="x", extract_pages=lambda p: [], generate=generate,
                            sink=lambda p, t: p)):
        raised = False
        try:
            bad()
        except (RuntimeError, ValueError):
            raised = True
        assert raised
    print("PASS — curriculum_qa_dataset_builder: injected extractor/model/sink (dataset "
          "never fabricated), strict JSON contract with counted drops (malformed/"
          "overflow/empty), page+chunk lineage on every pair, coverage reported verified")


if __name__ == "__main__":
    _selftest()
