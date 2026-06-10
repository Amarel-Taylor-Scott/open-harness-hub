#!/usr/bin/env python3
"""scripts.pipeline_runtime.cfpb_artifacts — CFPB record → MULTI-GRAIN typed, governed, lineaged artifacts.

Extends (does not replace) the existing structured decomposition: one CFPB record now emits distinct,
separately-governed artifact types — sentence, atomic_fact, narrative_allegation, entity_mention,
emotion_signal (model_interpretation), conclusion (derived, must cite support), context_pack, receipt —
each carrying full lineage (source artifact ids + processor id/version + config hash + run id + tenant +
security) and governance pulled from the single-source artifact-type registry.

Hard governance (enforced here, asserted by the proof):
  * atomic_fact (structured field)  → promotion_eligible per registry (True)
  * narrative_allegation            → source-grounded but NOT promotion eligible
  * emotion_signal                  → model_interpretation, NOT promotion eligible, REQUIRES processor metadata
  * conclusion                      → derived, requires_human_review, MUST cite ≥1 source-grounded artifact

CLI: imported by check_cfpb_multi_grain_artifacts.py / the reprocess-scope proofs.
"""
from __future__ import annotations

from typing import Any, Mapping

from scripts.ingest.decompose_structured import CLAIM_FACT, _sentiment, decompose_cfpb_complaint
from scripts.pipeline_runtime import artifact_types as AT
from scripts.pipeline_runtime.source_graph import build_cfpb_source_graph, content_hash
from scripts.pipeline_runtime.versioning import DerivedArtifact, ProcessorSpec
from scripts.security.tenant_catalog import TenantPolicy, security_metadata

# the processor set behind CFPB multi-grain (deterministic locally; emotion is a model_interpretation seam)
DECOMPOSE = ProcessorSpec("decompose.structured", "v1", code_hash="dc-v1", deterministic=True, data_access="tenant")
ENTITY = ProcessorSpec("entity.rules", "v1", code_hash="ent-v1", deterministic=True, data_access="tenant")
EMOTION = ProcessorSpec("emotion.lexicon", "v1", code_hash="emo-v1", model_id="lexicon", model_version="1",
                        params_hash="lex-1", deterministic=True, data_access="tenant")  # model_interpretation
CONCLUDE = ProcessorSpec("conclude.deterministic", "v1", code_hash="cc-v1", deterministic=True, data_access="tenant")
PACKAGE = ProcessorSpec("package.context_pack", "v1", code_hash="pk-v1", deterministic=True, data_access="tenant")
PROCESSORS = [DECOMPOSE, ENTITY, EMOTION, CONCLUDE, PACKAGE]

#: which processor produces which artifact type (the step that owns each grain → reprocess scoping)
PRODUCER: dict[str, ProcessorSpec] = {
    "sentence": DECOMPOSE, "atomic_fact": DECOMPOSE, "narrative_allegation": DECOMPOSE,
    "entity_mention": ENTITY, "emotion_signal": EMOTION, "conclusion": CONCLUDE,
    "context_pack": PACKAGE, "receipt": PACKAGE,
}


def _derived(*, artifact_type: str, key: str, tenant_id: str, run_id: str, pipeline_id: str,
             pipeline_version: str, proc: ProcessorSpec, source_ids: list[str], payload: dict,
             sec: dict, citations: list[str] | None = None, promotion_override: bool | None = None) -> DerivedArtifact:
    spec = AT.get(artifact_type)
    promo = spec.promotion_eligible_default if promotion_override is None else promotion_override
    return DerivedArtifact(
        artifact_id=f"{run_id}:{artifact_type}:{key}", tenant_id=tenant_id, artifact_type=artifact_type,
        run_id=run_id, content_hash=content_hash({"t": artifact_type, "k": key, "p": payload}),
        source_artifact_ids=list(source_ids), processor_id=proc.processor_id,
        processor_version=proc.processor_version, config_hash=proc.fingerprint(),
        pipeline_id=pipeline_id, pipeline_version=pipeline_version,
        claim_status=payload.get("claim_status", artifact_type), promotion_eligible=promo,
        citations=list(citations or []), payload_json=payload, security_json=sec)


