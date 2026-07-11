#!/usr/bin/env python3
"""scripts.check_source_to_consumption_generic — proof (GENERIC SOURCE→CONSUMPTION): an arbitrary structured
source (generic_json) AND a tenant-private CSV table each walk the SAME engines as the CFPB reference domain
(normalize → verify → optimize bake-off → consumption-readiness → serve) to a schema-valid ContextResponse —
served facts carry source handles, narrative allegations are held out, NEVER served as truth. A PDF source whose
parser is a cataloged candidate returns consumable:false with a parser_unavailable reason (no fake response).
The whole motion is deterministic, and a tenant_private CSV stays tenant-scoped (no global leak).

If the generic path were CFPB-specific, or fabricated a response for an unparseable source, or leaked a private
source's handle into a global scope, this proof could not pass.

CLI: python3 _repos/shared-backend-components/scripts/check_source_to_consumption_generic.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.runtime.schema_validator import validate_ref
from scripts.runtime.source_consumption import run_source_to_consumption

NOW = "2026-06-05T00:00:00Z"


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # ── 1) GENERIC JSON (not CFPB): reaches a schema-valid served ContextResponse ──
    gj = run_source_to_consumption("json", {"deadline_days": 10, "product": "Credit card",
                                            "narrative": "They charged twice. No refund yet."},
                                   tenant_id="demo", source_id="gen-json-1", scope="global_public",
                                   authority="official", now=NOW)
    check("generic_json is consumable + served", gj["consumable"] and gj["decision"] == "served", str(gj["summary"]))
    resp = gj["response"]
    check("generic_json response validates against ContextResponse",
          validate_ref(resp, "consumption/ContextResponse") == [],
          str(validate_ref(resp, "consumption/ContextResponse")[:3]))
    check("generic_json served facts carry source handles", bool(resp["served_facts"]) and all(f.get("source_handle") for f in resp["served_facts"]))
    check("generic_json narrative allegation is held out, NEVER served",
          any(h["artifact_id"].startswith("narrative-") for h in resp["held_out_warnings"])
          and not any(f.get("claim_status") == "unverified_allegation" for f in resp["served_facts"]))
    check("generic_json served facts carry verification + optimization lineage",
          all(f.get("verification_receipt_id") and f.get("optimization_receipt_id") for f in resp["served_facts"]))

    # ── 2) CSV TABLE (tenant_private): served + tenant-scoped, no global leak ──
    cv = run_source_to_consumption("csv", "id,amount,note\n1,35,Unfair fee charged. No refund yet.\n",
                                   tenant_id="acme", source_id="export-1", scope="tenant_private",
                                   authority="customer_private", now=NOW)
    check("csv_table is consumable + served", cv["consumable"] and cv["decision"] == "served", str(cv["summary"]))
    cresp = cv["response"]
    check("csv_table response validates against ContextResponse",
          validate_ref(cresp, "consumption/ContextResponse") == [])
    check("csv_table response stays tenant-scoped (tenant_id=acme)", cresp["tenant_id"] == "acme")
    leaked = [f["source_handle"] for f in cresp["served_facts"] if "ctx://tenant/acme/" not in f["source_handle"]]
    check("csv_table served facts NEVER leak to a global/public handle (all tenant-scoped)", leaked == [], str(leaked))
    check("csv_table free-text note is held out, not served as fact",
          any("note" in h.get("source_handle", "") or h["artifact_id"].startswith("narrative-") for h in cresp["held_out_warnings"]))

    # ── 3) PDF (parser unavailable): consumable:false + parser_unavailable reason, NOT a fake ContextResponse ──
    pdf = run_source_to_consumption("pdf", "%PDF-1.4 fake bytes representing a regulatory PDF",
                                    tenant_id="demo", source_id="reg.pdf", scope="global_public",
                                    authority="official", now=NOW)
    check("pdf source returns consumable:false (never a fake response)",
          pdf["consumable"] is False and pdf["response"] is None)
    check("pdf non_consumable_reason is parser_unavailable", "parser_unavailable" in pdf["non_consumable_reason"], pdf["non_consumable_reason"])
    check("pdf still stores the raw source artifact (lineage preserved)", len(pdf["source_artifacts"]) == 1)
    check("pdf summary reports non_consumable status + 0 served facts",
          pdf["summary"]["consumption_status"] == "non_consumable" and pdf["summary"]["served_fact_count"] == 0)

    # ── 4) DETERMINISM: same source → byte-identical response + summary ──
    gj2 = run_source_to_consumption("json", {"deadline_days": 10, "product": "Credit card",
                                             "narrative": "They charged twice. No refund yet."},
                                    tenant_id="demo", source_id="gen-json-1", scope="global_public",
                                    authority="official", now=NOW)
    check("generic source→consumption is deterministic (byte-identical response + summary)",
          gj["response"] == gj2["response"] and gj["summary"] == gj2["summary"])

    print(f"\n{'PASS — check_source_to_consumption_generic: a generic JSON source and a tenant-private CSV each reach a schema-valid served ContextResponse (facts carry handles, allegations held out, lineage attached, tenant-scoped, no global leak); a PDF source returns consumable:false with a parser_unavailable reason (no fake response); deterministic.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: generic source→consumption + honest non-consumable boundary.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
