"""src.teleon.synthesis.synthesis_tree — versioned decision tree with BACKTRACKING for capability synthesis.

Owner's model: each synthesis decision (which component for a DAG node, which outline step, which parameter) BRANCHES and
is VERSIONED; the cheapest option is tried first; if a chosen branch dead-ends (the component fails, OR the subtree below
it has no working leaf) the search JUMPS BACK UP and tries the next branch. Every branch — winners AND losers — is kept
with lineage (the LOSSLESS DISTILLATION law: a winner always has lineage to the losers; nothing is discarded). The result
is the cheapest working assembly, or an HONEST 'no solution in any branch' (never a fabricated success). Pure + deterministic
(testable offline); the LLM/test functions are injected. serves_truth=false; Teleon layer — never imports src.baltor.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class py_class_src_teleon_synthesis_synthesis_tree__Decision:
    """One versioned decision: at point `id`, we CHOSE `choice`; the untried `alternatives` are recorded, not discarded."""
    id: str
    choice: str
    alternatives: tuple = ()
    rationale: str = ""


@dataclass
class py_class_src_teleon_synthesis_synthesis_tree__Attempt:
    ok: bool
    note: str = ""
    cost: float = 0.0            # tracked per step (the descent's currency); summed into the trace
    confidence: float | None = None  # the tester's confidence in this component/assembly (for the discipline gate)


class py_class_src_teleon_synthesis_synthesis_tree__SynthesisNode:
    """A node = a taken decision. status: open -> working (a leaf/subtree that solves) | dead_end (this choice failed its
    own test) | abandoned (choice was fine but no descendant solved -> we backtracked past it)."""
    __slots__ = ("decision", "parent", "children", "status", "attempt")

    def __init__(self, decision: py_class_src_teleon_synthesis_synthesis_tree__Decision | None, parent: "SynthesisNode | None" = None):
        self.decision, self.parent, self.children = decision, parent, []
        self.status, self.attempt = "open", None

    @property
    def version(self) -> str:
        """Path of choices from the root = a deterministic version id (so every decision is addressable + replayable)."""
        py_local_src_teleon_synthesis_synthesis_tree__SynthesisNode_version__path, py_local_src_teleon_synthesis_synthesis_tree__SynthesisNode_version__n = [], self
        while py_local_src_teleon_synthesis_synthesis_tree__SynthesisNode_version__n is not None and py_local_src_teleon_synthesis_synthesis_tree__SynthesisNode_version__n.decision is not None:
            py_local_src_teleon_synthesis_synthesis_tree__SynthesisNode_version__path.append(f"{py_local_src_teleon_synthesis_synthesis_tree__SynthesisNode_version__n.decision.id}={py_local_src_teleon_synthesis_synthesis_tree__SynthesisNode_version__n.decision.choice}")
            py_local_src_teleon_synthesis_synthesis_tree__SynthesisNode_version__n = py_local_src_teleon_synthesis_synthesis_tree__SynthesisNode_version__n.parent
        return "/".join(reversed(py_local_src_teleon_synthesis_synthesis_tree__SynthesisNode_version__path)) or "root"

    def walk(self):
        yield self
        for py_local_src_teleon_synthesis_synthesis_tree__SynthesisNode_walk__c in self.children:
            yield from py_local_src_teleon_synthesis_synthesis_tree__SynthesisNode_walk__c.walk()


class py_class_src_teleon_synthesis_synthesis_tree__SynthesisTree:
    """DFS-with-backtracking over ordered decision POINTS. points = [(point_id, [options cheapest-first]), ...]. A tester
    decides if a (partial) assembly works: tester(chosen_decisions, partial: bool) -> Attempt. partial=True tests ONE
    component in isolation (stage-3 'test each component'); partial=False tests the COMPLETE assembly."""

    def __init__(self):
        self.root = py_class_src_teleon_synthesis_synthesis_tree__SynthesisNode(None)
        self.solution: list[py_class_src_teleon_synthesis_synthesis_tree__Decision] | None = None

    def synthesize(self, py_arg_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize__points, py_arg_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize__tester) -> list[py_class_src_teleon_synthesis_synthesis_tree__Decision] | None:
        if not py_arg_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize__points:
            self.solution = []
            return []

        def rec(py_arg_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__i: int, py_arg_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__parent: py_class_src_teleon_synthesis_synthesis_tree__SynthesisNode, py_arg_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__chosen: list[py_class_src_teleon_synthesis_synthesis_tree__Decision]):
            py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__pid, py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__options = py_arg_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize__points[py_arg_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__i]
            py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__last = py_arg_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__i == len(py_arg_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize__points) - 1
            for py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__opt in py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__options:                                    # cheapest-first; each option is a BRANCH
                node = py_class_src_teleon_synthesis_synthesis_tree__SynthesisNode(py_class_src_teleon_synthesis_synthesis_tree__Decision(py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__pid, py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__opt, tuple(o for o in py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__options if o != py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__opt)), py_arg_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__parent)
                py_arg_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__parent.children.append(node)
                py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__path = py_arg_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__chosen + [node.decision]
                py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__comp = py_arg_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize__tester(py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__path, partial=True)                  # stage 3: test THIS component in isolation
                node.attempt = py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__comp
                if not py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__comp.ok:
                    node.status = "dead_end"                       # component fails -> try the next branch here
                    continue
                if py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__last:                                           # full assembly -> test it end-to-end
                    py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__full = py_arg_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize__tester(py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__path, partial=False)
                    if py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__full.ok:
                        node.status = "working"
                        return list(py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__path)
                    node.status, node.attempt = "dead_end", py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__full   # assembly fails at this leaf -> next branch
                    continue
                py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__res = rec(py_arg_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__i + 1, node, py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__path)
                if py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__res is not None:
                    node.status = "working"
                    return py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_synthesize_rec__res
                node.status = "abandoned"                          # component ok but no descendant solved -> JUMP BACK UP
            return None                                            # every branch at this point failed -> backtrack
        self.solution = rec(0, self.root, [])
        return self.solution

    # ── lossless views (winners AND losers kept, with lineage) ───────────────────────────────────────────────────
    def branches(self) -> list[dict]:
        return [{"version": n.version, "status": n.status, "note": (n.attempt.note if n.attempt else ""),
                 "alternatives": list(n.decision.alternatives)} for n in self.root.walk() if n.decision is not None]

    def summary(self) -> dict:
        py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_summary__b = self.branches()
        return {
            "solved": self.solution is not None,
            "solution_version": "/".join(f"{d.id}={d.choice}" for d in self.solution) if self.solution else None,
            "branches_explored": len(py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_summary__b),
            "dead_ends": [x["version"] for x in py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_summary__b if x["status"] == "dead_end"],
            "abandoned": [x["version"] for x in py_local_src_teleon_synthesis_synthesis_tree__SynthesisTree_summary__b if x["status"] == "abandoned"],
            "lossless": True,        # every branch retained above with lineage (path = version)
            "serves_truth": False,
        }
