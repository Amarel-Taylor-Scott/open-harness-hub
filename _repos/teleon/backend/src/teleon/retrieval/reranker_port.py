"""src.teleon.retrieval.reranker_port — the RERANKER abstraction: any reranker behind ONE port (agnostic, registry-populated).

Mirrors ocr_port/llm_port: components depend on the PORT, never a specific reranker, so a future reranker drops in with
ZERO caller change. The selectable rerankers are POPULATED FROM the tool_registry `reranker` plane. The always-available
WIRED baseline is a deterministic LEXICAL reranker (BM25-lite, pure Python, no dependency) — so the port genuinely works
offline, not a stub; cross-encoder/API rerankers (bge/cohere/jina) escalate above it and are honest 'not wired' until the
model/key is present. The descent picks the cheapest reranker that meets the bar. serves_truth=false; Teleon layer.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import math
import re
from pathlib import Path
from typing import Protocol, runtime_checkable

py_var_src_teleon_retrieval_reranker_port___REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])
py_var_src_teleon_retrieval_reranker_port___TOK = re.compile(r"[a-z0-9]+")
#: reranker tool ids that need a model/key (escalation tier) — honest 'not wired' until present
py_var_src_teleon_retrieval_reranker_port___MODEL_RERANKERS = {"bge_reranker", "cohere_rerank", "jina_reranker", "mxbai_rerank", "colbert", "sbert_crossencoder", "flashrank"}


@runtime_checkable
class py_class_src_teleon_retrieval_reranker_port__RerankerPort(Protocol):
    name: str
    def rank(self, py_arg_src_teleon_retrieval_reranker_port__py_class_src_teleon_retrieval_reranker_port__RerankerPort_rank__query: str, py_arg_src_teleon_retrieval_reranker_port__py_class_src_teleon_retrieval_reranker_port__RerankerPort_rank__docs: list[str], *, top_k: int | None = None) -> list[tuple[int, float]]: ...


class py_class_src_teleon_retrieval_reranker_port__LexicalReranker:
    """Deterministic BM25-lite reranker (pure Python, ALWAYS available — the wired baseline). Returns (doc_index, score)
    sorted desc. No model, no network, no dependency."""
    name = "lexical_bm25"

    def rank(self, py_arg_src_teleon_retrieval_reranker_port__py_class_src_teleon_retrieval_reranker_port__LexicalReranker_rank__query: str, py_arg_src_teleon_retrieval_reranker_port__py_class_src_teleon_retrieval_reranker_port__LexicalReranker_rank__docs: list[str], *, top_k: int | None = None) -> list[tuple[int, float]]:
        py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__q = py_var_src_teleon_retrieval_reranker_port___TOK.findall(py_arg_src_teleon_retrieval_reranker_port__py_class_src_teleon_retrieval_reranker_port__LexicalReranker_rank__query.lower())
        py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__toks = [py_var_src_teleon_retrieval_reranker_port___TOK.findall(d.lower()) for d in py_arg_src_teleon_retrieval_reranker_port__py_class_src_teleon_retrieval_reranker_port__LexicalReranker_rank__docs]
        py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__N = len(py_arg_src_teleon_retrieval_reranker_port__py_class_src_teleon_retrieval_reranker_port__LexicalReranker_rank__docs) or 1
        py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__df = {}
        for py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__t in py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__toks:
            for py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__w in set(py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__t):
                py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__df[py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__w] = py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__df.get(py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__w, 0) + 1
        py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__avgdl = (sum(len(py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__t) for py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__t in py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__toks) / py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__N) or 1.0
        py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__k1, py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__b = 1.5, 0.75
        py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__scored = []
        for py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__i, py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__t in enumerate(py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__toks):
            py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__tf = {}
            for py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__w in py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__t:
                py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__tf[py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__w] = py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__tf.get(py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__w, 0) + 1
            py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__s = 0.0
            for py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__w in py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__q:
                if py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__w in py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__tf:
                    py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__idf = math.log(1 + (py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__N - py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__df.get(py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__w, 0) + 0.5) / (py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__df.get(py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__w, 0) + 0.5))
                    py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__s += py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__idf * (py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__tf[py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__w] * (py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__k1 + 1)) / (py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__tf[py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__w] + py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__k1 * (1 - py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__b + py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__b * len(py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__t) / py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__avgdl))
            py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__scored.append((py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__i, round(py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__s, 4)))
        py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__scored.sort(key=lambda py_arg_src_teleon_retrieval_reranker_port__py_class_src_teleon_retrieval_reranker_port__LexicalReranker_rank__x: (-py_arg_src_teleon_retrieval_reranker_port__py_class_src_teleon_retrieval_reranker_port__LexicalReranker_rank__x[1], py_arg_src_teleon_retrieval_reranker_port__py_class_src_teleon_retrieval_reranker_port__LexicalReranker_rank__x[0]))
        return py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__scored[:top_k] if top_k else py_local_src_teleon_retrieval_reranker_port__LexicalReranker_rank__scored


class py_class_src_teleon_retrieval_reranker_port__NotWiredReranker:
    """A registry reranker whose model/key isn't present — honest, never fabricates a ranking."""
    def __init__(self, name: str):
        self.name = name
    def rank(self, py_arg_src_teleon_retrieval_reranker_port__py_class_src_teleon_retrieval_reranker_port__NotWiredReranker_rank__query: str, py_arg_src_teleon_retrieval_reranker_port__py_class_src_teleon_retrieval_reranker_port__NotWiredReranker_rank__docs: list[str], *, top_k: int | None = None):
        raise RuntimeError(f"reranker '{self.name}' not wired (needs its model/key); use 'auto' for the lexical baseline")


