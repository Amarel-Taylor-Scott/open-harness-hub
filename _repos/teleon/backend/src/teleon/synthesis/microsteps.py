"""src.teleon.synthesis.microsteps — decompose a ladder rung into smaller MICRO-STEPS (finer components, more substitution).

A rung ('text_layer') is not atomic: it's open->detect_mime->detect_encoding->extract->normalize->segment, each a smaller
component typed by the seven primitives. Smaller rungs = more places to substitute a cheaper/deterministic component, test
in isolation, and back out of (the synthesis tree branches finer). Seeded by _repos/shared-backend-components/architecture/rung_microsteps.json; any
not-yet-decomposed rung gets generate_microstep_prompt() for the LLM to decompose (more components). serves_truth=false.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from functools import lru_cache
from pathlib import Path

from src.teleon.synthesis import intent_to_dag as I

py_var_src_teleon_synthesis_microsteps___REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])
py_var_src_teleon_synthesis_microsteps___PRIMITIVES = ("input", "knowledge_corpus", "if_statement", "action", "loop", "stop", "output")


@lru_cache(maxsize=1)
def py_function_src_teleon_synthesis_microsteps___decomps() -> dict:
    py_local_src_teleon_synthesis_microsteps__decomps__raw = json.loads((_resource("architecture") / "rung_microsteps.json").read_text(encoding="utf-8"))["decompositions"]
    return {(d["capability"], d["rung"]): d["microsteps"] for d in py_local_src_teleon_synthesis_microsteps__decomps__raw}


@lru_cache(maxsize=1)
def py_function_src_teleon_synthesis_microsteps___plane_tools() -> dict:
    py_local_src_teleon_synthesis_microsteps__plane_tools__out: dict = {}
    for py_local_src_teleon_synthesis_microsteps__plane_tools__t in json.loads((_resource("architecture") / "tool_registry.json").read_text())["tools"]:
        py_local_src_teleon_synthesis_microsteps__plane_tools__out.setdefault(py_local_src_teleon_synthesis_microsteps__plane_tools__t["plane"], []).append(py_local_src_teleon_synthesis_microsteps__plane_tools__t["id"])
    return py_local_src_teleon_synthesis_microsteps__plane_tools__out


def py_function_src_teleon_synthesis_microsteps__microsteps_for(py_arg_src_teleon_synthesis_microsteps__microsteps_for__capability: str, py_arg_src_teleon_synthesis_microsteps__microsteps_for__tier: str) -> list[dict]:
    """The atomic sub-steps a rung decomposes into ([] if not decomposed yet — use generate_microstep_prompt)."""
    return py_function_src_teleon_synthesis_microsteps___decomps().get((py_arg_src_teleon_synthesis_microsteps__microsteps_for__capability, py_arg_src_teleon_synthesis_microsteps__microsteps_for__tier), [])


def py_function_src_teleon_synthesis_microsteps__expand_to_micro_dag(py_arg_src_teleon_synthesis_microsteps__expand_to_micro_dag__intent: str) -> dict:
    """A FINER DAG: each rung that has micro-steps becomes its sub-step chain; un-decomposed rungs stay one node."""
    py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__dag = I.py_function_src_teleon_synthesis_intent_to_dag__build_dag(py_arg_src_teleon_synthesis_microsteps__expand_to_micro_dag__intent)
    py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__cap = py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__dag.get("capability")
    py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__nodes, py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__edges, py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__prev_last = [], [], None
    for py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__rung in py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__dag["nodes"]:
        py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__ms = py_function_src_teleon_synthesis_microsteps__microsteps_for(py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__cap, py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__rung["id"])
        if py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__ms:
            py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__chain = [{"id": f"{py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__rung['id']}.{m['id']}", "primitive": m["primitive"], "plane": m.get("plane_hint"),
                      "does": m["does"], "deterministic": m.get("deterministic", True), "rung": py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__rung["id"]} for m in py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__ms]
        else:
            py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__chain = [{"id": py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__rung["id"], "primitive": "action", "plane": (py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__rung["planes"] or [None])[0],
                      "does": py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__rung["id"], "deterministic": py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__rung["deterministic"], "rung": py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__rung["id"]}]
        for py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__i, py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__n in enumerate(py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__chain):
            py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__nodes.append(py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__n)
            if py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__i > 0:
                py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__edges.append((py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__chain[py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__i - 1]["id"], py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__n["id"]))
        if py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__prev_last is not None:
            py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__edges.append((py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__prev_last, py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__chain[0]["id"]))
        py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__prev_last = py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__chain[-1]["id"]
    return {"capability": py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__cap, "nodes": py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__nodes, "edges": py_local_src_teleon_synthesis_microsteps__expand_to_micro_dag__edges, "granularity": "micro"}


def py_function_src_teleon_synthesis_microsteps__micro_decision_points(py_arg_src_teleon_synthesis_microsteps__micro_decision_points__intent: str) -> list:
    """Decision points at MICRO granularity for the synthesis tree: each micro-step -> the tools on its plane (the finer
    component choice). A step with no concrete plane tool gets a deterministic stand-in option (still testable)."""
    py_local_src_teleon_synthesis_microsteps__micro_decision_points__pt = py_function_src_teleon_synthesis_microsteps___plane_tools()
    py_local_src_teleon_synthesis_microsteps__micro_decision_points__out = []
    for py_local_src_teleon_synthesis_microsteps__micro_decision_points__n in py_function_src_teleon_synthesis_microsteps__expand_to_micro_dag(py_arg_src_teleon_synthesis_microsteps__micro_decision_points__intent)["nodes"]:
        py_local_src_teleon_synthesis_microsteps__micro_decision_points__opts = py_local_src_teleon_synthesis_microsteps__micro_decision_points__pt.get(py_local_src_teleon_synthesis_microsteps__micro_decision_points__n.get("plane"), []) or [f"step:{py_local_src_teleon_synthesis_microsteps__micro_decision_points__n['id']}"]
        py_local_src_teleon_synthesis_microsteps__micro_decision_points__out.append((py_local_src_teleon_synthesis_microsteps__micro_decision_points__n["id"], py_local_src_teleon_synthesis_microsteps__micro_decision_points__opts))
    return py_local_src_teleon_synthesis_microsteps__micro_decision_points__out


def py_function_src_teleon_synthesis_microsteps__generate_microstep_prompt(py_arg_src_teleon_synthesis_microsteps__generate_microstep_prompt__capability: str, py_arg_src_teleon_synthesis_microsteps__generate_microstep_prompt__tier: str, py_arg_src_teleon_synthesis_microsteps__generate_microstep_prompt__method: str = "") -> str:
    """The GENERATOR (more components): ask the LLM to decompose a rung into atomic micro-steps typed by the 7 primitives.
    Used when a rung has no decomposition yet; output is validated against the primitives + planes before it's accepted."""
    return (f"Decompose the '{py_arg_src_teleon_synthesis_microsteps__generate_microstep_prompt__tier}' step of the '{py_arg_src_teleon_synthesis_microsteps__generate_microstep_prompt__capability}' capability ({py_arg_src_teleon_synthesis_microsteps__generate_microstep_prompt__method}) into the SMALLEST atomic micro-steps. "
            f"Type EACH by exactly one of the seven primitives {list(py_var_src_teleon_synthesis_microsteps___PRIMITIVES)}. For each: id, what it does, the "
            "tool-plane it uses, and whether it's deterministic. Prefer deterministic micro-steps; keep each independently "
            "testable. Do NOT collapse multiple operations into one step.")


def py_function_src_teleon_synthesis_microsteps__coverage() -> dict:
    """Which ladder rungs are decomposed into micro-steps (the rest are candidates for the generator)."""
    py_local_src_teleon_synthesis_microsteps__coverage__rungs = [(l["capability"], r["tier"]) for l in json.loads((_resource("architecture") / "capability_ladders.json").read_text())["ladders"] for r in l["rungs"]]
    py_local_src_teleon_synthesis_microsteps__coverage__decomposed = set(py_function_src_teleon_synthesis_microsteps___decomps())
    return {"rungs_total": len(py_local_src_teleon_synthesis_microsteps__coverage__rungs), "rungs_decomposed": sum(1 for r in py_local_src_teleon_synthesis_microsteps__coverage__rungs if r in py_local_src_teleon_synthesis_microsteps__coverage__decomposed),
            "microsteps_total": sum(len(v) for v in py_function_src_teleon_synthesis_microsteps___decomps().values()), "serves_truth": False}
