"""registry — the uniform Component model + the plane-invoker registry (seam 1: one invoke shape over bespoke ports).

Every plane has at most one INVOKER: a callable(inputs: dict) -> outputs: dict that wraps that plane's real port and
maps the uniform typed inputs to the port's bespoke call. A plane with no wired invoker is HONESTLY unavailable (invoke
raises ComponentUnavailable — never a fabricated output). A future port drops in via register_component_invoker with
zero change to callers (the agnostic-adapter rule). serves_truth=false.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable

from src.teleon.synthesis.dag_contract import py_function_src_teleon_synthesis_dag_contract__component_types

py_var_src_teleon_components_registry___REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])


class py_class_src_teleon_components_registry__ComponentUnavailable(RuntimeError):
    """The plane has no wired invoker, or its lane/provider is offline — an HONEST 'cannot run', not a fake result."""


# plane -> callable(inputs: dict) -> outputs: dict. Drop-in: register_component_invoker(plane, fn).
py_var_src_teleon_components_registry___PLANE_INVOKERS: dict[str, Callable[[dict], dict]] = {}


def py_function_src_teleon_components_registry__register_component_invoker(py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__register_component_invoker__plane: str, py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__register_component_invoker__fn: Callable[[dict], dict]) -> None:
    """Wire (or override) the uniform invoker for a plane. The future-proofing hook — callers of make_component/invoke
    never change when a new port is wired."""
    py_var_src_teleon_components_registry___PLANE_INVOKERS[py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__register_component_invoker__plane] = py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__register_component_invoker__fn


def py_function_src_teleon_components_registry__available_invokers() -> list:
    return sorted(py_var_src_teleon_components_registry___PLANE_INVOKERS)


@lru_cache(maxsize=1)
def py_function_src_teleon_components_registry___tool_index() -> dict:
    try:
        return {t["id"]: t for t in json.loads((_resource("architecture") / "tool_registry.json").read_text())["tools"]}
    except Exception:  # noqa: BLE001
        return {}


def py_function_src_teleon_components_registry___plane_of(py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__plane_of__component_id: str) -> str | None:
    py_local_src_teleon_components_registry__plane_of__bare = py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__plane_of__component_id.split(":", 1)[1] if ":" in py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__plane_of__component_id else py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__plane_of__component_id
    if py_local_src_teleon_components_registry__plane_of__bare == "llm":
        return "llm"
    py_local_src_teleon_components_registry__plane_of__t = py_function_src_teleon_components_registry___tool_index().get(py_local_src_teleon_components_registry__plane_of__bare)
    return py_local_src_teleon_components_registry__plane_of__t.get("plane") if py_local_src_teleon_components_registry__plane_of__t else None


@dataclass(frozen=True)
class py_class_src_teleon_components_registry__Component:
    """A registry component behind the uniform interface: invoke(typed_inputs) -> typed_outputs. consumes/produces are
    the plane's declared I/O types (from plane_io_contracts), so a DAG can type-check + thread values by type."""
    id: str
    plane: str | None
    consumes: tuple
    produces: tuple
    deterministic: bool

    def invoke(self, py_arg_src_teleon_components_registry__py_class_src_teleon_components_registry__Component_invoke__inputs: dict) -> dict:
        py_local_src_teleon_components_registry__Component_invoke__fn = py_var_src_teleon_components_registry___PLANE_INVOKERS.get(self.plane)
        if py_local_src_teleon_components_registry__Component_invoke__fn is None:
            raise py_class_src_teleon_components_registry__ComponentUnavailable(f"plane {self.plane!r} has no wired invoker — register_component_invoker({self.plane!r}, fn) to add one")
        py_local_src_teleon_components_registry__Component_invoke__out = py_local_src_teleon_components_registry__Component_invoke__fn(py_arg_src_teleon_components_registry__py_class_src_teleon_components_registry__Component_invoke__inputs)
        if not isinstance(py_local_src_teleon_components_registry__Component_invoke__out, dict):
            raise py_class_src_teleon_components_registry__ComponentUnavailable(f"invoker for plane {self.plane!r} returned {type(py_local_src_teleon_components_registry__Component_invoke__out).__name__}, not a typed-output dict")
        return py_local_src_teleon_components_registry__Component_invoke__out


def py_function_src_teleon_components_registry__make_component(py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__make_component__component_id: str, *, plane: str | None = None) -> py_class_src_teleon_components_registry__Component:
    """Resolve a component id (or a bare plane) to the uniform Component, typed from plane_io_contracts."""
    plane = plane or py_function_src_teleon_components_registry___plane_of(py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__make_component__component_id)
    py_local_src_teleon_components_registry__make_component__consumes, py_local_src_teleon_components_registry__make_component__produces = py_function_src_teleon_synthesis_dag_contract__component_types(plane)
    py_local_src_teleon_components_registry__make_component__bare = py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__make_component__component_id.split(":", 1)[1] if ":" in py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__make_component__component_id else py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__make_component__component_id
    py_local_src_teleon_components_registry__make_component__det = bool(py_function_src_teleon_components_registry___tool_index().get(py_local_src_teleon_components_registry__make_component__bare, {}).get("deterministic")) if py_local_src_teleon_components_registry__make_component__bare != "llm" else False
    return py_class_src_teleon_components_registry__Component(id=py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__make_component__component_id, plane=plane, consumes=tuple(py_local_src_teleon_components_registry__make_component__consumes), produces=tuple(py_local_src_teleon_components_registry__make_component__produces), deterministic=py_local_src_teleon_components_registry__make_component__det)


