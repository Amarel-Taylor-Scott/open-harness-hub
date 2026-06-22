"""src.teleon.synthesis.microsteps — decompose a ladder rung into smaller MICRO-STEPS (finer components, more substitution).

A rung ('text_layer') is not atomic: it's open->detect_mime->detect_encoding->extract->normalize->segment, each a smaller
component typed by the seven primitives. Smaller rungs = more places to substitute a cheaper/deterministic component, test
in isolation, and back out of (the synthesis tree branches finer). Seeded by architecture/rung_microsteps.json; any
not-yet-decomposed rung gets generate_microstep_prompt() for the LLM to decompose (more components). serves_truth=false.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from src.teleon.synthesis import intent_to_dag as I

_REPO = Path(__file__).resolve().parents[3]
_PRIMITIVES = ("input", "knowledge_corpus", "if_statement", "action", "loop", "stop", "output")


@lru_cache(maxsize=1)
def _decomps() -> dict:
    raw = json.loads((_REPO / "architecture" / "rung_microsteps.json").read_text(encoding="utf-8"))["decompositions"]
    return {(d["capability"], d["rung"]): d["microsteps"] for d in raw}


@lru_cache(maxsize=1)
def _plane_tools() -> dict:
    out: dict = {}
    for t in json.loads((_REPO / "architecture" / "tool_registry.json").read_text())["tools"]:
        out.setdefault(t["plane"], []).append(t["id"])
    return out


def microsteps_for(capability: str, tier: str) -> list[dict]:
    """The atomic sub-steps a rung decomposes into ([] if not decomposed yet — use generate_microstep_prompt)."""
    return _decomps().get((capability, tier), [])


def expand_to_micro_dag(intent: str) -> dict:
    """A FINER DAG: each rung that has micro-steps becomes its sub-step chain; un-decomposed rungs stay one node."""
    dag = I.build_dag(intent)
    cap = dag.get("capability")
    nodes, edges, prev_last = [], [], None
    for rung in dag["nodes"]:
        ms = microsteps_for(cap, rung["id"])
        if ms:
            chain = [{"id": f"{rung['id']}.{m['id']}", "primitive": m["primitive"], "plane": m.get("plane_hint"),
                      "does": m["does"], "deterministic": m.get("deterministic", True), "rung": rung["id"]} for m in ms]
        else:
            chain = [{"id": rung["id"], "primitive": "action", "plane": (rung["planes"] or [None])[0],
                      "does": rung["id"], "deterministic": rung["deterministic"], "rung": rung["id"]}]
        for i, n in enumerate(chain):
            nodes.append(n)
            if i > 0:
                edges.append((chain[i - 1]["id"], n["id"]))
        if prev_last is not None:
            edges.append((prev_last, chain[0]["id"]))
        prev_last = chain[-1]["id"]
    return {"capability": cap, "nodes": nodes, "edges": edges, "granularity": "micro"}


def micro_decision_points(intent: str) -> list:
    """Decision points at MICRO granularity for the synthesis tree: each micro-step -> the tools on its plane (the finer
    component choice). A step with no concrete plane tool gets a deterministic stand-in option (still testable)."""
    pt = _plane_tools()
    out = []
    for n in expand_to_micro_dag(intent)["nodes"]:
        opts = pt.get(n.get("plane"), []) or [f"step:{n['id']}"]
        out.append((n["id"], opts))
    return out


def generate_microstep_prompt(capability: str, tier: str, method: str = "") -> str:
    """The GENERATOR (more components): ask the LLM to decompose a rung into atomic micro-steps typed by the 7 primitives.
    Used when a rung has no decomposition yet; output is validated against the primitives + planes before it's accepted."""
    return (f"Decompose the '{tier}' step of the '{capability}' capability ({method}) into the SMALLEST atomic micro-steps. "
            f"Type EACH by exactly one of the seven primitives {list(_PRIMITIVES)}. For each: id, what it does, the "
            "tool-plane it uses, and whether it's deterministic. Prefer deterministic micro-steps; keep each independently "
            "testable. Do NOT collapse multiple operations into one step.")


def coverage() -> dict:
    """Which ladder rungs are decomposed into micro-steps (the rest are candidates for the generator)."""
    rungs = [(l["capability"], r["tier"]) for l in json.loads((_REPO / "architecture" / "capability_ladders.json").read_text())["ladders"] for r in l["rungs"]]
    decomposed = set(_decomps())
    return {"rungs_total": len(rungs), "rungs_decomposed": sum(1 for r in rungs if r in decomposed),
            "microsteps_total": sum(len(v) for v in _decomps().values()), "serves_truth": False}
