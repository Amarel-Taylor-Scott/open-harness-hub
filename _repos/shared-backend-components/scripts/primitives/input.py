"""Input primitive — the payload to work on."""
from __future__ import annotations

from scripts.pipeline_object import PipelineObject
from scripts.primitives.base import Primitive


class Input(Primitive):
    kind = "input"
    label = "Input"
    stage = "Input"
    exec_model = "static-information"
    description = "The payload to work on: text, document, HTML, PDF, image, audio/video, or a combination."
    schema_types = ()  # pipeline-structural, not a catalog component type

    def _run(self, po: PipelineObject) -> PipelineObject:
        po.set("input", self.config.get("value", po.input))
        po.input_type = self.config.get("input_type", po.input_type)
        return po
