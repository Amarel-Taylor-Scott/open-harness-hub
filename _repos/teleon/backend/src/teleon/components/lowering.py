"""lowering — seam 2: lower an abstract compiled DAG spec ({nodes, edges}) to the EXECUTABLE pipeline_dag, so it RUNS
on real ports via the uniform Component wrapper (not just a synthetic dry-run).

Each spec node becomes a real pipeline_dag.Node whose fn gathers its typed inputs (by TYPE) from its predecessors'
output dicts + the graph inputs, calls the Component's uniform invoke, and writes its typed-output dict to the bus under
its step id. The real executor then runs it in data-flow order (and raises on a cycle / missing producer). serves_truth
is False (a run produces candidates the verification rail dispositions).
"""
from __future__ import annotations

from src.teleon.components.registry import py_function_src_teleon_components_registry__make_component
from src.teleon.dag.pipeline_dag import DAG, Node

py_var_src_teleon_components_lowering___INPUTS_KEY = "__inputs__"


def py_function_src_teleon_components_lowering__lower_to_dag(py_arg_src_teleon_components_lowering__py_function_src_teleon_components_lowering__lower_to_dag__nodes: list, py_arg_src_teleon_components_lowering__py_function_src_teleon_components_lowering__lower_to_dag__edges: list) -> DAG:
    """nodes: [{"step", "component"|None, "plane"}]; edges: [[step_a, step_b]]. -> a runnable pipeline_dag.DAG."""
    py_local_src_teleon_components_lowering__lower_to_dag__steps = {py_local_src_teleon_components_lowering__lower_to_dag__n["step"] for py_local_src_teleon_components_lowering__lower_to_dag__n in py_arg_src_teleon_components_lowering__py_function_src_teleon_components_lowering__lower_to_dag__nodes}
    py_local_src_teleon_components_lowering__lower_to_dag__preds: dict = {py_local_src_teleon_components_lowering__lower_to_dag__n["step"]: [] for py_local_src_teleon_components_lowering__lower_to_dag__n in py_arg_src_teleon_components_lowering__py_function_src_teleon_components_lowering__lower_to_dag__nodes}
    for py_local_src_teleon_components_lowering__lower_to_dag__a, py_local_src_teleon_components_lowering__lower_to_dag__b in py_arg_src_teleon_components_lowering__py_function_src_teleon_components_lowering__lower_to_dag__edges:
        if py_local_src_teleon_components_lowering__lower_to_dag__a in py_local_src_teleon_components_lowering__lower_to_dag__steps and py_local_src_teleon_components_lowering__lower_to_dag__b in py_local_src_teleon_components_lowering__lower_to_dag__steps:
            py_local_src_teleon_components_lowering__lower_to_dag__preds[py_local_src_teleon_components_lowering__lower_to_dag__b].append(py_local_src_teleon_components_lowering__lower_to_dag__a)
    py_local_src_teleon_components_lowering__lower_to_dag__made = []
    for py_local_src_teleon_components_lowering__lower_to_dag__n in py_arg_src_teleon_components_lowering__py_function_src_teleon_components_lowering__lower_to_dag__nodes:
        py_local_src_teleon_components_lowering__lower_to_dag__comp = py_function_src_teleon_components_registry__make_component(py_local_src_teleon_components_lowering__lower_to_dag__n.get("component") or py_local_src_teleon_components_lowering__lower_to_dag__n["step"], plane=py_local_src_teleon_components_lowering__lower_to_dag__n.get("plane"))
        py_local_src_teleon_components_lowering__lower_to_dag__s = py_local_src_teleon_components_lowering__lower_to_dag__n["step"]

        def fn(bus, _comp=py_local_src_teleon_components_lowering__lower_to_dag__comp, _preds=tuple(py_local_src_teleon_components_lowering__lower_to_dag__preds[py_local_src_teleon_components_lowering__lower_to_dag__n["step"]])):
            py_local_src_teleon_components_lowering__lower_to_dag_fn__avail = dict(bus.get(py_var_src_teleon_components_lowering___INPUTS_KEY, {}))          # graph inputs (keyed by type)
            for py_local_src_teleon_components_lowering__lower_to_dag_fn__p in _preds:                                # + each predecessor's typed outputs
                py_local_src_teleon_components_lowering__lower_to_dag_fn__got = bus.get(py_local_src_teleon_components_lowering__lower_to_dag_fn__p)
                if isinstance(py_local_src_teleon_components_lowering__lower_to_dag_fn__got, dict):
                    py_local_src_teleon_components_lowering__lower_to_dag_fn__avail.update(py_local_src_teleon_components_lowering__lower_to_dag_fn__got)
            py_local_src_teleon_components_lowering__lower_to_dag_fn__typed_in = {t: py_local_src_teleon_components_lowering__lower_to_dag_fn__avail[t] for t in _comp.consumes if t in py_local_src_teleon_components_lowering__lower_to_dag_fn__avail}
            return _comp.invoke(py_local_src_teleon_components_lowering__lower_to_dag_fn__typed_in)                   # -> typed-output dict

        py_local_src_teleon_components_lowering__lower_to_dag__made.append(Node(id=py_local_src_teleon_components_lowering__lower_to_dag__s, produces=py_local_src_teleon_components_lowering__lower_to_dag__s, consumes=tuple(py_local_src_teleon_components_lowering__lower_to_dag__preds[py_local_src_teleon_components_lowering__lower_to_dag__s]), fn=fn,
                         cost=0.0 if py_local_src_teleon_components_lowering__lower_to_dag__comp.deterministic else 1.0))
    return DAG(tuple(py_local_src_teleon_components_lowering__lower_to_dag__made))


def py_function_src_teleon_components_lowering__run_compiled(py_arg_src_teleon_components_lowering__py_function_src_teleon_components_lowering__run_compiled__nodes: list, py_arg_src_teleon_components_lowering__py_function_src_teleon_components_lowering__run_compiled__edges: list, py_arg_src_teleon_components_lowering__py_function_src_teleon_components_lowering__run_compiled__graph_inputs: dict) -> dict:
    """Lower + RUN the composed DAG on real ports. graph_inputs: {type: value} available at the graph boundary.
    Returns the executor result (bus + receipt + path + total_cost). Raises ComponentUnavailable if a node's plane has
    no wired/ reachable port (honest), or DAGError on a malformed graph."""
    return py_function_src_teleon_components_lowering__lower_to_dag(py_arg_src_teleon_components_lowering__py_function_src_teleon_components_lowering__run_compiled__nodes, py_arg_src_teleon_components_lowering__py_function_src_teleon_components_lowering__run_compiled__edges).run({py_var_src_teleon_components_lowering___INPUTS_KEY: dict(py_arg_src_teleon_components_lowering__py_function_src_teleon_components_lowering__run_compiled__graph_inputs)})
