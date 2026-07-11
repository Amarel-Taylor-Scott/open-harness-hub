#!/usr/bin/env python3
"""scripts.runtime.builtin_processors — Processors that ADAPT existing logic to the contract layer.

Wrappers (not rewrites): source.cfpb_fixture@v1 emits source_record artifacts; decompose.cfpb_structured@v1
reuses scripts.ingest.decompose_structured to emit atomic_fact + narrative_allegation ArtifactEnvelopes
(preserving #field handles + governance: facts promotion_eligible=true, allegations false);
package.context_pack@v1 emits context_pack + receipt; vectorize/graph are deterministic stubs that emit
typed artifacts. None imports the admin server or a global bus — they use the RuntimeContext ports only.
"""
from __future__ import annotations

from scripts.ingest.decompose_structured import CLAIM_FACT, decompose_cfpb_complaint
from scripts.runtime.envelopes import ArtifactEnvelope, EventEnvelope, ProcessorResult, content_hash
from scripts.runtime.processor import Processor, ProcessorSpec

_SECURITY = {"classification": "demo_public", "kms_key_ref": "local://demo", "retention_policy_id": "demo"}


def _lineage(cmd) -> dict:
    return {"run_id": cmd.run_id, "pipeline_id": cmd.pipeline_id, "pipeline_version": cmd.pipeline_version,
            "processor_id": cmd.processor_id or "", "processor_version": cmd.processor_version or "",
            "processor_config_hash": content_hash({"p": cmd.processor_id, "v": cmd.processor_version})}


def _artifact(cmd, *, artifact_type, schema, key, payload, claim_status, promo, model_dep=False,
              human=False, source_ids=None, parents=None) -> ArtifactEnvelope:
    return ArtifactEnvelope(
        artifact_id=f"{cmd.run_id}:{artifact_type}:{key}", tenant_id=cmd.tenant_id, artifact_type=artifact_type,
        artifact_schema_version=schema, content_hash=content_hash({"t": artifact_type, "p": payload}),
        payload=payload, source_artifact_ids=list(source_ids or []), parent_artifact_ids=list(parents or []),
        lineage=_lineage(cmd),
        governance={"claim_status": claim_status, "promotion_eligible": promo, "model_dependent": model_dep,
                    "requires_human_review": human},
        security=dict(_SECURITY))


class CFPBFixtureSource(Processor):
    spec = ProcessorSpec("source.cfpb_fixture", "v1", output_artifact_types=["source_record"], side_effects=False)

    def handle(self, command, ctx):
        records = ctx.artifact_store.load_inputs(command)
        arts = [_artifact(command, artifact_type="source_record", schema="SourceRecord",
                          key=str(r.get("complaint_id") or i), payload={"source_id": str(r.get("complaint_id") or i), **r},
                          claim_status="source", promo=False) for i, r in enumerate(records)]
        return ProcessorResult.make_ok(run_id=command.run_id, step_id=command.step_id,
                                       processor_id=self.processor_id, processor_version=self.processor_version,
                                       artifacts=arts, metrics={"record_count": len(records), "artifact_count": len(arts)})


