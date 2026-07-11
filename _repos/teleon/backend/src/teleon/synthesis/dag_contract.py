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
from src.teleon.synthesis.io_contracts import py_function_src_teleon_synthesis_io_contracts__edge_compatible, py_function_src_teleon_synthesis_io_contracts__plane_io
from src.teleon.synthesis.type_system import py_function_src_teleon_synthesis_type_system__bridge

# the types a capability typically has in hand at the graph boundary (a source document / text / a query / a record).
py_const_src_teleon_synthesis_dag_contract__DEFAULT_GRAPH_INPUTS = ("document", "bytes", "image", "text", "query", "record")


def py_function_src_teleon_synthesis_dag_contract__component_types(py_arg_src_teleon_synthesis_dag_contract__component_types__plane) -> tuple:
    """(consumes, produces) types for a plane, or ([],[]) if the plane is not (yet) typed."""
    py_local_src_teleon_synthesis_dag_contract__component_types__io = py_function_src_teleon_synthesis_io_contracts__plane_io(py_arg_src_teleon_synthesis_dag_contract__component_types__plane)
    return (list(py_local_src_teleon_synthesis_dag_contract__component_types__io.get("consumes", [])), list(py_local_src_teleon_synthesis_dag_contract__component_types__io.get("produces", []))) if py_local_src_teleon_synthesis_dag_contract__component_types__io else ([], [])


def py_function_src_teleon_synthesis_dag_contract___acyclic_order(py_arg_src_teleon_synthesis_dag_contract__acyclic_order__steps: set, py_arg_src_teleon_synthesis_dag_contract__acyclic_order__edges: list) -> list:
    py_local_src_teleon_synthesis_dag_contract__acyclic_order__indeg = {py_local_src_teleon_synthesis_dag_contract__acyclic_order__s: 0 for py_local_src_teleon_synthesis_dag_contract__acyclic_order__s in py_arg_src_teleon_synthesis_dag_contract__acyclic_order__steps}
    for py_local_src_teleon_synthesis_dag_contract__acyclic_order__a, py_local_src_teleon_synthesis_dag_contract__acyclic_order__b in py_arg_src_teleon_synthesis_dag_contract__acyclic_order__edges:
        py_local_src_teleon_synthesis_dag_contract__acyclic_order__indeg[py_local_src_teleon_synthesis_dag_contract__acyclic_order__b] += 1
    py_local_src_teleon_synthesis_dag_contract__acyclic_order__q = [py_local_src_teleon_synthesis_dag_contract__acyclic_order__s for py_local_src_teleon_synthesis_dag_contract__acyclic_order__s in py_arg_src_teleon_synthesis_dag_contract__acyclic_order__steps if py_local_src_teleon_synthesis_dag_contract__acyclic_order__indeg[py_local_src_teleon_synthesis_dag_contract__acyclic_order__s] == 0]
    py_local_src_teleon_synthesis_dag_contract__acyclic_order__order: list = []
    while py_local_src_teleon_synthesis_dag_contract__acyclic_order__q:
        py_local_src_teleon_synthesis_dag_contract__acyclic_order__s = py_local_src_teleon_synthesis_dag_contract__acyclic_order__q.pop()
        py_local_src_teleon_synthesis_dag_contract__acyclic_order__order.append(py_local_src_teleon_synthesis_dag_contract__acyclic_order__s)
        for py_local_src_teleon_synthesis_dag_contract__acyclic_order__a, py_local_src_teleon_synthesis_dag_contract__acyclic_order__b in py_arg_src_teleon_synthesis_dag_contract__acyclic_order__edges:
            if py_local_src_teleon_synthesis_dag_contract__acyclic_order__a == py_local_src_teleon_synthesis_dag_contract__acyclic_order__s:
                py_local_src_teleon_synthesis_dag_contract__acyclic_order__indeg[py_local_src_teleon_synthesis_dag_contract__acyclic_order__b] -= 1
                if py_local_src_teleon_synthesis_dag_contract__acyclic_order__indeg[py_local_src_teleon_synthesis_dag_contract__acyclic_order__b] == 0:
                    py_local_src_teleon_synthesis_dag_contract__acyclic_order__q.append(py_local_src_teleon_synthesis_dag_contract__acyclic_order__b)
    return py_local_src_teleon_synthesis_dag_contract__acyclic_order__order


