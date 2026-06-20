#!/usr/bin/env python3
"""scripts.artifact_graph.conflict_detector — DETERMINISTIC conflict detectors over the artifact ledger.

Rules you can prove, no model in the loop:
  * deadline/numeric mismatch — same topic, incompatible value (Reg E "10 business_days" vs FAQ "30 days")
  * field-value mismatch       — same complaint_id + same field + different CURRENT value
  * source-handle divergence   — same source_handle, different content_hash
  * governance violation       — a PROMOTABLE artifact SUPPORTED_BY an unverified narrative_allegation

Each conflict cites BOTH artifacts + evidence and starts ``status='open'``. (Semantic conflicts are a
separate LLM-assisted layer that only PROPOSES candidates — never written here as truth.)

CLI: imported by scripts/check_cfpb_conflict_detection.py and the orchestrator.
"""
from __future__ import annotations

from itertools import combinations
from typing import Sequence

from scripts.artifact_graph.artifact_ledger import EPOCH, Conflict, chash


def _cid(a: str, b: str, ctype: str) -> str:
    lo, hi = sorted((a, b))
    return "conflict:" + chash({"a": lo, "b": hi, "t": ctype}).split(":")[1][:16]


def _conflict(tenant: str, a: str, b: str, ctype: str, detector: str, severity: str, evidence: dict,
              *, now: str = EPOCH) -> Conflict:
    return Conflict(conflict_id=_cid(a, b, ctype), tenant_id=tenant, artifact_a_id=a, artifact_b_id=b,
                    conflict_type=ctype, detector=detector, severity=severity, evidence_json=evidence,
                    status="open", created_at=now)


def detect(artifacts: Sequence, edges: Sequence = (), *, tenant_id: str, now: str = EPOCH) -> list[Conflict]:
    by_id = {a.artifact_id: a for a in artifacts}
    by_type: dict[str, list] = {}
    for a in artifacts:
        by_type.setdefault(a.artifact_type, []).append(a)
    out: dict[str, Conflict] = {}

    def add(c: Conflict):
        out[c.conflict_id] = c

    facts = [f for f in by_type.get("atomic_fact", []) if not f.superseded_by]

    # 1) deadline/numeric mismatch on the same topic
    topics: dict[str, list] = {}
    for f in facts:
        t = f.payload_json.get("topic")
        if t:
            topics.setdefault(t, []).append(f)
    for topic, fs in topics.items():
        for a, b in combinations(sorted(fs, key=lambda x: x.artifact_id), 2):
            va, vb = a.payload_json.get("value"), b.payload_json.get("value")
            ua, ub = a.payload_json.get("unit"), b.payload_json.get("unit")
            if (va, ua) != (vb, ub):
                add(_conflict(tenant_id, a.artifact_id, b.artifact_id, "deadline_mismatch", "numeric_deadline", "high",
                              {"topic": topic, "a": {"value": va, "unit": ua, "authority": a.payload_json.get("authority")},
                               "b": {"value": vb, "unit": ub, "authority": b.payload_json.get("authority")}}, now=now))

    # 2) same complaint_id + same field + different current value
    bykey: dict[tuple, list] = {}
    for f in facts:
        fld = f.payload_json.get("field")
        if fld:
            bykey.setdefault((f.source_id, fld), []).append(f)
    for (sid, fld), fs in bykey.items():
        for a, b in combinations(sorted(fs, key=lambda x: x.artifact_id), 2):
            if a.payload_json.get("value") != b.payload_json.get("value"):
                add(_conflict(tenant_id, a.artifact_id, b.artifact_id, "field_value_mismatch", "field_value", "high",
                              {"complaint": sid, "field": fld}, now=now))

    # 3) same source_handle + SAME artifact_type, different content_hash → a genuine divergent version.
    #    (A derived artifact and its source legitimately share a handle with different content — that is
    #    lineage, NOT a conflict — so we only compare artifacts of the SAME type.)
    byhandle: dict[tuple, list] = {}
    for a in artifacts:
        for h in a.source_handles_json:
            byhandle.setdefault((h, a.artifact_type), []).append(a)
    for (h, _atype), group in byhandle.items():
        for a, b in combinations(sorted(group, key=lambda x: x.artifact_id), 2):
            if a.content_hash != b.content_hash:
                add(_conflict(tenant_id, a.artifact_id, b.artifact_id, "source_handle_divergence", "source_handle", "medium",
                              {"source_handle": h, "artifact_type": a.artifact_type}, now=now))

    # 4) governance: a PROMOTABLE artifact supported by an unverified allegation
    for e in edges:
        if e.edge_type == "SUPPORTED_BY":
            frm, to = by_id.get(e.from_artifact_id), by_id.get(e.to_artifact_id)
            if frm and to and frm.promotion_eligible and to.artifact_type == "narrative_allegation":
                add(_conflict(tenant_id, frm.artifact_id, to.artifact_id, "promoted_depends_on_unverified", "governance", "high",
                              {"reason": "promotable artifact depends on an unverified allegation"}, now=now))

    return [out[k] for k in sorted(out)]
