#!/usr/bin/env python3
"""scripts.check_optimization_suite — proof (C43.1): Optimization is a generalized SUITE, not one optimizer.
A BaselineSnapshot is frozen; a CandidateGenerator produces MANY variants (dedupe / exclude-held-out /
authority-top-k / compression budgets / strict); the harness bakes them off against the SAME baseline and
promotes the best non-regressing candidate with a receipt; and a ConsumptionReadinessGate lets ONLY a verified
+ promoted + receipted + leak-free pack become consumable. Ties C40 (verify) → C43 (optimize) → consumption.

CLI: python3 scripts/check_optimization_suite.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scripts.runtime.optimization import (BaselineSnapshot, CandidateGenerator, ConsumptionReadinessGate,
                                          Optimizer, OptimizationHarness)
from scripts.runtime.schema_validator import validate_ref
from scripts.runtime.verification_gate import VerificationGate

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from src.baltor.runtime.registry.capability_registry import CapabilityRegistry  # noqa: E402

NOW = "2026-06-05T00:00:00Z"
EXCLUDED = {"fact-faq-30", "fact-stale"}  # reconciliation loser + stale (the gate/reconciler decided these)


def _pack() -> dict:
    rege = {"artifact_id": "fact-rege-10", "artifact_type": "atomic_fact", "claim_type": "atomic_fact",
            "subject": "reg-e error resolution", "predicate": "deadline_business_days", "object": "10",
            "source_handle": "ctx://cfpb/reg-e#deadline", "content_hash": "h-rege", "authority_rank": 3,
            "scope": "global_public", "tenant_id": "acme",
            "text": "Regulation E   requires   resolution   within 10 business days for billing errors."}
    return {"pack_id": "pack-bill-782", "tenant_id": "acme", "held_out": [],
            "artifacts": [rege, dict(rege),
                {"artifact_id": "fact-faq-30", "artifact_type": "atomic_fact", "claim_type": "atomic_fact",
                 "subject": "reg-e error resolution", "predicate": "deadline_business_days", "object": "30",
                 "source_handle": "ctx://cfpb/faq#deadline", "content_hash": "h-faq", "authority_rank": 1,
                 "scope": "global_public", "tenant_id": "acme", "text": "FAQ says 30 days."},
                {"artifact_id": "fact-stale", "artifact_type": "atomic_fact", "claim_type": "atomic_fact",
                 "subject": "fee", "predicate": "amount", "object": "$35", "source_handle": "ctx://cfpb/old#fee",
                 "content_hash": "h-stale", "authority_rank": 2, "scope": "global_public", "tenant_id": "acme"},
                {"artifact_id": "alleg-1", "artifact_type": "narrative_allegation", "claim_type": "narrative_allegation",
                 "subject": "complaint", "predicate": "alleges", "object": "not mine",
                 "source_handle": "ctx://cfpb/complaint/1#narrative.s1", "content_hash": "h-a1", "tenant_id": "acme"}]}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # baseline snapshot is frozen + deterministic
    snap = BaselineSnapshot.of(_pack(), answer_fact_ids=["fact-rege-10"])
    snap2 = BaselineSnapshot.of(_pack(), answer_fact_ids=["fact-rege-10"])
    check("baseline snapshot captures hash + pack id + answer + handle coverage",
          snap.snapshot_hash and snap.pack_id == "pack-bill-782" and snap.answer_fact_ids == ["fact-rege-10"])
    check("baseline snapshot is deterministic", snap.snapshot_hash == snap2.snapshot_hash)

    # MANY candidate variants are generated, each a chainable Optimizer
    gen = CandidateGenerator()
    cands = gen.generate(snap, excluded_ids=EXCLUDED)
    check("multiple candidate variants are generated", len(cands) >= 6, str(len(cands)))
    check("candidate ids are unique", len({c.candidate_id for c in cands}) == len(cands))
    check("every candidate is a chainable Optimizer", all(isinstance(c.optimizer, Optimizer) for c in cands))

    # bake-off: run all candidates vs the SAME baseline; promote the best non-regressing one
    h = OptimizationHarness()
    bake = h.optimize_many(_pack(), cands, answer_fact_ids=["fact-rege-10"], now=NOW)
    check("the bake-off ran every candidate", bake["candidate_count"] == len(cands))
    check("some candidates are promoted and some are rejected (regression gate filters)",
          0 < bake["promoted_count"] < bake["candidate_count"], f"{bake['promoted_count']}/{bake['candidate_count']}")
    best = bake["best"]
    check("a best candidate is selected", best is not None)
    kept = {a["artifact_id"] for a in best["candidate_pack"]["artifacts"]}
    check("best preserves the CFPB answer (Reg E 10 business days)", "fact-rege-10" in kept, str(kept))
    check("best excludes held-out FAQ-30, stale fact, and allegation", {"fact-faq-30", "fact-stale", "alleg-1"}.isdisjoint(kept))
    rege = next(a for a in best["candidate_pack"]["artifacts"] if a["artifact_id"] == "fact-rege-10")
    check("best preserves the source handle", rege.get("source_handle") == "ctx://cfpb/reg-e#deadline")
    check("best is the largest measured lift among promoted", best["lift"]["token_reduction"] == max(r["lift"]["token_reduction"] for r in bake["results"] if r["promoted"]))

    # end-to-end consumption readiness: verify (C40) → optimize/promote (C43) → consumable
    vgate = VerificationGate()
    vr = vgate.evaluate(rege, context={"now": 1_000_000, "requested_scope": "global_public"}, now=NOW)["receipt"].to_dict()
    check("the served answer fact is gate-verified (allow)", vr["decision"] == "allow")
    cgate = ConsumptionReadinessGate()
    rdy = cgate.assess(best["candidate_pack"], verification_receipt=vr, optimization_receipt=best["receipt"].to_dict(),
                       signals={"excluded_ids": EXCLUDED}, now=NOW)
    check("a verified + promoted + leak-free pack is CONSUMABLE", rdy.consumable is True, str(rdy.checks))
    check("ConsumptionReadinessReport validates against schema", validate_ref(rdy.to_dict(), "artifacts/ConsumptionReadinessReport.v1") == [], str(validate_ref(rdy.to_dict(), "artifacts/ConsumptionReadinessReport.v1")[:3]))
    rdy2 = cgate.assess(best["candidate_pack"], verification_receipt=vr, optimization_receipt=best["receipt"].to_dict(),
                        signals={"excluded_ids": EXCLUDED}, now=NOW)
    check("readiness report id is deterministic", rdy.report_id == rdy2.report_id)

    # consumption gate BLOCKS the unsafe cases
    unpromoted = cgate.assess(best["candidate_pack"], verification_receipt=vr,
                              optimization_receipt={"decision": "reject", "receipt_id": "optrcpt-x"}, signals={"excluded_ids": EXCLUDED}, now=NOW)
    check("an UNPROMOTED pack is NOT consumable", unpromoted.consumable is False)
    unverified = cgate.assess(best["candidate_pack"], verification_receipt={"decision": "hold_out", "receipt_id": "vrcpt-x"},
                              optimization_receipt=best["receipt"].to_dict(), signals={"excluded_ids": EXCLUDED}, now=NOW)
    check("an UNVERIFIED pack is NOT consumable", unverified.consumable is False)
    leaky = cgate.assess(_pack(), verification_receipt=vr, optimization_receipt={"decision": "promote", "receipt_id": "optrcpt-y"},
                         signals={"excluded_ids": EXCLUDED}, now=NOW)
    check("a pack still carrying held-out/allegation is NOT consumable", leaky.consumable is False
          and any(c["name"] == "no_held_out_or_conflict_served" and not c["ok"] for c in leaky.checks))

    # the external optimization/eval/tracking tools are cataloged as wrapped provider slots
    reg = CapabilityRegistry()
    want = {"prompt_optimization": "DSPy", "hyperparameter_optimization": "Optuna", "eval_runner": "promptfoo",
            "rag_evaluation": "Ragas", "experiment_tracking": "MLflow"}
    missing = []
    for slot, provider in want.items():
        try:
            s = reg.get_by_capability_slot(slot)
        except KeyError:
            missing.append(slot); continue
        roles = {a.get("role") for a in s["adapters"]}
        if not ("stub" in roles and any(a.get("provider") == provider for a in s["adapters"])):
            missing.append(f"{slot}:{provider}")
    check("DSPy/Optuna/promptfoo/Ragas/MLflow are cataloged as wrapped provider slots (stub + candidate)", missing == [], str(missing))

    print(f"\n{'PASS — check_optimization_suite: a baseline-snapshotted, multi-variant, bake-off optimization suite; best promoted with receipt; consumption-readiness gate admits only verified+promoted+leak-free packs; external optimizer/eval/tracker tools cataloged.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: generalized optimization suite + consumption readiness.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
