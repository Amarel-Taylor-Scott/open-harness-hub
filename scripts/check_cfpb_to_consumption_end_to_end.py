#!/usr/bin/env python3
"""scripts.check_cfpb_to_consumption_end_to_end — THE forcing function (C-CONSUME-1): the full CFPB pipeline
runs INGESTION → decomposition → verify (C40) → optimize bake-off (C43) → consumption-readiness → a served
ContextResponse, with the reference result. If any upstream section weren't wired, this proof could not produce a
schema-valid served response that contains the right answer with full receipt lineage.

CLI: python3 scripts/check_cfpb_to_consumption_end_to_end.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.runtime.consumption import run_cfpb_to_consumption
from scripts.runtime.schema_validator import validate_ref

NOW = "2026-06-05T00:00:00Z"


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    r = run_cfpb_to_consumption("demo", require_optimized=True, now=NOW)
    resp = r["response"]

    check("the pipeline reaches a SERVED ContextResponse", r["decision"] == "served", str(r.get("readiness")))
    check("ContextResponse validates against ContextResponse", validate_ref(resp, "consumption/ContextResponse") == [],
          str(validate_ref(resp, "consumption/ContextResponse")[:3]))
    check("ConsumptionReceipt validates against ConsumptionReceipt", validate_ref(r["receipt"], "consumption/ConsumptionReceipt") == [])

    # reference answer
    check("answer contains '10 business days'", "10 business days" in resp["answer"], resp["answer"])
    served_ids = [f["artifact_id"] for f in resp["served_facts"]]
    held_ids = [h["artifact_id"] for h in resp["held_out_warnings"]]
    check("the Reg E 10-business-days fact is served", "fact-rege-10" in served_ids, str(served_ids))
    check("FAQ 30-days appears ONLY as a held-out warning (never served)",
          "fact-faq-30" in held_ids and "fact-faq-30" not in served_ids)
    check("no narrative allegation is served as fact",
          not any(f.get("claim_status") == "unverified_allegation" for f in resp["served_facts"])
          and any(h["artifact_id"].startswith("alleg-") for h in resp["held_out_warnings"]))

    # every served fact carries a source handle + full receipt lineage
    check("every served fact carries a source handle", all(f.get("source_handle") for f in resp["served_facts"]))
    check("every served fact carries verification + optimization lineage",
          all(f.get("verification_receipt_id") and f.get("optimization_receipt_id") for f in resp["served_facts"]))
    rc = resp["receipts"]
    check("response carries verification + optimization + consumption receipt ids",
          all(rc.get(k) for k in ("verification_receipt_id", "optimization_receipt_id", "consumption_receipt_id")))
    check("lineage records source artifacts + context pack + promotion id",
          bool(resp["lineage"].get("source_artifact_ids")) and resp["lineage"].get("context_pack_id") and resp["lineage"].get("promotion_id"))

    # the optimization bake-off actually ran multiple variants and rejected at least one
    check("optimization ran multiple candidate variants and rejected ≥1", 0 < r["promoted_count"] < r["candidate_count"],
          f"{r['promoted_count']}/{r['candidate_count']}")

    # deterministic
    r2 = run_cfpb_to_consumption("demo", require_optimized=True, now=NOW)
    check("the served response is deterministic (byte-identical)", resp == r2["response"])

    print(f"\n{'PASS — check_cfpb_to_consumption_end_to_end: CFPB ingestion→decomposition→verify→optimize→consumption-readiness→served ContextResponse; answer = 10 business days; FAQ-30 + allegations held out; full receipt lineage; deterministic.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: CFPB ingestion→consumption end to end.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