def build_cfpb_artifacts(record: Mapping[str, Any], policy: TenantPolicy, *, run_id: str = "run-cfpb-multigrain",
                         pipeline_id: str = "cfpb_multigrain", pipeline_version: str = "v1") -> dict[str, Any]:
    """Emit the full multi-grain typed artifact set for one CFPB record, with lineage + governance."""
    source_graph = build_cfpb_source_graph(record, policy)
    source_id = next(iter(source_graph.values())).source_id
    decomp = decompose_cfpb_complaint(record, native_id=f"cfpb:{source_id}")
    sec = security_metadata(policy, classification="public", pii=True)
    arts: list[DerivedArtifact] = []

    # sentences (source-grounded grains, surfaced as typed artifacts from the source graph)
    sentence_ids: list[str] = []
    for a in source_graph.values():
        if a.artifact_type == "sentence":
            art = _derived(artifact_type="sentence", key=a.locator_json["handle"], tenant_id=policy.tenant_id,
                           run_id=run_id, pipeline_id=pipeline_id, pipeline_version=pipeline_version, proc=DECOMPOSE,
                           source_ids=[a.artifact_id], payload={"text": a.metadata_json.get("text", "")}, sec=sec)
            arts.append(art); sentence_ids.append(art.artifact_id)

    # atomic_fact (structured fields) + narrative_allegation (narrative sentences)
    fact_ids, alleg_ids = [], []
    for c in decomp["components"]:
        if c["claim_status"] == CLAIM_FACT:
            src = f"{source_id}:source_field:{c['field']}"
            art = _derived(artifact_type="atomic_fact", key=c["fact_id"], tenant_id=policy.tenant_id, run_id=run_id,
                           pipeline_id=pipeline_id, pipeline_version=pipeline_version, proc=DECOMPOSE,
                           source_ids=[src], payload={"text": c["text"], "claim_status": "fact"}, sec=sec)
            arts.append(art); fact_ids.append(art.artifact_id)
        else:  # unverified_allegation
            src = f"{source_id}:sentence:{c['field']}#s{c.get('sentence_index', 0)}"
            art = _derived(artifact_type="narrative_allegation", key=c["fact_id"], tenant_id=policy.tenant_id,
                           run_id=run_id, pipeline_id=pipeline_id, pipeline_version=pipeline_version, proc=DECOMPOSE,
                           source_ids=[src], payload={"text": c["text"], "claim_status": "unverified_allegation"}, sec=sec)
            arts.append(art); alleg_ids.append(art.artifact_id)

    # entity_mention (deterministic rule: company + product structured fields are entities)
    for fld in ("company", "product"):
        if record.get(fld):
            art = _derived(artifact_type="entity_mention", key=fld, tenant_id=policy.tenant_id, run_id=run_id,
                           pipeline_id=pipeline_id, pipeline_version=pipeline_version, proc=ENTITY,
                           source_ids=[f"{source_id}:source_field:{fld}"],
                           payload={"entity": record[fld], "kind": fld}, sec=sec)
            arts.append(art)

    # emotion_signal — model_interpretation over the narrative sentences (REQUIRES processor metadata)
    narrative = " ".join(record.get(f, "") for f in ("consumer_complaint_narrative", "narrative", "complaint_what_happened"))
    emotion = _derived(artifact_type="emotion_signal", key="narrative", tenant_id=policy.tenant_id, run_id=run_id,
                       pipeline_id=pipeline_id, pipeline_version=pipeline_version, proc=EMOTION,
                       source_ids=list(sentence_ids), payload={**_sentiment(narrative), "interpretation": True}, sec=sec)
    assert emotion.processor_ref and emotion.config_hash, "emotion_signal must carry processor metadata"
    arts.append(emotion)

    # conclusion — derived; MUST cite ≥1 source-grounded supporting artifact
    support = fact_ids + alleg_ids
    conclusion = _derived(artifact_type="conclusion", key="primary", tenant_id=policy.tenant_id, run_id=run_id,
                          pipeline_id=pipeline_id, pipeline_version=pipeline_version, proc=CONCLUDE,
                          source_ids=[], citations=support,
                          payload={"text": f"Complaint about {record.get('product','?')} against "
                                           f"{record.get('company','?')}: {len(fact_ids)} facts, "
                                           f"{len(alleg_ids)} allegations.", "claim_status": "derived"}, sec=sec)
    assert conclusion.citations, "conclusion must cite supporting artifacts"
    arts.append(conclusion)

    # context_pack + receipt (served, assembled)
    served = fact_ids + alleg_ids + [conclusion.artifact_id, emotion.artifact_id]
    pack = _derived(artifact_type="context_pack", key="primary", tenant_id=policy.tenant_id, run_id=run_id,
                    pipeline_id=pipeline_id, pipeline_version=pipeline_version, proc=PACKAGE,
                    source_ids=[], citations=served, payload={"served": len(served)}, sec=sec)
    arts.append(pack)
    receipt = _derived(artifact_type="receipt", key="primary", tenant_id=policy.tenant_id, run_id=run_id,
                       pipeline_id=pipeline_id, pipeline_version=pipeline_version, proc=PACKAGE,
                       source_ids=[], citations=[pack.artifact_id], payload={"pack": pack.artifact_id}, sec=sec)
    arts.append(receipt)

    by_type: dict[str, list[DerivedArtifact]] = {}
    for a in arts:
        by_type.setdefault(a.artifact_type, []).append(a)
    return {"source_graph": source_graph, "artifacts": arts, "by_type": by_type, "processors": PROCESSORS}