def py_function_src_teleon_synthesis_dag_contract___synthetic_dag(py_arg_src_teleon_synthesis_dag_contract__synthetic_dag__nodes: list, py_arg_src_teleon_synthesis_dag_contract__synthetic_dag__edges: list) -> DAG:
    """Lower the abstract spec to a real pipeline_dag.DAG whose fns emit a synthetic typed placeholder — so DAG.run
    exercises the REAL executor (data-flow order + cycle/missing-producer detection), proving the spec is runnable."""
    py_local_src_teleon_synthesis_dag_contract__synthetic_dag__preds: dict = {py_local_src_teleon_synthesis_dag_contract__synthetic_dag__n["step"]: [] for py_local_src_teleon_synthesis_dag_contract__synthetic_dag__n in py_arg_src_teleon_synthesis_dag_contract__synthetic_dag__nodes}
    for py_local_src_teleon_synthesis_dag_contract__synthetic_dag__a, py_local_src_teleon_synthesis_dag_contract__synthetic_dag__b in py_arg_src_teleon_synthesis_dag_contract__synthetic_dag__edges:
        if py_local_src_teleon_synthesis_dag_contract__synthetic_dag__b in py_local_src_teleon_synthesis_dag_contract__synthetic_dag__preds:
            py_local_src_teleon_synthesis_dag_contract__synthetic_dag__preds[py_local_src_teleon_synthesis_dag_contract__synthetic_dag__b].append(py_local_src_teleon_synthesis_dag_contract__synthetic_dag__a)
    py_local_src_teleon_synthesis_dag_contract__synthetic_dag__made = []
    for py_local_src_teleon_synthesis_dag_contract__synthetic_dag__n in py_arg_src_teleon_synthesis_dag_contract__synthetic_dag__nodes:
        py_local_src_teleon_synthesis_dag_contract__synthetic_dag__s = py_local_src_teleon_synthesis_dag_contract__synthetic_dag__n["step"]
        py_local_src_teleon_synthesis_dag_contract__synthetic_dag___, py_local_src_teleon_synthesis_dag_contract__synthetic_dag__produces = py_function_src_teleon_synthesis_dag_contract__component_types(py_local_src_teleon_synthesis_dag_contract__synthetic_dag__n.get("plane"))
        py_local_src_teleon_synthesis_dag_contract__synthetic_dag__tag = (py_local_src_teleon_synthesis_dag_contract__synthetic_dag__produces[0] if py_local_src_teleon_synthesis_dag_contract__synthetic_dag__produces else "value")
        py_local_src_teleon_synthesis_dag_contract__synthetic_dag__made.append(Node(id=py_local_src_teleon_synthesis_dag_contract__synthetic_dag__s, produces=py_local_src_teleon_synthesis_dag_contract__synthetic_dag__s, consumes=tuple(py_local_src_teleon_synthesis_dag_contract__synthetic_dag__preds[py_local_src_teleon_synthesis_dag_contract__synthetic_dag__s]),
                         fn=(lambda py_arg_src_teleon_synthesis_dag_contract__synthetic_dag__bus, py_arg_src_teleon_synthesis_dag_contract__synthetic_dag___t=py_local_src_teleon_synthesis_dag_contract__synthetic_dag__tag, py_arg_src_teleon_synthesis_dag_contract__synthetic_dag___p=py_local_src_teleon_synthesis_dag_contract__synthetic_dag__n.get("plane"): f"<{py_arg_src_teleon_synthesis_dag_contract__synthetic_dag___p}:{py_arg_src_teleon_synthesis_dag_contract__synthetic_dag___t}>"), cost=0.0))
    return DAG(tuple(py_local_src_teleon_synthesis_dag_contract__synthetic_dag__made))


