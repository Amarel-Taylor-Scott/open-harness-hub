"""src.teleon.retrieval.embedding_port — the EMBEDDING abstraction: any embedder behind ONE port (agnostic, registry-populated).

Same pattern as ocr_port/llm_port/reranker_port: consumers depend on the PORT, never a specific embedder, so a future
embedder drops in with ZERO caller change. Selectable embedders are POPULATED FROM the tool_registry `embedding` plane.
The always-available WIRED baseline is a deterministic LEXICAL embedder (the component-search embedding — pure Python, no
dep), so the port genuinely works offline; learned/API embedders (sentence-transformers/bge/openai/cohere) escalate above
it and are honest 'not wired' until the model/key is present. serves_truth=false; Teleon layer.
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Protocol, runtime_checkable

from src.teleon.registry.plane import Candidate, select
from src.teleon.synthesis.component_search import INDEX_DIM, embed as _lexical_embed

_OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
_LOCAL_EMBED_MODEL = "nomic-embed-text"
_NOMIC_DIM = 768

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


class LocalOllamaEmbedder:
    """LOCAL semantic embedder via Ollama (nomic-embed-text) — NO API KEY, runs on localhost, private + free.
    Local-first: the keyless, open-source answer to 'we need semantic embeddings'. Honest: raises if the local
    daemon isn't running (the caller falls back to the lexical baseline); never reaches for a cloud key."""
    name = "nomic_embed"
    dim = _NOMIC_DIM

    def embed(self, text: str) -> list[float]:
        body = json.dumps({"model": _LOCAL_EMBED_MODEL, "prompt": str(text)}).encode()
        req = urllib.request.Request(_OLLAMA_EMBED_URL, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as r:  # localhost only; no auth, no key
            return json.loads(r.read())["embedding"]

    def available(self) -> bool:
        try:
            v = self.embed("ping")
            return isinstance(v, list) and len(v) == self.dim
        except Exception:  # noqa: BLE001 — honest-offline: daemon down -> not available, caller falls back
            return False


_NAME_ADAPTERS = {"auto": LexicalEmbedder, "lexical": LexicalEmbedder, "tfidf_sklearn": LexicalEmbedder,
                  "nomic_embed": LocalOllamaEmbedder}  # local model wired -> no longer 'not wired', NO cloud key


def register_embedder_adapter(name: str, factory) -> None:
    """Future-proofing hook: wire a real embedder by name; callers of select_embedder never change."""
    _NAME_ADAPTERS[str(name)] = factory


#: the embedding PLANE — a declarative list of candidates the generic selector ranks. Add an embedder by appending
#: a Candidate (no selection-logic change); add a cloud embedder with keyless=False and it sorts LAST under
#: local_first but can win under best_quality. This replaces the rigid best_X() wrapper with a flexible plane.
def _embedding_plane() -> list[Candidate]:
    return [
        Candidate("lexical", LexicalEmbedder, locality="local", keyless=True, cost=0.0, quality=1),  # always-available floor
        Candidate("nomic_embed", LocalOllamaEmbedder, locality="local", keyless=True, cost=0.0, quality=3,
                  probe=lambda: LocalOllamaEmbedder().available()),
        # future: Candidate("openai_embed", OpenAIEmbedder, locality="cloud", keyless=False, cost=1.0, quality=4, probe=...)
    ]


def select_embedder_by_policy(policy: str = "local_first") -> EmbeddingPort:
    """Pick an embedder by POLICY over the plane (local_first | keyless_first | cheapest | best_quality | …),
    descending to the first available. Always returns a working embedder (the lexical floor backstops)."""
    return select(_embedding_plane(), policy) or LexicalEmbedder()


def best_embedder() -> EmbeddingPort:
    """Back-compat alias: the local-first policy over the embedding plane (local-semantic if up, else lexical).
    No longer a hardcoded branch — just one policy among many; never reaches for a cloud key."""
    return select_embedder_by_policy("local_first")


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
