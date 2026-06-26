#!/usr/bin/env python3
"""scripts.check_consumption_api — proof (C-CONSUME-1): POST /api/context/serve returns a schema-valid
ContextResponse from ConsumptionService with the CFPB reference result, and the route is registered. Tests the
pure request handler (no socket) so the contract is deterministic + offline.

CLI: python3 scripts/check_consumption_api.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.api_context_handler import handle
from scripts.runtime.schema_validator import validate_ref

_REPO = Path(__file__).resolve().parents[1]


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    code, resp = handle("POST", "/api/context/serve", {"tenant_id": "demo", "corpus": "cfpb", "require_optimized": True})
    check("POST /api/context/serve returns 200", code == 200, str(code))
    check("response is ContextResponse (schema-valid)", resp.get("schema_version") == "ContextResponse"
          and validate_ref(resp, "consumption/ContextResponse") == [], str(validate_ref(resp, "consumption/ContextResponse")[:3]))
    check("answer contains '10 business days'", "10 business days" in resp.get("answer", ""), resp.get("answer"))
    check("served_facts length > 0", len(resp.get("served_facts", [])) > 0)
    check("held_out_warnings length > 0", len(resp.get("held_out_warnings", [])) > 0)
    served_ids = [f["artifact_id"] for f in resp["served_facts"]]
    held_ids = [h["artifact_id"] for h in resp["held_out_warnings"]]
    check("FAQ-30 appears only in held_out_warnings", "fact-faq-30" in held_ids and "fact-faq-30" not in served_ids)
    check("every served fact has a source handle", all(f.get("source_handle") for f in resp["served_facts"]))
    check("every served fact has verification + optimization lineage",
          all(f.get("verification_receipt_id") and f.get("optimization_receipt_id") for f in resp["served_facts"]))
    rc = resp["receipts"]
    check("verification + optimization + consumption receipt ids present",
          all(rc.get(k) for k in ("verification_receipt_id", "optimization_receipt_id", "consumption_receipt_id")))
    check("no narrative allegation is served as fact",
          not any(f.get("claim_status") == "unverified_allegation" for f in resp["served_facts"]))

    # bad inputs fail cleanly (no crash)
    c2, p2 = handle("POST", "/api/context/serve", {"tenant_id": "demo", "corpus": "unknown"})
    check("unknown corpus returns 400 (not a crash)", c2 == 400 and "error" in p2)

    # the route is registered in the contract registry
    reg = json.loads((_REPO / "architecture" / "contract_registry.json").read_text())
    routes = {r["route"] for r in reg.get("api_routes", [])}
    check("POST /api/context/serve is registered in contract_registry.json", "POST /api/context/serve" in routes)

    print(f"\n{'PASS — check_consumption_api: POST /api/context/serve returns a schema-valid ContextResponse from ConsumptionService (answer 10 business days; FAQ-30 held out; handles + receipt lineage; no allegation served); route registered.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: consumption API serve.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
