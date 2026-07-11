"""Stop/End primitive — halt the pipeline early (guard / terminal condition)."""
from __future__ import annotations

from scripts.pipeline_object import PipelineObject
from scripts.primitives.base import Primitive


class StopEnd(Primitive):
    kind = "stop"
    label = "Stop / End"
    stage = "Stop / End"
    description = "Halt the pipeline early on a guard or terminal condition (sets the stop flag on the pipeline object)."
    schema_types = ()  # pipeline-structural

    def _run(self, po: PipelineObject) -> PipelineObject:
        if self.config.get("when", lambda _po: True)(po):
            po.set("__stopped__", True)
            po.set("__stop_reason__", self.config.get("reason", self.name))
        return po
