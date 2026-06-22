"""src.teleon.retrieval.reranker_port — the RERANKER abstraction: any reranker behind ONE port (agnostic, registry-populated).

Mirrors ocr_port/llm_port: components depend on the PORT, never a specific reranker, so a future reranker drops in with
ZERO caller change. The selectable rerankers are POPULATED FROM the tool_registry `reranker` plane. The always-available
WIRED baseline is a deterministic LEXICAL reranker (BM25-lite, pure Python, no dependency) — so the port genuinely works
offline, not a stub; cross-encoder/API rerankers (bge/cohere/jina) escalate above it and are honest 'not wired' until the
model/key is present. The descent picks the cheapest reranker that meets the bar. serves_truth=false; Teleon layer.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Protocol, runtime_checkable

_REPO = Path(__file__).resolve().parents[3]
_TOK = re.compile(r"[a-z0-9]+")
#: reranker tool ids that need a model/key (escalation tier) — honest 'not wired' until present
_MODEL_RERANKERS = {"bge_reranker", "cohere_rerank", "jina_reranker", "mxbai_rerank", "colbert", "sbert_crossencoder", "flashrank"}


@runtime_checkable
class RerankerPort(Protocol):
    name: str
    def rank(self, query: str, docs: list[str], *, top_k: int | None = None) -> list[tuple[int, float]]: ...


class LexicalReranker:
    """Deterministic BM25-lite reranker (pure Python, ALWAYS available — the wired baseline). Returns (doc_index, score)
    sorted desc. No model, no network, no dependency."""
    name = "lexical_bm25"

    def rank(self, query: str, docs: list[str], *, top_k: int | None = None) -> list[tuple[int, float]]:
        q = _TOK.findall(query.lower())
        toks = [_TOK.findall(d.lower()) for d in docs]
        N = len(docs) or 1
        df = {}
        for t in toks:
            for w in set(t):
                df[w] = df.get(w, 0) + 1
        avgdl = (sum(len(t) for t in toks) / N) or 1.0
        k1, b = 1.5, 0.75
        scored = []
        for i, t in enumerate(toks):
            tf = {}
            for w in t:
                tf[w] = tf.get(w, 0) + 1
            s = 0.0
            for w in q:
                if w in tf:
                    idf = math.log(1 + (N - df.get(w, 0) + 0.5) / (df.get(w, 0) + 0.5))
                    s += idf * (tf[w] * (k1 + 1)) / (tf[w] + k1 * (1 - b + b * len(t) / avgdl))
            scored.append((i, round(s, 4)))
        scored.sort(key=lambda x: (-x[1], x[0]))
        return scored[:top_k] if top_k else scored


class NotWiredReranker:
    """A registry reranker whose model/key isn't present — honest, never fabricates a ranking."""
    def __init__(self, name: str):
        self.name = name
    def rank(self, query: str, docs: list[str], *, top_k: int | None = None):
        raise RuntimeError(f"reranker '{self.name}' not wired (needs its model/key); use 'auto' for the lexical baseline")


_NAME_ADAPTERS = {"auto": LexicalReranker, "lexical_bm25": LexicalReranker, "rank_bm25": LexicalReranker}


def register_reranker_adapter(name: str, factory) -> None:
    """Future-proofing hook: wire a real reranker (e.g. a cross-encoder) by name; callers of select_reranker never change."""
    _NAME_ADAPTERS[str(name)] = factory


def available_rerankers() -> dict:
    reg = [t["id"] for t in json.loads((_REPO / "architecture" / "tool_registry.json").read_text())["tools"] if t.get("plane") == "reranker"]
    return {"registry_rerankers": sorted(reg), "wired": sorted(_NAME_ADAPTERS), "serves_truth": False}


def select_reranker(name: str = "auto") -> RerankerPort:
    """Resolve a reranker by name/registry-id. 'auto' -> the always-available lexical baseline; a model reranker not yet
    wired -> an honest NotWiredReranker; an explicitly-registered adapter -> that. Never raises."""
    if name in _NAME_ADAPTERS:
        return _NAME_ADAPTERS[name]()
    if name in _MODEL_RERANKERS:
        return NotWiredReranker(name)
    return LexicalReranker()
