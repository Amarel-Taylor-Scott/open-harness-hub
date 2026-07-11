"""src.teleon.dag.pipeline_dag — a flexible DAG of reusable STEPS for extraction/enrichment (not a linear cascade).

A pipeline is a directed acyclic, DATA-FLOW graph: each Node reads upstream artifacts (``consumes``) off a shared BUS
and writes one (``produces``). The graph supports the composition real document/enrichment work needs — far beyond
"OCR then cheapest model":

  - If (branch):    ``when(bus) -> bool`` conditionally skips a node (route text-vs-OCR; escalate-only-if-low-conf).
  - Loop (fan-out): ``map_over='passages'`` runs the node's fn per chunk and collects a list (chunking).
  - choice:         nodes sharing an ``alt_group`` are ALTERNATIVES for one stage; the DESCENT picks the cheapest
                    VIABLE one whose measured ``score`` clears the requirement floor (text<OCR<vision;
                    regex<nlp<cheap-LLM<frontier; cheap-search<premium-grounded).
  - merge (fan-in): a node consuming a list collapses it (merge chunks / merge fields).

Teleon descends a pipeline by choosing the cheapest viable alternative per choice-point — the linear cascade is just a
DAG whose choice-points are an ordered ladder. Pure + deterministic (step fns are injected; offline). serves_truth is
False (a pipeline output is a candidate the verification rail dispositions). Teleon-layer — never imports src.baltor.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


class DAGError(ValueError):
    """Raised on a malformed graph: a missing producer, an unsatisfiable consume, or a cycle."""


@dataclass(frozen=True)
class Node:
    """One step in a pipeline DAG. ``fn(bus) -> value`` computes the artifact named ``produces`` from the bus."""
    id: str
    produces: str                          # artifact name this node writes to the bus
    fn: Callable                           # (bus: dict) -> value  (for a map node: (bus_with_'_item') -> per-item value)
    consumes: tuple = ()                   # artifact names this node reads (data-flow edges)
    cost: float = 0.0                      # relative cost units
    primitive: str = "Action"             # one of the seven canonical primitives
    when: Callable | None = None           # If: run only if when(bus) is truthy (else skipped)
    map_over: str | None = None            # Loop: run fn once per item of bus[map_over]; produces a LIST
    alt_group: str | None = None           # choice: nodes with the same alt_group are alternatives for one stage
    viable: Callable | None = None         # descent: can this alternative run given the inputs? (bus) -> bool
    score: float = 1.0                     # descent: measured quality of this alternative (cheapest-that-meets uses it)


@dataclass(frozen=True)
class DAG:
    nodes: tuple

    def by_id(self) -> dict:
        return {n.id: n for n in self.nodes}

    def choose(self, inputs: dict, *, floor: float = 0.0) -> tuple[set, dict]:
        """Resolve choice-points: every non-alternative node is active; for each alt_group pick the CHEAPEST node that
        is viable on the inputs AND whose score clears the floor. Returns (active_ids, chosen_by_group)."""
        active: set = set()
        chosen: dict = {}
        groups: dict = {}
        for n in self.nodes:
            if n.alt_group:
                groups.setdefault(n.alt_group, []).append(n)
            else:
                active.add(n.id)
        for group, alts in groups.items():
            viable = [a for a in alts if (a.viable is None or a.viable(inputs)) and a.score >= floor]
            if not viable:                                  # nothing meets the floor: take the highest-scoring viable
                viable = sorted([a for a in alts if a.viable is None or a.viable(inputs)],
                                key=lambda a: -a.score)[:1]
            if not viable:
                raise DAGError(f"alt_group {group!r}: no viable alternative for the given inputs")
            pick = min(viable, key=lambda a: (a.cost, -a.score, a.id))
            active.add(pick.id)
            chosen[group] = pick.id
        return active, chosen

    def run(self, inputs: dict, *, floor: float = 0.0) -> dict:
        """Execute the chosen sub-graph in data-flow order. Returns the bus + a receipt (path, per-node cost,
        total cost, chosen alternatives). A node is run when all its consumed artifacts exist; ``when`` may skip it;
        ``map_over`` fans out over a list. serves_truth False."""
        active, chosen = self.choose(inputs, floor=floor)
        by_id = self.by_id()
        bus = dict(inputs)
        receipt: list[dict] = []
        cost = 0.0
        pending = [nid for nid in active]
        progressed = True
        while pending and progressed:
            progressed = False
            for nid in list(pending):
                n = by_id[nid]
                if any(c not in bus for c in n.consumes):
                    continue                                # upstream artifact not ready yet
                pending.remove(nid)
                progressed = True
                if n.when is not None and not n.when(bus):
                    receipt.append({"node": nid, "primitive": n.primitive, "skipped": "when=false", "cost": 0.0})
                    continue
                if n.map_over is not None:                  # Loop / fan-out
                    items = bus.get(n.map_over, []) or []
                    value = [n.fn({**bus, "_item": it}) for it in items]
                else:
                    value = n.fn(bus)
                bus[n.produces] = value
                cost += n.cost
                receipt.append({"node": nid, "primitive": n.primitive, "produces": n.produces,
                                "cost": round(n.cost, 4), "deterministic": n.fn is not None and n.alt_group is None or True})
        if pending:
            raise DAGError(f"unsatisfiable / cyclic nodes (missing inputs?): {sorted(pending)}")
        ran = [r["node"] for r in receipt if "produces" in r]
        return {"bus": bus, "receipt": receipt, "path": ran, "chosen_alternatives": chosen,
                "total_cost": round(cost, 4), "serves_truth": False}


def linear(nodes: list[Node]) -> DAG:
    """Convenience: a DAG (order is resolved by data-flow, not list position)."""
    return DAG(tuple(nodes))
