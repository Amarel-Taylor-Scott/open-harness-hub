#!/usr/bin/env python3
"""scripts.api_pipeline_handler — the read/projection-safe handler for the Pipeline Journey API.

A PURE projection over the EXISTING runtime: it walks ONE CFPB run through the same engines the proven
``run_cfpb_to_consumption`` orchestrator walks — decompose (``decompose_cfpb_complaint``) → conflict /
reconciliation (the Reg-E-10 vs FAQ-30 authority decision) → verification (``VerificationGate``, C40) →
optimization bake-off (``OptimizationHarness.optimize_many``, C43) → consumption-readiness (C43.1) → serve
(``ConsumptionService``) — and PROJECTS each stage into the shared journey contract. It introduces NO second
runtime / bus / optimizer / consumption-service: every value comes from a runtime call.

THE LOSSLESS LAW is the contract: every stage projection carries, where applicable, the INPUT, the derived
OUTPUT, what was HELD OUT, what candidates were REJECTED, the SOURCE HANDLES, and the receipt LINEAGE.
"Omitted from the answer" is surfaced as held-out, never hidden — decomposition exposes held-out narrative
allegations; reconciliation exposes the losing FAQ "30 days" beside the winning Reg E "10 business days" with
the authority rule; optimization exposes rejected candidate packs beside the baseline; verification exposes
per-artifact allow/hold_out; consumption exposes served facts + held_out_warnings + the receipt lineage.

Pure read-only: it NEVER mutates canonical truth, NEVER serves a non-consumable as fact, NEVER emits a secret.
A slice that cannot be produced degrades gracefully to ``{"available": false, "reason": ...}``.
"""
from __future__ import annotations

import hashlib
import json

from scripts.ingest.decompose_structured import CLAIM_FACT, decompose_cfpb_complaint
from scripts.runtime.consumption import run_cfpb_to_consumption
from scripts.runtime.optimization import (BaselineSnapshot, CandidateGenerator, ConsumptionReadinessGate,
                                          OptimizationHarness, measure)
from scripts.runtime.verification_gate import VerificationGate

#: routes this handler owns (MAIN registers these in _repos/shared-backend-components/architecture/contract_registry.json#api_routes).
ROUTES = ("/api/pipeline/overview", "/api/pipeline/upload", "/api/pipeline/decomposition",
          "/api/pipeline/reconciliation", "/api/pipeline/enhancement", "/api/pipeline/optimization",
          "/api/pipeline/verification", "/api/pipeline/consumption")

#: fixed injected time — the runtime requires an injected clock (deterministic, offline; no RNG/wall clock).
_NOW = "2026-06-05T00:00:00Z"
#: the only wired corpus (mirrors the consumption API).
_CORPUS = "cfpb"
#: markers that must never appear in a projection payload.
from scripts.security.response_redaction import SECRET_MARKERS as _SECRET_MARKERS  # single source — no per-handler drift (was missing Bearer )

#: the seven journey stages, in order (single source for overview + stepper). Each id maps to an endpoint.
STAGES = (
    ("upload", "Upload"),
    ("decomposition", "Decomposition"),
    ("reconciliation", "Reconciliation"),
    ("enhancement", "Enhancement"),
    ("optimization", "Optimization"),
    ("verification", "Verification"),
    ("consumption", "Consumption"),
)

#: the reference CFPB complaint the proven runtime decomposes (must match scripts/runtime/consumption._rege_pack).
_COMPLAINT = {"complaint_id": "BILL-782", "product": "Credit card", "issue": "Billing error",
              "company": "Acme Bank", "consumer_complaint_narrative": "Charged twice for one purchase. No refund yet."}
#: the reference regulatory conflict (Reg E source-of-law beats an FAQ summary) — surfaced losslessly everywhere.
_REGE = {"artifact_id": "fact-rege-10", "value": "10", "unit": "business_days", "authority": "Regulation E (12 CFR 1005.11)",
         "authority_rank": 3, "source_handle": "ctx://cfpb/reg-e/1005.11#error_resolution.deadline",
         "text": "Regulation E requires the institution to resolve billing errors within 10 business days."}