class CFPBStructuredDecomposer(Processor):
    spec = ProcessorSpec("decompose.cfpb_structured", "v1",
                         input_artifact_types=["source_record"],
                         output_artifact_types=["atomic_fact", "narrative_allegation"])

    def handle(self, command, ctx):
        records = ctx.artifact_store.load_inputs(command)
        arts, facts, alleg = [], 0, 0
        for rec in records:
            sid = str(rec.get("complaint_id") or rec.get("source_id") or "cfpb")
            for c in decompose_cfpb_complaint(rec, native_id=f"cfpb:{sid}")["components"]:
                if c["claim_status"] == CLAIM_FACT:
                    arts.append(_artifact(command, artifact_type="atomic_fact", schema="AtomicFact", key=c["fact_id"],
                                          payload={"text": c["text"], "field": c["field"], "value": c["value"],
                                                   "source_handle": c["source_handle"], "claim_status": "fact",
                                                   "promotion_eligible": True},
                                          claim_status="fact", promo=True, source_ids=[c["source_handle"]]))
                    facts += 1
                else:
                    arts.append(_artifact(command, artifact_type="narrative_allegation", schema="NarrativeAllegation",
                                          key=c["fact_id"],
                                          payload={"text": c["text"], "field": c["field"], "source_handle": c["source_handle"],
                                                   "claim_status": "unverified_allegation", "promotion_eligible": False},
                                          claim_status="unverified_allegation", promo=False, human=True,
                                          source_ids=[c["source_handle"]]))
                    alleg += 1
        ev = EventEnvelope(type="baltor.pipeline.step.completed", source="baltor.decompose.cfpb_structured",
                           subject=f"{command.run_id}/step/{command.step_id}", tenant_id=command.tenant_id,
                           run_id=command.run_id, causation_id=command.command_id,
                           data={"facts": facts, "allegations": alleg})
        return ProcessorResult.make_ok(run_id=command.run_id, step_id=command.step_id,
                                       processor_id=self.processor_id, processor_version=self.processor_version,
                                       artifacts=arts, events=[ev],
                                       metrics={"record_count": len(records), "atomic_fact": facts, "narrative_allegation": alleg})


class ContextPackBuilder(Processor):
    spec = ProcessorSpec("package.context_pack", "v1", input_artifact_types=["atomic_fact", "narrative_allegation"],
                         output_artifact_types=["context_pack", "receipt"])

    def handle(self, command, ctx):
        included = list(command.payload.get("included", []))
        held_out = list(command.payload.get("held_out", []))
        pack = _artifact(command, artifact_type="context_pack", schema="ContextPack", key="final",
                         payload={"included": included, "held_out": held_out}, claim_status="context_pack", promo=False)
        receipt = _artifact(command, artifact_type="receipt", schema="Receipt", key="final",
                            payload={"pack": pack.artifact_id, "served": len(included), "held_out": len(held_out)},
                            claim_status="receipt", promo=False, parents=[pack.artifact_id])
        return ProcessorResult.make_ok(run_id=command.run_id, step_id=command.step_id,
                                       processor_id=self.processor_id, processor_version=self.processor_version,
                                       artifacts=[pack, receipt], metrics={"served": len(included), "held_out": len(held_out)})


class DeterministicVectorizer(Processor):
    spec = ProcessorSpec("vectorize.deterministic_local", "v1", output_artifact_types=["embedding"])

    def handle(self, command, ctx):
        items = ctx.artifact_store.load_inputs(command)
        arts = [_artifact(command, artifact_type="embedding", schema="ArtifactEnvelope", key=str(i),
                          payload={"provider": "deterministic_local", "model": "hashed_lexical", "version": "v1", "dimensions": 64},
                          claim_status="embedding", promo=False, model_dep=True) for i in range(len(items))]
        return ProcessorResult.make_ok(run_id=command.run_id, step_id=command.step_id,
                                       processor_id=self.processor_id, processor_version=self.processor_version,
                                       artifacts=arts, metrics={"vectors": len(arts)})


class DeterministicGraphBuilder(Processor):
    spec = ProcessorSpec("graph.deterministic_edges", "v1", output_artifact_types=["artifact_edge"])

    def handle(self, command, ctx):
        ev = EventEnvelope(type="baltor.graph.edge.created", source="baltor.graph.deterministic_edges",
                           subject=f"{command.run_id}/graph", tenant_id=command.tenant_id, run_id=command.run_id,
                           data={"edges": int(command.payload.get("edge_count", 0))})
        return ProcessorResult.make_ok(run_id=command.run_id, step_id=command.step_id,
                                       processor_id=self.processor_id, processor_version=self.processor_version,
                                       events=[ev], metrics={"edges": int(command.payload.get("edge_count", 0))})


BUILTINS = [CFPBFixtureSource(), CFPBStructuredDecomposer(), ContextPackBuilder(),
            DeterministicVectorizer(), DeterministicGraphBuilder()]