# --- wired invokers: map the uniform typed I/O to each real port's bespoke call (honest when a lane is offline) -------

def py_function_src_teleon_components_registry___llm_invoker(py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__llm_invoker__inputs: dict) -> dict:
    from src.teleon.llm_port import select_llm
    py_local_src_teleon_components_registry__llm_invoker__port = select_llm("auto")
    if not py_local_src_teleon_components_registry__llm_invoker__port.available():
        raise py_class_src_teleon_components_registry__ComponentUnavailable("llm lane offline (no provider reachable)")
    py_local_src_teleon_components_registry__llm_invoker__text = py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__llm_invoker__inputs.get("text") or py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__llm_invoker__inputs.get("record") or ""
    return {"text": py_local_src_teleon_components_registry__llm_invoker__port.complete(system="You are one component in a data pipeline. Answer concisely.", user=str(py_local_src_teleon_components_registry__llm_invoker__text))}


def py_function_src_teleon_components_registry___embedding_invoker(py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__embedding_invoker__inputs: dict) -> dict:
    from src.teleon.retrieval.embedding_port import py_function_src_teleon_retrieval_embedding_port__select_embedder
    py_local_src_teleon_components_registry__embedding_invoker__emb = py_function_src_teleon_retrieval_embedding_port__select_embedder("auto")
    py_local_src_teleon_components_registry__embedding_invoker__t = py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__embedding_invoker__inputs.get("text") if py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__embedding_invoker__inputs.get("text") is not None else py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__embedding_invoker__inputs.get("text_chunks")
    if isinstance(py_local_src_teleon_components_registry__embedding_invoker__t, list):
        return {"vector": py_local_src_teleon_components_registry__embedding_invoker__emb.embed_batch(py_local_src_teleon_components_registry__embedding_invoker__t)}
    return {"vector": py_local_src_teleon_components_registry__embedding_invoker__emb.embed(str(py_local_src_teleon_components_registry__embedding_invoker__t or ""))}


def py_function_src_teleon_components_registry___reranker_invoker(py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__reranker_invoker__inputs: dict) -> dict:
    from src.teleon.retrieval.reranker_port import py_function_src_teleon_retrieval_reranker_port__select_reranker
    py_local_src_teleon_components_registry__reranker_invoker__q = str(py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__reranker_invoker__inputs.get("query") or "")
    py_local_src_teleon_components_registry__reranker_invoker__docs = list(py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__reranker_invoker__inputs.get("ranked_docs") or py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__reranker_invoker__inputs.get("docs") or [])
    py_local_src_teleon_components_registry__reranker_invoker__ranked = py_function_src_teleon_retrieval_reranker_port__select_reranker("auto").rank(py_local_src_teleon_components_registry__reranker_invoker__q, py_local_src_teleon_components_registry__reranker_invoker__docs)
    return {"ranked_docs": [py_local_src_teleon_components_registry__reranker_invoker__docs[i] for i, _ in py_local_src_teleon_components_registry__reranker_invoker__ranked]}


def py_function_src_teleon_components_registry___search_invoker(py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__search_invoker__inputs: dict) -> dict:
    from src.teleon.dag.real_steps import network_allowed
    from src.teleon.retrieval.search_port import py_function_src_teleon_retrieval_search_port__select_search
    if not network_allowed():
        raise py_class_src_teleon_components_registry__ComponentUnavailable("search needs network — honest offline (no fabricated results)")
    return {"sources": py_function_src_teleon_retrieval_search_port__select_search("auto").search(str(py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__search_invoker__inputs.get("query") or ""))}


def py_function_src_teleon_components_registry___ocr_invoker(py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__ocr_invoker__inputs: dict) -> dict:
    from src.teleon.extraction.ocr_port import select_ocr
    py_local_src_teleon_components_registry__ocr_invoker__src = py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__ocr_invoker__inputs.get("document") or py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__ocr_invoker__inputs.get("bytes") or py_arg_src_teleon_components_registry__py_function_src_teleon_components_registry__ocr_invoker__inputs.get("image")
    py_local_src_teleon_components_registry__ocr_invoker__port = select_ocr("auto")
    if not py_local_src_teleon_components_registry__ocr_invoker__port.available():
        raise py_class_src_teleon_components_registry__ComponentUnavailable("ocr provider not wired/reachable")
    return {"text": py_local_src_teleon_components_registry__ocr_invoker__port.extract(py_local_src_teleon_components_registry__ocr_invoker__src)}


for py_var_src_teleon_components_registry___p, py_var_src_teleon_components_registry___fn in {"llm": py_function_src_teleon_components_registry___llm_invoker, "embedding": py_function_src_teleon_components_registry___embedding_invoker, "reranker": py_function_src_teleon_components_registry___reranker_invoker,
                "search": py_function_src_teleon_components_registry___search_invoker, "ocr": py_function_src_teleon_components_registry___ocr_invoker}.items():
    py_function_src_teleon_components_registry__register_component_invoker(py_var_src_teleon_components_registry___p, py_var_src_teleon_components_registry___fn)
