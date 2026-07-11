#!/usr/bin/env python3
"""scripts.runtime.source_consumption — the GENERIC source→consumption orchestrator.

`run_cfpb_to_consumption` proved ONE domain (a hand-built CFPB pack) walks the whole motion. This module
generalizes that motion to ANY source TYPE: it routes a raw payload through the SourceAdapterPort
(`source_adapters.normalize`), assembles the normalized governed artifacts into a pack, and walks the SAME
existing engines — VerificationGate (C40, per artifact) → OptimizationHarness bake-off (C43) →
ConsumptionReadinessGate (C43.1) → ConsumptionService.serve — to a single ``ContextResponse`` OR an explicit
``non_consumable_reason``. It introduces NO second consumption service / optimizer / verifier / parser: it is
pure wiring over the seams that already exist.

The non-consumable boundary is honest: if a source's parser is a cataloged candidate (pdf/html) or the type is
unknown, ``normalize`` returns ``consumable: false`` and this function returns the stored raw source artifacts
plus a ``non_consumable_reason`` — NEVER a faked ContextResponse with served "facts". Structured official
fields become promotion-eligible atomic_facts; free-text becomes held-out narrative_allegations that ride along
as warnings and are never served as truth. Tenant-private sources stay tenant-scoped (no global leak).

Deterministic + offline: time is INJECTED (``now``); ids are content-addressed via the existing engines. No
clock, no RNG, stdlib only.
"""
from __future__ import annotations

import hashlib
import json

from scripts.ingest.source_adapters import normalize
from scripts.runtime.consumption import ConsumptionService
from scripts.runtime.optimization import (BaselineSnapshot, CandidateGenerator, ConsumptionReadinessGate,
                                          OptimizationHarness)
from scripts.runtime.verification_gate import VerificationGate

EPOCH = "1970-01-01T00:00:00Z"

#: source authority → an authority_rank used ONLY for deterministic in-pack ordering (the reconciler stays the
#: authority for cross-source conflicts; here it just stabilizes optimizer top-k / ordering).
_AUTHORITY_RANK = {"official": 3, "regulator": 3, "system_reference": 2, "customer_private": 1, "unknown": 0}

#: artifact types this orchestrator promotes into the consumable pack. source_record/source_field stay as
#: source/lineage artifacts only — they are NEVER assembled as servable facts.
_PACK_TYPES = ("atomic_fact", "narrative_allegation")


def _run_id(*, tenant_id: str, source_type: str, source_id: str, content_hash: str) -> str:
    body = {"t": tenant_id, "st": source_type, "sid": source_id, "ch": content_hash}
    return "srcrun-" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]


def _pack_id(*, tenant_id: str, source_id: str, content_hash: str) -> str:
    body = {"t": tenant_id, "sid": source_id, "ch": content_hash}
    return "srcpack-" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]


def _to_pack_artifact(a: dict, *, tenant_id: str, authority: str) -> dict:
    """Adapt a normalized governed artifact into the pack shape the gate/optimizer/consumption expect.

    Mirrors ``artifact_type`` into ``claim_type`` (the regression/consumption gates key off ``claim_type`` for
    held-out detection) and carries an ``authority_rank`` for deterministic ordering. Preserves source handle,
    content hash, scope, and tenant so isolation + lineage checks stay enforceable.
    """
    return {"artifact_id": a["artifact_id"], "artifact_type": a["artifact_type"],
            "claim_type": a["artifact_type"], "claim_status": a.get("claim_status", ""),
            "promotion_eligible": bool(a.get("promotion_eligible")),
            "subject": a.get("source_id", ""), "predicate": a["source_handle"].split("#")[-1],
            "object": str(a.get("value", a.get("text", ""))), "text": a.get("text", ""),
            "source_handle": a["source_handle"], "content_hash": a["content_hash"],
            "authority_rank": _AUTHORITY_RANK.get(authority, 0), "scope": a.get("scope", ""),
            "tenant_id": tenant_id}