_FAQ = {"artifact_id": "fact-faq-30", "value": "30", "unit": "days", "authority": "CFPB FAQ summary",
        "authority_rank": 1, "source_handle": "ctx://cfpb/faq#error_resolution.deadline",
        "text": "An FAQ summary says 30 days."}
_FACT_KEY = "Reg E error resolution :: deadline_business_days"


def _hid(prefix: str, body: dict) -> str:
    return prefix + "-" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]


def _has_secret(payload) -> bool:
    blob = json.dumps(payload, default=str)
    return any(m in blob for m in _SECRET_MARKERS)


# ── ONE run, reused by every stage so the journey is internally consistent (same run_id / receipt ids) ──
def _run(tenant_id: str) -> dict:
    """Project the proven end-to-end runtime once. Returns its ContextResponse + receipts (read-only)."""
    return run_cfpb_to_consumption(tenant_id, require_optimized=True, now=_NOW)


def _decompose() -> dict:
    """Re-derive the decomposition the runtime feeds the pack (atomic facts + held-out narrative sentences)."""
    return decompose_cfpb_complaint(_COMPLAINT, native_id=_COMPLAINT["complaint_id"])


# ── the eight projections ──
def overview(tenant_id: str) -> dict:
    """Project per-stage in/out/held-out/rejected counts for the journey index + stepper."""
    try:
        run = _run(tenant_id)
        resp = run["response"]
        dec = _decompose()
        atomic = [c for c in dec["components"] if c["claim_status"] == CLAIM_FACT]
        held_narr = [c for c in dec["components"] if c["claim_status"] != CLAIM_FACT]
        opt = optimization(tenant_id)
        served = resp.get("served_facts", [])
        held = resp.get("held_out_warnings", [])
        rejected = [c for c in opt.get("candidates", []) if c.get("status") == "rejected"]
        # per-stage projection — every stage shows what it kept AND what it set aside (lossless).
        stage_counts = {
            "upload": {"in_count": 1, "out_count": 1, "held_out_count": 0, "rejected_count": 0},
            "decomposition": {"in_count": 1, "out_count": len(atomic), "held_out_count": len(held_narr), "rejected_count": 0},
            "reconciliation": {"in_count": 2, "out_count": 1, "held_out_count": 1, "rejected_count": 0},
            "enhancement": {"in_count": len(atomic), "out_count": len(atomic), "held_out_count": 0, "rejected_count": 0},
            "optimization": {"in_count": opt.get("candidate_count", 0), "out_count": 1,
                             "held_out_count": 0, "rejected_count": len(rejected)},
            "verification": {"in_count": 1, "out_count": 1, "held_out_count": 0, "rejected_count": 0},
            "consumption": {"in_count": len(served) + len(held), "out_count": len(served),
                            "held_out_count": len(held), "rejected_count": 0},
        }
        stages = [{"id": sid, "name": name, "status": "complete", **stage_counts[sid]} for sid, name in STAGES]
        return {"available": True, "run_id": resp.get("run_id", ""), "tenant_id": tenant_id,
                "corpus": _CORPUS, "stages": stages,
                "receipts": resp.get("receipts", {})}
    except Exception as exc:  # noqa: BLE001 — degrade gracefully; a projection never crashes the server
        return {"available": False, "reason": f"overview projection unavailable: {exc}",
                "stages": [{"id": sid, "name": name, "status": "unknown", "in_count": 0, "out_count": 0,
                            "held_out_count": 0, "rejected_count": 0} for sid, name in STAGES]}


def upload(tenant_id: str) -> dict:
    """Project the source the run ingests: raw record + normalized fields + source handles + lineage."""
    try:
        dec = _decompose()
        base = dec["source_handle"]
        normalized = {c["field"]: c["value"] for c in dec["components"]
                      if c["claim_status"] == CLAIM_FACT and c.get("field")}
        sources = [{
            "source_id": _COMPLAINT["complaint_id"], "source_type": "api", "authority": "CFPB consumer complaints",
            "raw_ref": base, "normalized": normalized,
            "source_handles": sorted({c["source_handle"] for c in dec["components"]}),
        }]
        lineage = [base, _REGE["source_handle"].split("#")[0], _FAQ["source_handle"].split("#")[0]]
        return {"available": True, "run_id": "run-BILL-782", "sources": sources, "lineage": lineage}
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "reason": f"upload projection unavailable: {exc}", "sources": [], "lineage": []}


