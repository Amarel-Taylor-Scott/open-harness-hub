"""Action primitive — anything that does something (the THEN).

More specific actions extend this (add-persona, execute/call, transform,
model-call, model-transport, evaluate, benchmark); their per-subtype labels live
in `subtypes` so there is a single source, not a scattered magic dict.
"""
from __future__ import annotations

from typing import Any

from scripts.pipeline_object import PipelineObject
from scripts.primitives.base import Primitive


class Action(Primitive):
    kind = "action"
    label = "Action"
    stage = "Actions"
    description = ("Does something (the THEN): retrieve, rerank/prioritize, compress/polish with a small model, "
                   "transform (format/redact/normalize), execute code / call an API / fetch / extract / post / "
                   "webhook, add a persona, call the model, evaluate, or monitor.")
    schema_types = ("persona", "tool", "processor", "harness", "adapter", "rubric", "benchmark")
    subtypes = {
        "persona": "Add Persona", "tool": "Execute / Call", "processor": "Transform",
        "harness": "Model Call", "adapter": "Model Transport",
        "rubric": "Evaluate", "benchmark": "Benchmark",
    }

    def __init__(self, id: str, name: str = "", *, exec_model: str = "text-operation", **config: Any) -> None:
        super().__init__(id, name, **config)
        self.exec_model = exec_model

    def _run(self, po: PipelineObject) -> PipelineObject:
        return self.config.get("do", lambda po: po)(po) or po
