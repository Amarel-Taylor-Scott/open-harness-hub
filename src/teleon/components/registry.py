"""registry — the uniform Component model + the plane-invoker registry (seam 1: one invoke shape over bespoke ports).

Every plane has at most one INVOKER: a callable(inputs: dict) -> outputs: dict that wraps that plane's real port and
maps the uniform typed inputs to the port's bespoke call. A plane with no wired invoker is HONESTLY unavailable (invoke
raises ComponentUnavailable — never a fabricated output). A future port drops in via register_component_invoker with
zero change to callers (the agnostic-adapter rule). serves_truth=false.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable

from src.teleon.synthesis.dag_contract import component_types

_REPO = Path(__file__).resolve().parents[3]


class ComponentUnavailable(RuntimeError):
    """The plane has no wired invoker, or its lane/provider is offline — an HONEST 'cannot run', not a fake result."""


# plane -> callable(inputs: dict) -> outputs: dict. Drop-in: register_component_invoker(plane, fn).
_PLANE_INVOKERS: dict[str, Callable[[dict], dict]] = {}


def register_component_invoker(plane: str, fn: Callable[[dict], dict]) -> None:
    """Wire (or override) the uniform invoker for a plane. The future-proofing hook — callers of make_component/invoke
    never change when a new port is wired."""
    _PLANE_INVOKERS[plane] = fn


def available_invokers() -> list:
    return sorted(_PLANE_INVOKERS)


@lru_cache(maxsize=1)
def _tool_index() -> dict:
    try:
        return {t["id"]: t for t in json.loads((_REPO / "architecture" / "tool_registry.json").read_text())["tools"]}
    except Exception:  # noqa: BLE001
        return {}


def _plane_of(component_id: str) -> str | None:
    bare = component_id.split(":", 1)[1] if ":" in component_id else component_id
    if bare == "llm":
        return "llm"
    t = _tool_index().get(bare)
    return t.get("plane") if t else None


@dataclass(frozen=True)
class Component:
    """A registry component behind the uniform interface: invoke(typed_inputs) -> typed_outputs. consumes/produces are
    the plane's declared I/O types (from plane_io_contracts), so a DAG can type-check + thread values by type."""
    id: str
    plane: str | None
    consumes: tuple
    produces: tuple
    deterministic: bool

    def invoke(self, inputs: dict) -> dict:
        fn = _PLANE_INVOKERS.get(self.plane)
        if fn is None:
            raise ComponentUnavailable(f"plane {self.plane!r} has no wired invoker — register_component_invoker({self.plane!r}, fn) to add one")
        out = fn(inputs)
        if not isinstance(out, dict):
            raise ComponentUnavailable(f"invoker for plane {self.plane!r} returned {type(out).__name__}, not a typed-output dict")
        return out


def make_component(component_id: str, *, plane: str | None = None) -> Component:
    """Resolve a component id (or a bare plane) to the uniform Component, typed from plane_io_contracts."""
    plane = plane or _plane_of(component_id)
    consumes, produces = component_types(plane)
    bare = component_id.split(":", 1)[1] if ":" in component_id else component_id
    det = bool(_tool_index().get(bare, {}).get("deterministic")) if bare != "llm" else False
    return Component(id=component_id, plane=plane, consumes=tuple(consumes), produces=tuple(produces), deterministic=det)


# --- wired invokers: map the uniform typed I/O to each real port's bespoke call (honest when a lane is offline) -------

def _llm_invoker(inputs: dict) -> dict:
    from src.teleon.llm_port import select_llm
    port = select_llm("auto")
    if not port.available():
        raise ComponentUnavailable("llm lane offline (no provider reachable)")
    text = inputs.get("text") or inputs.get("record") or ""
    return {"text": port.complete(system="You are one component in a data pipeline. Answer concisely.", user=str(text))}


def _embedding_invoker(inputs: dict) -> dict:
    from src.teleon.retrieval.embedding_port import select_embedder
    emb = select_embedder("auto")
    t = inputs.get("text") if inputs.get("text") is not None else inputs.get("text_chunks")
    if isinstance(t, list):
        return {"vector": emb.embed_batch(t)}
    return {"vector": emb.embed(str(t or ""))}


def _reranker_invoker(inputs: dict) -> dict:
    from src.teleon.retrieval.reranker_port import select_reranker
    q = str(inputs.get("query") or "")
    docs = list(inputs.get("ranked_docs") or inputs.get("docs") or [])
    ranked = select_reranker("auto").rank(q, docs)
    return {"ranked_docs": [docs[i] for i, _ in ranked]}


def _search_invoker(inputs: dict) -> dict:
    from src.teleon.dag.real_steps import network_allowed
    from src.teleon.retrieval.search_port import select_search
    if not network_allowed():
        raise ComponentUnavailable("search needs network — honest offline (no fabricated results)")
    return {"sources": select_search("auto").search(str(inputs.get("query") or ""))}


def _ocr_invoker(inputs: dict) -> dict:
    from src.teleon.extraction.ocr_port import select_ocr
    src = inputs.get("document") or inputs.get("bytes") or inputs.get("image")
    port = select_ocr("auto")
    if not port.available():
        raise ComponentUnavailable("ocr provider not wired/reachable")
    return {"text": port.extract(src)}


for _p, _fn in {"llm": _llm_invoker, "embedding": _embedding_invoker, "reranker": _reranker_invoker,
                "search": _search_invoker, "ocr": _ocr_invoker}.items():
    register_component_invoker(_p, _fn)
