"""src.teleon.evolution.capability_graph — the EVOLUTION GRAPH of a capability's runners.

A capability is realized by RUNNERS (implementations) that evolve from non-deterministic toward
most-deterministic. Each runner version is a NODE; each evolution event is a directed EDGE:
  fork     — a DOCUMENTED fork: trade capability coverage for determinism (e.g. a 100%-deterministic rule that
             covers 90% of cases). The parent is PRESERVED and the uncovered residual is routed to it.
  distill  — distill a non-deterministic runner into a deterministic rule at (ideally) equal coverage.
  promote  — make a candidate runner the current hot path (reversible).
  rollback — revert to a preserved ancestor runner.
  heal     — replace a drifted runner with a re-healed version after a source change.

The graph is LOSSLESS (the lossless-distillation law). An evolution event NEVER deletes its parent: a fork that
loses coverage must route the residual to a preserved higher-coverage runner, so nothing the model could do is
lost. You can always (a) read any runner's full lineage to the root, (b) walk the descent root -> most-
deterministic, and (c) roll back along a preserved edge. The "most deterministic as possible" runner is the
highest-determinism runner that still meets a required coverage bar — the rest routes to a richer runner.

Pure + deterministic (no clock/RNG/IO). Stdlib only; Teleon-layer — never imports src.baltor. A graph node is a
routing/lineage record, never a fact: serves_truth is pinned False on every node.
"""
from __future__ import annotations

from dataclasses import dataclass

#: evolution event kinds (the edge labels).
EDGE_FORK = "fork"          # documented fork: trade coverage for determinism; parent preserved, residual routed
EDGE_DISTILL = "distill"    # non-det -> deterministic rule at (ideally) equal coverage
EDGE_PROMOTE = "promote"    # make a candidate the current hot path (reversible)
EDGE_ROLLBACK = "rollback"  # revert to a preserved ancestor
EDGE_HEAL = "heal"          # replace a drifted runner with a re-healed version (post source-change)
EDGE_KINDS = (EDGE_FORK, EDGE_DISTILL, EDGE_PROMOTE, EDGE_ROLLBACK, EDGE_HEAL)

#: edges that move a capability toward determinism (define the descent path).
_DESCENT_EDGES = (EDGE_FORK, EDGE_DISTILL)
_EPS = 1e-9


class EvolutionError(ValueError):
    """Raised on a malformed graph: missing node, cycle, or a lossless-invariant violation (dropped residual)."""


@dataclass(frozen=True)
class RunnerNode:
    """One runner VERSION of a capability. ``tier`` is the escalation-ladder tier (0 = most deterministic
    template ... 4 = human); ``determinism`` and ``capability_coverage`` are 0..1; ``cost`` is relative units.
    A node is a lineage/routing record — never a fact (serves_truth pinned False)."""
    runner_id: str
    capability_slot: str
    kind: str
    tier: int
    determinism: float
    capability_coverage: float
    cost: float = 0.0
    serves_truth: bool = False

    def __post_init__(self) -> None:
        if not self.runner_id or not self.capability_slot:
            raise EvolutionError("a runner needs a runner_id and a capability_slot")
        for f in ("determinism", "capability_coverage"):
            v = getattr(self, f)
            if not (0.0 - _EPS <= float(v) <= 1.0 + _EPS):
                raise EvolutionError(f"{f} must be in [0,1], got {v}")
        if not (0 <= int(self.tier) <= 4):
            raise EvolutionError(f"tier must be an escalation-ladder tier 0..4, got {self.tier}")
        if self.serves_truth is not False:
            raise EvolutionError("a graph node is a routing/lineage record and can never serve truth")

    def as_dict(self) -> dict:
        return {"runner_id": self.runner_id, "capability_slot": self.capability_slot, "kind": self.kind,
                "tier": self.tier, "determinism": self.determinism, "capability_coverage": self.capability_coverage,
                "cost": self.cost, "serves_truth": False}


@dataclass(frozen=True)
class EvolutionEdge:
    """A directed evolution event parent -> child. ``residual_routed_to`` names the runner that handles the cases
    the child does NOT cover (lossless: a coverage-losing fork can never drop the residual)."""
    parent_id: str
    child_id: str
    kind: str
    rationale: str = ""
    residual_routed_to: str | None = None

    def as_dict(self) -> dict:
        return {"parent_id": self.parent_id, "child_id": self.child_id, "kind": self.kind,
                "rationale": self.rationale, "residual_routed_to": self.residual_routed_to}


