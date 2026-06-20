#!/usr/bin/env python3
"""scripts.check_context_response_retrieval_api — proof (C-CONSUME-1): a served ContextResponse is retrievable
by id, its receipts are retrievable by id, missing ids return a clear 404 JSON, and no response leaks secrets
or private memory. Tests the pure handler offline.

CLI: python3 scripts/check_context_response_retrieval_api.py --self-test
"""
from __future__ import annotations

import argparse
import json

from scripts.api_context_handler import handle


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # serve, then retrieve
    _, resp = handle("POST", "/api/context/serve", {"tenant_id": "demo", "corpus": "cfpb"})
    rid = resp["response_id"]
    code, got = handle("GET", f"/api/context/responses/{rid}", None)
    check("GET /api/context/responses/<id> returns the same response", code == 200 and got.get("response_id") == rid)

    crid = resp["receipts"]["consumption_receipt_id"]
    c2, rec = handle("GET", f"/api/context/receipts/{crid}", None)
    check("GET /api/context/receipts/<id> returns the receipt", c2 == 200 and rec.get("receipt_id") == crid)
    # the verification + optimization receipts referenced by the response are also retrievable
    for k in ("verification_receipt_id", "optimization_receipt_id"):
        rk = resp["receipts"][k]
        ck, rr = handle("GET", f"/api/context/receipts/{rk}", None)
        check(f"receipt {k} is retrievable", ck == 200 and rr.get("receipt_id") == rk)

    # missing ids → clear 404 JSON
    c3, p3 = handle("GET", "/api/context/responses/nope", None)
    check("missing response id returns 404 JSON", c3 == 404 and "error" in p3)
    c4, p4 = handle("GET", "/api/context/receipts/nope", None)
    check("missing receipt id returns 404 JSON", c4 == 404 and "error" in p4)

    # no secrets / private memory in any payload
    blob = json.dumps([resp, got, rec])
    leaks = [m for m in ("OH_SHOWCASE_TOKEN", "sk-", "MEMORY.md", "/memory/", ".agent/") if m in blob]
    check("no secret/private-memory marker in API payloads", leaks == [], str(leaks))

    print(f"\n{'PASS — check_context_response_retrieval_api: responses + receipts retrievable by id; missing ids return clean 404 JSON; no secrets/private memory in responses.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: context response/receipt retrieval API.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
