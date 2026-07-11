"""src.teleon.synthesis.synthesis_trace — per-step DATA TRACKING for capability synthesis (the telemetry layer).

Owner: track data at every step. From a finished SynthesisTree this builds an ordered, persistable trace — one record
per decision node: version, stage, choice, alternatives considered, test outcome, cost, confidence, status (working /
dead_end / abandoned). This is the per-step execution telemetry the cognitive-compiler moat needs: it turns the
synthesis from modeled into MEASURED, and it's what the descent brain learns from (winners AND losers). Pure +
deterministic; persistence is plain JSONL (the caller stamps time). serves_truth=false; Teleon layer.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field


@dataclass
class py_class_src_teleon_synthesis_synthesis_trace__SynthesisStep:
    version: str                 # decision-path id (addressable + replayable)
    decision_id: str
    choice: str
    status: str                  # working | dead_end | abandoned | open
    alternatives_considered: list = field(default_factory=list)
    test_ok: bool | None = None
    cost: float = 0.0
    confidence: float | None = None
    note: str = ""


@dataclass
class py_class_src_teleon_synthesis_synthesis_trace__SynthesisTrace:
    intent: str = ""
    strategy: str = ""           # which escape strategy produced this attempt (base / sprout / reframe / ...)
    steps: list = field(default_factory=list)

    @classmethod
    def from_tree(cls, py_arg_src_teleon_synthesis_synthesis_trace__SynthesisTrace_from_tree__tree, *, intent: str = "", strategy: str = "base") -> "SynthesisTrace":
        py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_from_tree__steps = []
        for py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_from_tree__n in py_arg_src_teleon_synthesis_synthesis_trace__SynthesisTrace_from_tree__tree.root.walk():
            if py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_from_tree__n.decision is None:
                continue
            py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_from_tree__a = py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_from_tree__n.attempt
            py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_from_tree__steps.append(py_class_src_teleon_synthesis_synthesis_trace__SynthesisStep(
                version=py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_from_tree__n.version, decision_id=py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_from_tree__n.decision.id, choice=py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_from_tree__n.decision.choice, status=py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_from_tree__n.status,
                alternatives_considered=list(py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_from_tree__n.decision.alternatives),
                test_ok=(py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_from_tree__a.ok if py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_from_tree__a else None), cost=(py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_from_tree__a.cost if py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_from_tree__a else 0.0),
                confidence=(py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_from_tree__a.confidence if py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_from_tree__a else None), note=(py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_from_tree__a.note if py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_from_tree__a else "")))
        return cls(intent=intent, strategy=strategy, steps=py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_from_tree__steps)

    # ── tracked aggregates (the data the brain + the user see) ───────────────────────────────────────────────
    def total_cost(self) -> float:
        return round(sum(s.cost for s in self.steps), 6)

    def deterministic_ratio(self) -> float:
        """share of explored choices that were deterministic (model:/llm: choices are not) — the descent's health."""
        if not self.steps:
            return 0.0
        py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_deterministic_ratio__det = sum(1 for s in self.steps if not (s.choice.startswith("llm") or s.choice.startswith("model")))
        return round(py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_deterministic_ratio__det / len(self.steps), 3)

    def explored_vs_committed(self) -> dict:
        """did we 'jump down too fast'? high explored-but-not-committed = healthy breadth; 0 alternatives = a red flag."""
        py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_explored_vs_committed__working = [s for s in self.steps if s.status == "working"]
        py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_explored_vs_committed__considered = sum(len(s.alternatives_considered) for s in py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_explored_vs_committed__working)
        return {"committed": len(py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_explored_vs_committed__working), "alternatives_considered_on_path": py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_explored_vs_committed__considered,
                "jumped_without_alternatives": [s.version for s in py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_explored_vs_committed__working if not s.alternatives_considered]}

    def summary(self) -> dict:
        py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_summary__st = {}
        for py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_summary__s in self.steps:
            py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_summary__st[py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_summary__s.status] = py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_summary__st.get(py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_summary__s.status, 0) + 1
        return {"intent": self.intent, "strategy": self.strategy, "steps": len(self.steps), "by_status": py_local_src_teleon_synthesis_synthesis_trace__SynthesisTrace_summary__st,
                "total_cost": self.total_cost(), "deterministic_ratio": self.deterministic_ratio(),
                "exploration": self.explored_vs_committed(), "serves_truth": False}

    def to_jsonl(self) -> str:
        return "\n".join(json.dumps({"intent": self.intent, "strategy": self.strategy, **asdict(s)}) for s in self.steps)
