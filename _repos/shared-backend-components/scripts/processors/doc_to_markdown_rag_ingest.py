#!/usr/bin/env python3
"""Backs `processor/doc-to-markdown-rag-ingest` (process_kind ``extract.doc_to_rag``).

End-to-end document ingestion for a local agentic store (the Trove pattern):
convert a document to clean Markdown (INJECTED converter — markitdown/
docling adapters in production), auto-summarize it (INJECTED model adapter;
without one the summary is the deterministic first-paragraph extract,
HONESTLY labeled), chunk via the single-source recursive chunker, embed via
the injected embedder (or the repo's hash placeholder, labeled), and write
markdown + summary + chunks into the INJECTED store. Emits the index_record
identity (content-addressed) for the row-family discipline.

Contract: side_effects=write (the injected store only); on_error=raise.
Inputs document_path, task_id, chunk_size_tokens, chunk_stride_tokens,
model_adapter_ref, dense_embed, embedding_adapter_ref → markdown_path,
summary, chunk_count, scope_id, index_record_id.

CLI / self-test: python3 _repos/shared-backend-components/scripts/processors/doc_to_markdown_rag_ingest.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Callable

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _RR = str(next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2]))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts.embeddings import HASH_MODEL_ID, hash_embed
from scripts.processors.retrieval.recursive_character_chunker import run as chunk_run

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

DEFAULT_CHUNK_SIZE_TOKENS = 384
DEFAULT_CHUNK_STRIDE_TOKENS = 48

SUMMARY_METHOD_MODEL = "model-adapter"
SUMMARY_METHOD_FALLBACK = "first-paragraph extract (no model adapter — deterministic)"

HASH_ALGORITHM = "sha256"
INDEX_RECORD_PREFIX = "idx:"
SCOPE_PREFIX = "scope:"
ID_HEX_LEN = 24


def run(*, document_path: str, task_id: str,
        chunk_size_tokens: int = DEFAULT_CHUNK_SIZE_TOKENS,
        chunk_stride_tokens: int = DEFAULT_CHUNK_STRIDE_TOKENS,
        convert: Callable[[str], str] | None = None,
        summarize: Callable[[str], str] | None = None,
        dense_embed: bool = True,
        embedder: Callable[[str], list[float]] | None = None,
        store: dict[str, Any] | None = None) -> dict[str, Any]:
    """Ingest ``document_path`` end-to-end into the injected ``store``."""
    if not isinstance(document_path, str) or not document_path:
        raise ValueError("document_path must be a non-empty path/URI string")
    if not isinstance(task_id, str) or not task_id:
        raise ValueError("task_id must be a non-empty str")
    if convert is None:
        raise RuntimeError("doc_to_markdown_rag_ingest requires an injected converter "
                           "(convert=(path) -> markdown); converted text is never faked")
    if store is None or not isinstance(store, dict):
        raise TypeError("store must be the injected ingest store (a dict)")
    markdown = str(convert(document_path)).strip()
    if not markdown:
        raise ValueError("converter returned empty markdown — refusing to ingest nothing")

    if summarize is not None:
        summary = str(summarize(markdown)).strip()
        summary_method = SUMMARY_METHOD_MODEL
    else:
        summary = markdown.split("\n\n", 1)[0][:500]
        summary_method = SUMMARY_METHOD_FALLBACK

    chunked = chunk_run(document=markdown, chunk_size=chunk_size_tokens,
                        overlap=chunk_stride_tokens)["chunks"]
    embed = embedder if embedder is not None else hash_embed
    placeholder = embedder is None
    chunks = []
    for c in chunked["chunks"]:
        row = {**c, "task_id": task_id}
        if dense_embed:
            row["embedding"] = embed(c["text"])
            row["embedding_model"] = HASH_MODEL_ID if placeholder else "injected-embedder"
            row["embedding_is_placeholder"] = placeholder
        chunks.append(row)

    content_hash = hashlib.new(HASH_ALGORITHM, markdown.encode("utf-8")).hexdigest()
    scope_id = SCOPE_PREFIX + hashlib.new(
        HASH_ALGORITHM, f"{task_id}|{document_path}".encode()).hexdigest()[:ID_HEX_LEN]
    index_record_id = INDEX_RECORD_PREFIX + hashlib.new(
        HASH_ALGORITHM, f"{scope_id}|{content_hash}".encode()).hexdigest()[:ID_HEX_LEN]
    markdown_path = f"{scope_id}/document.md"
    store[markdown_path] = markdown                 # the write — injected store only
    store[f"{scope_id}/summary.md"] = summary
    store[f"{scope_id}/chunks.json"] = chunks
    store[f"{scope_id}/index_record.json"] = {
        "index_record_id": index_record_id, "scope_id": scope_id,
        "source_path": document_path, "content_hash": f"{HASH_ALGORITHM}:{content_hash}",
        "chunk_count": len(chunks), "summary_method": summary_method,
        "serves_truth": False,
    }
    return {"markdown_path": markdown_path, "summary": summary,
            "chunk_count": len(chunks), "scope_id": scope_id,
            "index_record_id": index_record_id, "summary_method": summary_method,
            "embedding_is_placeholder": placeholder if dense_embed else None}


def _selftest() -> None:
    doc_md = ("# Error resolution guide\n\nBanks must give provisional credit within ten "
              "business days of a notice.\n\n" + ("Detail paragraph about timelines. " * 40))
    converter = lambda p: doc_md
    store: dict[str, Any] = {}
    out = run(document_path="docs/guide.pdf", task_id="t-001", convert=converter,
              summarize=lambda md: "Guide to Reg E error-resolution timing.",
              store=store, chunk_size_tokens=80, chunk_stride_tokens=10)
    # The full pipeline ran: markdown + summary + chunks + index record in the store.
    assert store[out["markdown_path"]] == doc_md.strip()
    assert out["summary"].startswith("Guide to Reg E") and out["summary_method"] == SUMMARY_METHOD_MODEL
    assert out["chunk_count"] >= 2
    rec = store[f"{out['scope_id']}/index_record.json"]
    assert rec["index_record_id"] == out["index_record_id"]
    assert rec["content_hash"].startswith("sha256:") and rec["serves_truth"] is False
    # Chunks carry placeholder-honest embeddings (hash lane) by default.
    chunks = store[f"{out['scope_id']}/chunks.json"]
    assert all(c["embedding_is_placeholder"] is True and c["embedding_model"] == HASH_MODEL_ID
               for c in chunks)
    assert out["embedding_is_placeholder"] is True
    # No model adapter → deterministic first-paragraph summary, labeled.
    s2: dict[str, Any] = {}
    fb = run(document_path="docs/guide.pdf", task_id="t-002", convert=converter, store=s2)
    assert fb["summary_method"] == SUMMARY_METHOD_FALLBACK
    assert fb["summary"].startswith("# Error resolution guide")
    # Identity discipline: same (task, path, content) → same ids; new content → new index id.
    again = run(document_path="docs/guide.pdf", task_id="t-001", convert=converter, store={})
    assert again["scope_id"] == out["scope_id"] and again["index_record_id"] == out["index_record_id"]
    changed = run(document_path="docs/guide.pdf", task_id="t-001",
                  convert=lambda p: doc_md + " updated", store={})
    assert changed["index_record_id"] != out["index_record_id"]
    assert changed["scope_id"] == out["scope_id"]   # same scope, new content version
    # Refusals: no converter, empty conversion, no store.
    for bad in (lambda: run(document_path="x", task_id="t", store={}),
                lambda: run(document_path="x", task_id="t", convert=lambda p: " ", store={}),
                lambda: run(document_path="x", task_id="t", convert=converter)):
        raised = False
        try:
            bad()
        except (RuntimeError, ValueError, TypeError):
            raised = True
        assert raised
    print("PASS — doc_to_markdown_rag_ingest: injected converter (never faked), labeled "
          "model/fallback summaries, single-source chunker, placeholder-honest "
          "embeddings, content-addressed scope/index ids, store-only writes verified")


if __name__ == "__main__":
    _selftest()
