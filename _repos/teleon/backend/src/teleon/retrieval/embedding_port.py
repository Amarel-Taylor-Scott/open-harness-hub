"""src.teleon.retrieval.embedding_port — the EMBEDDING abstraction: any embedder behind ONE port (agnostic, registry-populated).

Same pattern as ocr_port/llm_port/reranker_port: consumers depend on the PORT, never a specific embedder, so a future
embedder drops in with ZERO caller change. Selectable embedders are POPULATED FROM the tool_registry `embedding` plane.
The always-available WIRED baseline is a deterministic LEXICAL embedder (the component-search embedding — pure Python, no
dep), so the port genuinely works offline; learned/API embedders (sentence-transformers/bge/openai/cohere) escalate above
it and are honest 'not wired' until the model/key is present. serves_truth=false; Teleon layer.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import urllib.request
from pathlib import Path
from typing import Protocol, runtime_checkable

from src.teleon.registry.plane import py_class_src_teleon_registry_plane__Candidate, py_function_src_teleon_registry_plane__select
from src.teleon.synthesis.component_search import py_const_src_teleon_synthesis_component_search__INDEX_DIM, py_function_src_teleon_synthesis_component_search__embed as _lexical_embed

py_var_src_teleon_retrieval_embedding_port___OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
py_var_src_teleon_retrieval_embedding_port___LOCAL_EMBED_MODEL = "nomic-embed-text"
py_var_src_teleon_retrieval_embedding_port___NOMIC_DIM = 768

py_var_src_teleon_retrieval_embedding_port___REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])
#: embedding tool ids that need a model/key (escalation tier) — honest 'not wired' until present
py_var_src_teleon_retrieval_embedding_port___MODEL_EMBEDDERS = {"sentence_transformers", "bge_embed", "nomic_embed", "gte", "instructor_embed", "openai_embed",
                    "voyage_embed", "model2vec", "glove", "gensim"}


@runtime_checkable
class py_class_src_teleon_retrieval_embedding_port__EmbeddingPort(Protocol):
    name: str
    dim: int
    def embed(self, py_arg_src_teleon_retrieval_embedding_port__py_class_src_teleon_retrieval_embedding_port__EmbeddingPort_embed__text: str) -> list[float]: ...


class py_class_src_teleon_retrieval_embedding_port__LexicalEmbedder:
    """Deterministic lexical embedder (char-trigram hash, ALWAYS available — the wired baseline). No model, no network."""
    name = "lexical"
    dim = py_const_src_teleon_synthesis_component_search__INDEX_DIM
    def embed(self, py_arg_src_teleon_retrieval_embedding_port__py_class_src_teleon_retrieval_embedding_port__LexicalEmbedder_embed__text: str) -> list[float]:
        return _lexical_embed(py_arg_src_teleon_retrieval_embedding_port__py_class_src_teleon_retrieval_embedding_port__LexicalEmbedder_embed__text)
    def embed_batch(self, py_arg_src_teleon_retrieval_embedding_port__py_class_src_teleon_retrieval_embedding_port__LexicalEmbedder_embed_batch__texts: list[str]) -> list[list[float]]:
        return [_lexical_embed(t) for t in py_arg_src_teleon_retrieval_embedding_port__py_class_src_teleon_retrieval_embedding_port__LexicalEmbedder_embed_batch__texts]


class py_class_src_teleon_retrieval_embedding_port__NotWiredEmbedder:
    """A registry embedder whose model/key isn't present — honest, never fabricates a vector."""
    def __init__(self, name: str):
        self.name, self.dim = name, 0
    def embed(self, py_arg_src_teleon_retrieval_embedding_port__py_class_src_teleon_retrieval_embedding_port__NotWiredEmbedder_embed__text: str) -> list[float]:
        raise RuntimeError(f"embedder '{self.name}' not wired (needs its model/key); use 'auto' for the lexical baseline")


