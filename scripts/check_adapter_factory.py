#!/usr/bin/env python3
"""check_adapter_factory — the OpenAPI→Component factory (collapse N×M integrations to N+M).

Proves: from_openapi turns a whole spec into one typed component per operation (correct id/method/path, I/O types
inferred from the schema); the HTTP invoke is network-gated + honest offline (no fabricated response). serves_truth=false.

  python3 scripts/check_adapter_factory.py --self-test
"""
from __future__ import annotations

from src.teleon.components import adapter_factory as AF

_SPEC = {
    "openapi": "3.0.0",
    "servers": [{"url": "https://api.example.com"}],
    "paths": {
        "/search": {"get": {"operationId": "search_people", "parameters": [{"name": "q", "in": "query"}],
                            "responses": {"200": {"content": {"application/json": {"schema": {"type": "array"}}}}}}},
        "/enrich": {"post": {"operationId": "enrich_company", "requestBody": {"content": {"application/json": {"schema": {"type": "object"}}}},
                             "responses": {"200": {"content": {"application/json": {"schema": {"type": "object"}}}}}}},
    },
}


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    comps = AF.from_openapi(_SPEC)
    by_id = {c["component_id"]: c for c in comps}
    ck("a whole API spec -> one component per operation in ONE call (N×M -> N+M)", len(comps) == 2 and set(by_id) == {"search_people", "enrich_company"})
    ck("method + path + base_url captured", by_id["search_people"]["method"] == "GET" and by_id["enrich_company"]["path"] == "/enrich" and by_id["search_people"]["base_url"] == "https://api.example.com")
    ck("I/O types inferred from the schema (GET+params -> query->record; POST+body -> record->record)",
       by_id["search_people"]["consumes"] == ["query"] and by_id["enrich_company"]["consumes"] == ["record"] and by_id["enrich_company"]["produces"] == ["record"])
    ck("derived components are external (non-deterministic) by default", all(c["deterministic"] is False and c["source"] == "openapi" for c in comps))

    # the HTTP invoke is network-gated + honest offline (no fabricated response)
    res = AF.http_invoke(by_id["enrich_company"], {"domain": "acme.com"}, network_allowed=False)
    ck("HTTP invoke is HONESTLY unavailable offline (no fabricated API response)", res["available"] is False and "record" not in res)
    ck("serves_truth=false", all(c["serves_truth"] is False for c in comps) and res["serves_truth"] is False)

    print("\n" + ("PASS - check_adapter_factory: an OpenAPI spec becomes typed components in one call (N×M->N+M); "
                  "network-gated honest invoke." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
