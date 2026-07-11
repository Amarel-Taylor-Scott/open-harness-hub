"""The generic shell every pipeline primitive extends.

`Primitive` is compatible with the pipeline object: `run(po) -> po`. Each
concrete primitive lives in its own file and declares its own metadata as class
attributes (single source — no magic-string dicts elsewhere):

  kind · label · stage · exec_model · description · schema_types · subtypes

`schema_types` lists the catalog `type` values that are subtypes of this
primitive; `subtypes` gives a per-subtype display suffix. Everything the rest of
the system needs (labels, stages, descriptions) is DERIVED from these.
"""
from __future__ import annotations

import time
from typing import Any

from scripts.pipeline_object import PipelineObject, StepLog


class Primitive:
    kind: str = "primitive"
    label: str = "Primitive"
    stage: str = ""
    exec_model: str = "text-operation"   # static-information | text-operation | code-executing
    description: str = ""
    schema_types: tuple[str, ...] = ()   # catalog `type`s that extend this primitive
    subtypes: dict[str, str] = {}        # schema_type -> subtype label suffix

    def __init__(self, id: str, name: str = "", **config: Any) -> None:
        self.id = id
        self.name = name or id
        self.config = config

    def _run(self, po: PipelineObject) -> PipelineObject:  # pragma: no cover
        raise NotImplementedError

    def run(self, po: PipelineObject) -> PipelineObject:
        if po.get("__stopped__"):
            po.log(StepLog(self.id, self.id, stage=self.stage, exec_model=self.exec_model, status="skipped"))
            return po
        t0 = time.time()
        before = set(po.variables)
        po = self._run(po)
        po.log(StepLog(self.id, self.id, stage=self.stage or self.kind, exec_model=self.exec_model,
                       duration_ms=int((time.time() - t0) * 1000),
                       writes=[k for k in po.variables if k not in before], note=self.name))
        return po

    @classmethod
    def label_for(cls, schema_type: str) -> str:
        return f"{cls.label}: {cls.subtypes[schema_type]}" if schema_type in cls.subtypes else cls.label