def _summary(*, run_id, tenant_id, source_type, scope, parser_provider, source_artifact_count, atomic_fact_count,
             allegation_count, conflict_count, verification_status, optimization_status, consumption_status,
             served_fact_count, held_out_warning_count, non_consumable_reason) -> dict:
    return {"run_id": run_id, "tenant_id": tenant_id, "source_type": source_type, "source_scope": scope,
            "parser_provider": parser_provider, "source_artifact_count": source_artifact_count,
            "atomic_fact_count": atomic_fact_count, "allegation_count": allegation_count,
            "conflict_count": conflict_count, "verification_status": verification_status,
            "optimization_status": optimization_status, "consumption_status": consumption_status,
            "served_fact_count": served_fact_count, "held_out_warning_count": held_out_warning_count,
            "non_consumable_reason": non_consumable_reason}


def run_source_to_consumption(source_type: str, payload, *, tenant_id: str, source_id: str,
                              scope: str = "global_public", authority: str = "unknown",
                              require_optimized: bool = True, now: str = EPOCH) -> dict:
    """Route ONE source through normalize→verify→optimize→consumption-readiness→serve. Returns either a served
    ``ContextResponse`` (consumable) or a ``non_consumable_reason`` (candidate/unknown parser) — never both."""
    norm = normalize(source_type, payload, tenant_id=tenant_id, source_id=source_id, scope=scope, authority=authority)
    parser_provider = norm.get("parser_provider", "")
    source_artifacts = norm.get("source_artifacts", [])

    # ── honest non-consumable boundary: pdf/html/unknown parser → raw stored, no claim served, no fake response ──
    if not norm.get("consumable"):
        reason = norm.get("reason", "non_consumable")
        run_id = _run_id(tenant_id=tenant_id, source_type=source_type, source_id=source_id,
                         content_hash=norm.get("content_hash", reason))
        summary = _summary(run_id=run_id, tenant_id=tenant_id, source_type=source_type, scope=scope,
                           parser_provider=parser_provider, source_artifact_count=len(source_artifacts),
                           atomic_fact_count=0, allegation_count=0, conflict_count=0,
                           verification_status="skipped", optimization_status="skipped",
                           consumption_status="non_consumable", served_fact_count=0, held_out_warning_count=0,
                           non_consumable_reason=reason)
        return {"consumable": False, "non_consumable_reason": reason, "source_type": source_type,
                "parser_provider": parser_provider, "source_artifacts": source_artifacts,
                "response": None, "summary": summary}

    content_hash = norm.get("content_hash", "")
    run_id = _run_id(tenant_id=tenant_id, source_type=source_type, source_id=source_id, content_hash=content_hash)

    # ── assemble ONLY the atomic_fact / narrative_allegation artifacts into a pack (deterministic order) ──
    pack_arts = [_to_pack_artifact(a, tenant_id=tenant_id, authority=authority)
                 for a in norm.get("artifacts", []) if a.get("artifact_type") in _PACK_TYPES]
    pack_arts.sort(key=lambda a: a["artifact_id"])
    facts = [a for a in pack_arts if a["artifact_type"] == "atomic_fact"]
    allegations = [a for a in pack_arts if a["artifact_type"] == "narrative_allegation"]
    answer_fact_ids = [a["artifact_id"] for a in facts]
    excluded_ids = {a["artifact_id"] for a in allegations}
    pack = {"pack_id": _pack_id(tenant_id=tenant_id, source_id=source_id, content_hash=content_hash),
            "tenant_id": tenant_id, "held_out": [], "artifacts": pack_arts}

    # ── verification (C40): every fact must be gate-`allow` ──
    vgate = VerificationGate()
    vctx = {"now": 1_000_000, "requested_scope": scope}
    fact_receipts = [vgate.evaluate(a, context=vctx, now=now)["receipt"].to_dict() for a in facts]
    all_allowed = bool(fact_receipts) and all(r["decision"] == "allow" for r in fact_receipts)
    # HARDENING (red-team finding): the verification receipt that drives the consumption gate must reflect
    # EVERY fact, not just fact[0] — else a mixed pack (fact[0] allow, a later fact hold_out) could serve a
    # held-out fact (ConsumptionService serves all pack facts). If any fact is not allow → vr=hold_out → the
    # readiness gate refuses the whole pack, so no held-out fact is ever served.
    vr = ({"decision": "allow", "receipt_id": fact_receipts[0]["receipt_id"]} if all_allowed
          else {"decision": "hold_out", "receipt_id": (fact_receipts[0]["receipt_id"] if fact_receipts else "")})
    verification_status = "allow" if all_allowed else ("hold_out" if facts else "no_facts")

    # ── optimization (C43): bake off candidate variants against the source pack; promote the best ──
    snap = BaselineSnapshot.of(pack, answer_fact_ids=answer_fact_ids)
    cands = CandidateGenerator().generate(snap, excluded_ids=excluded_ids)
    bake = OptimizationHarness().optimize_many(pack, cands, answer_fact_ids=answer_fact_ids, now=now)
    best = bake["best"]
    if best is None:
        opt_receipt = {"decision": "reject", "receipt_id": ""}
        promoted_pack = pack
    else:
        opt_receipt = best["receipt"].to_dict()
        promoted_pack = best["candidate_pack"]
    optimization_status = opt_receipt["decision"]

    # require_optimized: a served pack must have been PROMOTED by the harness, not passed through raw
    pack_for_readiness = promoted_pack if (best is not None or not require_optimized) else pack

    # ── consumption readiness (C43.1): consumable only if verified + promoted + leak-free ──
    rdy = ConsumptionReadinessGate().assess(pack_for_readiness, verification_receipt=vr,
                                            optimization_receipt=opt_receipt,
                                            signals={"excluded_ids": excluded_ids}, now=now)

    # ── held-out: every narrative allegation surfaced SEPARATELY as a warning, never as fact ──
    held_out = [{**a, "reason": "narrative allegation — not certified as fact"} for a in allegations]

    # ── serve (the existing ConsumptionService — NOT a second one) ──
    answer = (f"{len(facts)} verified fact(s) from {source_type} source {source_id}" if facts
              else f"no verifiable facts in {source_type} source {source_id}")
    svc = ConsumptionService()
    out = svc.serve(tenant_id=tenant_id, promoted_pack=pack_for_readiness, verification_receipt=vr,
                    optimization_receipt=opt_receipt, readiness_report=rdy, held_out=held_out, answer=answer,
                    lineage={"source_artifact_ids": [s["artifact_id"] for s in source_artifacts]},
                    run_id=run_id, pipeline_id=f"source:{source_type}", pipeline_version="v1",
                    source_snapshot_hash=snap.snapshot_hash, now=now)
    response = out["response"].to_dict()
    consumption_status = out["decision"]  # "served" | "refused"
    non_consumable_reason = ("" if consumption_status == "served"
                             else "; ".join(response.get("warnings", [])) or "pack not consumable after readiness gate")

    summary = _summary(run_id=run_id, tenant_id=tenant_id, source_type=source_type, scope=scope,
                       parser_provider=parser_provider, source_artifact_count=len(source_artifacts),
                       atomic_fact_count=len(facts), allegation_count=len(allegations), conflict_count=0,
                       verification_status=verification_status, optimization_status=optimization_status,
                       consumption_status=consumption_status,
                       served_fact_count=len(response.get("served_facts", [])),
                       held_out_warning_count=len(response.get("held_out_warnings", [])),
                       non_consumable_reason=non_consumable_reason)
    return {"consumable": True, "non_consumable_reason": non_consumable_reason, "source_type": source_type,
            "parser_provider": parser_provider, "source_artifacts": source_artifacts,
            "response": response, "receipt": out["receipt"].to_dict(), "readiness": rdy.to_dict(),
            "decision": consumption_status, "promoted_count": bake["promoted_count"],
            "candidate_count": bake["candidate_count"], "summary": summary}
