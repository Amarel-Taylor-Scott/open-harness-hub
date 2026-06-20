#!/usr/bin/env python3
"""scripts.pipeline_runtime.reprocess_planner — minimal, classified reprocessing plans.

Given a CHANGE (source content / pipeline config / processor version / security policy), compute the
MINIMAL set of steps + artifacts to rerun, and classify the work:
  semantic_reprocess_required · storage_migration_required · reencrypt_required
plus the affected source/derived artifact ids, steps_to_rerun / steps_to_skip, human-approval flag, and
reason_codes. The scoping uses the artifact-type dependency DAG so a single changed narrative sentence
reruns sentence→allegation→emotion→conclusion→pack (but NOT the unrelated structured-field facts), while a
KMS rotation is re-encryption only and an isolation upgrade is storage migration only — never a needless
semantic reprocess.

CLI: imported by the check_reprocess_*.py proofs.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from scripts.pipeline_runtime.versioning import DerivedArtifact, PipelineSpec, pipeline_config_hash
from scripts.security.tenant_catalog import TenantPolicy

#: artifact-type dependency DAG — type → the upstream types it consumes (source grains have no typed upstream).
DEPENDS_ON: dict[str, list[str]] = {
    "sentence": [],
    "atomic_fact": [],
    "entity_mention": [],
    "narrative_allegation": ["sentence"],
    "emotion_signal": ["sentence"],
    "conclusion": ["atomic_fact", "narrative_allegation"],
    "context_pack": ["atomic_fact", "narrative_allegation", "conclusion", "emotion_signal", "entity_mention"],
    "receipt": ["context_pack"],
}
ALL_DERIVED_TYPES = list(DEPENDS_ON)


def downstream_closure(seed_types: set[str]) -> set[str]:
    """All derived types that (transitively) consume any seed type, plus the seeds themselves."""
    affected = set(seed_types)
    changed = True
    while changed:
        changed = False
        for t, ups in DEPENDS_ON.items():
            if t not in affected and any(u in affected for u in ups):
                affected.add(t); changed = True
    return affected


def _seed_types_for_source(artifact_type: str, field_name: str = "") -> set[str]:
    """Map a changed SOURCE artifact to the derived grain types directly re-derived from it."""
    if artifact_type in ("sentence", "source_block"):
        return {"sentence"}
    if artifact_type == "source_field":
        seeds = {"atomic_fact"}
        if field_name in ("company", "product"):
            seeds.add("entity_mention")
        return seeds
    if artifact_type == "source_record":
        return set(ALL_DERIVED_TYPES)
    return set()


@dataclass
class ReprocessPlan:
    change_kind: str
    semantic_reprocess_required: bool = False
    storage_migration_required: bool = False
    reencrypt_required: bool = False
    affected_source_artifacts: list[str] = field(default_factory=list)
    affected_derived_artifacts: list[str] = field(default_factory=list)
    steps_to_rerun: list[str] = field(default_factory=list)
    steps_to_skip: list[str] = field(default_factory=list)
    requires_human_approval: bool = False
    reason_codes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {**self.__dict__}


def _split_steps(rerun: set[str]) -> tuple[list[str], list[str]]:
    return sorted(rerun), sorted(t for t in ALL_DERIVED_TYPES if t not in rerun)


def plan_for_source_change(old_graph: dict, new_graph: dict, prior_artifacts: list[DerivedArtifact] | None = None) -> ReprocessPlan:
    from scripts.pipeline_runtime.source_graph import diff_source_graph
    d = diff_source_graph(old_graph, new_graph)
    changed_ids = d["changed"] + d["added"] + d["removed"]
    plan = ReprocessPlan("source_change")
    if not changed_ids:
        plan.reason_codes = ["no_source_change"]
        plan.steps_to_skip = list(ALL_DERIVED_TYPES)
        return plan
    seeds: set[str] = set()
    for aid in d["changed"] + d["added"]:
        art = new_graph.get(aid) or old_graph.get(aid)
        if art:
            seeds |= _seed_types_for_source(art.artifact_type, art.metadata_json.get("field", ""))
            plan.reason_codes.append(f"source_changed:{art.artifact_type}:{art.locator_json.get('field', aid)}")
    for aid in d["removed"]:
        art = old_graph.get(aid)
        if art:
            seeds |= _seed_types_for_source(art.artifact_type, art.metadata_json.get("field", ""))
    rerun = downstream_closure(seeds)
    plan.semantic_reprocess_required = bool(rerun)
    plan.affected_source_artifacts = sorted(set(changed_ids))
    plan.steps_to_rerun, plan.steps_to_skip = _split_steps(rerun)
    plan.affected_derived_artifacts = sorted(a.artifact_id for a in (prior_artifacts or []) if a.artifact_type in rerun)
    return plan


def plan_for_pipeline_change(old_spec: PipelineSpec, new_spec: PipelineSpec,
                             prior_artifacts: list[DerivedArtifact] | None = None) -> ReprocessPlan:
    plan = ReprocessPlan("pipeline_change")
    if pipeline_config_hash(old_spec) == pipeline_config_hash(new_spec):
        plan.reason_codes = ["no_pipeline_change"]
        plan.steps_to_skip = [s.step_id for s in new_spec.steps]
        return plan
    old_steps = {s.step_id: s for s in old_spec.steps}
    changed: set[str] = set()
    for s in new_spec.steps:
        o = old_steps.get(s.step_id)
        if (o is None or o.processor_ref != s.processor_ref
                or sorted(o.input_artifact_types) != sorted(s.input_artifact_types)
                or sorted(o.output_artifact_types) != sorted(s.output_artifact_types)
                or sorted(o.depends_on) != sorted(s.depends_on)):
            changed.add(s.step_id)
    changed |= (set(old_steps) - {s.step_id for s in new_spec.steps})  # removed steps
    if sorted(old_spec.gates) != sorted(new_spec.gates) or old_spec.artifact_policy != new_spec.artifact_policy:
        changed |= {s.step_id for s in new_spec.steps}  # manifest-level change → all steps affected
    # downstream dependents (steps whose depends_on reaches a changed step)
    rerun = set(changed)
    grew = True
    while grew:
        grew = False
        for s in new_spec.steps:
            if s.step_id not in rerun and any(dep in rerun for dep in s.depends_on):
                rerun.add(s.step_id); grew = True
    plan.semantic_reprocess_required = True
    plan.steps_to_rerun = sorted(rerun)
    plan.steps_to_skip = sorted(s.step_id for s in new_spec.steps if s.step_id not in rerun)
    plan.affected_derived_artifacts = sorted(a.artifact_id for a in (prior_artifacts or []))
    plan.reason_codes = [f"pipeline_config_changed:{old_spec.pipeline_version}->{new_spec.pipeline_version}",
                         f"config_hash:{pipeline_config_hash(old_spec)}->{pipeline_config_hash(new_spec)}"]
    plan.requires_human_approval = False  # versioned new run; old outputs preserved until it succeeds
    return plan


def plan_for_processor_change(processor_id: str, old_version: str, new_version: str,
                              prior_artifacts: list[DerivedArtifact] | None = None) -> ReprocessPlan:
    from scripts.pipeline_runtime.cfpb_artifacts import PRODUCER
    plan = ReprocessPlan("processor_change")
    if old_version == new_version:
        plan.reason_codes = ["no_processor_change"]
        plan.steps_to_skip = list(ALL_DERIVED_TYPES)
        return plan
    seeds = {t for t, p in PRODUCER.items() if p.processor_id == processor_id and t in DEPENDS_ON}
    rerun = downstream_closure(seeds)
    plan.semantic_reprocess_required = bool(rerun)
    plan.steps_to_rerun, plan.steps_to_skip = _split_steps(rerun)
    plan.affected_derived_artifacts = sorted(a.artifact_id for a in (prior_artifacts or [])
                                             if a.artifact_type in rerun)
    plan.reason_codes = [f"processor_version_changed:{processor_id}:{old_version}->{new_version}"]
    return plan


def plan_for_security_policy_change(old_policy: TenantPolicy, new_policy: TenantPolicy,
                                    prior_artifacts: list[DerivedArtifact] | None = None) -> ReprocessPlan:
    plan = ReprocessPlan("security_policy_change")
    prior = prior_artifacts or []
    if new_policy.kms_key_version != old_policy.kms_key_version:
        plan.reencrypt_required = True
        plan.reason_codes.append(f"kms_key_rotation:{old_policy.kms_key_version}->{new_policy.kms_key_version}")
    if new_policy.isolation_mode != old_policy.isolation_mode:
        plan.storage_migration_required = True
        plan.requires_human_approval = True
        plan.reason_codes.append(f"isolation_upgrade:{old_policy.isolation_mode}->{new_policy.isolation_mode}")
    if new_policy.data_residency != old_policy.data_residency:
        plan.storage_migration_required = True
        plan.requires_human_approval = True
        plan.reason_codes.append(f"residency_change:{old_policy.data_residency}->{new_policy.data_residency}")
    if new_policy.retention_policy_id != old_policy.retention_policy_id:
        plan.reason_codes.append(f"retention_change:{old_policy.retention_policy_id}->{new_policy.retention_policy_id}")
    # security/governance changes NEVER trigger a semantic reprocess (content_hash is unchanged)
    plan.semantic_reprocess_required = False
    if plan.reencrypt_required or plan.storage_migration_required:
        plan.affected_source_artifacts = []  # whole-tenant operation
        plan.affected_derived_artifacts = sorted(a.artifact_id for a in prior)
    if not plan.reason_codes:
        plan.reason_codes = ["no_security_change"]
    plan.steps_to_skip = list(ALL_DERIVED_TYPES)  # no semantic steps rerun
    return plan
