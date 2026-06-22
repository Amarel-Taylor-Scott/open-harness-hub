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
class Decision:
    """One versioned decision: at point `id`, we CHOSE `choice`; the untried `alternatives` are recorded, not discarded."""
    id: str
    choice: str
    alternatives: tuple = ()
    rationale: str = ""


@dataclass
class Attempt:
    ok: bool
    note: str = ""
    cost: float = 0.0            # tracked per step (the descent's currency); summed into the trace
    confidence: float | None = None  # the tester's confidence in this component/assembly (for the discipline gate)


class SynthesisNode:
    """A node = a taken decision. status: open -> working (a leaf/subtree that solves) | dead_end (this choice failed its
    own test) | abandoned (choice was fine but no descendant solved -> we backtracked past it)."""
    __slots__ = ("decision", "parent", "children", "status", "attempt")

    def __init__(self, decision: Decision | None, parent: "SynthesisNode | None" = None):
        self.decision, self.parent, self.children = decision, parent, []
        self.status, self.attempt = "open", None

    @property
    def version(self) -> str:
        """Path of choices from the root = a deterministic version id (so every decision is addressable + replayable)."""
        path, n = [], self
        while n is not None and n.decision is not None:
            path.append(f"{n.decision.id}={n.decision.choice}")
            n = n.parent
        return "/".join(reversed(path)) or "root"

    def walk(self):
        yield self
        for c in self.children:
            yield from c.walk()


class SynthesisTree:
    """DFS-with-backtracking over ordered decision POINTS. points = [(point_id, [options cheapest-first]), ...]. A tester
    decides if a (partial) assembly works: tester(chosen_decisions, partial: bool) -> Attempt. partial=True tests ONE
    component in isolation (stage-3 'test each component'); partial=False tests the COMPLETE assembly."""

    def __init__(self):
        self.root = SynthesisNode(None)
        self.solution: list[Decision] | None = None

    def synthesize(self, points, tester) -> list[Decision] | None:
        if not points:
            self.solution = []
            return []

        def rec(i: int, parent: SynthesisNode, chosen: list[Decision]):
            pid, options = points[i]
            last = i == len(points) - 1
            for opt in options:                                    # cheapest-first; each option is a BRANCH
                node = SynthesisNode(Decision(pid, opt, tuple(o for o in options if o != opt)), parent)
                parent.children.append(node)
                path = chosen + [node.decision]
                comp = tester(path, partial=True)                  # stage 3: test THIS component in isolation
                node.attempt = comp
                if not comp.ok:
                    node.status = "dead_end"                       # component fails -> try the next branch here
                    continue
                if last:                                           # full assembly -> test it end-to-end
                    full = tester(path, partial=False)
                    if full.ok:
                        node.status = "working"
                        return list(path)
                    node.status, node.attempt = "dead_end", full   # assembly fails at this leaf -> next branch
                    continue
                res = rec(i + 1, node, path)
                if res is not None:
                    node.status = "working"
                    return res
                node.status = "abandoned"                          # component ok but no descendant solved -> JUMP BACK UP
            return None                                            # every branch at this point failed -> backtrack
        self.solution = rec(0, self.root, [])
        return self.solution

    # ── lossless views (winners AND losers kept, with lineage) ───────────────────────────────────────────────────
    def branches(self) -> list[dict]:
        return [{"version": n.version, "status": n.status, "note": (n.attempt.note if n.attempt else ""),
                 "alternatives": list(n.decision.alternatives)} for n in self.root.walk() if n.decision is not None]

    def summary(self) -> dict:
        b = self.branches()
        return {
            "solved": self.solution is not None,
            "solution_version": "/".join(f"{d.id}={d.choice}" for d in self.solution) if self.solution else None,
            "branches_explored": len(b),
            "dead_ends": [x["version"] for x in b if x["status"] == "dead_end"],
            "abandoned": [x["version"] for x in b if x["status"] == "abandoned"],
            "lossless": True,        # every branch retained above with lineage (path = version)
            "serves_truth": False,
        }
