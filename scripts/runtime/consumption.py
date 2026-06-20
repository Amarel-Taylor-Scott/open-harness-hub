#!/usr/bin/env python3
"""scripts.runtime.consumption — the Consumption Runtime: the FORCING FUNCTION for the whole pipeline.

A consumer asks for context and receives a ``ContextResponse`` that contains ONLY verified + promoted +
consumable facts — each with source handles and full receipt lineage (verification + optimization +
consumption) — plus held-out items surfaced SEPARATELY as warnings. No unverified allegation, unresolved
conflict, stale fragile fact, cross-tenant private fact, or unpromoted optimization candidate may be served as
truth. No artifact is consumable merely because it exists.

`ConsumptionService` is domain-agnostic (pack + receipts → ContextResponse). `run_cfpb_to_consumption` is the
end-to-end orchestrator that walks the EXISTING engines — decompose → verify (C40) → optimize bake-off (C43) →
consumption-readiness → serve — proving every upstream section is wired. Deterministic + offline (time
injected; ids content-addressed). Reuses the runtime; introduces no second bus/store/gateway/optimizer.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from scripts.ingest.decompose_structured import CLAIM_FACT, decompose_cfpb_complaint
from scripts.runtime.optimization import (BaselineSnapshot, CandidateGenerator, ConsumptionReadinessGate,
                                          OptimizationHarness)
from scripts.runtime.verification_gate import VerificationGate

EPOCH = "1970-01-01T00:00:00Z"


def _hid(prefix: str, body: dict) -> str:
    return prefix + "-" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]


def _handles(a: dict) -> list:
    return a.get("source_handles") or ([a["source_handle"]] if a.get("source_handle") else [])


@dataclass
class ConsumptionReceipt:
    receipt_id: str
    response_id: str
    tenant_id: str
    decision: str                 # "served" | "refused"
    served_fact_count: int
    held_out_count: int
    verification_receipt_id: str
    optimization_receipt_id: str
    consumption_readiness_id: str
    reasons: list
    created_at: str
    schema_version: str = "ConsumptionReceipt.v1"

    def to_dict(self) -> dict:
        return {"schema_version": self.schema_version, "receipt_id": self.receipt_id, "response_id": self.response_id,
                "tenant_id": self.tenant_id, "decision": self.decision, "served_fact_count": self.served_fact_count,
                "held_out_count": self.held_out_count, "verification_receipt_id": self.verification_receipt_id,
                "optimization_receipt_id": self.optimization_receipt_id, "consumption_readiness_id": self.consumption_readiness_id,
                "reasons": list(self.reasons), "created_at": self.created_at}


@dataclass
class ContextResponse:
    response_id: str
    tenant_id: str
    answer: str
    served_facts: list
    held_out_warnings: list
    receipts: dict
    lineage: dict
    freshness: dict
    created_at: str
    run_id: str = ""
    pipeline_id: str = ""
    pipeline_version: str = ""
    source_snapshot_hash: str = ""
    conflicts: list = field(default_factory=list)
    reconciliations: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    schema_version: str = "ContextResponse.v1"

    def to_dict(self) -> dict:
        return {"schema_version": self.schema_version, "response_id": self.response_id, "tenant_id": self.tenant_id,
                "run_id": self.run_id, "pipeline_id": self.pipeline_id, "pipeline_version": self.pipeline_version,
                "source_snapshot_hash": self.source_snapshot_hash, "answer": self.answer,
                "served_facts": list(self.served_facts), "held_out_warnings": list(self.held_out_warnings),
                "conflicts": list(self.conflicts), "reconciliations": list(self.reconciliations),
                "receipts": dict(self.receipts), "freshness": dict(self.freshness), "lineage": dict(self.lineage),
                "warnings": list(self.warnings), "metrics": dict(self.metrics), "created_at": self.created_at}


class ConsumptionService:
    """Serve ONLY consumable packs. Builds a ContextResponse + writes a ConsumptionReceipt. Domain-agnostic."""

    def serve(self, *, tenant_id: str, promoted_pack: dict, verification_receipt: dict, optimization_receipt: dict,
              readiness_report, held_out: list, answer: str, conflicts=None, reconciliations=None,
              lineage=None, freshness=None, run_id: str = "", pipeline_id: str = "", pipeline_version: str = "",
              source_snapshot_hash: str = "", now: str = EPOCH) -> dict:
        rdy = readiness_report.to_dict() if hasattr(readiness_report, "to_dict") else dict(readiness_report)
        consumable = bool(rdy.get("consumable"))
        vr_id = verification_receipt.get("receipt_id", "")
        opt_id = optimization_receipt.get("receipt_id", "")
        rdy_id = rdy.get("report_id", "")
        reasons: list[str] = []

        served_facts: list[dict] = []
        if consumable:
            for a in promoted_pack.get("artifacts", []):
                # truth-only: never serve an allegation/derived non-fact; require a source handle
                if a.get("claim_type") == "narrative_allegation" or a.get("artifact_type") == "narrative_allegation":
                    continue
                hs = _handles(a)
                if not hs:
                    continue
                served_facts.append({"artifact_id": a.get("artifact_id"), "source_handle": hs[0],
                                     "claim_status": a.get("claim_status", "fact"), "content_hash": a.get("content_hash", ""),
                                     "subject": a.get("subject", ""), "predicate": a.get("predicate", ""),
                                     "object": str(a.get("object", "")),
                                     "verification_receipt_id": vr_id, "optimization_receipt_id": opt_id})
        else:
            reasons.append("pack failed ConsumptionReadinessGate: " +
                           ", ".join(c["name"] for c in rdy.get("checks", []) if not c.get("ok")))

        warnings_out = [{"artifact_id": h.get("artifact_id"), "reason": h.get("reason", "held out"),
                         "claim_status": h.get("claim_status", ""), "source_handle": (_handles(h)[0] if _handles(h) else "")}
                        for h in (held_out or [])]

        decision = "served" if (consumable and served_facts) else "refused"
        response_id = _hid("ctxresp", {"t": tenant_id, "pack": promoted_pack.get("pack_id", ""),
                                       "facts": sorted(f["artifact_id"] for f in served_facts), "ans": answer,
                                       "vr": vr_id, "opt": opt_id})
        cr_id = _hid("consrcpt", {"resp": response_id, "decision": decision,
                                  "n": len(served_facts), "h": len(warnings_out)})
        receipt = ConsumptionReceipt(receipt_id=cr_id, response_id=response_id, tenant_id=tenant_id, decision=decision,
                                     served_fact_count=len(served_facts), held_out_count=len(warnings_out),
                                     verification_receipt_id=vr_id, optimization_receipt_id=opt_id,
                                     consumption_readiness_id=rdy_id, reasons=reasons, created_at=now)
        lineage = dict(lineage or {})
        lineage.setdefault("artifact_ids", [a.get("artifact_id") for a in promoted_pack.get("artifacts", [])])
        lineage.setdefault("canonical_fact_ids", [f["artifact_id"] for f in served_facts])
        lineage.setdefault("context_pack_id", promoted_pack.get("pack_id", ""))
        lineage.setdefault("promotion_id", opt_id)
        freshness = dict(freshness or {"as_of": now, "stale_fact_count": 0, "fragile_fact_count": 0})
        response = ContextResponse(
            response_id=response_id, tenant_id=tenant_id, answer=(answer if decision == "served" else ""),
            served_facts=served_facts, held_out_warnings=warnings_out,
            receipts={"verification_receipt_id": vr_id, "optimization_receipt_id": opt_id,
                      "consumption_receipt_id": cr_id, "consumption_readiness_id": rdy_id},
            lineage=lineage, freshness=freshness, run_id=run_id, pipeline_id=pipeline_id,
            pipeline_version=pipeline_version, source_snapshot_hash=source_snapshot_hash,
            conflicts=list(conflicts or []), reconciliations=list(reconciliations or []),
            warnings=reasons, metrics={"served_fact_count": len(served_facts), "held_out_count": len(warnings_out)},
            created_at=now)
        return {"response": response, "receipt": receipt, "decision": decision}


# ── the end-to-end orchestrator: decompose → verify → optimize → consumption-readiness → serve ──
def _rege_pack(tenant_id: str) -> tuple:
    """Build the CFPB pack: real decomposed complaint facts/allegations + the reference Reg E (10) vs FAQ (30)
    regulatory conflict. Returns (pack, answer_fact_id, excluded_ids, source_artifact_ids)."""
    complaint = {"complaint_id": "BILL-782", "product": "Credit card", "issue": "Billing error",
                 "company": "Acme Bank", "consumer_complaint_narrative": "Charged twice for one purchase. No refund yet."}
    dec = decompose_cfpb_complaint(complaint, native_id="BILL-782")
    arts: list[dict] = []
    for c in dec["components"]:
        is_fact = c["claim_status"] == CLAIM_FACT
        arts.append({"artifact_id": c["fact_id"], "artifact_type": "atomic_fact" if is_fact else "narrative_allegation",
                     "claim_type": "atomic_fact" if is_fact else "narrative_allegation", "claim_status": c["claim_status"],
                     "subject": "Complaint BILL-782", "predicate": c.get("field", ""), "object": str(c.get("value", c.get("text", ""))),
                     "source_handle": c["source_handle"], "content_hash": _hid("h", {"sh": c["source_handle"], "v": c.get("value", c.get("text"))}),
                     "authority_rank": 2, "scope": "global_public", "tenant_id": tenant_id, "text": c.get("text", "")})
    rege = {"artifact_id": "fact-rege-10", "artifact_type": "atomic_fact", "claim_type": "atomic_fact", "claim_status": "fact",
            "subject": "Reg E error resolution", "predicate": "deadline_business_days", "object": "10", "unit": "business_days",
            "source_handle": "ctx://cfpb/reg-e/1005.11#error_resolution.deadline", "content_hash": "h-rege-10",
            "authority_rank": 3, "scope": "global_public", "tenant_id": tenant_id,
            "text": "Regulation E requires the institution to resolve billing errors within 10 business days."}
    faq = {"artifact_id": "fact-faq-30", "artifact_type": "atomic_fact", "claim_type": "atomic_fact", "claim_status": "fact",
           "subject": "Reg E error resolution", "predicate": "deadline_business_days", "object": "30",
           "source_handle": "ctx://cfpb/faq#error_resolution.deadline", "content_hash": "h-faq-30",
           "authority_rank": 1, "scope": "global_public", "tenant_id": tenant_id, "text": "An FAQ summary says 30 days."}
    arts = [rege, faq] + arts
    pack = {"pack_id": "pack-BILL-782", "tenant_id": tenant_id, "held_out": [], "artifacts": arts}
    return pack, "fact-rege-10", {"fact-faq-30"}, [dec["source_handle"], "ctx://cfpb/reg-e/1005.11", "ctx://cfpb/faq"]


def run_cfpb_to_consumption(tenant_id: str = "demo", *, require_optimized: bool = True, now: str = EPOCH) -> dict:
    pack, answer_fact_id, excluded_ids, source_ids = _rege_pack(tenant_id)

    # verification (C40): the answer fact must be gate-`allow`
    vgate = VerificationGate()
    answer_art = next(a for a in pack["artifacts"] if a["artifact_id"] == answer_fact_id)
    vr = vgate.evaluate(answer_art, context={"now": 1_000_000, "requested_scope": "global_public"}, now=now)["receipt"].to_dict()

    # optimization (C43): bake off candidate variants; promote the best non-regressing one
    snap = BaselineSnapshot.of(pack, answer_fact_ids=[answer_fact_id])
    cands = CandidateGenerator().generate(snap, excluded_ids=excluded_ids)
    bake = OptimizationHarness().optimize_many(pack, cands, answer_fact_ids=[answer_fact_id], now=now)
    best = bake["best"]
    if best is None:  # no safe improving candidate — refuse rather than serve unverified
        opt_receipt = {"decision": "reject", "receipt_id": ""}
        promoted_pack = pack
    else:
        opt_receipt = best["receipt"].to_dict()
        promoted_pack = best["candidate_pack"]

    # consumption readiness (C43.1): consumable only if verified + promoted + leak-free
    rdy = ConsumptionReadinessGate().assess(promoted_pack, verification_receipt=vr, optimization_receipt=opt_receipt,
                                            signals={"excluded_ids": excluded_ids}, now=now)

    # held-out warnings: the FAQ-30 conflict loser + every narrative allegation
    held_out = []
    for a in pack["artifacts"]:
        if a["artifact_id"] in excluded_ids:
            held_out.append({**a, "reason": "lower-authority conflict superseded by Reg E (10 business days)"})
        elif a.get("claim_type") == "narrative_allegation":
            held_out.append({**a, "reason": "narrative allegation — not certified as fact"})

    answer = f"{answer_art['object']} {answer_art.get('unit', 'business_days').replace('_', ' ')}"
    conflicts = [{"conflict_type": "deadline_mismatch", "artifacts": [answer_fact_id, "fact-faq-30"],
                  "winner": answer_fact_id, "held_out": "fact-faq-30"}]
    reconciliations = [{"decision": "resolved_by_authority", "winning_artifact_id": answer_fact_id,
                        "held_out_artifact_ids": ["fact-faq-30"], "reason": "Reg E (source-of-law) outranks FAQ summary"}]

    svc = ConsumptionService()
    out = svc.serve(tenant_id=tenant_id, promoted_pack=promoted_pack, verification_receipt=vr,
                    optimization_receipt=opt_receipt, readiness_report=rdy, held_out=held_out, answer=answer,
                    conflicts=conflicts, reconciliations=reconciliations,
                    lineage={"source_artifact_ids": source_ids}, run_id="run-BILL-782",
                    pipeline_id="cfpb_artifact_graph", pipeline_version="v1",
                    source_snapshot_hash=snap.snapshot_hash, now=now)
    return {"response": out["response"].to_dict(), "receipt": out["receipt"].to_dict(),
            "decision": out["decision"], "readiness": rdy.to_dict(),
            "receipts": {"verification": vr, "optimization": opt_receipt, "consumption": out["receipt"].to_dict()},
            "promoted_count": bake["promoted_count"], "candidate_count": bake["candidate_count"]}
