"""type_system — System 6 / the representation-agnostic seam: the type LATTICE (subtyping) + coercion graph.

Grounded in type-directed component-based synthesis (SyPeT models a typed component library as a Petri net; TYGAR adds
polymorphism; APIphany shows SEMANTIC types both specify intent and direct the search). Two mechanisms:
  - SUBTYPING widens what composes for free: a producer of a SUBTYPE satisfies a consumer of its SUPERTYPE (a jpeg can
    feed an image consumer).
  - COERCION auto-inserts a converter COMPONENT when two types don't match even by subtyping (html -> markdown), the way
    a compiler inserts a cast. coercion_path returns the converter sequence; the composer inserts those nodes.
Single source: architecture/type_lattice.json. serves_truth=false (it types the flow; it does not judge truth).
"""
from __future__ import annotations

import json
from collections import deque
from functools import lru_cache
from pathlib import Path

_LATTICE = Path(__file__).resolve().parents[3] / "architecture" / "type_lattice.json"


@lru_cache(maxsize=1)
def _lattice() -> dict:
    return json.loads(_LATTICE.read_text())


def supertype_chain(t: str) -> list:
    """[t, supertype(t), ...] up to the root, cycle-safe."""
    subs = _lattice()["subtypes"]
    chain, cur, seen = [t], t, {t}
    while cur in subs and subs[cur] not in seen:
        cur = subs[cur]
        chain.append(cur)
        seen.add(cur)
    return chain


def is_subtype(a: str, b: str) -> bool:
    """a <: b — a value of type a is usable where b is expected (a == b, or b is a supertype of a)."""
    return b in supertype_chain(a)


def types_compatible(produced, consumed) -> bool:
    """A producer (any of `produced`) can feed a consumer (any of `consumed`) iff some produced type IS-A some consumed
    type (subtyping-aware). Empty either side → True (untyped, never block)."""
    produced, consumed = list(produced or []), list(consumed or [])
    if not produced or not consumed:
        return True
    return any(is_subtype(p, c) for p in produced for c in consumed)


@lru_cache(maxsize=1)
def _coercion_adj() -> dict:
    adj: dict = {}
    for c in _lattice()["coercions"]:
        adj.setdefault(c["from"], []).append((c["to"], c["via"]))
    return adj


def coercion_path(from_t: str, to_t: str) -> list | None:
    """Shortest sequence of converter components turning from_t into something IS-A to_t (subtyping is free). [] if
    already compatible; None if nothing bridges. BFS = fewest converters."""
    if is_subtype(from_t, to_t):
        return []
    adj, seen, q = _coercion_adj(), {from_t}, deque([(from_t, [])])
    while q:
        cur, path = q.popleft()
        for nxt, via in adj.get(cur, []):
            if nxt in seen:
                continue
            np = path + [via]
            if is_subtype(nxt, to_t):
                return np
            seen.add(nxt)
            q.append((nxt, np))
    return None


def bridge(produced, consumed) -> list | None:
    """[] if already type-compatible; the shortest converter sequence if a coercion bridges some produced→consumed pair;
    None if nothing bridges (honest — the composer cannot connect this edge)."""
    produced, consumed = list(produced or []), list(consumed or [])
    if types_compatible(produced, consumed):
        return []
    best = None
    for p in produced:
        for c in consumed:
            path = coercion_path(p, c)
            if path is not None and (best is None or len(path) < len(best)):
                best = path
    return best
