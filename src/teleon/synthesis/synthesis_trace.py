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
class SynthesisStep:
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
class SynthesisTrace:
    intent: str = ""
    strategy: str = ""           # which escape strategy produced this attempt (base / sprout / reframe / ...)
    steps: list = field(default_factory=list)

    @classmethod
    def from_tree(cls, tree, *, intent: str = "", strategy: str = "base") -> "SynthesisTrace":
        steps = []
        for n in tree.root.walk():
            if n.decision is None:
                continue
            a = n.attempt
            steps.append(SynthesisStep(
                version=n.version, decision_id=n.decision.id, choice=n.decision.choice, status=n.status,
                alternatives_considered=list(n.decision.alternatives),
                test_ok=(a.ok if a else None), cost=(a.cost if a else 0.0),
                confidence=(a.confidence if a else None), note=(a.note if a else "")))
        return cls(intent=intent, strategy=strategy, steps=steps)

    # ── tracked aggregates (the data the brain + the user see) ───────────────────────────────────────────────
    def total_cost(self) -> float:
        return round(sum(s.cost for s in self.steps), 6)

    def deterministic_ratio(self) -> float:
        """share of explored choices that were deterministic (model:/llm: choices are not) — the descent's health."""
        if not self.steps:
            return 0.0
        det = sum(1 for s in self.steps if not (s.choice.startswith("llm") or s.choice.startswith("model")))
        return round(det / len(self.steps), 3)

    def explored_vs_committed(self) -> dict:
        """did we 'jump down too fast'? high explored-but-not-committed = healthy breadth; 0 alternatives = a red flag."""
        working = [s for s in self.steps if s.status == "working"]
        considered = sum(len(s.alternatives_considered) for s in working)
        return {"committed": len(working), "alternatives_considered_on_path": considered,
                "jumped_without_alternatives": [s.version for s in working if not s.alternatives_considered]}

    def summary(self) -> dict:
        st = {}
        for s in self.steps:
            st[s.status] = st.get(s.status, 0) + 1
        return {"intent": self.intent, "strategy": self.strategy, "steps": len(self.steps), "by_status": st,
                "total_cost": self.total_cost(), "deterministic_ratio": self.deterministic_ratio(),
                "exploration": self.explored_vs_committed(), "serves_truth": False}

    def to_jsonl(self) -> str:
        return "\n".join(json.dumps({"intent": self.intent, "strategy": self.strategy, **asdict(s)}) for s in self.steps)