py_var_src_teleon_retrieval_reranker_port___NAME_ADAPTERS = {"auto": py_class_src_teleon_retrieval_reranker_port__LexicalReranker, "lexical_bm25": py_class_src_teleon_retrieval_reranker_port__LexicalReranker, "rank_bm25": py_class_src_teleon_retrieval_reranker_port__LexicalReranker}


def py_function_src_teleon_retrieval_reranker_port__register_reranker_adapter(py_arg_src_teleon_retrieval_reranker_port__py_function_src_teleon_retrieval_reranker_port__register_reranker_adapter__name: str, py_arg_src_teleon_retrieval_reranker_port__py_function_src_teleon_retrieval_reranker_port__register_reranker_adapter__factory) -> None:
    """Future-proofing hook: wire a real reranker (e.g. a cross-encoder) by name; callers of select_reranker never change."""
    py_var_src_teleon_retrieval_reranker_port___NAME_ADAPTERS[str(py_arg_src_teleon_retrieval_reranker_port__py_function_src_teleon_retrieval_reranker_port__register_reranker_adapter__name)] = py_arg_src_teleon_retrieval_reranker_port__py_function_src_teleon_retrieval_reranker_port__register_reranker_adapter__factory


def py_function_src_teleon_retrieval_reranker_port__available_rerankers() -> dict:
    py_local_src_teleon_retrieval_reranker_port__available_rerankers__reg = [t["id"] for t in json.loads((_resource("architecture") / "tool_registry.json").read_text())["tools"] if t.get("plane") == "reranker"]
    return {"registry_rerankers": sorted(py_local_src_teleon_retrieval_reranker_port__available_rerankers__reg), "wired": sorted(py_var_src_teleon_retrieval_reranker_port___NAME_ADAPTERS), "serves_truth": False}


def py_function_src_teleon_retrieval_reranker_port__select_reranker(py_arg_src_teleon_retrieval_reranker_port__py_function_src_teleon_retrieval_reranker_port__select_reranker__name: str = "auto") -> py_class_src_teleon_retrieval_reranker_port__RerankerPort:
    """Resolve a reranker by name/registry-id. 'auto' -> the always-available lexical baseline; a model reranker not yet
    wired -> an honest NotWiredReranker; an explicitly-registered adapter -> that. Never raises."""
    if py_arg_src_teleon_retrieval_reranker_port__py_function_src_teleon_retrieval_reranker_port__select_reranker__name in py_var_src_teleon_retrieval_reranker_port___NAME_ADAPTERS:
        return py_var_src_teleon_retrieval_reranker_port___NAME_ADAPTERS[py_arg_src_teleon_retrieval_reranker_port__py_function_src_teleon_retrieval_reranker_port__select_reranker__name]()
    if py_arg_src_teleon_retrieval_reranker_port__py_function_src_teleon_retrieval_reranker_port__select_reranker__name in py_var_src_teleon_retrieval_reranker_port___MODEL_RERANKERS:
        return py_class_src_teleon_retrieval_reranker_port__NotWiredReranker(py_arg_src_teleon_retrieval_reranker_port__py_function_src_teleon_retrieval_reranker_port__select_reranker__name)
    return py_class_src_teleon_retrieval_reranker_port__LexicalReranker()
