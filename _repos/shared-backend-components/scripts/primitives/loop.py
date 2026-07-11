"""Loop primitive — control flow / iteration over sub-steps."""
from __future__ import annotations

from scripts.pipeline_object import PipelineObject
from scripts.primitives.base import Primitive


class Loop(Primitive):
    kind = "loop"
    label = "Loop / Flow"
    stage = "Flow / Loops"
    description = "Control flow: repeat a body over items or while a condition holds (for-each / while / branch / parallel / map-reduce)."
    schema_types = ("pattern", "pipeline")
    subtypes = {"pipeline": "Pipeline"}

    def _run(self, po: PipelineObject) -> PipelineObject:
        body = self.config.get("body", [])
        items = self.config.get("items", po.get(self.config.get("items_key", ""), []))
        for item in items[: int(self.config.get("max_iter", 100))]:
            po.set("__loop_item__", item)
            for step in body:
                po = step.run(po)
                if po.get("__stopped__"):
                    return po
        return po
