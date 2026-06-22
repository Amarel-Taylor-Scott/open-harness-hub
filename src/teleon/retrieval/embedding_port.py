"""src.teleon.retrieval.embedding_port — the EMBEDDING abstraction: any embedder behind ONE port (agnostic, registry-populated).

Same pattern as ocr_port/llm_port/reranker_port: consumers depend on the PORT, never a specific embedder, so a future
embedder drops in with ZERO caller change. Selectable embedders are POPULATED FROM the tool_registry `embedding` plane.
The always-available WIRED baseline is a deterministic LEXICAL embedder (the component-search embedding — pure Python, no
dep), so the port genuinely works offline; learned/API embedders (sentence-transformers/bge/openai/cohere) escalate above
it and are honest 'not wired' until the model/key is present. serves_truth=false; Teleon layer.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol, runtime_checkable

from src.teleon.synthesis.component_search import INDEX_DIM, embed as _lexical_embed

_REPO = Path(__file__).resolve().parents[3]
#: embedding tool ids that need a model/key (escalation tier) — honest 'not wired' until present
_MODEL_EMBEDDERS = {"sentence_transformers", "bge_embed", "nomic_embed", "gte", "instructor_embed", "openai_embed",
                    "voyage_embed", "model2vec", "glove", "gensim"}


@runtime_checkable
class EmbeddingPort(Protocol):
    name: str
    dim: int
    def embed(self, text: str) -> list[float]: ...


class LexicalEmbedder:
    """Deterministic lexical embedder (char-trigram hash, ALWAYS available — the wired baseline). No model, no network."""
    name = "lexical"
    dim = INDEX_DIM
    def embed(self, text: str) -> list[float]:
        return _lexical_embed(text)
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [_lexical_embed(t) for t in texts]


class NotWiredEmbedder:
    """A registry embedder whose model/key isn't present — honest, never fabricates a vector."""
    def __init__(self, name: str):
        self.name, self.dim = name, 0
    def embed(self, text: str) -> list[float]:
        raise RuntimeError(f"embedder '{self.name}' not wired (needs its model/key); use 'auto' for the lexical baseline")


_NAME_ADAPTERS = {"auto": LexicalEmbedder, "lexical": LexicalEmbedder, "tfidf_sklearn": LexicalEmbedder}


def register_embedder_adapter(name: str, factory) -> None:
    """Future-proofing hook: wire a real embedder by name; callers of select_embedder never change."""
    _NAME_ADAPTERS[str(name)] = factory


def available_embedders() -> dict:
    reg = [t["id"] for t in json.loads((_REPO / "architecture" / "tool_registry.json").read_text())["tools"] if t.get("plane") == "embedding"]
    return {"registry_embedders": sorted(reg), "wired": sorted(_NAME_ADAPTERS), "serves_truth": False}


def select_embedder(name: str = "auto") -> EmbeddingPort:
    """Resolve an embedder by name/registry-id. 'auto' -> the always-available lexical baseline; a model embedder not yet
    wired -> an honest NotWiredEmbedder; an explicitly-registered adapter -> that. Never raises."""
    if name in _NAME_ADAPTERS:
        return _NAME_ADAPTERS[name]()
    if name in _MODEL_EMBEDDERS:
        return NotWiredEmbedder(name)
    return LexicalEmbedder()
