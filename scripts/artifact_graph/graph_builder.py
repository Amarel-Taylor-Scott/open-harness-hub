#!/usr/bin/env python3
"""scripts.artifact_graph.graph_builder — DETERMINISTIC graph edges over the artifact ledger (rules first).

Edges are built from rules, not models: parent/child structure, source→fact/allegation derivation, entity
mentions, same-complaint/company/product/issue links, conclusion support, and (after reconciliation) pack
inclusion / hold-out / receipt attestation. Every edge_id is a deterministic hash of
(tenant_id, from, edge_type, to, run_id) and carries evidence_json — so the edge SET is byte-identical
across runs. NetworkX-style operations can project this table later; the edge TABLE stays the source of
truth (optionally projected into Neo4j / RDF). LLM-proposed edges are a SEPARATE edge_source ('llm'),
never written here.

CLI: imported by scripts/check_cfpb_deterministic_graph.py and the orchestrator.
"""
from __future__ import annotations

from itertools import combinations
from typing import Sequence

from scripts.artifact_graph.artifact_ledger import EPOCH, Edge, chash

PIPELINE_ID = "cfpb_artifact_graph"
PROC = "graph.deterministic"

DETERMINISTIC_EDGE_TYPES = (
    "CONTAINS", "HAS_FIELD", "HAS_SENTENCE", "YIELDS_FACT", "YIELDS_ALLEGATION", "MENTIONS",
    "SAME_COMPLAINT_AS", "SAME_COMPANY_AS", "SAME_PRODUCT_AS", "SAME_ISSUE_AS", "SUPPORTED_BY",
)
PACK_EDGE_TYPES = ("INCLUDED_IN_PACK", "HELD_OUT_FROM_PACK", "RECEIPT_ATTESTS")


def _edge(tenant: str, frm: str, etype: str, to: str, run_id: str, evidence: dict,
          *, edge_source: str = "deterministic", confidence: float = 1.0, now: str = EPOCH) -> Edge:
    eid = "edge:" + chash({"t": tenant, "f": frm, "e": etype, "to": to, "r": run_id}).split(":")[1][:16]
    return Edge(edge_id=eid, tenant_id=tenant, from_artifact_id=frm, to_artifact_id=to, edge_type=etype,
                edge_source=edge_source, confidence=confidence, evidence_json=evidence,
                pipeline_id=PIPELINE_ID, processor_id=PROC, run_id=run_id, created_at=now)


def build_edges(artifacts: Sequence, *, tenant_id: str, run_id: str, now: str = EPOCH) -> list[Edge]:
    by_id = {a.artifact_id: a for a in artifacts}
    by_type: dict[str, list] = {}
    for a in artifacts:
        by_type.setdefault(a.artifact_type, []).append(a)
    edges: dict[str, Edge] = {}

    def add(frm, etype, to, evidence):
        if frm in by_id and to in by_id and frm != to:
            e = _edge(tenant_id, frm, etype, to, run_id, evidence, now=now)
            edges[e.edge_id] = e

    # parent/child structure
    for a in artifacts:
        p = a.parent_artifact_id
        if not p or p not in by_id:
            continue
        ptype = by_id[p].artifact_type
        if a.artifact_type == "source_field" and ptype == "source_record":
            add(p, "HAS_FIELD", a.artifact_id, {"reason": "record has field"})
            add(p, "CONTAINS", a.artifact_id, {"reason": "record contains field"})
        elif a.artifact_type == "sentence":
            add(p, "HAS_SENTENCE", a.artifact_id, {"reason": "block has sentence"})
        else:
            add(p, "CONTAINS", a.artifact_id, {"reason": f"{ptype} contains {a.artifact_type}"})

    # source_field → atomic_fact / narrative_allegation
    for f in by_type.get("atomic_fact", []):
        fld = f.payload_json.get("field")
        if fld:
            sf = f"{run_id}:source_field:{f.source_id}:{fld}"
            add(sf, "YIELDS_FACT", f.artifact_id, {"field": fld})
    for al in by_type.get("narrative_allegation", []):
        fld = al.payload_json.get("field")
        if fld:
            sb = f"{run_id}:source_block:{al.source_id}:{fld}"
            sf = f"{run_id}:source_field:{al.source_id}:{fld}"
            add(sb if sb in by_id else sf, "YIELDS_ALLEGATION", al.artifact_id, {"field": fld})

    # entity mentions (text contains the entity value)
    ents = by_type.get("entity_mention", [])
    for claim in by_type.get("atomic_fact", []) + by_type.get("narrative_allegation", []):
        for e in ents:
            if e.source_id == claim.source_id and str(e.payload_json.get("entity", "")).lower() in (claim.text or "").lower():
                add(claim.artifact_id, "MENTIONS", e.artifact_id, {"entity": e.payload_json.get("entity")})

    # same-complaint + same-company/product/issue links among atomic facts
    facts = [f for f in by_type.get("atomic_fact", []) if f.source_id not in ("reg-e", "faq")]
    for a, b in combinations(sorted(facts, key=lambda x: x.artifact_id), 2):
        if a.source_id == b.source_id:
            add(a.artifact_id, "SAME_COMPLAINT_AS", b.artifact_id, {"complaint": a.source_id})
        for fld, etype in (("company", "SAME_COMPANY_AS"), ("product", "SAME_PRODUCT_AS"), ("issue", "SAME_ISSUE_AS")):
            if (a.payload_json.get("field") == fld and b.payload_json.get("field") == fld
                    and a.payload_json.get("value") == b.payload_json.get("value")):
                add(a.artifact_id, etype, b.artifact_id, {"field": fld, "value": a.payload_json.get("value")})

    # conclusion SUPPORTED_BY facts/allegations of the same complaint
    for co in by_type.get("conclusion", []):
        for claim in by_type.get("atomic_fact", []) + by_type.get("narrative_allegation", []):
            if claim.source_id == co.source_id:
                add(co.artifact_id, "SUPPORTED_BY", claim.artifact_id, {"complaint": co.source_id})

    return [edges[k] for k in sorted(edges)]


def build_pack_edges(*, tenant_id: str, run_id: str, pack_id: str, receipt_id: str,
                     included_ids: list[str], held_out_ids: list[str], now: str = EPOCH) -> list[Edge]:
    edges = []
    for aid in included_ids:
        edges.append(_edge(tenant_id, pack_id, "INCLUDED_IN_PACK", aid, run_id, {"reason": "promotable/reconciled"}, now=now))
    for aid in held_out_ids:
        edges.append(_edge(tenant_id, pack_id, "HELD_OUT_FROM_PACK", aid, run_id, {"reason": "held out (lower authority / unresolved)"}, now=now))
    edges.append(_edge(tenant_id, receipt_id, "RECEIPT_ATTESTS", pack_id, run_id, {"reason": "receipt attests pack"}, now=now))
    return sorted(edges, key=lambda e: e.edge_id)
