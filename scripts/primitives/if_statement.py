"""If Statement primitive — a condition/predicate over the working state."""
from __future__ import annotations

from scripts.pipeline_object import PipelineObject
from scripts.primitives.base import Primitive


class IfStatement(Primitive):
    kind = "if"
    label = "If Statement"
    stage = "If Statements"
    description = ("A condition over the working state — contains Y / matches /…/ / similar-to-X (vector) / "
                   "classifier=Z / graph check — that triggers an Action. The IF, kept separate from the THEN.")
    schema_types = ("rule-pack", "logic-pack")

    def when(self, po: PipelineObject) -> bool:
        return bool(self.config.get("when", lambda _po: False)(po))

    def _run(self, po: PipelineObject) -> PipelineObject:
        po.set(self.config.get("flag", f"{self.id}__ok"), self.when(po))
        return po
