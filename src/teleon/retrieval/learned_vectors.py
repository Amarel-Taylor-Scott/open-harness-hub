#!/usr/bin/env python3
"""src.teleon.retrieval.learned_vectors — LEARNED semantic-vector port (real model when available; else HONEST lexical floor).

Upgrade #16 to the hybrid search. embedding_port already wires a deterministic LexicalEmbedder (the always-on floor)
and a local nomic LocalOllamaEmbedder; this port reaches one rung HIGHER for a LEARNED semantic model —
sentence-transformers (scripts._config.DEFAULT_SENTENCE_TRANSFORMERS_EMBEDDING_MODEL, dim DEFAULT_EMBEDDING_DIMENSIONS)
or local nomic-embed via Ollama — and falls back to the repo's existing deterministic lexical embedding when no model
is installed/reachable. It NEVER fabricates a model vector: the resolved backend reports its TRUE identity
(`is_learned`), so a lexical fallback can never masquerade as a learned model. It lives BEHIND the existing ports
(reusing their embedder classes) and modifies no existing file. serves_truth=false; Teleon layer.

  --self-test
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:                       # sys.path insert so a direct `python3 .../learned_vectors.py` run works
    sys.path.insert(0, str(_REPO))

from scripts._config import DEFAULT_EMBEDDING_DIMENSIONS, DEFAULT_SENTENCE_TRANSFORMERS_EMBEDDING_MODEL
from src.teleon.retrieval.embedding_port import LexicalEmbedder, LocalOllamaEmbedder, register_embedder_adapter
from src.teleon.synthesis.component_search import INDEX_DIM  # the lexical floor's dim (single source)

SERVES_TRUTH = False
#: backend names that denote a REAL learned model (so the façade can label honesty). Mirrors embedding_port names.
_LEARNED_BACKENDS = {"sentence_transformers", "nomic_embed"}


def _st_available() -> bool:
    """Network-free probe: is the sentence-transformers dependency importable? (Does NOT load/download a model.)"""
    return importlib.util.find_spec("sentence_transformers") is not None


class SentenceTransformersEmbedder:
    """LEARNED semantic embedder via sentence-transformers (config-driven model + dim). Lazy load; honest-raises if the
    dep/model is absent so the resolver falls back. Never fabricates a vector. Conforms to embedding_port.EmbeddingPort."""
    name = "sentence_transformers"

    def __init__(self, model_id: str = DEFAULT_SENTENCE_TRANSFORMERS_EMBEDDING_MODEL):
        self.model_id = model_id
        self.dim = DEFAULT_EMBEDDING_DIMENSIONS                       # config-driven; never a literal dim
        self._model = None

    def available(self) -> bool:
        return _st_available()

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_id)
        return self._model

    def embed(self, text: str) -> list[float]:
        v = self._load().encode([str(text)], normalize_embeddings=True)[0]
        return [float(x) for x in v]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        vs = self._load().encode([str(t) for t in texts], normalize_embeddings=True)
        return [[float(x) for x in v] for v in vs]


def resolve_learned_embedder(*, allow_model: bool = True, probe_st=None, probe_nomic=None):
    """Resolve the best AVAILABLE embedder, learned-first, with an HONEST deterministic-lexical fallback:
      sentence-transformers (dep present + a probe vector succeeds) → local nomic (Ollama up) → lexical floor.
    Probes are injectable so tests force them False to assert the fallback deterministically + offline (no network)."""
    probe_st = _st_available if probe_st is None else probe_st
    if allow_model:
        if probe_st():
            st = SentenceTransformersEmbedder()
            try:
                if len(st.embed("probe")) == st.dim:
                    return st
            except Exception:  # noqa: BLE001 — honest: dep present but model can't load offline → fall through
                pass
        nomic = LocalOllamaEmbedder()
        nprobe = nomic.available if probe_nomic is None else probe_nomic
        try:
            if nprobe():
                return nomic
        except Exception:  # noqa: BLE001 — honest: local daemon down → fall through
            pass
    return LexicalEmbedder()                                          # always-available deterministic floor


class LearnedVectorPort:
    """Uniform LEARNED-vector port: resolves a real semantic model when available, else the repo's lexical floor.
    Exposes the EmbeddingPort shape (name/dim/embed) plus `is_learned`/`backend_name` so callers know whether the
    vectors are semantic or the honest lexical fallback — a drop-in for embedding_port.select_embedder consumers."""
    name = "learned_vector"

    def __init__(self, *, allow_model: bool = True, probe_st=None, probe_nomic=None, backend=None):
        be = backend or resolve_learned_embedder(allow_model=allow_model, probe_st=probe_st, probe_nomic=probe_nomic)
        self._be = be
        self.backend_name = getattr(be, "name", "lexical")
        self.dim = getattr(be, "dim", INDEX_DIM)
        self.is_learned = self.backend_name in _LEARNED_BACKENDS
        self.serves_truth = False

    def embed(self, text: str) -> list[float]:
        return self._be.embed(text or "")

    def embed_batch(self, texts) -> list[list[float]]:
        f = getattr(self._be, "embed_batch", None)
        return f(list(texts)) if f else [self._be.embed(t or "") for t in texts]

    def info(self) -> dict:
        return {"name": self.name, "backend_name": self.backend_name, "dim": self.dim,
                "is_learned": self.is_learned, "serves_truth": False}


def register_learned_embedder(name: str = "learned_vector") -> None:
    """Opt-in: wire this learned port behind embedding_port.select_embedder(<name>) WITHOUT any import side effect
    (callers choose to call it; the existing port file is never modified)."""
    register_embedder_adapter(name, LearnedVectorPort)


def self_test() -> int:
    from src.teleon.synthesis.component_search import embed as _lex
    # forced model-unavailable → HONEST lexical fallback (never a fake model)
    p = LearnedVectorPort(allow_model=False)
    assert p.is_learned is False and p.backend_name == "lexical", p.info()
    assert p.dim == INDEX_DIM, (p.dim, INDEX_DIM)
    assert p.embed("agent orchestration") == _lex("agent orchestration"), "fallback IS the repo's lexical embed (no fake model)"
    assert p.embed("x") == p.embed("x") and len(p.embed("hello")) == p.dim, "deterministic + correct dim"
    # injected-false probes fall back deterministically (offline) → proves the resolution order is honest
    p2 = LearnedVectorPort(allow_model=True, probe_st=lambda: False, probe_nomic=lambda: False)
    assert p2.backend_name == "lexical" and p2.is_learned is False, "forced-unavailable model → honest lexical fallback"
    assert isinstance(_st_available(), bool), "ST dep-probe is network-free and returns a bool"
    assert resolve_learned_embedder(allow_model=False).__class__ is LexicalEmbedder, "resolver floor is the lexical embedder"
    st = SentenceTransformersEmbedder()
    assert st.name == "sentence_transformers" and st.dim == DEFAULT_EMBEDDING_DIMENSIONS, "learned identity is config-driven (no literal dim)"
    print(f"learned_vectors self-test: OK (learned model when available [sentence-transformers dim={DEFAULT_EMBEDDING_DIMENSIONS} / "
          f"local nomic], HONEST lexical fallback dim={INDEX_DIM} == repo embed, never fakes a model) serves_truth={SERVES_TRUTH}")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    print("usage: learned_vectors.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
