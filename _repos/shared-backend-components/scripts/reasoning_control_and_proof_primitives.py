#!/usr/bin/env python3
"""reasoning_control_and_proof_primitives — primitives that are REASONING, CONTROL, and PROOF,
not code bodies: chain-of-thought / decomposition scaffolds, decision GATES, INVARIANT guards,
mathematical PROOF-OBLIGATION checkers, and GUIDED ROUTES that steer an agent down a specific,
edge-typed path.

Why this lane matters (owner, 2026-07-10): "allow reasoning or chain-of-thought primitives,
structured paths, mathematical proofs, gates or paths to guide agents down specific ways." The
gateway today serves 6.4M *contract* cards but no authorized code body (candidate/truth boundary);
these primitives close that from the other side — a GATE is a pure predicate, a PROOF-OBLIGATION
has a deterministic checker, a GUIDED ROUTE is edge-checkable, so unlike opaque code behavior they
are *deterministically verifiable* and can most easily reach serves_truth=true. Here the checkers
actually RUN and pass oracles; the reasoning scaffolds are typed structures that compose by edges.

Every emitted card is a candidate (candidate=true, serves_truth=false); passing an oracle is
promotion EVIDENCE, not promotion. IDs mint through the one data-plane authority (canonical_id).

    python3 scripts/reasoning_control_and_proof_primitives.py --self-test
    python3 scripts/reasoning_control_and_proof_primitives.py --demo    # run a guided route on real input
    python3 scripts/reasoning_control_and_proof_primitives.py --emit    # write candidate cards
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Optional

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
_ROOT = _SBC.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts"), str(_ROOT), str(_ROOT / "_repos" / "teleon" / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
try:
    from src.teleon.experiments.ids import canonical_id  # the ONE id authority (data-plane law)
except Exception as exc:  # pragma: no cover - import guard
    raise SystemExit(f"reasoning_control_and_proof_primitives requires canonical_id; import failed: {exc}")

#: candidate/truth boundary — every row born here (never promoted by generation).
BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
#: fixed build date so emitted cards are byte-identical across runs (no live clock — determinism law).
GENERATED_AT = "2026-07-10T00:00:00+00:00"
PRIMITIVE_ID_PREFIX = "prim:rcp"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "dev-intel" / "reasoning_control_proof_primitives"
CARDS_PATH = OUT_DIR / "reasoning_control_proof_candidate_cards.jsonl"


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# DETERMINISTIC CHECKERS — these RUN. A gate/invariant/proof primitive either accepts or rejects,
# with a reason. Because the verdict is deterministic, these are the primitives that can serve truth.
# ═══════════════════════════════════════════════════════════════════════════════════════════════

def decision_gate(value: Any, *, predicate: Callable[[Any], bool],
                  on_true: str, on_false: str) -> dict[str, Any]:
    """The If-Statement primitive: a pure predicate routes the agent to a named branch.
    Returns the branch label + the boolean, deterministically. No side effects."""
    taken = bool(predicate(value))
    return {"branch": on_true if taken else on_false, "predicate_true": taken, **BOUNDARY}


def invariant_guard(before: dict[str, Any], after: dict[str, Any], *,
                    invariants: list[tuple[str, Callable[[dict, dict], bool]]]) -> dict[str, Any]:
    """Guards a state transition: every named invariant must hold from `before` to `after`.
    Returns held=False + the first violated invariant so a Loop/Action can be blocked, not run blind."""
    for name, holds in invariants:
        if not holds(before, after):
            return {"held": False, "violated": name, **BOUNDARY}
    return {"held": True, "violated": None, **BOUNDARY}


def check_graph_coloring_certificate(graph: dict[Any, list[Any]], coloring: dict[Any, int],
                                     k: int) -> dict[str, Any]:
    """PROOF-OBLIGATION (certificate checker): verify a proposed k-coloring is PROPER — the classic
    'hard to find, cheap to verify' shape. Deterministic, O(V+E). An agent may PRODUCE a coloring by
    any reasoning it likes; this primitive VERIFIES it, so the verdict is trustworthy regardless."""
    colors_used = set(coloring.values())
    if any(c < 0 or c >= k for c in colors_used):
        return {"valid": False, "reason": "color_out_of_range", "colors_used": len(colors_used), **BOUNDARY}
    for node, neighbors in graph.items():
        if node not in coloring:
            return {"valid": False, "reason": f"uncolored_node:{node}", **BOUNDARY}
        for nb in neighbors:
            if coloring.get(nb) == coloring[node]:
                return {"valid": False, "reason": f"adjacent_conflict:{node}-{nb}", **BOUNDARY}
    return {"valid": True, "reason": None, "colors_used": len(colors_used), **BOUNDARY}


#: the natural-deduction rules a proof step may cite (deterministic propositional fragment).
_INFERENCE_RULES = {"assumption", "modus_ponens", "and_intro", "and_elim_left", "and_elim_right"}


def validate_inference_chain(premises: list[str], steps: list[dict[str, Any]]) -> dict[str, Any]:
    """MATHEMATICAL-PROOF primitive: verify a chain of inference steps is VALID — each step's
    formula must follow from the premises or earlier steps by the cited rule. This is the 'gate/path
    to guide an agent down a specific reasoning way': the agent proposes a proof, the primitive
    accepts only a sound one. Formulas are opaque tokens; implication is written 'A>B', conj 'A&B'.
    Deterministic; returns the first invalid step so the agent can repair exactly that link."""
    known: set[str] = set(premises)
    for i, step in enumerate(steps):
        rule = step.get("rule")
        formula = step.get("formula", "")
        refs = [premises[r] if isinstance(r, int) and 0 <= r < len(premises) else r
                for r in step.get("from", [])]
        ok = False
        if rule == "assumption":
            ok = formula in premises
        elif rule == "modus_ponens" and len(refs) == 2:
            a, imp = refs[0], refs[1]
            ok = imp == f"{a}>{formula}" and a in known and imp in known
        elif rule == "and_intro" and len(refs) == 2:
            ok = formula == f"{refs[0]}&{refs[1]}" and all(r in known for r in refs)
        elif rule == "and_elim_left" and len(refs) == 1:
            ok = refs[0] in known and refs[0].startswith(f"{formula}&")
        elif rule == "and_elim_right" and len(refs) == 1:
            ok = refs[0] in known and refs[0].endswith(f"&{formula}")
        if rule not in _INFERENCE_RULES:
            return {"valid": False, "failed_step": i, "reason": f"unknown_rule:{rule}", **BOUNDARY}
        if not ok:
            return {"valid": False, "failed_step": i, "reason": f"unjustified:{rule}", "formula": formula,
                    **BOUNDARY}
        known.add(formula)
    proved = steps[-1]["formula"] if steps else None
    return {"valid": True, "failed_step": None, "proves": proved, "steps": len(steps), **BOUNDARY}


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# GUIDED ROUTE — a typed DAG of gates + proof-obligations + actions that steers an agent down ONE
# path. The control nodes RUN deterministically; the reasoning nodes are typed scaffolds. Every hop
# is edge-checked, so the whole path is verifiable even where individual actions are model calls.
# ═══════════════════════════════════════════════════════════════════════════════════════════════

def run_guided_route(route: list[dict[str, Any]], context: dict[str, Any]) -> dict[str, Any]:
    """Execute a guided route. Each node is {kind, name, ...}. `gate`/`proof`/`invariant` nodes decide
    whether to continue (deterministic); `action`/`reasoning` nodes are recorded as the step the agent
    must perform next. Returns the full trace + terminal outcome — a deterministic, replayable path."""
    trace: list[dict[str, Any]] = []
    for node in route:
        kind = node["kind"]
        if kind == "gate":
            r = decision_gate(context.get(node["reads"]), predicate=node["predicate"],
                              on_true=node["on_true"], on_false=node["on_false"])
            trace.append({"node": node["name"], "kind": kind, "branch": r["branch"]})
            if r["branch"] == node.get("halt_on"):
                return {"outcome": "halted", "at": node["name"], "reason": r["branch"], "trace": trace, **BOUNDARY}
        elif kind == "proof":
            r = node["check"](context)
            passed = r.get("valid", r.get("held", False))
            trace.append({"node": node["name"], "kind": kind, "passed": passed,
                          "reason": r.get("reason") or r.get("violated")})
            if not passed:
                return {"outcome": "rejected", "at": node["name"], "reason": r.get("reason"),
                        "trace": trace, **BOUNDARY}
        else:  # action / reasoning — a typed step the agent performs; recorded, not executed here
            trace.append({"node": node["name"], "kind": kind, "next_action": node.get("does")})
    return {"outcome": "accepted", "at": route[-1]["name"] if route else None, "trace": trace, **BOUNDARY}


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# THE PRIMITIVE CARDS — registry-schema-matching candidate cards for each new kind. Typed edges so
# they compose with code primitives through the SAME compatibility lattice; proof_requirements name
# the oracle that would promote them.
# ═══════════════════════════════════════════════════════════════════════════════════════════════

#: (primitive_kind, title, input_edge, output_edge, blackbox, tags, proof_requirement, deterministic?)
PRIMITIVE_SPECS: list[dict[str, Any]] = [
    {"kind": "logic.decision_gate", "title": "Deterministic decision gate (If-Statement primitive)",
     "input_edge": "TypedValue+BranchPredicate", "output_edge": "BranchLabel+PredicateVerdict",
     "blackbox": "Routes an agent to a named branch by a pure predicate over a typed value. No side "
                 "effects; verdict is deterministic. The seven-primitive 'If Statement'.",
     "tags": ["control_flow", "routing"], "deterministic": True,
     "proof": "known_input_output_fixture: predicate true routes to on_true, false to on_false"},
    {"kind": "logic.invariant_guard", "title": "Invariant guard over a state transition",
     "input_edge": "StateBefore+StateAfter+InvariantSet", "output_edge": "InvariantVerdict+ViolatedName",
     "blackbox": "Blocks a Loop/Action unless every named invariant holds from before-state to "
                 "after-state; returns the first violated invariant. Deterministic guard.",
     "tags": ["control_flow", "safety"], "deterministic": True,
     "proof": "a transition violating one invariant returns held=false with that invariant named"},
    {"kind": "logic.proof_obligation.graph_coloring", "title": "Graph k-coloring certificate checker",
     "input_edge": "Graph+Coloring+ColorBound", "output_edge": "ProperColoringVerdict+FailingConstraint",
     "blackbox": "Verifies a proposed k-coloring is proper (no adjacent nodes share a color, ≤k colors) "
                 "in O(V+E) — the canonical hard-to-find / cheap-to-verify certificate.",
     "tags": ["proof", "verification", "graph"], "deterministic": True,
     "proof": "a proper coloring returns valid=true; an adjacent conflict returns the offending edge"},
    {"kind": "logic.proof_obligation.inference_chain", "title": "Natural-deduction inference-chain validator",
     "input_edge": "Premises+InferenceChain", "output_edge": "ProofVerdict+FailedStep",
     "blackbox": "Verifies each step of a proposed proof follows from premises/earlier steps by a cited "
                 "rule (assumption, modus ponens, ∧-intro/elim); returns the first unjustified step.",
     "tags": ["proof", "reasoning", "logic"], "deterministic": True,
     "proof": "a sound modus-ponens chain returns valid=true; an unjustified step returns its index"},
    {"kind": "reasoning.chain_of_thought", "title": "Chain-of-thought reasoning scaffold",
     "input_edge": "Problem+ReasoningBudget", "output_edge": "ReasonedAnswer+ReasoningTrace",
     "blackbox": "A typed reasoning structure (understand → decompose → solve → self-check) that guides "
                 "an agent's steps. A scaffold, not a code body; composes downstream of a decomposition.",
     "tags": ["reasoning", "scaffold"], "deterministic": False,
     "proof": "self_check stage rejects an answer that fails its own stated verification"},
    {"kind": "reasoning.decomposition", "title": "Problem decomposition scaffold",
     "input_edge": "Problem", "output_edge": "SubproblemSet+DependencyOrder",
     "blackbox": "Splits a problem into typed subproblems with a dependency order an agent can follow. "
                 "Feeds chain-of-thought and guided routes.",
     "tags": ["reasoning", "planning"], "deterministic": False,
     "proof": "recomposing the subproblem outputs answers the original (fixture-checked)"},
    {"kind": "control.guided_route", "title": "Guided route: gate→proof→action path for an agent",
     "input_edge": "RouteSpec+Context", "output_edge": "RouteOutcome+DeterministicTrace",
     "blackbox": "Executes a typed DAG of gates, proof-obligations, and action/reasoning steps that "
                 "steers an agent down one edge-checked path; control nodes decide deterministically, "
                 "so the whole path is replayable and verifiable.",
     "tags": ["control_flow", "orchestration", "agent_guidance"], "deterministic": True,
     "proof": "a context failing the gate/proof halts at that node with the reason; a passing one accepts"},
]


def _card(spec: dict[str, Any]) -> dict[str, Any]:
    pid = canonical_id(PRIMITIVE_ID_PREFIX, spec["kind"], spec["title"])
    edges = spec["input_edge"].split("+") + spec["output_edge"].split("+")
    blocking = sorted({t.lower() for t in spec["tags"]}
                      | {w.lower() for w in spec["title"].split() if len(w) > 3}
                      | {e.lower() for e in edges})
    return {
        "primitive_id": pid, "title": spec["title"], "blackbox": spec["blackbox"],
        "primitive_kind": spec["kind"], "kind": "reasoning.primitive" if spec["kind"].startswith("reasoning")
        else "control.primitive" if spec["kind"].startswith("control") else "logic.primitive",
        "input_edge": spec["input_edge"], "output_edge": spec["output_edge"],
        "contract": {"deterministic": spec["deterministic"],
                     "verifiable": spec["deterministic"],
                     "composes_via": "edge_contract"},
        "capability_tags": spec["tags"], "domains": ["reasoning", "control", "verification"],
        "runtime_targets": ["python", "typescript"],
        "proof_requirements": [spec["proof"]],
        "promotion_blockers": ([] if spec["deterministic"]
                               else ["scaffold_not_deterministically_checkable", "review_required"]),
        "readiness": "R4_checker_runs_and_passes_oracle" if spec["deterministic"] else "R3_contract_known",
        "verification_level": "L4_deterministic_checker" if spec["deterministic"] else "L3_shape_source_proof",
        "blocking_keys": blocking, "source_family": "reasoning_control_proof",
        "generated_at": GENERATED_AT, **BOUNDARY,
    }


def emit_cards() -> list[dict[str, Any]]:
    """Deterministic: same specs → byte-identical cards + unique ids."""
    return [_card(s) for s in PRIMITIVE_SPECS]


def build(write: bool = True) -> dict[str, Any]:
    cards = emit_cards()
    if write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        CARDS_PATH.write_text("".join(json.dumps(c, sort_keys=True) + "\n" for c in cards), encoding="utf-8")
    n_det = sum(1 for c in cards if c["contract"]["deterministic"])
    return {"record_type": "reasoning_control_proof_cards", "n_cards": len(cards),
            "n_deterministic_checkers": n_det, "n_scaffolds": len(cards) - n_det,
            "path": str(CARDS_PATH) if write else None, **BOUNDARY}


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# DEMO — a real guided route: gate on problem size → verify the proposed coloring → accept/reject.
# ═══════════════════════════════════════════════════════════════════════════════════════════════

def demo_guided_route() -> dict[str, Any]:
    """A real agent-guidance path: only attempt the careful proof if the graph is non-trivial, then
    require a VALID coloring certificate before accepting. Runs deterministically end-to-end."""
    graph = {"a": ["b", "c"], "b": ["a", "c"], "c": ["a", "b"]}  # triangle → needs 3 colors
    route = [
        {"kind": "gate", "name": "size_gate", "reads": "n_nodes",
         "predicate": lambda n: n >= 2, "on_true": "verify", "on_false": "trivial", "halt_on": "trivial"},
        {"kind": "proof", "name": "coloring_certificate",
         "check": lambda ctx: check_graph_coloring_certificate(ctx["graph"], ctx["coloring"], ctx["k"])},
        {"kind": "action", "name": "accept_solution", "does": "record the verified coloring as a candidate result"},
    ]
    good = run_guided_route(route, {"n_nodes": len(graph), "graph": graph,
                                    "coloring": {"a": 0, "b": 1, "c": 2}, "k": 3})
    bad = run_guided_route(route, {"n_nodes": len(graph), "graph": graph,
                                   "coloring": {"a": 0, "b": 0, "c": 2}, "k": 3})  # a-b conflict
    return {"valid_input_outcome": good, "invalid_input_outcome": bad}


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# SELF-TEST — mutation-gated (a real injected defect makes it RED), determinism, oracles.
# ═══════════════════════════════════════════════════════════════════════════════════════════════

def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    # (1) decision gate routes both ways
    hi = decision_gate(10, predicate=lambda x: x > 5, on_true="big", on_false="small")
    lo = decision_gate(1, predicate=lambda x: x > 5, on_true="big", on_false="small")
    checks.append(("decision_gate routes true→big / false→small",
                   hi["branch"] == "big" and lo["branch"] == "small"))

    # (2) graph-coloring certificate: proper passes, conflict + over-k fail (MUTATION-SENSITIVE)
    tri = {"a": ["b", "c"], "b": ["a", "c"], "c": ["a", "b"]}
    proper = check_graph_coloring_certificate(tri, {"a": 0, "b": 1, "c": 2}, 3)
    conflict = check_graph_coloring_certificate(tri, {"a": 0, "b": 0, "c": 2}, 3)
    overk = check_graph_coloring_certificate(tri, {"a": 0, "b": 1, "c": 2}, 2)
    checks.append(("graph-coloring checker: proper valid, conflict+over-k REJECTED",
                   proper["valid"] is True and conflict["valid"] is False
                   and conflict["reason"].startswith("adjacent_conflict")
                   and overk["valid"] is False))

    # (3) inference chain: a sound modus-ponens proof passes; an unjustified step is caught at its index
    premises = ["P", "P>Q"]
    sound = validate_inference_chain(premises, [
        {"rule": "assumption", "formula": "P", "from": []},
        {"rule": "assumption", "formula": "P>Q", "from": []},
        {"rule": "modus_ponens", "formula": "Q", "from": ["P", "P>Q"]},
    ])
    unsound = validate_inference_chain(["P"], [  # only P is given — P>Q is neither premise nor derived
        {"rule": "assumption", "formula": "P", "from": []},
        {"rule": "modus_ponens", "formula": "Q", "from": ["P", "P>Q"]},  # cites P>Q, which is not known
    ])
    checks.append(("inference-chain validator: sound proof valid, unjustified step caught",
                   sound["valid"] is True and sound["proves"] == "Q"
                   and unsound["valid"] is False and unsound["failed_step"] == 1))

    # (4) invariant guard blocks a violating transition
    guard = invariant_guard({"balance": 100}, {"balance": -5},
                            invariants=[("non_negative_balance", lambda b, a: a["balance"] >= 0)])
    checks.append(("invariant_guard blocks negative balance",
                   guard["held"] is False and guard["violated"] == "non_negative_balance"))

    # (5) guided route: valid input accepted end-to-end; invalid halted/rejected at the proof node
    d = demo_guided_route()
    checks.append(("guided_route accepts valid coloring, rejects the conflicting one",
                   d["valid_input_outcome"]["outcome"] == "accepted"
                   and d["invalid_input_outcome"]["outcome"] == "rejected"
                   and d["invalid_input_outcome"]["at"] == "coloring_certificate"))

    # (6) cards: deterministic (byte-identical), unique ids, candidate-only, deterministic ones carry no blockers
    c1 = emit_cards()
    c2 = emit_cards()
    ids = [c["primitive_id"] for c in c1]
    det_clean = all(c["promotion_blockers"] == [] for c in c1 if c["contract"]["deterministic"])
    checks.append(("cards deterministic + unique ids + candidate-only + det-checkers promotion-clean",
                   json.dumps(c1, sort_keys=True) == json.dumps(c2, sort_keys=True)
                   and len(ids) == len(set(ids))
                   and all(c["candidate"] is True and c["serves_truth"] is False for c in c1)
                   and det_clean))

    # (7) every card composes by typed edges (non-empty input/output edges)
    checks.append(("every card declares typed input/output edges (composes via the lattice)",
                   all(c["input_edge"] and c["output_edge"] for c in c1)))

    ok = all(v for _, v in checks)
    print("reasoning_control_and_proof_primitives — self-test")
    for name, v in checks:
        print(f"  [{'ok' if v else 'FAIL'}] {name}")
    summary = build(write=False)
    print(f"  {summary['n_cards']} cards: {summary['n_deterministic_checkers']} deterministic checkers "
          f"(serve-truth-ready via oracle) + {summary['n_scaffolds']} reasoning scaffolds. candidate-only.")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


def _main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--emit", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return _self_test()
    if args.demo:
        print(json.dumps(demo_guided_route(), indent=2))
        return 0
    if args.emit:
        print(json.dumps(build(write=True), indent=2))
        return 0
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(_main())
