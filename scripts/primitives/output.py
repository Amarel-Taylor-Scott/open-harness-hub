"""Output primitive — finalize the result + trace into the pipeline object."""
from __future__ import annotations

from scripts.pipeline_object import PipelineObject
from scripts.primitives.base import Primitive


class Output(Primitive):
    kind = "output"
    label = "Output"
    stage = "Output"
    description = "Finalize the delivered result + trace into the pipeline object's outputs."
    schema_types = ()  # pipeline-structural

    def _run(self, po: PipelineObject) -> PipelineObject:
        keys = self.config.get("from_keys")
        if keys:
            for k in keys:
                po.add_output(k, po.get(k))
        else:
            po.add_output("result", self.config.get("value", po.get("result")))
        return po