class CapabilityEvolutionGraph:
    """The evolution graph for one capability_slot: runner nodes + evolution edges, with lossless invariants and
    descent queries (lineage, descent path, the most-deterministic-within-coverage runner)."""

    def __init__(self, capability_slot: str) -> None:
        if not capability_slot:
            raise EvolutionError("a graph needs a capability_slot")
        self.capability_slot = capability_slot
        self._nodes: dict[str, RunnerNode] = {}
        self._edges: list[EvolutionEdge] = []

    # ── construction ───────────────────────────────────────────────────────────────────────────────────────
    def add_runner(self, node: RunnerNode) -> RunnerNode:
        if node.capability_slot != self.capability_slot:
            raise EvolutionError(f"runner {node.runner_id!r} is for {node.capability_slot!r}, not {self.capability_slot!r}")
        if node.runner_id in self._nodes:
            raise EvolutionError(f"duplicate runner_id {node.runner_id!r}")
        self._nodes[node.runner_id] = node
        return node

    def add_edge(self, edge: EvolutionEdge) -> EvolutionEdge:
        if edge.kind not in EDGE_KINDS:
            raise EvolutionError(f"unknown edge kind {edge.kind!r}; known: {EDGE_KINDS}")
        for nid in (edge.parent_id, edge.child_id):
            if nid not in self._nodes:
                raise EvolutionError(f"edge references unknown runner {nid!r}")
        if edge.parent_id == edge.child_id:
            raise EvolutionError("an evolution edge cannot be a self-loop")
        parent, child = self._nodes[edge.parent_id], self._nodes[edge.child_id]
        # descent edges move toward determinism and may only LOSE coverage (never invent it by getting simpler).
        if edge.kind in _DESCENT_EDGES:
            if child.determinism < parent.determinism - _EPS:
                raise EvolutionError(f"{edge.kind} {edge.child_id!r} is LESS deterministic than its parent")
            if child.capability_coverage > parent.capability_coverage + _EPS:
                raise EvolutionError(f"{edge.kind} {edge.child_id!r} claims MORE coverage than its parent — "
                                     "a more-deterministic runner cannot gain capability for free")
            # LOSSLESS: a coverage-losing fork MUST route the residual to a preserved higher-coverage runner.
            if child.capability_coverage < parent.capability_coverage - _EPS:
                residual = edge.residual_routed_to or edge.parent_id
                if residual not in self._nodes:
                    raise EvolutionError(f"coverage-losing {edge.kind} {edge.child_id!r} routes its residual to "
                                         f"unknown runner {residual!r} (lossless violation — residual dropped)")
                if self._nodes[residual].capability_coverage < child.capability_coverage - _EPS:
                    raise EvolutionError(f"residual handler {residual!r} covers less than the fork itself — "
                                         "the residual would be dropped (lossless violation)")
        self._edges.append(edge)
        self._check_acyclic()
        return edge

    def document_fork(self, parent_id: str, child: RunnerNode, *, rationale: str = "",
                      residual_routed_to: str | None = None, kind: str = EDGE_FORK) -> RunnerNode:
        """Add a forked/distilled child runner AND its edge in one lossless step. The residual (cases the child
        does not cover) routes to ``residual_routed_to`` (default: the parent, which has higher coverage)."""
        self.add_runner(child)
        self.add_edge(EvolutionEdge(parent_id, child.runner_id, kind, rationale,
                                    residual_routed_to=residual_routed_to or parent_id))
        return child

    # ── queries ────────────────────────────────────────────────────────────────────────────────────────────
    def node(self, runner_id: str) -> RunnerNode:
        if runner_id not in self._nodes:
            raise EvolutionError(f"unknown runner {runner_id!r}")
        return self._nodes[runner_id]

    def _incoming(self, runner_id: str) -> list[EvolutionEdge]:
        return [e for e in self._edges if e.child_id == runner_id]

    def _children(self, runner_id: str) -> list[EvolutionEdge]:
        return [e for e in self._edges if e.parent_id == runner_id]

    def roots(self) -> list[RunnerNode]:
        """Runners with no incoming descent/heal edge — the original non-deterministic runner(s)."""
        structural = {e.child_id for e in self._edges if e.kind in (_DESCENT_EDGES + (EDGE_HEAL,))}
        return [self._nodes[nid] for nid in sorted(self._nodes) if nid not in structural]

    def root(self) -> RunnerNode:
        rs = self.roots()
        if len(rs) != 1:
            raise EvolutionError(f"expected exactly one root runner, found {len(rs)}")
        return rs[0]

    def lineage(self, runner_id: str) -> list[RunnerNode]:
        """The chain root -> runner_id (following descent/heal parent edges). Proves any runner traces to the root."""
        self.node(runner_id)
        chain, cur, seen = [], runner_id, set()
        while cur is not None:
            if cur in seen:
                raise EvolutionError("cycle in lineage")
            seen.add(cur)
            chain.append(self._nodes[cur])
            parents = [e for e in self._incoming(cur) if e.kind in (_DESCENT_EDGES + (EDGE_HEAL,))]
            cur = parents[0].parent_id if parents else None
        return list(reversed(chain))

    def descent_path(self) -> list[RunnerNode]:
        """Walk root -> most-deterministic: at each step follow the descent child with the LOWEST tier (break ties
        by highest determinism, then highest coverage, then runner_id). The non-det -> most-det spine of the graph."""
        path, cur = [], self.root()
        seen: set[str] = set()
        while cur is not None and cur.runner_id not in seen:
            seen.add(cur.runner_id)
            path.append(cur)
            kids = [self._nodes[e.child_id] for e in self._children(cur.runner_id) if e.kind in _DESCENT_EDGES]
            cur = min(kids, key=lambda n: (n.tier, -n.determinism, -n.capability_coverage, n.runner_id)) if kids else None
        return path

    def most_deterministic_runner(self, *, min_coverage: float = 0.0) -> RunnerNode:
        """The most-deterministic-as-possible runner that still meets ``min_coverage`` — highest determinism, then
        highest coverage, then lowest cost, then runner_id. This is the runner Teleon should run for the covered
        cases; the residual routes to a higher-coverage ancestor."""
        eligible = [n for n in self._nodes.values() if n.capability_coverage >= min_coverage - _EPS]
        if not eligible:
            raise EvolutionError(f"no runner meets min_coverage={min_coverage}")
        return max(eligible, key=lambda n: (n.determinism, n.capability_coverage, -n.cost, _neg_str(n.runner_id)))

    def forks(self) -> list[dict]:
        """Every documented fork/distill with its trade (coverage/determinism/cost deltas + residual route)."""
        out = []
        for e in self._edges:
            if e.kind not in _DESCENT_EDGES:
                continue
            p, c = self._nodes[e.parent_id], self._nodes[e.child_id]
            out.append({"from": e.parent_id, "to": e.child_id, "kind": e.kind,
                        "coverage_delta": round(c.capability_coverage - p.capability_coverage, 6),
                        "determinism_delta": round(c.determinism - p.determinism, 6),
                        "cost_delta": round(c.cost - p.cost, 6),
                        "residual_routed_to": e.residual_routed_to, "rationale": e.rationale})
        return out

    def _check_acyclic(self) -> None:
        adj: dict[str, list[str]] = {nid: [] for nid in self._nodes}
        for e in self._edges:
            if e.kind in (_DESCENT_EDGES + (EDGE_HEAL,)):
                adj[e.parent_id].append(e.child_id)
        WHITE, GREY, BLACK = 0, 1, 2
        color = {nid: WHITE for nid in self._nodes}

        def visit(n: str) -> None:
            color[n] = GREY
            for m in adj[n]:
                if color[m] == GREY:
                    raise EvolutionError("cycle detected in the evolution graph")
                if color[m] == WHITE:
                    visit(m)
            color[n] = BLACK

        for nid in self._nodes:
            if color[nid] == WHITE:
                visit(nid)

    def validate(self) -> None:
        """Re-check the lossless invariants over the whole graph (acyclic; descent edges lose-coverage-only and
        route residuals; serves_truth False everywhere). Raises EvolutionError on any violation."""
        self._check_acyclic()
        for n in self._nodes.values():
            if n.serves_truth is not False:
                raise EvolutionError(f"runner {n.runner_id!r} serves truth")
        # re-validate each descent edge's lossless residual routing
        for e in self._edges:
            if e.kind in _DESCENT_EDGES:
                p, c = self._nodes[e.parent_id], self._nodes[e.child_id]
                if c.capability_coverage < p.capability_coverage - _EPS:
                    residual = e.residual_routed_to or e.parent_id
                    if residual not in self._nodes or self._nodes[residual].capability_coverage < c.capability_coverage - _EPS:
                        raise EvolutionError(f"lossless violation on edge {e.parent_id}->{e.child_id}")

    def to_dict(self) -> dict:
        self.validate()
        return {"capability_slot": self.capability_slot,
                "runners": [self._nodes[nid].as_dict() for nid in sorted(self._nodes)],
                "edges": [e.as_dict() for e in self._edges],
                "root": self.root().runner_id,
                "descent_path": [n.runner_id for n in self.descent_path()],
                "forks": self.forks(),
                "serves_truth": False}


def _neg_str(s: str) -> tuple:
    """Sort key so that, after maximizing numeric fields, the LOWEST runner_id wins (deterministic tie-break)."""
    return tuple(-ord(ch) for ch in s)


def record_heal(graph: CapabilityEvolutionGraph, *, drifted_runner_id: str, healed_runner: RunnerNode,
                rationale: str = "") -> RunnerNode:
    """The BRIDGE from self-healing into the shared lineage. ``src.teleon.self_healing`` (reactive) produces a
    re-healed runner after a source change; this records it as a ``heal`` edge in the evolution graph, so the
    capability's history is one book with two authors (healing writes heal edges; evolution writes fork/distill
    edges). Keeps the two concerns separate in LOGIC while sharing the LINEAGE. The healed runner restores
    coverage — a heal edge carries no descent (coverage/determinism) constraint; that is evolution's job."""
    graph.add_runner(healed_runner)
    graph.add_edge(EvolutionEdge(drifted_runner_id, healed_runner.runner_id, EDGE_HEAL, rationale))
    return healed_runner
