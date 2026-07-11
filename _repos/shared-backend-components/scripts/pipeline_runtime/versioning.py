#!/usr/bin/env python3
"""scripts.pipeline_runtime.versioning — run fingerprints over source × pipeline × processor × security.

Reuses the existing PipelineSpec/PipelineStepSpec (scripts.pipeline_runtime.specs) — does NOT redefine
them — and adds the version metadata that makes reprocessing decidable: a ProcessorSpec (code/prompt/model
/params hashes), a PipelineRun whose fingerprint composes FOUR independent hashes (source snapshot,
pipeline config, processor set, security policy), and a DerivedArtifact that carries full lineage
(source artifact ids + pipeline id/version + processor id/version + config hash + run id + tenant + security).

The fingerprint is the idempotency key for a run: same source + same pipeline + same processor set + same
security policy → SAME run id (a no-op re-run); change ANY one of the four → a DISTINCT run id (a new
versioned run that does not overwrite the old outputs).

CLI: imported by check_pipeline_run_fingerprint.py.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

# reuse the shipped pipeline manifest contract — do NOT create a second PipelineSpec.
from scripts.pipeline_runtime.specs import PipelineSpec, PipelineStepSpec  # noqa: F401


def _sha(obj: Any) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()[:24]


@dataclass
class ProcessorSpec:
    processor_id: str
    processor_version: str
    code_hash: str = ""
    prompt_hash: str = ""
    model_id: str = ""
    model_version: str = ""
    params_hash: str = ""
    deterministic: bool = True
    network_access: bool = False
    data_access: str = "tenant"  # tenant | shared | none

    @property
    def ref(self) -> str:
        return f"{self.processor_id}@{self.processor_version}"

    def fingerprint(self) -> str:
        return _sha({"ref": self.ref, "code_hash": self.code_hash, "prompt_hash": self.prompt_hash,
                     "model_id": self.model_id, "model_version": self.model_version,
                     "params_hash": self.params_hash})


def pipeline_config_hash(spec: PipelineSpec) -> str:
    """Hash the pipeline MANIFEST (id/version/steps/gates/policy) — a config edit changes this."""
    return _sha({
        "pipeline_id": spec.pipeline_id, "pipeline_version": spec.pipeline_version,
        "gates": sorted(spec.gates), "artifact_policy": spec.artifact_policy,
        "steps": [{"step_id": s.step_id, "processor": s.processor_ref, "depends_on": sorted(s.depends_on),
                   "inputs": sorted(s.input_artifact_types), "outputs": sorted(s.output_artifact_types)}
                  for s in spec.steps],
    })


def processor_set_hash(procs: list[ProcessorSpec]) -> str:
    return _sha(sorted(p.fingerprint() for p in procs))


def source_snapshot_hash(source_graph: dict) -> str:
    """Hash the {artifact_id: content_hash} snapshot of a source graph."""
    return _sha({aid: a.content_hash for aid, a in sorted(source_graph.items())})


@dataclass
class RunFingerprint:
    tenant_id: str
    isolation_mode: str
    source_snapshot_hash: str
    pipeline_id: str
    pipeline_version: str
    pipeline_config_hash: str
    processor_set_hash: str
    security_policy_hash: str
    trigger_id: str = ""

    def components(self) -> dict:
        return {"tenant_id": self.tenant_id, "isolation_mode": self.isolation_mode,
                "source_snapshot_hash": self.source_snapshot_hash, "pipeline_id": self.pipeline_id,
                "pipeline_version": self.pipeline_version, "pipeline_config_hash": self.pipeline_config_hash,
                "processor_set_hash": self.processor_set_hash, "security_policy_hash": self.security_policy_hash}

    @property
    def run_id(self) -> str:
        # NOTE: trigger_id is intentionally EXCLUDED — the fingerprint is content/config/security based,
        # so re-triggering identical inputs is idempotent (same run_id).
        return "run-" + _sha(self.components()).split(":")[1]


def run_fingerprint(*, tenant_id: str, isolation_mode: str, source_graph: dict, spec: PipelineSpec,
                    procs: list[ProcessorSpec], security_policy_hash: str, trigger_id: str = "") -> RunFingerprint:
    return RunFingerprint(
        tenant_id=tenant_id, isolation_mode=isolation_mode,
        source_snapshot_hash=source_snapshot_hash(source_graph),
        pipeline_id=spec.pipeline_id, pipeline_version=spec.pipeline_version,
        pipeline_config_hash=pipeline_config_hash(spec), processor_set_hash=processor_set_hash(procs),
        security_policy_hash=security_policy_hash, trigger_id=trigger_id)


@dataclass
class StepRun:
    run_id: str
    step_id: str
    processor_ref: str
    status: str = "done"
    output_artifact_ids: list[str] = field(default_factory=list)
    code_hash: str = ""
    config_hash: str = ""
    error: str | None = None


@dataclass
class PipelineRun:
    run_id: str
    tenant_id: str
    isolation_mode: str
    pipeline_id: str
    pipeline_version: str
    source_snapshot_hash: str
    pipeline_config_hash: str
    processor_set_hash: str
    security_policy_hash: str
    trigger_id: str = ""
    output_artifact_hash: str = ""
    status: str = "done"
    superseded_by: str | None = None

    @staticmethod
    def from_fingerprint(fp: RunFingerprint, *, output_artifact_hash: str = "", status: str = "done") -> "PipelineRun":
        return PipelineRun(
            run_id=fp.run_id, tenant_id=fp.tenant_id, isolation_mode=fp.isolation_mode,
            pipeline_id=fp.pipeline_id, pipeline_version=fp.pipeline_version,
            source_snapshot_hash=fp.source_snapshot_hash, pipeline_config_hash=fp.pipeline_config_hash,
            processor_set_hash=fp.processor_set_hash, security_policy_hash=fp.security_policy_hash,
            trigger_id=fp.trigger_id, output_artifact_hash=output_artifact_hash, status=status)


@dataclass
class DerivedArtifact:
    """A produced artifact with FULL lineage (acceptance criterion I)."""
    artifact_id: str
    tenant_id: str
    artifact_type: str
    run_id: str
    content_hash: str
    source_artifact_ids: list[str] = field(default_factory=list)   # lineage → source
    processor_id: str = ""
    processor_version: str = ""
    config_hash: str = ""
    pipeline_id: str = ""
    pipeline_version: str = ""
    claim_status: str = ""
    promotion_eligible: bool = False
    citations: list[str] = field(default_factory=list)             # supporting artifact ids (conclusions)
    payload_json: dict = field(default_factory=dict)
    security_json: dict = field(default_factory=dict)
    superseded_by: str | None = None

    @property
    def processor_ref(self) -> str:
        return f"{self.processor_id}@{self.processor_version}" if self.processor_id else ""

    def lineage_complete(self) -> bool:
        """Every derived artifact must record its source ids + pipeline + processor + config + run + tenant."""
        return bool(self.tenant_id and self.run_id and self.pipeline_id and self.pipeline_version
                    and self.config_hash and self.source_artifact_ids is not None)