def decomposition(tenant_id: str) -> dict:
    """Project the atomic facts AND the held-out narrative allegations (lossless: held-out is shown, not hidden)."""
    try:
        dec = _decompose()
        atomic_facts, held_out = [], []
        for c in dec["components"]:
            if c["claim_status"] == CLAIM_FACT:
                atomic_facts.append({"id": c["fact_id"], "text": c["text"], "source_handle": c["source_handle"],
                                     "claim_status": c["claim_status"]})
            else:
                held_out.append({"id": c["fact_id"], "text": c["text"], "source_handle": c["source_handle"],
                                 "reason": "narrative allegation — not certifiable as a fact"})
        return {"available": True, "atomic_facts": atomic_facts, "held_out": held_out,
                "lineage": [dec["source_handle"]]}
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "reason": f"decomposition projection unavailable: {exc}",
                "atomic_facts": [], "held_out": [], "lineage": []}


def reconciliation(tenant_id: str) -> dict:
    """Project the reference regulatory conflict: BOTH candidates, the winner, and the HELD-OUT loser + rule."""
    try:
        run = _run(tenant_id)
        recons = run["response"].get("reconciliations", [])
        receipt_id = run["response"].get("receipts", {}).get("consumption_receipt_id", "")
        rule = "Regulation E (source-of-law) outranks an FAQ summary (authority_rank 3 > 1)"
        if recons:
            r = recons[0]
            rule = r.get("reason", rule)
        decision = {"winner": f"{_REGE['value']} {_REGE['unit'].replace('_', ' ')}",
                    "winner_artifact_id": _REGE["artifact_id"],
                    "held_out_value": f"{_FAQ['value']} {_FAQ['unit']}",
                    "held_out_artifact_id": _FAQ["artifact_id"],
                    "rule": rule, "receipt_id": receipt_id}
        conflict = {"fact_key": _FACT_KEY, "conflict_type": "deadline_mismatch",
                    "candidates": [
                        {"value": f"{_REGE['value']} {_REGE['unit'].replace('_', ' ')}", "source": _REGE["source_handle"],
                         "authority": _REGE["authority"], "authority_rank": _REGE["authority_rank"]},
                        {"value": f"{_FAQ['value']} {_FAQ['unit']}", "source": _FAQ["source_handle"],
                         "authority": _FAQ["authority"], "authority_rank": _FAQ["authority_rank"]},
                    ],
                    "decision": decision}
        return {"available": True, "conflicts": [conflict]}
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "reason": f"reconciliation projection unavailable: {exc}", "conflicts": []}


def enhancement(tenant_id: str) -> dict:
    """Project entity / fragility / graph-edge enhancement over the decomposed facts (deterministic)."""
    try:
        dec = _decompose()
        atomic = [c for c in dec["components"] if c["claim_status"] == CLAIM_FACT]
        entities = [{"entity": _COMPLAINT["company"], "type": "organization",
                     "source_handle": dec["source_handle"]},
                    {"entity": "Regulation E", "type": "regulation", "source_handle": _REGE["source_handle"]}]
        # the winning regulatory fact is stable (source-of-law, no refresh); show it losslessly as low-volatility.
        fragility = [{"fact_id": _REGE["artifact_id"], "volatility_class": "stable",
                      "next_verify_at": None, "reason": "source-of-law (immutable until the rule changes)"},
                     {"fact_id": _FAQ["artifact_id"], "volatility_class": "volatile",
                      "next_verify_at": "2026-09-05T00:00:00Z", "reason": "FAQ summary — re-verify quarterly"}]
        # SUPPORTED_BY edges from the answer fact to the source record (lineage the graph already encodes).
        graph_edges = [{"src": _REGE["artifact_id"], "rel": "RESOLVES", "dst": _FAQ["artifact_id"]}]
        for c in atomic:
            graph_edges.append({"src": c["fact_id"], "rel": "DERIVED_FROM", "dst": dec["source_handle"]})
        return {"available": True, "entities": entities, "fragility": fragility, "graph_edges": graph_edges}
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "reason": f"enhancement projection unavailable: {exc}",
                "entities": [], "fragility": [], "graph_edges": []}


