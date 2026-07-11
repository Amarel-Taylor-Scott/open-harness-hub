#!/usr/bin/env python3
"""scripts.check_consumption_blocks_bad_artifacts — proof (C-CONSUME-1): the consumption path REFUSES to serve
unsafe outputs. An unverified pack, an unpromoted optimization candidate, a pack still carrying an unresolved
conflict / held-out artifact, a served allegation, and a cross-tenant private artifact are each blocked — no
served facts, decision=refused, reasons recorded.

CLI: python3 _repos/shared-backend-components/scripts/check_consumption_blocks_bad_artifacts.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.runtime.consumption import ConsumptionService
from scripts.runtime.optimization import ConsumptionReadinessGate

NOW = "2026-06-05T00:00:00Z"
ALLOW = {"decision": "allow", "receipt_id": "vrcpt-x"}
PROMOTE = {"decision": "promote", "receipt_id": "optrcpt-x"}


def _fact(**o):
    base = {"artifact_id": "fact-1", "artifact_type": "atomic_fact", "claim_type": "atomic_fact", "claim_status": "fact",
            "subject": "s", "predicate": "p", "object": "10", "source_handle": "ctx://x#a", "content_hash": "h1",
            "scope": "global_public", "tenant_id": "demo"}
    base.update(o); return base


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    svc = ConsumptionService()
    gate = ConsumptionReadinessGate()

    def refused(pack, vr, opt, signals):
        rdy = gate.assess(pack, verification_receipt=vr, optimization_receipt=opt, signals=signals, now=NOW)
        out = svc.serve(tenant_id="demo", promoted_pack=pack, verification_receipt=vr, optimization_receipt=opt,
                        readiness_report=rdy, held_out=[], answer="10 business days", now=NOW)
        r = out["response"].to_dict()
        return out["decision"] == "refused" and r["served_facts"] == []

    good = {"pack_id": "p", "tenant_id": "demo", "artifacts": [_fact()]}
    # baseline: a clean, verified, promoted pack IS served (so the blocks below are meaningful)
    rdy_ok = gate.assess(good, verification_receipt=ALLOW, optimization_receipt=PROMOTE, signals={"excluded_ids": set()}, now=NOW)
    served = svc.serve(tenant_id="demo", promoted_pack=good, verification_receipt=ALLOW, optimization_receipt=PROMOTE,
                       readiness_report=rdy_ok, held_out=[], answer="10 business days", now=NOW)
    check("a clean verified+promoted pack IS served (control)", served["decision"] == "served")

    check("UNVERIFIED pack is blocked", refused(good, {"decision": "hold_out", "receipt_id": "v"}, PROMOTE, {"excluded_ids": set()}))
    check("UNPROMOTED optimization candidate is blocked", refused(good, ALLOW, {"decision": "reject", "receipt_id": "o"}, {"excluded_ids": set()}))
    check("a served narrative ALLEGATION is blocked",
          refused({"pack_id": "p", "tenant_id": "demo", "artifacts": [_fact(artifact_id="alleg-1", artifact_type="narrative_allegation", claim_type="narrative_allegation", claim_status="unverified_allegation")]},
                  ALLOW, PROMOTE, {"excluded_ids": set()}))
    check("an UNRESOLVED/held-out conflict left in the pack is blocked",
          refused({"pack_id": "p", "tenant_id": "demo", "artifacts": [_fact(), _fact(artifact_id="fact-faq-30", object="30")]},
                  ALLOW, PROMOTE, {"excluded_ids": {"fact-faq-30"}}))
    check("a CROSS-TENANT private artifact is blocked",
          refused({"pack_id": "p", "tenant_id": "demo", "artifacts": [_fact(), _fact(artifact_id="tp-1", tenant_id="other", scope="tenant_private")]},
                  ALLOW, PROMOTE, {"excluded_ids": set()}))

    print(f"\n{'PASS — check_consumption_blocks_bad_artifacts: unverified / unpromoted / allegation / unresolved-conflict / cross-tenant packs are all refused (no served facts); only a clean verified+promoted pack is served.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: consumption blocks bad artifacts.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