def py_function_src_teleon_synthesis_dag_contract__verify_buildable_dag(py_arg_src_teleon_synthesis_dag_contract__verify_buildable_dag__nodes: list, py_arg_src_teleon_synthesis_dag_contract__verify_buildable_dag__edges: list, *, graph_inputs: tuple = py_const_src_teleon_synthesis_dag_contract__DEFAULT_GRAPH_INPUTS,
                         py_arg_src_teleon_synthesis_dag_contract__verify_buildable_dag__dry_run: bool = True) -> dict:
    """nodes: [{"step": str, "plane": str, ...}]; edges: [[step_a, step_b]]. Returns the verdict (see module docstring)."""
    py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__steps = {py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__n["step"]: py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__n for py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__n in py_arg_src_teleon_synthesis_dag_contract__verify_buildable_dag__nodes}
    py_arg_src_teleon_synthesis_dag_contract__verify_buildable_dag__edges = [[py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__a, py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__b] for py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__a, py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__b in py_arg_src_teleon_synthesis_dag_contract__verify_buildable_dag__edges if py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__a in py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__steps and py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__b in py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__steps]

    py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__order = py_function_src_teleon_synthesis_dag_contract___acyclic_order(set(py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__steps), py_arg_src_teleon_synthesis_dag_contract__verify_buildable_dag__edges)
    py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__acyclic = len(py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__order) == len(py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__steps)

    # (2) edge type-compatibility — GATING (a producer output type the consumer cannot accept)
    py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__type_incompatible = [[py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__a, py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__b] for py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__a, py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__b in py_arg_src_teleon_synthesis_dag_contract__verify_buildable_dag__edges if not py_function_src_teleon_synthesis_io_contracts__edge_compatible(py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__steps[py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__a].get("plane"), py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__steps[py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__b].get("plane"))]
    # ...but an incompatible edge may be COERCIBLE — a converter component can bridge the types (html→markdown). The
    # compiler can auto-insert these (System 6), so we surface them rather than just rejecting (additive suggestion).
    py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__coercible = []
    for py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__a, py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__b in py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__type_incompatible:
        py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__pa, py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__pb = py_function_src_teleon_synthesis_io_contracts__plane_io(py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__steps[py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__a].get("plane")), py_function_src_teleon_synthesis_io_contracts__plane_io(py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__steps[py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__b].get("plane"))
        if py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__pa and py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__pb:
            py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__br = py_function_src_teleon_synthesis_type_system__bridge(py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__pa.get("produces", []), py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__pb.get("consumes", []))
            if py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__br:
                py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__coercible.append({"edge": [py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__a, py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__b], "via": py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__br})

    # (3) data-flow type satisfiability — every consumed type comes from a direct predecessor or a graph input
    py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__preds: dict = {py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__s: [] for py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__s in py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__steps}
    for py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__a, py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__b in py_arg_src_teleon_synthesis_dag_contract__verify_buildable_dag__edges:
        py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__preds[py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__b].append(py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__a)
    py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__avail_in = set(graph_inputs)
    py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__unsatisfied = []
    for py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__s, py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__n in py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__steps.items():
        py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__consumes, py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag___ = py_function_src_teleon_synthesis_dag_contract__component_types(py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__n.get("plane"))
        if not py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__consumes:                                   # un-typed plane -> don't block
            continue
        py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__upstream = set()
        for py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__p in py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__preds[py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__s]:
            py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag___, py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__pp = py_function_src_teleon_synthesis_dag_contract__component_types(py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__steps[py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__p].get("plane"))
            py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__upstream |= set(py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__pp)
        if not (set(py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__consumes) & (py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__upstream | py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__avail_in)):    # none of its inputs are available
            py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__unsatisfied.append(py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__s)

    # (4) terminal output node(s)
    py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__has_out = {py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__a for py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__a, py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__b in py_arg_src_teleon_synthesis_dag_contract__verify_buildable_dag__edges}
    py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__output_nodes = [py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__s for py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__s in py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__steps if py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__s not in py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__has_out]

    # (5) execution dry-run through the REAL pipeline_dag executor on synthetic typed data
    py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__dry_ok, py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__dry_err = None, None
    if py_arg_src_teleon_synthesis_dag_contract__verify_buildable_dag__dry_run:
        try:
            py_function_src_teleon_synthesis_dag_contract___synthetic_dag(py_arg_src_teleon_synthesis_dag_contract__verify_buildable_dag__nodes, py_arg_src_teleon_synthesis_dag_contract__verify_buildable_dag__edges).run({t: f"<input:{t}>" for t in graph_inputs})
            py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__dry_ok = True
        except (DAGError, Exception) as py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__e:  # noqa: BLE001
            py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__dry_ok, py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__dry_err = False, f"{type(py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__e).__name__}: {py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__e}"

    py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__verified = bool(py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__steps) and py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__acyclic and not py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__type_incompatible and not py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__unsatisfied and bool(py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__output_nodes) and py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__dry_ok is not False
    return {"verified_working": py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__verified, "acyclic": py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__acyclic, "type_incompatible_edges": py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__type_incompatible,
            "coercible_edges": py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__coercible, "unsatisfied_inputs": py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__unsatisfied, "output_nodes": py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__output_nodes,
            "dry_run_ok": py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__dry_ok, "dry_run_error": py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__dry_err, "n_components": len(py_local_src_teleon_synthesis_dag_contract__verify_buildable_dag__steps), "serves_truth": False}