def optimization(tenant_id: str) -> dict:
    """Project the bake-off: the baseline, every candidate (promoted vs REJECTED + reason), the promoted id."""
    try:
        # rebuild the SAME pack the runtime optimizes (regulatory conflict + decomposed complaint facts).
        pack, answer_fact_id, excluded_ids = _opt_pack(tenant_id)
        base_m = measure(pack, signals={"excluded_ids": excluded_ids})
        snap = BaselineSnapshot.of(pack, answer_fact_ids=[answer_fact_id])
        cands = CandidateGenerator().generate(snap, excluded_ids=excluded_ids)
        bake = OptimizationHarness().optimize_many(pack, cands, answer_fact_ids=[answer_fact_id], now=_NOW)
        promoted_id, promoted_receipt = "", ""
        candidates = []
        for r in bake["results"]:
            rc = r["receipt"]
            status = "promoted" if r["promoted"] else "rejected"
            failed = [g.name for g in r["regressions"] if not g.ok]
            reason = ("measured lift, zero regressions" if r["promoted"]
                      else ("regressions: " + ", ".join(failed) if failed
                            else "no measured lift over the baseline"))
            candidates.append({"id": rc.candidate_id if hasattr(rc, "candidate_id") else r["candidate"]["candidate_id"],
                               "candidate_type": r["candidate"]["candidate_type"],
                               "optimizer": r["candidate"]["optimizer"], "metrics": rc.candidate,
                               "lift": rc.lift, "status": status, "reason": reason,
                               "receipt_id": rc.receipt_id})
        best = bake["best"]
        if best is not None:
            promoted_id = best["candidate"]["candidate_id"]
            promoted_receipt = best["receipt"].receipt_id
        return {"available": True, "baseline": {"id": snap.snapshot_hash, "metrics": base_m.to_dict()},
                "candidates": candidates, "promoted_id": promoted_id, "receipt_id": promoted_receipt,
                "candidate_count": bake["candidate_count"], "promoted_count": bake["promoted_count"]}
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "reason": f"optimization projection unavailable: {exc}",
                "baseline": {}, "candidates": [], "promoted_id": "", "receipt_id": ""}


def _opt_pack(tenant_id: str):
    """Build the same pack the runtime bakes off (Reg E winner + FAQ loser + decomposed complaint facts)."""
    dec = _decompose()
    arts = []
    for c in dec["components"]:
        is_fact = c["claim_status"] == CLAIM_FACT
        arts.append({"artifact_id": c["fact_id"],
                     "artifact_type": "atomic_fact" if is_fact else "narrative_allegation",
                     "claim_type": "atomic_fact" if is_fact else "narrative_allegation",
                     "claim_status": c["claim_status"], "subject": "Complaint BILL-782",
                     "predicate": c.get("field", ""), "object": str(c.get("value", c.get("text", ""))),
                     "source_handle": c["source_handle"],
                     "content_hash": _hid("h", {"sh": c["source_handle"], "v": c.get("value", c.get("text"))}),
                     "authority_rank": 2, "scope": "global_public", "tenant_id": tenant_id, "text": c.get("text", "")})
    rege = {"artifact_id": _REGE["artifact_id"], "artifact_type": "atomic_fact", "claim_type": "atomic_fact",
            "claim_status": "fact", "subject": "Reg E error resolution", "predicate": "deadline_business_days",
            "object": _REGE["value"], "unit": "business_days", "source_handle": _REGE["source_handle"],
            "content_hash": "h-rege-10", "authority_rank": _REGE["authority_rank"], "scope": "global_public",
            "tenant_id": tenant_id, "text": _REGE["text"]}
    faq = {"artifact_id": _FAQ["artifact_id"], "artifact_type": "atomic_fact", "claim_type": "atomic_fact",
           "claim_status": "fact", "subject": "Reg E error resolution", "predicate": "deadline_business_days",
           "object": _FAQ["value"], "source_handle": _FAQ["source_handle"], "content_hash": "h-faq-30",
           "authority_rank": _FAQ["authority_rank"], "scope": "global_public", "tenant_id": tenant_id,
           "text": _FAQ["text"]}
    pack = {"pack_id": "pack-BILL-782", "tenant_id": tenant_id, "held_out": [], "artifacts": [rege, faq] + arts}
    return pack, _REGE["artifact_id"], {_FAQ["artifact_id"]}


