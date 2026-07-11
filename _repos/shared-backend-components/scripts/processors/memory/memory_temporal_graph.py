#!/usr/bin/env python3
"""Backs `processor/memory-temporal-graph` (process_kind ``memory.temporal_graph``).

Zep/Graphiti-style **temporal knowledge graph** writer: facts are edges with
VALIDITY INTERVALS, so the graph answers "what was true *when*" instead of
only "what is true now". An incoming event ``(subject, predicate, object,
observed_at)`` becomes an edge valid from its observation time; when a newer
value arrives for the same ``(subject, predicate)``, the old edge is
**superseded — closed, never deleted** (the lossless law): its ``valid_to``
is set and it stays in the graph as queryable history.

Temporal semantics (all tested):

  * new value for an open ``(subject, predicate)`` → close the old edge at
    the new ``observed_at`` and link it ``superseded_by`` the new edge.
  * the SAME ``(subject, predicate, object)`` already open → idempotent
    no-op (replays add nothing).
  * an event OLDER than the open edge (out-of-order arrival) → inserted as
    already-closed history ending where the open edge begins; newer truth is
    never rewritten by late data.
  * time is the event's own ``observed_at`` — required, injected, never a
    wall clock.

Runtime contract (matches the manifest): ``process_kind =
memory.temporal_graph``; **idempotent**; **side_effects = write** — but ONLY
via the explicitly injected ``graph`` dict; **on_error = raise**.

Public API:
    from scripts.processors.memory.memory_temporal_graph import query_at, run
    out = run(event={"subject": "ohio", "predicate": "usury_rate_cap",
                     "object": "8%", "observed_at": t1}, graph=g)
    query_at(g, subject="ohio", predicate="usury_rate_cap", at=t1)  # -> "8%"

CLI / self-test:
    python3 _repos/shared-backend-components/scripts/processors/memory/memory_temporal_graph.py
    python3 -m scripts.processors.memory.memory_temporal_graph
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

# ── Configuration constants (single source of truth; No-Magic-Values) ────────

#: Hash algorithm + prefix for content-addressed edge ids. The id covers
#: (subject, predicate, object, observed_at) so the same event always mints
#: the same edge id — replays dedupe instead of duplicating.
HASH_ALGORITHM = "sha256"
EDGE_ID_PREFIX = "edge:"
EDGE_ID_HEX_LEN = 24

#: Required event fields (single definition; the validator reads it).
REQUIRED_EVENT_FIELDS = ("subject", "predicate", "object", "observed_at")


def edge_id_for(subject: str, predicate: str, obj: Any, observed_at: float) -> str:
    payload = json.dumps(
        {"s": subject, "p": predicate, "o": obj, "t": float(observed_at)},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.new(HASH_ALGORITHM, payload.encode("utf-8")).hexdigest()
    return EDGE_ID_PREFIX + digest[:EDGE_ID_HEX_LEN]


def _empty_graph() -> dict[str, Any]:
    return {"nodes": {}, "edges": {}}


def query_at(graph: dict[str, Any], *, subject: str, predicate: str, at: float) -> Any:
    """The object valid for (subject, predicate) AT time ``at`` — or None.

    Intervals are closed-open ``[valid_from, valid_to)``: at the instant a
    fact is superseded, the NEW value answers.
    """
    for edge in graph.get("edges", {}).values():
        if edge["subject"] != subject or edge["predicate"] != predicate:
            continue
        starts = edge["valid_from"] <= float(at)
        ends = edge["valid_to"] is None or float(at) < edge["valid_to"]
        if starts and ends:
            return edge["object"]
    return None


def run(*, event: dict[str, Any], graph: dict[str, Any] | None = None) -> dict[str, Any]:
    """Write ``event`` into the temporal graph (created when ``graph`` is None).

    Returns ``{"graph_delta": {...}}`` per the manifest's single output; the
    (possibly new) graph rides along in the envelope so a None-graph call is
    still fully usable.
    """
    if not isinstance(event, dict):
        raise TypeError(f"event must be a dict, got {type(event).__name__}")
    missing = [f for f in REQUIRED_EVENT_FIELDS if f not in event]
    if missing:
        raise ValueError(f"event is missing required fields {missing}; "
                         f"required: {list(REQUIRED_EVENT_FIELDS)}")
    if not isinstance(event["observed_at"], (int, float)):
        raise ValueError("observed_at must be a number (the event's own injected time)")
    if graph is None:
        graph = _empty_graph()
    if not isinstance(graph, dict):
        raise TypeError(f"graph must be a dict or None, got {type(graph).__name__}")
    nodes = graph.setdefault("nodes", {})
    edges = graph.setdefault("edges", {})

    subject = str(event["subject"])
    predicate = str(event["predicate"])
    obj = event["object"]
    observed_at = float(event["observed_at"])
    source_id = event.get("source_id")

    added: list[str] = []
    closed: list[str] = []
    noop = False

    # The open edge (if any) for this (subject, predicate).
    open_edge = next(
        (e for e in edges.values()
         if e["subject"] == subject and e["predicate"] == predicate and e["valid_to"] is None),
        None)

    if open_edge is not None and open_edge["object"] == obj:
        noop = True  # same fact already open — replay-safe
    else:
        eid = edge_id_for(subject, predicate, obj, observed_at)
        if eid in edges:
            noop = True  # exact event already recorded (even as closed history)
        elif open_edge is not None and observed_at < open_edge["valid_from"]:
            # Out-of-order arrival: insert as already-closed history ending
            # where current truth begins. Newer truth is never rewritten.
            edges[eid] = {
                "edge_id": eid, "subject": subject, "predicate": predicate,
                "object": obj, "valid_from": observed_at,
                "valid_to": open_edge["valid_from"],
                "superseded_by": open_edge["edge_id"], "source_id": source_id,
            }
            added.append(eid)
        else:
            if open_edge is not None:
                # SUPERSEDE: close the old edge — it stays queryable forever.
                open_edge["valid_to"] = observed_at
                open_edge["superseded_by"] = eid
                closed.append(open_edge["edge_id"])
            edges[eid] = {
                "edge_id": eid, "subject": subject, "predicate": predicate,
                "object": obj, "valid_from": observed_at, "valid_to": None,
                "superseded_by": None, "source_id": source_id,
            }
            added.append(eid)
        nodes.setdefault(subject, {"name": subject})

    return {"graph_delta": {
        "added_edges": added,
        "closed_edges": closed,
        "noop": noop,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "graph": graph,
    }}


def _selftest() -> None:
    day = 24 * 3600.0
    g: dict[str, Any] = {}

    # Supersede chain A → B → C over one (subject, predicate).
    e1 = {"subject": "ohio", "predicate": "usury_rate_cap", "object": "8%",
          "observed_at": 10 * day, "source_id": "orc-1343.01@2019"}
    e2 = {**e1, "object": "6%", "observed_at": 50 * day, "source_id": "orc-1343.01@2024"}
    e3 = {**e1, "object": "7%", "observed_at": 90 * day, "source_id": "orc-1343.01@2026"}
    d1 = run(event=e1, graph=g)["graph_delta"]
    assert d1["added_edges"] and not d1["closed_edges"] and d1["noop"] is False
    d2 = run(event=e2, graph=g)["graph_delta"]
    assert d2["closed_edges"] == d1["added_edges"]  # A closed by B
    d3 = run(event=e3, graph=g)["graph_delta"]
    assert d3["closed_edges"] == d2["added_edges"]  # B closed by C

    # "What was true when": each era answers with its own value; closed-open
    # boundaries hand off exactly at the supersession instant.
    assert query_at(g, subject="ohio", predicate="usury_rate_cap", at=5 * day) is None
    assert query_at(g, subject="ohio", predicate="usury_rate_cap", at=10 * day) == "8%"
    assert query_at(g, subject="ohio", predicate="usury_rate_cap", at=49 * day) == "8%"
    assert query_at(g, subject="ohio", predicate="usury_rate_cap", at=50 * day) == "6%"
    assert query_at(g, subject="ohio", predicate="usury_rate_cap", at=200 * day) == "7%"

    # Lossless: superseding never deleted anything — all three edges remain,
    # each closed edge linked to its successor.
    assert len(g["edges"]) == 3
    a_edge = g["edges"][d1["added_edges"][0]]
    assert a_edge["valid_to"] == 50 * day and a_edge["superseded_by"] == d2["added_edges"][0]

    # Replay of the open fact is a noop (no new edges, nothing closed).
    replay = run(event=e3, graph=g)["graph_delta"]
    assert replay["noop"] is True and replay["edge_count"] == 3
    assert replay["added_edges"] == [] and replay["closed_edges"] == []

    # Out-of-order older arrival becomes closed history; current truth untouched.
    late = {**e1, "object": "9%", "observed_at": 1 * day, "source_id": "orc-1343.01@2015"}
    dl = run(event=late, graph=g)["graph_delta"]
    assert dl["added_edges"] and dl["closed_edges"] == []
    late_edge = g["edges"][dl["added_edges"][0]]
    assert late_edge["valid_to"] == 90 * day or late_edge["valid_to"] == 10 * day
    # It must end exactly where the OPEN edge began at insertion time.
    assert late_edge["valid_to"] == 90 * day
    assert query_at(g, subject="ohio", predicate="usury_rate_cap", at=200 * day) == "7%"
    assert query_at(g, subject="ohio", predicate="usury_rate_cap", at=2 * day) == "9%"

    # Edge count only ever grows (nothing is deleted, ever).
    assert len(g["edges"]) == 4

    # Deterministic ids: same event → same edge id, even across graphs.
    g2 = run(event=e1)["graph_delta"]["graph"]
    assert set(g2["edges"]) == {d1["added_edges"][0]}

    # Independent predicates do not interfere.
    other = {"subject": "ohio", "predicate": "judgment_interest_rate", "object": "5%",
             "observed_at": 60 * day}
    run(event=other, graph=g)
    assert query_at(g, subject="ohio", predicate="usury_rate_cap", at=200 * day) == "7%"
    assert query_at(g, subject="ohio", predicate="judgment_interest_rate", at=200 * day) == "5%"

    # on_error=raise: missing observed_at (no wall-clock fallback) and bad types.
    raised = False
    try:
        run(event={"subject": "x", "predicate": "y", "object": "z"})
    except ValueError:
        raised = True
    assert raised, "missing observed_at must raise ValueError (never wall-clock)"
    raised = False
    try:
        run(event="not a dict")  # type: ignore[arg-type]
    except TypeError:
        raised = True
    assert raised, "non-dict event must raise TypeError"

    print(
        "PASS — memory_temporal_graph: validity-interval edges with supersede-"
        "never-delete (A→B→C chain queryable at every era), closed-open handoff, "
        "out-of-order arrivals filed as closed history, replay noops, "
        "content-addressed edge ids, observed_at required (no wall clock) "
        "verified"
    )


if __name__ == "__main__":
    _selftest()
