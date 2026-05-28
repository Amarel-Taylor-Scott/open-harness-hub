"""Conditional primitive — the decision layer (the IF), kept separate from the THEN.

Holds three distinct node subtypes:
  • Condition  — a predicate over the working state (matches / classifier=Z /
                 similar-to-X (vector) / threshold / graph check);
  • Logical Operator — AND / OR / NOT / XOR that combines conditions into one boolean;
  • Expression — a free-form code predicate (e.g. `return score>0.8 and corridor in HIGH_RISK`).

The boolean it produces decides which Action (the THEN) runs. (Renamed from
"If Statement" — a Conditional naturally holds operators and custom logic, not
just a single if.)
"""
from __future__ import annotations

from scripts.pipeline_object import PipelineObject
from scripts.primitives.base import Primitive


class Conditional(Primitive):
    kind = "conditional"
    label = "Conditional"
    stage = "Conditional"
    description = ("The decision layer (the IF): a Condition (predicate), a Logical Operator "
                   "(AND/OR/NOT) combining conditions, or an Expression (free-form code). Decides "
                   "which Action (the THEN) runs — kept separate from the THEN.")
    # Display-only node subtypes (distinct from `subtypes`, which is the schema_type
    # label-suffix map and stays empty so label_for(rule-pack) == "Conditional").
    node_subtypes: tuple[str, ...] = (
        "Condition (predicate)", "Logical Operator (AND/OR/NOT)", "Expression (free-form code)")
    schema_types = ("rule-pack", "logic-pack")

    def when(self, po: PipelineObject) -> bool:
        return bool(self.config.get("when", lambda _po: False)(po))

    def _run(self, po: PipelineObject) -> PipelineObject:
        po.set(self.config.get("flag", f"{self.id}__ok"), self.when(po))
        return po