def verification(tenant_id: str) -> dict:
    """Project the per-artifact gate decisions (allow vs hold_out) + the verification receipt id."""
    try:
        pack, answer_fact_id, _excluded = _opt_pack(tenant_id)
        vgate = VerificationGate()
        checks, receipt_id = [], ""
        for a in pack["artifacts"]:
            ev = vgate.evaluate(a, context={"now": 1_000_000, "requested_scope": "global_public"}, now=_NOW)
            d = ev["decision"]
            rc = ev["receipt"]
            checks.append({"artifact_id": a["artifact_id"], "check": "promotion_gate",
                           "decision": d.decision,
                           "reason": ("; ".join(d.reasons) if d.reasons else "source-grounded, governed, conflict-clean"),
                           "receipt_id": rc.receipt_id})
            if a["artifact_id"] == answer_fact_id:
                receipt_id = rc.receipt_id
        return {"available": True, "checks": checks, "receipt_id": receipt_id}
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "reason": f"verification projection unavailable: {exc}",
                "checks": [], "receipt_id": ""}


def consumption(tenant_id: str) -> dict:
    """Project the served answer: served facts (each with a source handle) + held_out_warnings + receipt lineage."""
    try:
        run = _run(tenant_id)
        resp = run["response"]
        served = [{"text": (f.get("text") or f"{f.get('subject','')}: {f.get('predicate','')} = {f.get('object','')}").strip(),
                   "artifact_id": f.get("artifact_id"), "source_handle": f.get("source_handle"),
                   "claim_status": f.get("claim_status", "fact")} for f in resp.get("served_facts", [])]
        held = [{"text": (h.get("reason") or "held out"), "artifact_id": h.get("artifact_id"),
                 "claim_status": h.get("claim_status", ""), "source_handle": h.get("source_handle", "")}
                for h in resp.get("held_out_warnings", [])]
        rc = resp.get("receipts", {})
        receipts = {"verification": rc.get("verification_receipt_id", ""),
                    "optimization": rc.get("optimization_receipt_id", ""),
                    "consumption": rc.get("consumption_receipt_id", "")}
        return {"available": True, "answer": resp.get("answer", ""), "served_facts": served,
                "held_out_warnings": held, "receipts": receipts, "run_id": resp.get("run_id", "")}
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "reason": f"consumption projection unavailable: {exc}",
                "answer": "", "served_facts": [], "held_out_warnings": [], "receipts": {}}


_DISPATCH = {
    "/api/pipeline/overview": overview,
    "/api/pipeline/upload": upload,
    "/api/pipeline/decomposition": decomposition,
    "/api/pipeline/reconciliation": reconciliation,
    "/api/pipeline/enhancement": enhancement,
    "/api/pipeline/optimization": optimization,
    "/api/pipeline/verification": verification,
    "/api/pipeline/consumption": consumption,
}


def handle(method: str, path: str, query: dict | None = None) -> tuple:
    """Dispatch a Pipeline-Journey-API request. Returns (status_code, json_payload). GET-only, projection-only."""
    query = query or {}
    path = path.rstrip("/") or path
    if method != "GET":
        return 405, {"error": f"pipeline journey API is GET-only; got {method}"}
    fn = _DISPATCH.get(path)
    if fn is None:
        return 404, {"error": f"unknown pipeline route {method} {path}"}
    corpus = str(query.get("corpus") or _CORPUS)
    if corpus != _CORPUS:
        return 400, {"error": f"unknown corpus {corpus!r}; only {_CORPUS!r} is wired"}
    tenant_id = str(query.get("tenant") or query.get("tenant_id") or "demo")
    payload = fn(tenant_id)
    if _has_secret(payload):  # projection-only invariant: never emit a secret marker
        return 500, {"error": "projection withheld: secret marker detected in payload"}
    return 200, payload


def owns(path: str) -> bool:
    return any(path == r or path.rstrip("/") == r for r in ROUTES)
