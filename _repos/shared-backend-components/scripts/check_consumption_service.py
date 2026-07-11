#!/usr/bin/env python3
"""scripts.check_consumption_service — proof (C-CONSUME-1): the ConsumptionService serves ONLY consumable
packs, every served fact carries a source handle + receipt lineage, held-out artifacts appear only as
warnings, allegations are never served, and a non-consumable pack is REFUSED (no served facts). Also covers
ContextResponse schema failure cases (missing receipts / missing source handle on a served fact).

CLI: python3 _repos/shared-backend-components/scripts/check_consumption_service.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.runtime.consumption import ConsumptionService
from scripts.runtime.optimization import ConsumptionReadinessGate
from scripts.runtime.schema_validator import validate_ref

NOW = "2026-06-05T00:00:00Z"
VR = {"decision": "allow", "receipt_id": "vrcpt-x"}
OPT = {"decision": "promote", "receipt_id": "optrcpt-x"}


def _pack(extra=None) -> dict:
    arts = [{"artifact_id": "fact-1", "artifact_type": "atomic_fact", "claim_type": "atomic_fact", "claim_status": "fact",
             "subject": "s", "predicate": "p", "object": "10", "source_handle": "ctx://x#a", "content_hash": "h1",
             "scope": "global_public", "tenant_id": "demo"}]
    if extra:
        arts += extra
    return {"pack_id": "pack-1", "tenant_id": "demo", "artifacts": arts}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    svc = ConsumptionService()
    gate = ConsumptionReadinessGate()

    # consumable case: an allegation in the pack must NOT be served (truth-only), only the fact
    pack = _pack(extra=[{"artifact_id": "alleg-1", "artifact_type": "narrative_allegation", "claim_type": "narrative_allegation",
                         "claim_status": "unverified_allegation", "source_handle": "ctx://x#n", "content_hash": "h2", "tenant_id": "demo"}])
    rdy = gate.assess(pack, verification_receipt=VR, optimization_receipt=OPT, signals={"excluded_ids": set()}, now=NOW)
    # the allegation makes the pack non-consumable (held-out present) — so it must be excluded BEFORE serving
    pack_clean = _pack()
    rdy_clean = gate.assess(pack_clean, verification_receipt=VR, optimization_receipt=OPT, signals={"excluded_ids": set()}, now=NOW)
    out = svc.serve(tenant_id="demo", promoted_pack=pack_clean, verification_receipt=VR, optimization_receipt=OPT,
                    readiness_report=rdy_clean, held_out=[{"artifact_id": "fact-faq-30", "reason": "lower authority", "claim_status": "fact"}],
                    answer="10 business days", now=NOW)
    resp = out["response"].to_dict()
    check("a consumable pack is SERVED", out["decision"] == "served")
    check("ContextResponse validates", validate_ref(resp, "consumption/ContextResponse") == [], str(validate_ref(resp, "consumption/ContextResponse")[:3]))
    check("ConsumptionReceipt validates", validate_ref(out["receipt"].to_dict(), "consumption/ConsumptionReceipt") == [])
    check("every served fact has a source handle + verification + optimization lineage",
          all(f.get("source_handle") and f.get("verification_receipt_id") and f.get("optimization_receipt_id") for f in resp["served_facts"]))
    check("held-out artifacts appear only as warnings", [h["artifact_id"] for h in resp["held_out_warnings"]] == ["fact-faq-30"]
          and "fact-faq-30" not in [f["artifact_id"] for f in resp["served_facts"]])

    # allegations are never served even if present in the promoted pack
    out2 = svc.serve(tenant_id="demo", promoted_pack=pack, verification_receipt=VR, optimization_receipt=OPT,
                     readiness_report=rdy_clean, held_out=[], answer="10 business days", now=NOW)
    check("an allegation in the pack is NEVER served as a fact",
          not any(f["artifact_id"] == "alleg-1" for f in out2["response"].to_dict()["served_facts"]))

    # NON-consumable pack → refused, no served facts
    refused = svc.serve(tenant_id="demo", promoted_pack=pack_clean, verification_receipt=VR, optimization_receipt=OPT,
                        readiness_report=rdy, held_out=[], answer="10 business days", now=NOW)  # rdy = non-consumable (allegation present)
    rr = refused["response"].to_dict()
    check("a NON-consumable pack is REFUSED with NO served facts", refused["decision"] == "refused" and rr["served_facts"] == [] and rr["answer"] == "")

    # deterministic
    again = svc.serve(tenant_id="demo", promoted_pack=pack_clean, verification_receipt=VR, optimization_receipt=OPT,
                      readiness_report=rdy_clean, held_out=[{"artifact_id": "fact-faq-30", "reason": "lower authority", "claim_status": "fact"}],
                      answer="10 business days", now=NOW)
    check("serving is deterministic", resp == again["response"].to_dict())

    # schema failure cases
    bad_missing_receipt = dict(resp); bad_missing_receipt.pop("receipts")
    check("a ContextResponse missing receipts FAILS schema", validate_ref(bad_missing_receipt, "consumption/ContextResponse") != [])
    bad_handle = json_with_handleless(resp)
    check("a served fact missing a source handle FAILS schema", validate_ref(bad_handle, "consumption/ContextResponse") != [])

    print(f"\n{'PASS — check_consumption_service: serves only consumable packs (handles + receipt lineage on every served fact, held-out as warnings, allegations never served); refuses non-consumable packs; deterministic; schema enforced.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def json_with_handleless(resp: dict) -> dict:
    import copy
    bad = copy.deepcopy(resp)
    if bad["served_facts"]:
        bad["served_facts"][0].pop("source_handle", None)
    else:
        bad["served_facts"] = [{"artifact_id": "x", "claim_status": "fact"}]
    return bad


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: ConsumptionService.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
