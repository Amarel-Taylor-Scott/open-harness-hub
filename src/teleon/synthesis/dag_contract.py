"""dag_contract — verify a COMPOSED DAG is a *verified working build*, not just an acyclic spec.

This is the compatibility-verification layer for building verified working DAGs from MANY components: it joins the typed
I/O contracts (plane_io_contracts) with the real executable DAG (pipeline_dag) into one verdict. Strictly stronger than
the compiler's acyclic + hallucination + non-gating type-WARNING checks. A DAG is `verified_working` when ALL hold:

  1. acyclic (a pipeline, not a loop);
  2. every EDGE is type-compatible — the upstream produces a type the downstream consumes (gating, not a warning);
  3. every node's CONSUMED types are satisfied by a direct upstream producer OR a declared graph input (no dangling input);
  4. the graph has a terminal OUTPUT node (it produces something);
  5. it DRY-RUNS end-to-end through the real pipeline_dag executor on synthetic typed data (proves it lowers to a
     runnable graph — connecting the abstract compiled spec to the executable engine).

An UN-TYPED plane never blocks (partial-but-grounded coverage): its edges/inputs are treated as satisfiable so the
verifier never false-fails on a plane we haven't typed yet. Deterministic, offline. serves_truth=false (it proves the
GRAPH is sound + runnable; the verification rail still dispositions the actual OUTPUTS).
"""
from __future__ import annotations

from src.teleon.dag.pipeline_dag import DAG, DAGError, Node
from src.teleon.synthesis.io_contracts import edge_compatible, plane_io
from src.teleon.synthesis.type_system import bridge

# the types a capability typically has in hand at the graph boundary (a source document / text / a query / a record).
DEFAULT_GRAPH_INPUTS = ("document", "bytes", "image", "text", "query", "record")


def component_types(plane) -> tuple:
    """(consumes, produces) types for a plane, or ([],[]) if the plane is not (yet) typed."""
    io = plane_io(plane)
    return (list(io.get("consumes", [])), list(io.get("produces", []))) if io else ([], [])


def _acyclic_order(steps: set, edges: list) -> list:
    indeg = {s: 0 for s in steps}
    for a, b in edges:
        indeg[b] += 1
    q = [s for s in steps if indeg[s] == 0]
    order: list = []
    while q:
        s = q.pop()
        order.append(s)
        for a, b in edges:
            if a == s:
                indeg[b] -= 1
                if indeg[b] == 0:
                    q.append(b)
    return order


def _synthetic_dag(nodes: list, edges: list) -> DAG:
    """Lower the abstract spec to a real pipeline_dag.DAG whose fns emit a synthetic typed placeholder — so DAG.run
    exercises the REAL executor (data-flow order + cycle/missing-producer detection), proving the spec is runnable."""
    preds: dict = {n["step"]: [] for n in nodes}
    for a, b in edges:
        if b in preds:
            preds[b].append(a)
    made = []
    for n in nodes:
        s = n["step"]
        _, produces = component_types(n.get("plane"))
        tag = (produces[0] if produces else "value")
        made.append(Node(id=s, produces=s, consumes=tuple(preds[s]),
                         fn=(lambda bus, _t=tag, _p=n.get("plane"): f"<{_p}:{_t}>"), cost=0.0))
    return DAG(tuple(made))


def verify_buildable_dag(nodes: list, edges: list, *, graph_inputs: tuple = DEFAULT_GRAPH_INPUTS,
                         dry_run: bool = True) -> dict:
    """nodes: [{"step": str, "plane": str, ...}]; edges: [[step_a, step_b]]. Returns the verdict (see module docstring)."""
    steps = {n["step"]: n for n in nodes}
    edges = [[a, b] for a, b in edges if a in steps and b in steps]

    order = _acyclic_order(set(steps), edges)
    acyclic = len(order) == len(steps)

    # (2) edge type-compatibility — GATING (a producer output type the consumer cannot accept)
    type_incompatible = [[a, b] for a, b in edges if not edge_compatible(steps[a].get("plane"), steps[b].get("plane"))]
    # ...but an incompatible edge may be COERCIBLE — a converter component can bridge the types (html→markdown). The
    # compiler can auto-insert these (System 6), so we surface them rather than just rejecting (additive suggestion).
    coercible = []
    for a, b in type_incompatible:
        pa, pb = plane_io(steps[a].get("plane")), plane_io(steps[b].get("plane"))
        if pa and pb:
            br = bridge(pa.get("produces", []), pb.get("consumes", []))
            if br:
                coercible.append({"edge": [a, b], "via": br})

    # (3) data-flow type satisfiability — every consumed type comes from a direct predecessor or a graph input
    preds: dict = {s: [] for s in steps}
    for a, b in edges:
        preds[b].append(a)
    avail_in = set(graph_inputs)
    unsatisfied = []
    for s, n in steps.items():
        consumes, _ = component_types(n.get("plane"))
        if not consumes:                                   # un-typed plane -> don't block
            continue
        upstream = set()
        for p in preds[s]:
            _, pp = component_types(steps[p].get("plane"))
            upstream |= set(pp)
        if not (set(consumes) & (upstream | avail_in)):    # none of its inputs are available
            unsatisfied.append(s)

    # (4) terminal output node(s)
    has_out = {a for a, b in edges}
    output_nodes = [s for s in steps if s not in has_out]

    # (5) execution dry-run through the REAL pipeline_dag executor on synthetic typed data
    dry_ok, dry_err = None, None
    if dry_run:
        try:
            _synthetic_dag(nodes, edges).run({t: f"<input:{t}>" for t in graph_inputs})
            dry_ok = True
        except (DAGError, Exception) as e:  # noqa: BLE001
            dry_ok, dry_err = False, f"{type(e).__name__}: {e}"

    verified = bool(steps) and acyclic and not type_incompatible and not unsatisfied and bool(output_nodes) and dry_ok is not False
    return {"verified_working": verified, "acyclic": acyclic, "type_incompatible_edges": type_incompatible,
            "coercible_edges": coercible, "unsatisfied_inputs": unsatisfied, "output_nodes": output_nodes,
            "dry_run_ok": dry_ok, "dry_run_error": dry_err, "n_components": len(steps), "serves_truth": False}
