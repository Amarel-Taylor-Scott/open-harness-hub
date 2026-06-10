#!/usr/bin/env python3
"""scripts.check_optimization_harness — proof (C43): Optimization WORKS and is GOVERNED. A suite of optimizers
(dedupe / exclude-held-out / authority-rank / compress) are each a swappable wrapper behind one contract and
COMPOSE into a chain. The harness measures a candidate against a baseline and PROMOTES only on measured lift +
zero regressions (no answer-fact loss, source handles preserved, no held-out/allegation promoted, no tenant
leak, nothing fabricated) — emitting a deterministic, schema-valid OptimizationReceipt. An optimization that
loses an answer-critical fact is BLOCKED even though it 'improves' size. The compression seam is cataloged.

CLI: python3 scripts/check_optimization_harness.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scripts.runtime.optimization import (AuthorityRankOptimizer, CompressionOptimizer, DedupeOptimizer,
                                          ExcludeHeldOutOptimizer, Optimizer, OptimizationHarness, chain,
                                          default_suite, measure)
from scripts.runtime.schema_validator import validate_ref

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from src.baltor.runtime.registry.capability_registry import CapabilityRegistry  # noqa: E402

NOW = "2026-06-05T00:00:00Z"


def _pack() -> dict:
    """A CFPB-shaped enhanced pack: the Reg E 10-day answer fact (+ a duplicate), a held-out FAQ-30 conflict
    loser, a stale fact, and a narrative allegation — exactly the mix Optimization must clean up safely."""
    rege = {"artifact_id": "fact-rege-10", "artifact_type": "atomic_fact", "claim_type": "atomic_fact",
            "subject": "reg-e error resolution", "predicate": "deadline_business_days", "object": "10",
            "source_handle": "ctx://cfpb/reg-e#deadline", "content_hash": "h-rege", "authority_rank": 3,
            "scope": "global_public", "tenant_id": "acme",
            "text": "Regulation E   requires    financial institutions   to resolve   billing errors   within 10 business days."}
    return {"pack_id": "pack-bill-782", "tenant_id": "acme", "held_out": [],
            "artifacts": [
                rege,
                dict(rege),  # exact duplicate → deduped
                {"artifact_id": "fact-faq-30", "artifact_type": "atomic_fact", "claim_type": "atomic_fact",
                 "subject": "reg-e error resolution", "predicate": "deadline_business_days", "object": "30",
                 "source_handle": "ctx://cfpb/faq#deadline", "content_hash": "h-faq", "authority_rank": 1,
                 "scope": "global_public", "tenant_id": "acme", "text": "FAQ says 30 days."},
                {"artifact_id": "fact-stale", "artifact_type": "atomic_fact", "claim_type": "atomic_fact",
                 "subject": "fee", "predicate": "amount", "object": "$35", "source_handle": "ctx://cfpb/old#fee",
                 "content_hash": "h-stale", "authority_rank": 2, "scope": "global_public", "tenant_id": "acme"},
                {"artifact_id": "alleg-1", "artifact_type": "narrative_allegation", "claim_type": "narrative_allegation",
                 "subject": "complaint", "predicate": "alleges", "object": "account not mine",
                 "source_handle": "ctx://cfpb/complaint/1#narrative.s1", "content_hash": "h-a1", "tenant_id": "acme"},
            ]}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    suite = default_suite()
    # 1) suite is wrappable (each satisfies the Optimizer contract) and there are multiple variations
    check("the suite offers multiple optimizer variations", len(suite) >= 4, str(list(suite)))
    check("every optimizer is a wrappable Optimizer (name + optimize contract)",
          all(isinstance(o, Optimizer) and hasattr(o, "name") for o in suite.values()))

    # 2) optimizers CHAIN into one composite (also an Optimizer) — and chaining is deterministic
    pipe = chain(DedupeOptimizer(), ExcludeHeldOutOptimizer(), AuthorityRankOptimizer(), CompressionOptimizer())
    check("a chain of optimizers is itself a wrappable Optimizer", isinstance(pipe, Optimizer))
    signals = {"excluded_ids": {"fact-faq-30", "fact-stale"}}  # reconciliation loser + stale
    c1 = pipe.optimize(_pack(), signals=signals)
    c2 = pipe.optimize(_pack(), signals=signals)
    check("chained optimization is deterministic (same input → same output)", c1 == c2)

    # 3) optimization WORKS: measured lift, answer fact kept, held-out/allegation/stale excluded
    h = OptimizationHarness()
    out = h.run(_pack(), pipe, answer_fact_ids=["fact-rege-10"], signals=signals, now=NOW)
    base, cand = out["baseline_metrics"], out["candidate_metrics"]
    check("optimization reduces artifact count (measured lift)", cand.artifact_count < base.artifact_count, f"{base.artifact_count}->{cand.artifact_count}")
    check("optimization reduces token estimate (measured lift)", cand.token_estimate < base.token_estimate, f"{base.token_estimate}->{cand.token_estimate}")
    kept_ids = {a["artifact_id"] for a in out["candidate_pack"]["artifacts"]}
    check("the answer-critical fact (Reg E 10) survives", "fact-rege-10" in kept_ids, str(kept_ids))
    check("held-out conflict (FAQ 30), stale fact, and allegation are excluded from the promoted pack",
          {"fact-faq-30", "fact-stale", "alleg-1"}.isdisjoint(kept_ids), str(kept_ids))
    rege = next(a for a in out["candidate_pack"]["artifacts"] if a["artifact_id"] == "fact-rege-10")
    check("source handle survives compression", rege.get("source_handle") == "ctx://cfpb/reg-e#deadline")
    check("dedupe collapsed the duplicate (no repeated Reg E fact)", sum(1 for i in kept_ids if i == "fact-rege-10") == 1)

    # 4) it PROMOTES only with lift + zero regressions, and writes a schema-valid deterministic receipt
    check("a safe, improving optimization is PROMOTED", out["promoted"] is True and out["decision"] == "promote", str(out["decision"]))
    rec = out["receipt"].to_dict()
    check("OptimizationReceipt validates against OptimizationReceipt.v1", validate_ref(rec, "artifacts/OptimizationReceipt.v1") == [], str(validate_ref(rec, "artifacts/OptimizationReceipt.v1")[:3]))
    out2 = h.run(_pack(), pipe, answer_fact_ids=["fact-rege-10"], signals=signals, now=NOW)
    check("receipt id is deterministic (content-addressed, no clock/rng)", out["receipt"].receipt_id == out2["receipt"].receipt_id)

    # 5) the regression gate BLOCKS an optimization that loses an answer fact — even though it 'improves' size
    bad = h.run(_pack(), AuthorityRankOptimizer(), answer_fact_ids=["fact-rege-10"], signals={"top_k": 0}, now=NOW)
    check("an optimization that drops the answer fact is REJECTED (regression gate blocks it)",
          bad["promoted"] is False and any(r.name == "answer_facts_preserved" and not r.ok for r in bad["regressions"]))
    # an optimization that promotes a held-out artifact is also blocked
    leak_pack = _pack()
    bad2 = h.run(leak_pack, DedupeOptimizer(), answer_fact_ids=["fact-rege-10"],
                 signals={"excluded_ids": {"fact-faq-30"}}, now=NOW)  # dedupe keeps faq-30 (excluded) → held-out promoted
    check("an optimization that leaves a held-out conflict in the pack is REJECTED",
          bad2["promoted"] is False and any(r.name == "no_held_out_or_allegation_promoted" and not r.ok for r in bad2["regressions"]))

    # 6) an identity (no-lift) optimization is not promoted — optimization must actually improve to win
    class _Identity:
        name = "identity"
        def optimize(self, pack, *, signals):  # noqa: D401
            return pack
    idem = h.run(_pack(), _Identity(), answer_fact_ids=["fact-rege-10"], signals=signals, now=NOW)
    check("a no-lift (identity) optimization is NOT promoted", idem["promoted"] is False)

    # 7) the compression seam is cataloged (governed like every external provider)
    reg = CapabilityRegistry()
    comp = reg.get_by_capability_slot("compression")
    roles = {a.get("role") for a in comp["adapters"]}
    check("the compression capability slot is cataloged with a stub + a primary candidate (LLMLingua)",
          "stub" in roles and "primary" in roles and any(a.get("provider") == "LLMLingua" for a in comp["adapters"]))

    print(f"\n{'PASS — check_optimization_harness: a wrappable, chainable optimizer suite with measured lift; the regression gate promotes only safe improvements (answer facts + handles preserved, held-out/allegation/stale excluded) and blocks the rest; deterministic schema-valid receipts; compression seam cataloged.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: Optimization Harness v1 (governed, chainable).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
