#!/usr/bin/env python3
"""scripts.artifact_graph.cfpb_artifacts — CFPB records → the full set of decomposed, governed, lineaged
Artifact rows for the single-table ledger (reuses source_graph + decompose_structured; does NOT replace them).

Emits source_record · source_field · sentence · context_object · atomic_fact · narrative_allegation ·
entity_mention · emotion_signal · conclusion, plus a regulatory SEED (Reg E "10 business days" vs FAQ
"30 days") that creates the known authoritative-vs-summary contradiction the conflict detector finds.
context_pack + receipt are emitted by the orchestrator AFTER reconciliation (the final pack depends on it).

Governance is fixed at construction: atomic_fact from a structured field is promotion-eligible; narrative
allegations are not; emotion_signal is model_dependent + not promotable; conclusion cites support + is not
promotable until signed off. Every artifact carries content_hash + source_handles + full lineage.

CLI: imported by _repos/shared-backend-components/scripts/cfpb_artifact_graph_demo.py and the C32 proofs.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from scripts.artifact_graph.artifact_ledger import EPOCH, Artifact, chash
from scripts.ingest.decompose_structured import CLAIM_FACT, _sentiment, decompose_cfpb_complaint
from scripts.pipeline_runtime.source_graph import build_cfpb_source_graph
from scripts.security.tenant_catalog import TenantPolicy

PIPELINE_ID = "cfpb_artifact_graph"
PIPELINE_VERSION = "v1"
SCHEMA_VERSION = "v1"

# Source authority is no longer a static rank dict — it is EARNED from each source's provenance
# (publisher/domain + verified signature) via scripts/artifact_graph/source_authority against
# _repos/shared-backend-components/architecture/source_authority_registry.json, and recorded in the reconciliation receipt's
# authority_basis. To grant a source authority, add a publisher there — never hand-type a rank here.

PROC = {  # artifact_type → (processor_id, processor_version, model_dependent)
    "source_record": ("source.cfpb", "v1", False), "source_field": ("source.cfpb", "v1", False),
    "source_block": ("source.cfpb", "v1", False), "sentence": ("source.cfpb", "v1", False),
    "context_object": ("assemble.context_object", "v1", False),
    "atomic_fact": ("decompose.structured", "v1", False),
    "narrative_allegation": ("decompose.structured", "v1", False),
    "entity_mention": ("entity.rules", "v1", False), "emotion_signal": ("emotion.lexicon", "v1", True),
    "conclusion": ("conclude.deterministic", "v1", False), "context_pack": ("package.context_pack", "v1", False),
    "receipt": ("package.context_pack", "v1", False), "regulation_fact": ("regulation.seed", "v1", False),
}


def run_id_for(records: Sequence[Mapping[str, Any]], tenant_id: str) -> str:
    return "run-cfpb-graph-" + chash({"tenant": tenant_id, "records": list(records)}).split(":")[1][:12]


def _map_src_id(rid: str, src_aid: str) -> str:
    """source_graph id '{source_id}:{type}:{locator}' → C32 ledger id '{rid}:{type}:{source_id}:{locator}'."""
    p = src_aid.split(":")
    return f"{rid}:{p[1]}:{p[0]}:{':'.join(p[2:])}"


def _art(*, artifact_type: str, key: str, tenant_id: str, source_id: str, run_id: str, text: str,
         payload: dict, handles: list, claim_status: str, parent: str | None = None,
         promotion_eligible: bool = False, now: str = EPOCH, source_version: str = "v1") -> Artifact:
    pid, pver, md = PROC.get(artifact_type, ("unknown", "v1", False))
    aid = f"{run_id}:{artifact_type}:{key}"
    return Artifact(
        artifact_id=aid, tenant_id=tenant_id, source_id=source_id, source_version=source_version,
        artifact_type=artifact_type, schema_version=SCHEMA_VERSION, text=text,
        payload_json=payload, content_hash=chash({"t": artifact_type, "text": text, "p": payload}),
        parent_artifact_id=parent, source_handles_json=list(handles), pipeline_id=PIPELINE_ID,
        pipeline_version=PIPELINE_VERSION, processor_id=pid, processor_version=pver, run_id=run_id,
        claim_status=claim_status, promotion_eligible=promotion_eligible, model_dependent=md, created_at=now)


def build_artifacts(records: Sequence[Mapping[str, Any]], policy: TenantPolicy, *,
                    run_id: str | None = None, now: str = EPOCH) -> dict[str, Any]:
    tenant = policy.tenant_id
    rid = run_id or run_id_for(records, tenant)
    arts: list[Artifact] = []

    for rec in records:
        source_id = str(rec.get("complaint_id") or rec.get("id") or "cfpb")
        sg = build_cfpb_source_graph(rec, policy)
        for sa in sg.values():  # source_record / source_field / source_block / sentence
            parts = sa.artifact_id.split(":")  # "{source_id}:{type}:{locator}" → key "{source_id}:{locator}"
            arts.append(_art(artifact_type=sa.artifact_type, key=f"{parts[0]}:{':'.join(parts[2:])}",
                             tenant_id=tenant, source_id=source_id, run_id=rid,
                             text=str(sa.metadata_json.get("text") or sa.metadata_json.get("value") or ""),
                             payload=sa.metadata_json, handles=[sa.locator_json.get("handle", "")],
                             claim_status="source",
                             parent=_map_src_id(rid, sa.parent_artifact_id) if sa.parent_artifact_id else None, now=now))
        co_handle = f"ctx://cfpb/{source_id}"
        co = _art(artifact_type="context_object", key=source_id, tenant_id=tenant, source_id=source_id,
                  run_id=rid, text=f"CFPB complaint {source_id}", payload={"complaint_id": source_id},
                  handles=[co_handle], claim_status="context_object",
                  parent=_map_src_id(rid, f"{source_id}:source_record:root"), now=now)
        arts.append(co)

        decomp = decompose_cfpb_complaint(rec, native_id=f"cfpb:{source_id}")
        for c in decomp["components"]:
            if c["claim_status"] == CLAIM_FACT:
                arts.append(_art(artifact_type="atomic_fact", key=c["fact_id"], tenant_id=tenant,
                                 source_id=source_id, run_id=rid, text=c["text"],
                                 payload={"field": c["field"], "value": c["value"], "source": "complaint"},
                                 handles=[c["source_handle"]], claim_status="fact", parent=co.artifact_id,
                                 promotion_eligible=True, now=now))
            else:
                arts.append(_art(artifact_type="narrative_allegation", key=c["fact_id"], tenant_id=tenant,
                                 source_id=source_id, run_id=rid, text=c["text"],
                                 payload={"field": c["field"], "claim_status": "unverified_allegation"},
                                 handles=[c["source_handle"]], claim_status="unverified_allegation",
                                 parent=co.artifact_id, promotion_eligible=False, now=now))
        for fld in ("company", "product", "issue", "state"):
            if rec.get(fld):
                arts.append(_art(artifact_type="entity_mention", key=f"{source_id}:{fld}", tenant_id=tenant,
                                 source_id=source_id, run_id=rid, text=str(rec[fld]),
                                 payload={"entity": rec[fld], "kind": fld},
                                 handles=[f"{co_handle}#{fld}"], claim_status="entity", parent=co.artifact_id, now=now))
        narrative = " ".join(rec.get(f, "") for f in ("consumer_complaint_narrative", "narrative", "complaint_what_happened"))
        if narrative.strip():
            arts.append(_art(artifact_type="emotion_signal", key=source_id, tenant_id=tenant, source_id=source_id,
                             run_id=rid, text=f"sentiment={_sentiment(narrative)['direction']}",
                             payload={**_sentiment(narrative), "interpretation": True},
                             handles=[f"{co_handle}#narrative"], claim_status="model_interpretation",
                             parent=co.artifact_id, promotion_eligible=False, now=now))
        # deterministic conclusion citing the structured facts (support recorded as edges by graph_builder)
        arts.append(_art(artifact_type="conclusion", key=source_id, tenant_id=tenant, source_id=source_id,
                         run_id=rid, text=f"Complaint {source_id}: {rec.get('issue','?')} re {rec.get('product','?')} "
                                          f"against {rec.get('company','?')}.",
                         payload={"complaint_id": source_id, "claim_status": "derived_conclusion"},
                         handles=[co_handle], claim_status="derived_conclusion", parent=co.artifact_id,
                         promotion_eligible=False, now=now))

    # ── regulatory SEED: the known Reg E (10 business days) vs FAQ (30 days) contradiction ──
    # Authority is EARNED from provenance (scripts/artifact_graph/source_authority), not a fixture rank:
    # Reg E is the codified rule published at the eCFR (source-of-law, verified) → it OUTRANKS a vendor
    # FAQ summary published at an unlisted domain (earns no authority). Flip the publisher and the winner
    # flips — proven by check_source_authority. No `source_rank` typed on the artifact.
    rege = _art(artifact_type="atomic_fact", key="reg_e_deadline", tenant_id=tenant, source_id="reg-e",
                run_id=rid, text="Regulation E: error investigation deadline is 10 business days.",
                payload={"topic": "investigation_deadline", "value": 10, "unit": "business_days",
                         "source": "regulation", "authority": "Regulation E (12 CFR 1005.11)",
                         "publisher": "Electronic Code of Federal Regulations (GPO)",
                         "source_uri": "https://www.ecfr.gov/current/title-12/chapter-X/part-1005/section-1005.11",
                         "source_signed": True},
                handles=["ctx://reg-e/1005.11#deadline"], claim_status="fact", promotion_eligible=True,
                source_version="reg-e-2025", now=now)
    faq = _art(artifact_type="atomic_fact", key="faq_deadline", tenant_id=tenant, source_id="faq",
               run_id=rid, text="FAQ summary: investigation deadline is 30 days.",
               payload={"topic": "investigation_deadline", "value": 30, "unit": "days",
                        "source": "faq_summary", "authority": "Third-party compliance FAQ (vendor summary)",
                        "publisher": "Acme Compliance LLC (vendor summary)",
                        "source_uri": "https://acme-compliance.example.com/reg-e/faq#deadlines",
                        "source_signed": False},
               handles=["ctx://faq/deadlines#q3"], claim_status="fact", promotion_eligible=True,
               source_version="faq-2026", now=now)
    arts += [rege, faq]

    by_type: dict[str, list[Artifact]] = {}
    for a in arts:
        by_type.setdefault(a.artifact_type, []).append(a)
    return {"artifacts": arts, "by_type": by_type, "run_id": rid,
            "reg_e_id": rege.artifact_id, "faq_id": faq.artifact_id}


def build_context_pack_and_receipt(*, tenant_id: str, source_id: str, run_id: str, included_ids: list[str],
                                   held_out_ids: list[str], winning: dict, now: str = EPOCH) -> tuple[Artifact, Artifact]:
    """Built by the orchestrator AFTER reconciliation: the final pack includes only promotable/reconciled
    facts; held-out (lower-authority/unresolved) artifacts are recorded but excluded."""
    pack = _art(artifact_type="context_pack", key="final", tenant_id=tenant_id, source_id=source_id, run_id=run_id,
                text="CFPB reconciled context pack", claim_status="context_pack",
                payload={"included": included_ids, "held_out": held_out_ids, "winning": winning},
                handles=[f"ctx://pack/{run_id}"], now=now)
    receipt = _art(artifact_type="receipt", key="final", tenant_id=tenant_id, source_id=source_id, run_id=run_id,
                   text="receipt attesting the reconciled context pack", claim_status="receipt",
                   payload={"pack": pack.artifact_id, "included": len(included_ids), "held_out": len(held_out_ids),
                            "winning": winning}, handles=[f"ctx://receipt/{run_id}"], parent=pack.artifact_id, now=now)
    return pack, receipt
