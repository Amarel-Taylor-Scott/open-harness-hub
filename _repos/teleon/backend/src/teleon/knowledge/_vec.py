"""knowledge._vec — shared embedding + cosine helpers for the Global Software Knowledge Graph.

The embedder is a PLANE (fork/variation law): runtime defaults to best_embedder() (local Ollama nomic-embed when
present, lexical floor otherwise), but any callable can be injected — proofs inject the deterministic lexical floor
so the gate is embedder-agnostic and fast (no network)."""
from __future__ import annotations

import math

py_var_src_teleon_knowledge__vec___DEFAULT = None


def py_function_src_teleon_knowledge__vec___default_embedder():
    global py_var_src_teleon_knowledge__vec___DEFAULT
    if py_var_src_teleon_knowledge__vec___DEFAULT is None:
        from ..retrieval.embedding_port import py_function_src_teleon_retrieval_embedding_port__best_embedder
        py_var_src_teleon_knowledge__vec___DEFAULT = py_function_src_teleon_retrieval_embedding_port__best_embedder()
    return py_var_src_teleon_knowledge__vec___DEFAULT


def py_function_src_teleon_knowledge__vec__embed(py_arg_src_teleon_knowledge__vec__py_function_src_teleon_knowledge__vec__embed__text: str, py_arg_src_teleon_knowledge__vec__py_function_src_teleon_knowledge__vec__embed__embed_fn=None) -> list[float]:
    if py_arg_src_teleon_knowledge__vec__py_function_src_teleon_knowledge__vec__embed__embed_fn is not None:
        return py_arg_src_teleon_knowledge__vec__py_function_src_teleon_knowledge__vec__embed__embed_fn(py_arg_src_teleon_knowledge__vec__py_function_src_teleon_knowledge__vec__embed__text or "")
    return py_function_src_teleon_knowledge__vec___default_embedder().embed(py_arg_src_teleon_knowledge__vec__py_function_src_teleon_knowledge__vec__embed__text or "")


def py_function_src_teleon_knowledge__vec__cosine(py_arg_src_teleon_knowledge__vec__py_function_src_teleon_knowledge__vec__cosine__a: list[float], py_arg_src_teleon_knowledge__vec__py_function_src_teleon_knowledge__vec__cosine__b: list[float]) -> float:
    if not py_arg_src_teleon_knowledge__vec__py_function_src_teleon_knowledge__vec__cosine__a or not py_arg_src_teleon_knowledge__vec__py_function_src_teleon_knowledge__vec__cosine__b or len(py_arg_src_teleon_knowledge__vec__py_function_src_teleon_knowledge__vec__cosine__a) != len(py_arg_src_teleon_knowledge__vec__py_function_src_teleon_knowledge__vec__cosine__b):
        return 0.0
    py_local_src_teleon_knowledge__vec__cosine__dot = sum(x * y for x, y in zip(py_arg_src_teleon_knowledge__vec__py_function_src_teleon_knowledge__vec__cosine__a, py_arg_src_teleon_knowledge__vec__py_function_src_teleon_knowledge__vec__cosine__b))
    py_local_src_teleon_knowledge__vec__cosine__na = math.sqrt(sum(x * x for x in py_arg_src_teleon_knowledge__vec__py_function_src_teleon_knowledge__vec__cosine__a))
    py_local_src_teleon_knowledge__vec__cosine__nb = math.sqrt(sum(y * y for y in py_arg_src_teleon_knowledge__vec__py_function_src_teleon_knowledge__vec__cosine__b))
    return py_local_src_teleon_knowledge__vec__cosine__dot / (py_local_src_teleon_knowledge__vec__cosine__na * py_local_src_teleon_knowledge__vec__cosine__nb) if py_local_src_teleon_knowledge__vec__cosine__na and py_local_src_teleon_knowledge__vec__cosine__nb else 0.0


def py_function_src_teleon_knowledge__vec__lexical_embed_fn():
    """The deterministic, keyless lexical embedder (one fork) — used by proofs for reproducibility."""
    from ..retrieval.embedding_port import py_class_src_teleon_retrieval_embedding_port__LexicalEmbedder
    return py_class_src_teleon_retrieval_embedding_port__LexicalEmbedder().embed
