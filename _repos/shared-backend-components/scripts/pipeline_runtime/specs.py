#!/usr/bin/env python3
"""scripts.pipeline_runtime.specs — versioned pipeline + processor + run contracts (stdlib only).

A PipelineSpec is a MANIFEST (JSON on disk), not Python glue: versioned steps, each naming a
``processor@version`` from the registry, declared input/output artifact types, gates, and an
idempotency-key template that includes BOTH the input version AND the pipeline version — so a changed
document OR a changed pipeline config triggers reprocessing (a distinct run). Discoverable + validatable.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

VALID_STATUS = ("active", "experimental", "deprecated")


@dataclass
class PipelineStepSpec:
    step_id: str
    processor_id: str
    processor_version: str
    queue: str = ""
    input_artifact_types: list[str] = field(default_factory=list)
    output_artifact_types: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    timeout_seconds: int = 120
    can_run_parallel: bool = True
    retry_policy: dict = field(default_factory=lambda: {"max_attempts": 3})

    @property
    def processor_ref(self) -> str:
        return f"{self.processor_id}@{self.processor_version}"

    @staticmethod
    def from_dict(d: dict) -> "PipelineStepSpec":
        proc = d.get("processor", "")
        pid, _, pver = proc.partition("@")
        return PipelineStepSpec(
            step_id=d["step_id"], processor_id=pid or d.get("processor_id", ""),
            processor_version=pver or d.get("processor_version", ""),
            queue=d.get("queue", ""),
            input_artifact_types=list(d.get("inputs") or d.get("input_artifact_types") or []),
            output_artifact_types=list(d.get("outputs") or d.get("output_artifact_types") or []),
            depends_on=list(d.get("depends_on") or []),
            timeout_seconds=int(d.get("timeout_seconds", 120)),
            can_run_parallel=bool(d.get("can_run_parallel", True)),
            retry_policy=dict(d.get("retry_policy") or {"max_attempts": 3}))


@dataclass
class PipelineSpec:
    pipeline_id: str
    pipeline_version: str
    description: str
    status: str
    input_schema: str
    output_schema: str
    partition_key: str
    idempotency_key_template: str
    steps: list[PipelineStepSpec]
    gates: list[str] = field(default_factory=list)
    artifact_policy: dict = field(default_factory=dict)
    retry_policy: dict = field(default_factory=dict)
    isolation: str = "shared"  # shared | per_tenant_db (data-isolation requirement)

    @property
    def ref(self) -> str:
        return f"{self.pipeline_id}@{self.pipeline_version}"

    @staticmethod
    def from_dict(d: dict) -> "PipelineSpec":
        return PipelineSpec(
            pipeline_id=d["pipeline_id"], pipeline_version=d["pipeline_version"],
            description=d.get("description", ""), status=d.get("status", "active"),
            input_schema=d.get("input_schema", ""), output_schema=d.get("output_schema", ""),
            partition_key=d.get("partition_key", "tenant_id"),
            idempotency_key_template=d.get("idempotency_key_template", ""),
            steps=[PipelineStepSpec.from_dict(s) for s in d.get("steps", [])],
            gates=list(d.get("gates") or []),
            artifact_policy=dict(d.get("artifact_policy") or {}),
            retry_policy=dict(d.get("retry_policy") or {}),
            isolation=d.get("isolation", "shared"))


def load_manifest(path: str | Path) -> PipelineSpec:
    return PipelineSpec.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


_PIPELINES_DIR = _resource("pipelines")


def discover(pipelines_dir: str | Path = _PIPELINES_DIR) -> dict[str, PipelineSpec]:
    """Load every ``pipelines/*.json`` manifest → {pipeline_id@version: PipelineSpec}."""
    out: dict[str, PipelineSpec] = {}
    for p in sorted(Path(pipelines_dir).glob("*.json")):
        spec = load_manifest(p)
        out[spec.ref] = spec
    return out


def validate(spec: PipelineSpec, *, registry: Any | None = None) -> list[str]:
    """Return a list of contract violations (empty = valid). registry is a ProcessorRegistry (optional)."""
    errs: list[str] = []
    if spec.status not in VALID_STATUS:
        errs.append(f"{spec.ref}: invalid status {spec.status!r}")
    if spec.status == "active" and not spec.idempotency_key_template:
        errs.append(f"{spec.ref}: active pipeline missing idempotency_key_template")
    if not spec.steps:
        errs.append(f"{spec.ref}: no steps")
    step_ids = {s.step_id for s in spec.steps}
    for s in spec.steps:
        if not s.output_artifact_types:
            errs.append(f"{spec.ref}.{s.step_id}: no output_artifact_types declared")
        if s.step_id != spec.steps[0].step_id and not (s.input_artifact_types or s.depends_on):
            errs.append(f"{spec.ref}.{s.step_id}: non-source step declares no inputs/depends_on")
        for dep in s.depends_on:
            if dep not in step_ids:
                errs.append(f"{spec.ref}.{s.step_id}: depends_on unknown step {dep!r}")
        if spec.status == "active" and registry is not None and not registry.has(s.processor_ref):
            errs.append(f"{spec.ref}.{s.step_id}: active step references unregistered processor {s.processor_ref}")
    return errs
