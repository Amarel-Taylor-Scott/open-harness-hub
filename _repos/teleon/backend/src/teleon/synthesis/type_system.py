"""type_system — System 6 / the representation-agnostic seam: the type LATTICE (subtyping) + coercion graph.

Grounded in type-directed component-based synthesis (SyPeT models a typed component library as a Petri net; TYGAR adds
polymorphism; APIphany shows SEMANTIC types both specify intent and direct the search). Two mechanisms:
  - SUBTYPING widens what composes for free: a producer of a SUBTYPE satisfies a consumer of its SUPERTYPE (a jpeg can
    feed an image consumer).
  - COERCION auto-inserts a converter COMPONENT when two types don't match even by subtyping (html -> markdown), the way
    a compiler inserts a cast. coercion_path returns the converter sequence; the composer inserts those nodes.
Single source: _repos/shared-backend-components/architecture/type_lattice.json. serves_truth=false (it types the flow; it does not judge truth).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from collections import deque
from functools import lru_cache
from pathlib import Path

py_var_src_teleon_synthesis_type_system___LATTICE = _resource("architecture") / "type_lattice.json"


@lru_cache(maxsize=1)
def py_function_src_teleon_synthesis_type_system___lattice() -> dict:
    return json.loads(py_var_src_teleon_synthesis_type_system___LATTICE.read_text())


def py_function_src_teleon_synthesis_type_system__supertype_chain(py_arg_src_teleon_synthesis_type_system__supertype_chain__t: str) -> list:
    """[t, supertype(t), ...] up to the root, cycle-safe."""
    py_local_src_teleon_synthesis_type_system__supertype_chain__subs = py_function_src_teleon_synthesis_type_system___lattice()["subtypes"]
    py_local_src_teleon_synthesis_type_system__supertype_chain__chain, py_local_src_teleon_synthesis_type_system__supertype_chain__cur, py_local_src_teleon_synthesis_type_system__supertype_chain__seen = [py_arg_src_teleon_synthesis_type_system__supertype_chain__t], py_arg_src_teleon_synthesis_type_system__supertype_chain__t, {py_arg_src_teleon_synthesis_type_system__supertype_chain__t}
    while py_local_src_teleon_synthesis_type_system__supertype_chain__cur in py_local_src_teleon_synthesis_type_system__supertype_chain__subs and py_local_src_teleon_synthesis_type_system__supertype_chain__subs[py_local_src_teleon_synthesis_type_system__supertype_chain__cur] not in py_local_src_teleon_synthesis_type_system__supertype_chain__seen:
        py_local_src_teleon_synthesis_type_system__supertype_chain__cur = py_local_src_teleon_synthesis_type_system__supertype_chain__subs[py_local_src_teleon_synthesis_type_system__supertype_chain__cur]
        py_local_src_teleon_synthesis_type_system__supertype_chain__chain.append(py_local_src_teleon_synthesis_type_system__supertype_chain__cur)
        py_local_src_teleon_synthesis_type_system__supertype_chain__seen.add(py_local_src_teleon_synthesis_type_system__supertype_chain__cur)
    return py_local_src_teleon_synthesis_type_system__supertype_chain__chain


def py_function_src_teleon_synthesis_type_system__is_subtype(py_arg_src_teleon_synthesis_type_system__is_subtype__a: str, py_arg_src_teleon_synthesis_type_system__is_subtype__b: str) -> bool:
    """a <: b — a value of type a is usable where b is expected (a == b, or b is a supertype of a)."""
    return py_arg_src_teleon_synthesis_type_system__is_subtype__b in py_function_src_teleon_synthesis_type_system__supertype_chain(py_arg_src_teleon_synthesis_type_system__is_subtype__a)


def py_function_src_teleon_synthesis_type_system__types_compatible(py_arg_src_teleon_synthesis_type_system__types_compatible__produced, py_arg_src_teleon_synthesis_type_system__types_compatible__consumed) -> bool:
    """A producer (any of `produced`) can feed a consumer (any of `consumed`) iff some produced type IS-A some consumed
    type (subtyping-aware). Empty either side → True (untyped, never block)."""
    py_arg_src_teleon_synthesis_type_system__types_compatible__produced, py_arg_src_teleon_synthesis_type_system__types_compatible__consumed = list(py_arg_src_teleon_synthesis_type_system__types_compatible__produced or []), list(py_arg_src_teleon_synthesis_type_system__types_compatible__consumed or [])
    if not py_arg_src_teleon_synthesis_type_system__types_compatible__produced or not py_arg_src_teleon_synthesis_type_system__types_compatible__consumed:
        return True
    return any(py_function_src_teleon_synthesis_type_system__is_subtype(p, c) for p in py_arg_src_teleon_synthesis_type_system__types_compatible__produced for c in py_arg_src_teleon_synthesis_type_system__types_compatible__consumed)


@lru_cache(maxsize=1)
def py_function_src_teleon_synthesis_type_system___coercion_adj() -> dict:
    py_local_src_teleon_synthesis_type_system__coercion_adj__adj: dict = {}
    for py_local_src_teleon_synthesis_type_system__coercion_adj__c in py_function_src_teleon_synthesis_type_system___lattice()["coercions"]:
        py_local_src_teleon_synthesis_type_system__coercion_adj__adj.setdefault(py_local_src_teleon_synthesis_type_system__coercion_adj__c["from"], []).append((py_local_src_teleon_synthesis_type_system__coercion_adj__c["to"], py_local_src_teleon_synthesis_type_system__coercion_adj__c["via"]))
    return py_local_src_teleon_synthesis_type_system__coercion_adj__adj


def py_function_src_teleon_synthesis_type_system__coercion_path(py_arg_src_teleon_synthesis_type_system__coercion_path__from_t: str, py_arg_src_teleon_synthesis_type_system__coercion_path__to_t: str) -> list | None:
    """Shortest sequence of converter components turning from_t into something IS-A to_t (subtyping is free). [] if
    already compatible; None if nothing bridges. BFS = fewest converters."""
    if py_function_src_teleon_synthesis_type_system__is_subtype(py_arg_src_teleon_synthesis_type_system__coercion_path__from_t, py_arg_src_teleon_synthesis_type_system__coercion_path__to_t):
        return []
    py_local_src_teleon_synthesis_type_system__coercion_path__adj, py_local_src_teleon_synthesis_type_system__coercion_path__seen, py_local_src_teleon_synthesis_type_system__coercion_path__q = py_function_src_teleon_synthesis_type_system___coercion_adj(), {py_arg_src_teleon_synthesis_type_system__coercion_path__from_t}, deque([(py_arg_src_teleon_synthesis_type_system__coercion_path__from_t, [])])
    while py_local_src_teleon_synthesis_type_system__coercion_path__q:
        py_local_src_teleon_synthesis_type_system__coercion_path__cur, py_local_src_teleon_synthesis_type_system__coercion_path__path = py_local_src_teleon_synthesis_type_system__coercion_path__q.popleft()
        for py_local_src_teleon_synthesis_type_system__coercion_path__nxt, py_local_src_teleon_synthesis_type_system__coercion_path__via in py_local_src_teleon_synthesis_type_system__coercion_path__adj.get(py_local_src_teleon_synthesis_type_system__coercion_path__cur, []):
            if py_local_src_teleon_synthesis_type_system__coercion_path__nxt in py_local_src_teleon_synthesis_type_system__coercion_path__seen:
                continue
            py_local_src_teleon_synthesis_type_system__coercion_path__np = py_local_src_teleon_synthesis_type_system__coercion_path__path + [py_local_src_teleon_synthesis_type_system__coercion_path__via]
            if py_function_src_teleon_synthesis_type_system__is_subtype(py_local_src_teleon_synthesis_type_system__coercion_path__nxt, py_arg_src_teleon_synthesis_type_system__coercion_path__to_t):
                return py_local_src_teleon_synthesis_type_system__coercion_path__np
            py_local_src_teleon_synthesis_type_system__coercion_path__seen.add(py_local_src_teleon_synthesis_type_system__coercion_path__nxt)
            py_local_src_teleon_synthesis_type_system__coercion_path__q.append((py_local_src_teleon_synthesis_type_system__coercion_path__nxt, py_local_src_teleon_synthesis_type_system__coercion_path__np))
    return None


def py_function_src_teleon_synthesis_type_system__bridge(py_arg_src_teleon_synthesis_type_system__bridge__produced, py_arg_src_teleon_synthesis_type_system__bridge__consumed) -> list | None:
    """[] if already type-compatible; the shortest converter sequence if a coercion bridges some produced→consumed pair;
    None if nothing bridges (honest — the composer cannot connect this edge)."""
    py_arg_src_teleon_synthesis_type_system__bridge__produced, py_arg_src_teleon_synthesis_type_system__bridge__consumed = list(py_arg_src_teleon_synthesis_type_system__bridge__produced or []), list(py_arg_src_teleon_synthesis_type_system__bridge__consumed or [])
    if py_function_src_teleon_synthesis_type_system__types_compatible(py_arg_src_teleon_synthesis_type_system__bridge__produced, py_arg_src_teleon_synthesis_type_system__bridge__consumed):
        return []
    py_local_src_teleon_synthesis_type_system__bridge__best = None
    for py_local_src_teleon_synthesis_type_system__bridge__p in py_arg_src_teleon_synthesis_type_system__bridge__produced:
        for py_local_src_teleon_synthesis_type_system__bridge__c in py_arg_src_teleon_synthesis_type_system__bridge__consumed:
            py_local_src_teleon_synthesis_type_system__bridge__path = py_function_src_teleon_synthesis_type_system__coercion_path(py_local_src_teleon_synthesis_type_system__bridge__p, py_local_src_teleon_synthesis_type_system__bridge__c)
            if py_local_src_teleon_synthesis_type_system__bridge__path is not None and (py_local_src_teleon_synthesis_type_system__bridge__best is None or len(py_local_src_teleon_synthesis_type_system__bridge__path) < len(py_local_src_teleon_synthesis_type_system__bridge__best)):
                py_local_src_teleon_synthesis_type_system__bridge__best = py_local_src_teleon_synthesis_type_system__bridge__path
    return py_local_src_teleon_synthesis_type_system__bridge__best