class py_class_src_teleon_retrieval_embedding_port__LocalOllamaEmbedder:
    """LOCAL semantic embedder via Ollama (nomic-embed-text) — NO API KEY, runs on localhost, private + free.
    Local-first: the keyless, open-source answer to 'we need semantic embeddings'. Honest: raises if the local
    daemon isn't running (the caller falls back to the lexical baseline); never reaches for a cloud key."""
    name = "nomic_embed"
    dim = py_var_src_teleon_retrieval_embedding_port___NOMIC_DIM

    def embed(self, py_arg_src_teleon_retrieval_embedding_port__py_class_src_teleon_retrieval_embedding_port__LocalOllamaEmbedder_embed__text: str) -> list[float]:
        py_local_src_teleon_retrieval_embedding_port__LocalOllamaEmbedder_embed__body = json.dumps({"model": py_var_src_teleon_retrieval_embedding_port___LOCAL_EMBED_MODEL, "prompt": str(py_arg_src_teleon_retrieval_embedding_port__py_class_src_teleon_retrieval_embedding_port__LocalOllamaEmbedder_embed__text)}).encode()
        py_local_src_teleon_retrieval_embedding_port__LocalOllamaEmbedder_embed__req = urllib.request.Request(py_var_src_teleon_retrieval_embedding_port___OLLAMA_EMBED_URL, data=py_local_src_teleon_retrieval_embedding_port__LocalOllamaEmbedder_embed__body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(py_local_src_teleon_retrieval_embedding_port__LocalOllamaEmbedder_embed__req, timeout=20) as py_local_src_teleon_retrieval_embedding_port__LocalOllamaEmbedder_embed__r:  # localhost only; no auth, no key
            return json.loads(py_local_src_teleon_retrieval_embedding_port__LocalOllamaEmbedder_embed__r.read())["embedding"]

    def available(self) -> bool:
        try:
            py_local_src_teleon_retrieval_embedding_port__LocalOllamaEmbedder_available__v = self.embed("ping")
            return isinstance(py_local_src_teleon_retrieval_embedding_port__LocalOllamaEmbedder_available__v, list) and len(py_local_src_teleon_retrieval_embedding_port__LocalOllamaEmbedder_available__v) == self.dim
        except Exception:  # noqa: BLE001 — honest-offline: daemon down -> not available, caller falls back
            return False


py_var_src_teleon_retrieval_embedding_port___NAME_ADAPTERS = {"auto": py_class_src_teleon_retrieval_embedding_port__LexicalEmbedder, "lexical": py_class_src_teleon_retrieval_embedding_port__LexicalEmbedder, "tfidf_sklearn": py_class_src_teleon_retrieval_embedding_port__LexicalEmbedder,
                  "nomic_embed": py_class_src_teleon_retrieval_embedding_port__LocalOllamaEmbedder}  # local model wired -> no longer 'not wired', NO cloud key


def py_function_src_teleon_retrieval_embedding_port__register_embedder_adapter(py_arg_src_teleon_retrieval_embedding_port__py_function_src_teleon_retrieval_embedding_port__register_embedder_adapter__name: str, py_arg_src_teleon_retrieval_embedding_port__py_function_src_teleon_retrieval_embedding_port__register_embedder_adapter__factory) -> None:
    """Future-proofing hook: wire a real embedder by name; callers of select_embedder never change."""
    py_var_src_teleon_retrieval_embedding_port___NAME_ADAPTERS[str(py_arg_src_teleon_retrieval_embedding_port__py_function_src_teleon_retrieval_embedding_port__register_embedder_adapter__name)] = py_arg_src_teleon_retrieval_embedding_port__py_function_src_teleon_retrieval_embedding_port__register_embedder_adapter__factory


#: the embedding PLANE — a declarative list of candidates the generic selector ranks. Add an embedder by appending
#: a Candidate (no selection-logic change); add a cloud embedder with keyless=False and it sorts LAST under
#: local_first but can win under best_quality. This replaces the rigid best_X() wrapper with a flexible plane.
def py_function_src_teleon_retrieval_embedding_port___embedding_plane() -> list[py_class_src_teleon_registry_plane__Candidate]:
    return [
        py_class_src_teleon_registry_plane__Candidate("lexical", py_class_src_teleon_retrieval_embedding_port__LexicalEmbedder, locality="local", keyless=True, cost=0.0, quality=1),  # always-available floor
        py_class_src_teleon_registry_plane__Candidate("nomic_embed", py_class_src_teleon_retrieval_embedding_port__LocalOllamaEmbedder, locality="local", keyless=True, cost=0.0, quality=3,
                  probe=lambda: py_class_src_teleon_retrieval_embedding_port__LocalOllamaEmbedder().available()),
        # future: Candidate("openai_embed", OpenAIEmbedder, locality="cloud", keyless=False, cost=1.0, quality=4, probe=...)
    ]


def py_function_src_teleon_retrieval_embedding_port__select_embedder_by_policy(py_arg_src_teleon_retrieval_embedding_port__py_function_src_teleon_retrieval_embedding_port__select_embedder_by_policy__policy: str = "local_first") -> py_class_src_teleon_retrieval_embedding_port__EmbeddingPort:
    """Pick an embedder by POLICY over the plane (local_first | keyless_first | cheapest | best_quality | …),
    descending to the first available. Always returns a working embedder (the lexical floor backstops)."""
    return py_function_src_teleon_registry_plane__select(py_function_src_teleon_retrieval_embedding_port___embedding_plane(), py_arg_src_teleon_retrieval_embedding_port__py_function_src_teleon_retrieval_embedding_port__select_embedder_by_policy__policy) or py_class_src_teleon_retrieval_embedding_port__LexicalEmbedder()


def py_function_src_teleon_retrieval_embedding_port__best_embedder() -> py_class_src_teleon_retrieval_embedding_port__EmbeddingPort:
    """Back-compat alias: the local-first policy over the embedding plane (local-semantic if up, else lexical).
    No longer a hardcoded branch — just one policy among many; never reaches for a cloud key."""
    return py_function_src_teleon_retrieval_embedding_port__select_embedder_by_policy("local_first")


def py_function_src_teleon_retrieval_embedding_port__available_embedders() -> dict:
    py_local_src_teleon_retrieval_embedding_port__available_embedders__reg = [t["id"] for t in json.loads((_resource("architecture") / "tool_registry.json").read_text())["tools"] if t.get("plane") == "embedding"]
    return {"registry_embedders": sorted(py_local_src_teleon_retrieval_embedding_port__available_embedders__reg), "wired": sorted(py_var_src_teleon_retrieval_embedding_port___NAME_ADAPTERS), "serves_truth": False}


def py_function_src_teleon_retrieval_embedding_port__select_embedder(py_arg_src_teleon_retrieval_embedding_port__py_function_src_teleon_retrieval_embedding_port__select_embedder__name: str = "auto") -> py_class_src_teleon_retrieval_embedding_port__EmbeddingPort:
    """Resolve an embedder by name/registry-id. 'auto' -> the always-available lexical baseline; a model embedder not yet
    wired -> an honest NotWiredEmbedder; an explicitly-registered adapter -> that. Never raises."""
    if py_arg_src_teleon_retrieval_embedding_port__py_function_src_teleon_retrieval_embedding_port__select_embedder__name in py_var_src_teleon_retrieval_embedding_port___NAME_ADAPTERS:
        return py_var_src_teleon_retrieval_embedding_port___NAME_ADAPTERS[py_arg_src_teleon_retrieval_embedding_port__py_function_src_teleon_retrieval_embedding_port__select_embedder__name]()
    if py_arg_src_teleon_retrieval_embedding_port__py_function_src_teleon_retrieval_embedding_port__select_embedder__name in py_var_src_teleon_retrieval_embedding_port___MODEL_EMBEDDERS:
        return py_class_src_teleon_retrieval_embedding_port__NotWiredEmbedder(py_arg_src_teleon_retrieval_embedding_port__py_function_src_teleon_retrieval_embedding_port__select_embedder__name)
    return py_class_src_teleon_retrieval_embedding_port__LexicalEmbedder()
