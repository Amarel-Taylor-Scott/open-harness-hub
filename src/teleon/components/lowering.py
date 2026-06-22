"""lowering — seam 2: lower an abstract compiled DAG spec ({nodes, edges}) to the EXECUTABLE pipeline_dag, so it RUNS
on real ports via the uniform Component wrapper (not just a synthetic dry-run).

Each spec node becomes a real pipeline_dag.Node whose fn gathers its typed inputs (by TYPE) from its predecessors'
output dicts + the graph inputs, calls the Component's uniform invoke, and writes its typed-output dict to the bus under
its step id. The real executor then runs it in data-flow order (and raises on a cycle / missing producer). serves_truth
is False (a run produces candidates the verification rail dispositions).
"""
from __future__ import annotations

from src.teleon.components.registry import make_component
from src.teleon.dag.pipeline_dag import DAG, Node

_INPUTS_KEY = "__inputs__"


def lower_to_dag(nodes: list, edges: list) -> DAG:
    """nodes: [{"step", "component"|None, "plane"}]; edges: [[step_a, step_b]]. -> a runnable pipeline_dag.DAG."""
    steps = {n["step"] for n in nodes}
    preds: dict = {n["step"]: [] for n in nodes}
    for a, b in edges:
        if a in steps and b in steps:
            preds[b].append(a)
    made = []
    for n in nodes:
        comp = make_component(n.get("component") or n["step"], plane=n.get("plane"))
        s = n["step"]

        def fn(bus, _comp=comp, _preds=tuple(preds[n["step"]])):
            avail = dict(bus.get(_INPUTS_KEY, {}))          # graph inputs (keyed by type)
            for p in _preds:                                # + each predecessor's typed outputs
                got = bus.get(p)
                if isinstance(got, dict):
                    avail.update(got)
            typed_in = {t: avail[t] for t in _comp.consumes if t in avail}
            return _comp.invoke(typed_in)                   # -> typed-output dict

        made.append(Node(id=s, produces=s, consumes=tuple(preds[s]), fn=fn,
                         cost=0.0 if comp.deterministic else 1.0))
    return DAG(tuple(made))


def run_compiled(nodes: list, edges: list, graph_inputs: dict) -> dict:
    """Lower + RUN the composed DAG on real ports. graph_inputs: {type: value} available at the graph boundary.
    Returns the executor result (bus + receipt + path + total_cost). Raises ComponentUnavailable if a node's plane has
    no wired/ reachable port (honest), or DAGError on a malformed graph."""
    return lower_to_dag(nodes, edges).run({_INPUTS_KEY: dict(graph_inputs)})
