"""Flexible, config-driven embedding provider for OpenHubForAI.

ONE place that resolves *which backend, which model, which dimension* so the
whole fleet (vector-store build, pgvector load, daily embedding batch, readiness
audit) shares a single embedding source — **local now, cloud later, by env var
only** (no code change to move to hosted). Per `_repos/shared-backend-components/docs/codex/no-magic-values.md`,
model→dim lives in `scripts._config.EMBEDDING_MODELS`; this module is the logic.

Backends (selected via ``OH_EMBED_BACKEND``, else ``auto``):

  * ``local-st``     sentence-transformers, on-box. **Promotable.** (needs the dep)
  * ``http-openai``  OpenAI-compatible ``/embeddings`` over stdlib ``urllib``.
                     **Promotable.** Cloud-ready: set ``OH_EMBED_BASE_URL`` +
                     ``OH_EMBED_API_KEY`` + a model. Works against OpenAI, Azure,
                     Together, vLLM/Ollama OpenAI-compat servers, etc.
  * ``hash``         deterministic feature-hashing bag-of-words. **NOT
                     promotable** (placeholder); the offline default so the
                     pipeline always runs with no deps and no network.

Environment:

  ===================  =====================================================
  OH_EMBED_BACKEND     auto | local-st | http-openai | hash   (default: auto)
  OH_EMBED_MODEL       model id (default: _config.DEFAULT_EMBEDDING_MODEL)
  OH_EMBED_BASE_URL    e.g. https://api.openai.com/v1   (http-openai)
  OH_EMBED_API_KEY     bearer token                      (http-openai)
  OH_EMBED_DIM         override output dim (else from the registry)
  ===================  =====================================================

``auto`` tries ``local-st`` (if importable), then ``http-openai`` (if base_url +
key are set), then falls back to ``hash``. Nothing fabricates a real vector:
only ``local-st`` and ``http-openai`` are ``promotable``. The resolved backend
reports its **true** identity — so a hash fallback can never masquerade as a
real model and slip past the promotion gate.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import urllib.request
from dataclasses import dataclass
from typing import Callable

from scripts._config import DEFAULT_EMBEDDING_MODEL, EMBEDDING_MODELS, HASH_BOW_FALLBACK_DIMENSIONS

# --- offline hash backend (single source; build_vector_store imports these) --
HASH_MODEL_ID = "hash-bow-v1"
HASH_DIM = HASH_BOW_FALLBACK_DIMENSIONS
_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_.+-]{1,40}")
_HTTP_TIMEOUT_S = 60


def content_hash(text: str) -> str:
    """Stable content hash so re-embeds are detectable and index deltas
    deterministic (the model id + dim + this hash travel with every vector)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _l2(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    return [v / norm for v in vec] if norm else vec


def hash_embed(text: str, dim: int = HASH_DIM) -> list[float]:
    """Deterministic signed feature-hashing bag-of-words, L2-normalized.

    Reproducible and searchable, but NOT semantic — placeholder only.
    """
    vec = [0.0] * dim
    for tok in _TOKEN_RE.findall(text.lower()):
        h = hashlib.sha1(tok.encode("utf-8")).digest()
        idx = int.from_bytes(h[:4], "big") % dim
        vec[idx] += 1.0 if (h[4] & 1) else -1.0
    return _l2(vec)


# --- backend value object ---------------------------------------------------
@dataclass
class EmbeddingBackend:
    """A resolved embedding backend with a uniform interface and honest identity."""

    name: str            # backend kind: local-st | http-openai | hash
    model_id: str        # the model actually producing vectors
    dim: int
    promotable: bool     # real semantic vectors? (hash => False => staging only)
    _embed_batch: Callable[[list[str]], list[list[float]]]
    normalization: str = "l2"

    def embed_one(self, text: str) -> list[float]:
        return self._embed_batch([text])[0]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return self._embed_batch(list(texts)) if texts else []

    def provenance(self) -> dict:
        """Reproducibility envelope stored alongside each vector."""
        return {
            "backend": self.name,
            "embedding_model": self.model_id,
            "dim": self.dim,
            "promotable": self.promotable,
            "normalization": self.normalization,
        }


# --- backend constructors ---------------------------------------------------
def _hash_backend(model_id: str = HASH_MODEL_ID) -> EmbeddingBackend:
    return EmbeddingBackend(
        name="hash", model_id=model_id, dim=HASH_DIM, promotable=False,
        _embed_batch=lambda texts: [hash_embed(t) for t in texts],
    )


def _local_st_backend(model_id: str) -> EmbeddingBackend:
    """sentence-transformers on-box. Raises if the dep/model is unavailable."""
    from sentence_transformers import SentenceTransformer  # type: ignore

    st = SentenceTransformer(model_id)
    dim = int(st.get_sentence_embedding_dimension())

    def batch(texts: list[str]) -> list[list[float]]:
        out = st.encode(texts, normalize_embeddings=True)
        return [[float(x) for x in row] for row in out]

    return EmbeddingBackend("local-st", model_id, dim, True, batch)


def _http_openai_backend(model_id: str, base_url: str, api_key: str,
                         dim: int | None = None) -> EmbeddingBackend:
    """OpenAI-compatible ``POST {base_url}/embeddings``. Cloud-ready, stdlib-only."""
    dim = dim or EMBEDDING_MODELS.get(model_id)
    if not dim:
        raise ValueError(
            f"unknown output dim for hosted model {model_id!r}; "
            "add it to scripts._config.EMBEDDING_MODELS or set OH_EMBED_DIM"
        )
    url = base_url.rstrip("/") + "/embeddings"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    def batch(texts: list[str]) -> list[list[float]]:
        payload = json.dumps({"model": model_id, "input": texts}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT_S) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        rows = sorted(data["data"], key=lambda d: d["index"])
        return [_l2([float(x) for x in row["embedding"]]) for row in rows]

    return EmbeddingBackend("http-openai", model_id, dim, True, batch)


# --- resolution -------------------------------------------------------------
def resolve_backend(model: str | None = None, backend: str | None = None) -> EmbeddingBackend:
    """Resolve the embedding backend from args + env. See module docstring."""
    model_id = model or os.environ.get("OH_EMBED_MODEL") or DEFAULT_EMBEDDING_MODEL
    backend = backend or os.environ.get("OH_EMBED_BACKEND") or "auto"
    base_url = os.environ.get("OH_EMBED_BASE_URL")
    api_key = os.environ.get("OH_EMBED_API_KEY")
    dim_env = os.environ.get("OH_EMBED_DIM")
    dim_override = int(dim_env) if dim_env else None

    # The hash backend is selected explicitly or by a recognized hash model id —
    # NOT by any id that merely starts with "hash" (that silently masked a real
    # model like "hash2vec" as the non-promotable placeholder).
    is_hash_id = model_id == HASH_MODEL_ID or model_id.startswith("hash-bow")
    if backend == "hash" or is_hash_id:
        return _hash_backend(model_id if is_hash_id else HASH_MODEL_ID)
    if backend == "local-st":
        return _local_st_backend(model_id)
    if backend == "http-openai":
        if not (base_url and api_key):
            raise ValueError("http-openai backend needs OH_EMBED_BASE_URL and OH_EMBED_API_KEY")
        return _http_openai_backend(model_id, base_url, api_key, dim_override)

    # auto: prefer on-box real vectors, then hosted, then the offline fallback.
    try:
        return _local_st_backend(model_id)
    except Exception:
        pass
    if base_url and api_key:
        try:
            return _http_openai_backend(model_id, base_url, api_key, dim_override)
        except Exception:
            pass
    return _hash_backend()


def describe_backend(model: str | None = None, backend: str | None = None) -> dict:
    """Resolve and summarise the active backend without embedding anything."""
    b = resolve_backend(model=model, backend=backend)
    prov = b.provenance()
    prov["note"] = (
        "real semantic vectors (promotable)" if b.promotable
        else "PLACEHOLDER hash vectors — staging only, blocked from promotion"
    )
    return prov


def _self_test() -> int:
    # 1. offline default resolves to the non-promotable hash backend.
    b = resolve_backend(backend="hash")
    assert b.name == "hash" and b.promotable is False and b.dim == HASH_DIM, b
    v = b.embed_one("reduce token cost with compression")
    assert len(v) == HASH_DIM and abs(math.sqrt(sum(x * x for x in v)) - 1.0) < 1e-6, "not L2-normalized"

    # 2. auto with no deps + no hosted creds falls back to hash (never fabricates).
    for var in ("OH_EMBED_BACKEND", "OH_EMBED_BASE_URL", "OH_EMBED_API_KEY", "OH_EMBED_MODEL"):
        os.environ.pop(var, None)
    auto = resolve_backend()
    assert auto.name == "hash" and auto.promotable is False, auto.provenance()

    # 3. http-openai requires creds; dim comes from the registry.
    try:
        resolve_backend(backend="http-openai")
        raise AssertionError("http-openai should require creds")
    except ValueError:
        pass
    os.environ["OH_EMBED_BASE_URL"] = "https://example.invalid/v1"
    os.environ["OH_EMBED_API_KEY"] = "sk-test"
    http = resolve_backend(model="text-embedding-3-small", backend="http-openai")
    assert http.name == "http-openai" and http.promotable is True and http.dim == 1536, http.provenance()
    for var in ("OH_EMBED_BASE_URL", "OH_EMBED_API_KEY"):
        os.environ.pop(var, None)

    print(json.dumps({
        "ok": True,
        "hash": _hash_backend().provenance(),
        "auto_offline": auto.provenance(),
        "http_openai_example": http.provenance(),
    }, indent=2))
    return 0


if __name__ == "__main__":
    import sys
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print(json.dumps(describe_backend(), indent=2))
